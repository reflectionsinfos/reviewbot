"""
Agent-mode Autonomous Review Orchestrator — Hybrid 3-Phase Routing

Phase 0: Deterministic pre-filter (in StrategyRouter._auto_route)
  - keyword/area rules classify ~25-35 items instantly, zero LLM calls
  - file_presence, pattern_scan, metadata_check, human_required resolved here

Phase 1: Planning LLM (one call before item loop)
  - sends file tree + project description + remaining llm_analysis items
  - returns per-item JSON plan: strategy, complexity (simple|complex), files_to_read
  - prefers local Ollama for planning (free, no rate limit)

Phase 2: Parallel-ish execution
  - deterministic items run immediately with no LLM
  - llm_analysis[simple]  → local Ollama (factual, 1-2 file checks)
  - llm_analysis[complex] → cloud LLM priority chain with 429 fallback
  - locked areas (Architecture, Security, Governance) always use cloud LLM
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from openai import RateLimitError, APIConnectionError, APITimeoutError, APIStatusError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import AutonomousReviewJob, AutonomousReviewResult, Checklist
from .connectors.agent_scan import AgentFileIndex
from .connectors.llm import (
    LLMChainExhaustedError,
    build_client,
    get_config_chain,
    get_local_client,
    get_planning_client,
)
from app.agents.strategy_router_agent import StrategyRouter, StrategyConfig
from .analyzers.file_presence import FilePresenceAnalyzer
from .analyzers.pattern_scan import PatternScanAnalyzer
from .analyzers.llm_analyzer import LLMAnalyzer
from .analyzers.metadata_check import MetadataCheckAnalyzer
from .analyzers.base import AnalysisResult
from .progress import progress_manager

logger = logging.getLogger(__name__)

_ANALYZERS = {
    "file_presence":  FilePresenceAnalyzer(),
    "pattern_scan":   PatternScanAnalyzer(),
    "llm_analysis":   LLMAnalyzer(),
    "metadata_check": MetadataCheckAnalyzer(),
}

# Areas that must always use the cloud LLM regardless of the planning decision.
# These require deep cross-file reasoning and domain expertise.
_CLOUD_LOCKED_AREAS = {
    "architecture", "architecture & design", "architecture and design",
    "security", "security architecture", "security design",
    "governance", "compliance & governance", "compliance",
    "sign-off", "approval",
}


# ── Planning data types ───────────────────────────────────────────────────────

@dataclass
class PlanEntry:
    strategy: str = "llm_analysis"
    complexity: str = "complex"          # "simple" | "complex"
    files: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    rationale: str = ""


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_agent_review(job_id: int) -> None:
    """Entry point called by BackgroundTask in the agent upload endpoint."""
    async with AsyncSessionLocal() as db:
        try:
            await _execute_agent_review(job_id, db)
        except Exception as exc:
            logger.exception("Agent review job %s crashed: %s", job_id, exc)
            try:
                async with AsyncSessionLocal() as db2:
                    job = await db2.get(AutonomousReviewJob, job_id)
                    if job:
                        job.status = "failed"
                        job.error_message = str(exc)
                        await db2.commit()
            except Exception:
                pass
            await progress_manager.broadcast(job_id, {"type": "error", "message": str(exc)})


async def _execute_agent_review(job_id: int, db) -> None:
    from app.api.routes.agent import add_file_request, get_file_content, count_file_content

    # ── Load job ──────────────────────────────────────────────────────────────
    result = await db.execute(
        select(AutonomousReviewJob)
        .where(AutonomousReviewJob.id == job_id)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist).selectinload(Checklist.items),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    job.status = "running"
    job.started_at = datetime.utcnow()
    await db.commit()

    # ── Build file index ──────────────────────────────────────────────────────
    metadata: dict = {"files": [], "total_size_mb": 0, "language_stats": {}}
    scan_data = (job.agent_metadata or {}).get("scan_result", {})
    if scan_data:
        metadata["files"] = scan_data.get("files", [])
        metadata["total_size_mb"] = scan_data.get("total_size_mb", 0)
        metadata["language_stats"] = scan_data.get("language_stats", {})

    class _ContentProxy:
        def get(self, key, default=None):
            return get_file_content(job_id, key) or default
        def __len__(self) -> int:
            return count_file_content(job_id)

    file_index = AgentFileIndex(metadata, _ContentProxy())
    fs = file_index.summary()

    await progress_manager.broadcast(job_id, {
        "type": "scan_complete",
        "total_files": fs["total_files"],
        "text_files": fs["text_files"],
        "extensions": fs["extensions"],
        "agent_mode": True,
    })

    # ── Prepare items + load LLM chain once ───────────────────────────────────
    items = sorted(job.checklist.items, key=lambda x: x.order)
    job.total_items = len(items)
    await db.commit()

    config_chain = await get_config_chain(db)

    await progress_manager.broadcast(job_id, {
        "type": "started",
        "job_id": job_id,
        "total_items": len(items),
        "project": job.project.name,
        "checklist": job.checklist.name,
        "mode": "agent_hybrid",
    })

    # ── Phase 0: Deterministic pre-filter (inside StrategyRouter._auto_route) ─
    router = StrategyRouter()
    phase0_results: dict[int, StrategyConfig] = {}   # item.id → StrategyConfig
    llm_items = []                                    # items that still need planning

    for item in items:
        cfg = router.route(item)
        if cfg.strategy == "llm_analysis":
            llm_items.append(item)
        else:
            phase0_results[item.id] = cfg

    logger.info(
        "Job %s — Phase 0: %d items classified deterministically, %d need planning",
        job_id, len(phase0_results), len(llm_items),
    )
    await progress_manager.broadcast(job_id, {
        "type": "phase0_complete",
        "deterministic_count": len(phase0_results),
        "llm_count": len(llm_items),
    })

    # ── Phase 1: Planning LLM (one call for remaining llm_analysis items) ─────
    routing_plan: dict[int, PlanEntry] = {}
    if llm_items:
        routing_plan = await _build_routing_plan(job, llm_items, file_index, config_chain)
        # Persist plan for audit / re-use
        try:
            job.routing_plan = {
                str(item_id): {
                    "strategy": e.strategy,
                    "complexity": e.complexity,
                    "files": e.files,
                    "rationale": e.rationale,
                }
                for item_id, e in routing_plan.items()
            }
            await db.commit()
        except Exception:
            pass  # routing_plan column may not exist pre-migration

    # ── Phase 2: Execute all items ────────────────────────────────────────────
    counters = {"green": 0, "amber": 0, "red": 0, "skipped": 0, "na": 0}

    for idx, item in enumerate(items):
        # Determine strategy from Phase 0 or Phase 1 plan
        if item.id in phase0_results:
            strategy_cfg = phase0_results[item.id]
            plan_entry = PlanEntry(strategy=strategy_cfg.strategy)
        else:
            plan_entry = routing_plan.get(item.id, PlanEntry())
            strategy_cfg = _plan_to_strategy_config(item, plan_entry)

        await progress_manager.broadcast(job_id, {
            "type": "item_start",
            "item_id": item.id,
            "item_code": item.item_code,
            "area": item.area,
            "question": item.question[:120],
            "strategy": strategy_cfg.strategy,
            "complexity": plan_entry.complexity if strategy_cfg.strategy == "llm_analysis" else None,
            "index": idx,
            "total": len(items),
        })

        analysis = await _execute_item(
            item, strategy_cfg, plan_entry, file_index,
            config_chain, job_id, get_file_content, add_file_request, db,
        )

        review_result = AutonomousReviewResult(
            job_id=job_id,
            checklist_item_id=item.id,
            strategy=strategy_cfg.strategy,
            rag_status=analysis.rag_status,
            evidence=analysis.evidence,
            confidence=analysis.confidence,
            files_checked=analysis.files_checked,
            skip_reason=analysis.skip_reason,
            evidence_hint=analysis.evidence_hint,
        )
        db.add(review_result)
        job.completed_items = idx + 1
        counters[analysis.rag_status] = counters.get(analysis.rag_status, 0) + 1
        await db.commit()

        await progress_manager.broadcast(job_id, {
            "type": "item_complete",
            "item_id": item.id,
            "item_code": item.item_code,
            "area": item.area,
            "question": item.question[:120],
            "rag_status": analysis.rag_status,
            "evidence": analysis.evidence[:300],
            "strategy": strategy_cfg.strategy,
            "files_checked": (analysis.files_checked or [])[:5],
            "evidence_hint": analysis.evidence_hint,
            "index": idx + 1,
            "total": len(items),
            "counters": dict(counters),
        })

    # ── Finalise ──────────────────────────────────────────────────────────────
    auto_total = counters["green"] + counters["amber"] + counters["red"]
    compliance = round(counters["green"] / auto_total * 100, 1) if auto_total else 0.0

    job.status = "completed"
    job.completed_at = datetime.utcnow()
    job.green_count = counters["green"]
    job.amber_count = counters["amber"]
    job.red_count = counters["red"]
    job.skipped_count = counters["skipped"]
    job.compliance_score = compliance
    await db.commit()

    await progress_manager.broadcast(job_id, {
        "type": "completed",
        "job_id": job_id,
        "mode": "agent_hybrid",
        "total_items": len(items),
        "deterministic_items": len(phase0_results),
        "planned_items": len(llm_items),
        "green": counters["green"],
        "amber": counters["amber"],
        "red": counters["red"],
        "skipped": counters["skipped"],
        "na": counters["na"],
        "compliance_score": compliance,
        "duration_seconds": (datetime.utcnow() - job.started_at).seconds if job.started_at else 0,
    })


# ── Phase 1: Planning LLM ─────────────────────────────────────────────────────

_PLANNING_PROMPT = """\
You are a technical review planner. Given a project's file structure and checklist \
items, assign the most efficient analysis strategy to each item.

PROJECT: {project_name}
DESCRIPTION: {description}
STACK: {stack}

FILE TREE (paths and sizes only — no file content):
{file_tree}

CHECKLIST ITEMS TO PLAN:
{items_json}

For each item output a JSON array entry in ONE of these shapes:

Pattern scan (no LLM needed — detectable by regex):
  {{"item_id": N, "strategy": "pattern_scan", "patterns": ["regex1"], \
"files_scope": ["*.py"], "rationale": "one line"}}

File presence (no LLM needed — check if file/dir exists):
  {{"item_id": N, "strategy": "file_presence", "file_patterns": ["Dockerfile"], \
"rationale": "one line"}}

LLM analysis — simple (factual, answerable from 1-2 specific files):
  {{"item_id": N, "strategy": "llm_analysis", "complexity": "simple", \
"files_to_read": ["src/auth.py"], "rationale": "one line"}}

LLM analysis — complex (cross-file reasoning, design/quality/security judgement):
  {{"item_id": N, "strategy": "llm_analysis", "complexity": "complex", \
"files_to_read": ["src/auth.py", "src/middleware.py"], "rationale": "one line"}}

Rules:
- Only reference files that exist exactly as listed in FILE TREE
- Prefer pattern_scan and file_presence over llm_analysis wherever possible
- Use complexity=complex for quality, architecture, security posture, design questions
- Use complexity=simple for presence/configuration/single-fact questions
- Output ONLY the JSON array, no other text, no markdown fences
"""


async def _build_routing_plan(
    job: AutonomousReviewJob,
    items: list,
    file_index: AgentFileIndex,
    config_chain: list,
) -> dict[int, PlanEntry]:
    """
    Phase 1: One LLM call → per-item routing plan.
    Uses local Ollama if available, otherwise lowest-priority cloud config.
    """
    fs = file_index.summary()
    file_tree = _format_file_tree(fs)
    stack = _detect_stack(fs.get("extensions", {}))
    item_list = [
        {"id": item.id, "area": item.area or "", "question": item.question or ""}
        for item in items
    ]
    prompt = _PLANNING_PROMPT.format(
        project_name=job.project.name if job.project else "Unknown",
        description=(job.project.description or "No description provided") if job.project else "",
        stack=stack,
        file_tree=file_tree,
        items_json=json.dumps(item_list, indent=2),
    )

    try:
        planning_client, planning_cfg = await get_planning_client(chain=config_chain)
        logger.info("Phase 1 planning using: %s (%s)", planning_cfg.name, planning_cfg.provider)

        response = await planning_client.chat.completions.create(
            model=planning_cfg.model_name,
            messages=[
                {"role": "system", "content": "You are a JSON-only technical review planner. Output only valid JSON arrays."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.0,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model wraps output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        plan_list = json.loads(raw)
        return _validate_plan(plan_list, items, file_index)

    except json.JSONDecodeError as exc:
        logger.warning("Phase 1 planning returned invalid JSON — all items default to complex llm_analysis: %s", exc)
        return {item.id: PlanEntry(strategy="llm_analysis", complexity="complex") for item in items}
    except LLMChainExhaustedError as exc:
        logger.warning("Phase 1 planning: no LLM available — all items default to complex llm_analysis: %s", exc)
        return {item.id: PlanEntry(strategy="llm_analysis", complexity="complex") for item in items}
    except Exception as exc:
        logger.warning("Phase 1 planning failed unexpectedly — all items default to complex llm_analysis", exc_info=True)
        return {item.id: PlanEntry(strategy="llm_analysis", complexity="complex") for item in items}


def _validate_plan(
    raw_plan: list,
    items: list,
    file_index: AgentFileIndex,
) -> dict[int, PlanEntry]:
    """Cross-check plan file paths against actual file index; fill missing items."""
    valid_paths = set(getattr(file_index, "_paths", {}).keys())
    item_ids = {i.id for i in items}
    result: dict[int, PlanEntry] = {}

    for entry in raw_plan:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("item_id")
        if item_id not in item_ids:
            continue

        files = entry.get("files_to_read") or entry.get("file_patterns") or []
        valid_files = [f for f in files if f in valid_paths or "*" in f]

        result[item_id] = PlanEntry(
            strategy=entry.get("strategy", "llm_analysis"),
            complexity=entry.get("complexity", "complex"),
            files=valid_files,
            patterns=entry.get("patterns", []),
            rationale=entry.get("rationale", ""),
        )

    # Items missing from plan → safe default
    for item in items:
        if item.id not in result:
            result[item.id] = PlanEntry(strategy="llm_analysis", complexity="complex")

    return result


# ── Phase 2: Item execution ───────────────────────────────────────────────────

def _effective_complexity(item, plan_entry: PlanEntry) -> str:
    """Override complexity to 'complex' for locked areas regardless of plan."""
    area = (item.area or "").lower()
    if any(locked in area for locked in _CLOUD_LOCKED_AREAS):
        return "complex"
    return plan_entry.complexity


def _plan_to_strategy_config(item, plan_entry: PlanEntry) -> StrategyConfig:
    """Convert a PlanEntry back to a StrategyConfig for the analyzer layer."""
    s = plan_entry.strategy
    keywords = (item.area or "").split() + (item.item_code or "").split("_")

    if s == "file_presence":
        return StrategyConfig(strategy="file_presence",
                              file_patterns=plan_entry.files,
                              context_keywords=keywords)
    if s == "pattern_scan":
        return StrategyConfig(strategy="pattern_scan",
                              scan_patterns=plan_entry.patterns,
                              context_keywords=keywords)
    if s == "metadata_check":
        return StrategyConfig(strategy="metadata_check",
                              context_keywords=keywords)
    return StrategyConfig(strategy="llm_analysis",
                          context_keywords=plan_entry.files or keywords,
                          focus_prompt=item.question or "")


async def _execute_item(
    item, strategy_cfg: StrategyConfig, plan_entry: PlanEntry,
    file_index, config_chain, job_id, get_file_content, add_file_request, db,
) -> AnalysisResult:
    """Execute one checklist item using the resolved strategy."""
    try:
        if strategy_cfg.strategy == "human_required":
            return _skipped(
                strategy_cfg.skip_reason or "Human review required",
                strategy_cfg.evidence_hint or "",
            )

        if strategy_cfg.strategy in ("file_presence", "metadata_check"):
            return await _ANALYZERS[strategy_cfg.strategy].analyze(item, file_index, strategy_cfg)

        if strategy_cfg.strategy == "pattern_scan":
            relevant = file_index.get_relevant_files(
                keywords=(item.area or "").split() + (item.item_code or "").split("_"),
                max_files=5,
            )
            has_content = any(get_file_content(job_id, p) is not None for p in relevant)
            if has_content:
                return await _ANALYZERS["pattern_scan"].analyze(item, file_index, strategy_cfg)
            for p in (relevant or [])[:3]:
                add_file_request(job_id, p, f"Required for pattern_scan on {item.item_code}")
            return _skipped("File content not yet uploaded for pattern_scan", "")

        # llm_analysis — Phase 2 complexity split
        complexity = _effective_complexity(item, plan_entry)
        return await _run_llm_item(item, strategy_cfg, plan_entry, complexity,
                                   file_index, config_chain, job_id,
                                   get_file_content, add_file_request, db)

    except Exception as exc:
        logger.warning("Analyzer failed for item %s: %s", item.item_code, exc, exc_info=True)
        return AnalysisResult(rag_status="na", evidence=f"Analyzer error: {type(exc).__name__}: {exc}", confidence=0.0)


async def _run_llm_item(
    item, strategy_cfg: StrategyConfig, plan_entry: PlanEntry, complexity: str,
    file_index, config_chain, job_id, get_file_content, add_file_request, db,
) -> AnalysisResult:
    """
    Run llm_analysis for one item.
    simple  → local Ollama preferred
    complex → cloud LLM with 429 fallback chain
    """
    relevant = file_index.get_relevant_files(
        keywords=strategy_cfg.context_keywords or
                 (item.area or "").split() + (item.item_code or "").split("_"),
        max_files=6,
    )
    # Use plan-specified files if valid
    if plan_entry.files:
        relevant = plan_entry.files[:6]

    has_content = any(get_file_content(job_id, p) is not None for p in relevant)
    if not has_content:
        for p in (relevant or [])[:3]:
            add_file_request(job_id, p, f"Required for llm_analysis on {item.item_code}")
        return _skipped("File content not yet uploaded for llm_analysis",
                        strategy_cfg.evidence_hint or "")

    tried_ids: set[int] = set()
    last_error = "No configs available"

    # Build candidate list based on complexity
    if complexity == "simple":
        candidates = [c for c in config_chain if c.provider == "ollama"]
        if not candidates:
            candidates = list(reversed(config_chain))  # lowest-priority cloud as fallback
    else:
        candidates = [c for c in config_chain if c.provider != "ollama"]
        if not candidates:
            candidates = list(config_chain)  # Ollama as last resort for complex too

    for cfg in candidates:
        if cfg.id in tried_ids:
            continue
        tried_ids.add(cfg.id)
        client = build_client(cfg)
        try:
            result = await _ANALYZERS["llm_analysis"].analyze(
                item, file_index, strategy_cfg, client=client, model=cfg.model_name,
            )
            logger.debug(
                "Item %s analysed by %s (%s, complexity=%s)",
                item.item_code, cfg.name, cfg.provider, complexity,
            )
            return result
        except RateLimitError as exc:
            logger.warning(
                "Rate limit on '%s' for item %s — trying next in chain",
                cfg.name, item.item_code,
            )
            last_error = f"Rate limit on {cfg.name}"
            continue
        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning("Network error on '%s' for item %s: %s", cfg.name, item.item_code, exc)
            last_error = f"Network error on {cfg.name}: {exc}"
            continue
        except APIStatusError as exc:
            if exc.status_code >= 500:
                # Server-side error — try next config
                logger.warning("Server error %d on '%s' for item %s", exc.status_code, cfg.name, item.item_code)
                last_error = f"Server error {exc.status_code} on {cfg.name}"
                continue
            # 4xx client errors (bad key, bad model name) — stop trying this config but log clearly
            logger.error("Client error %d on '%s' for item %s: %s", exc.status_code, cfg.name, item.item_code, exc)
            last_error = f"Client error {exc.status_code} on {cfg.name}"
            continue

    logger.error("All LLM configs exhausted for item %s: %s", item.item_code, last_error)
    return AnalysisResult(
        rag_status="na",
        evidence=f"All LLM providers exhausted: {last_error}",
        confidence=0.0,
    )


def _skipped(reason: str, hint: str = "") -> AnalysisResult:
    return AnalysisResult(
        rag_status="skipped",
        evidence=reason,
        confidence=1.0,
        files_checked=[],
        skip_reason=reason,
        evidence_hint=hint or None,
    )


# ── File tree helpers ─────────────────────────────────────────────────────────

def _format_file_tree(fs: dict) -> str:
    """Format the file index summary into a compact text tree for the planning prompt."""
    files = fs.get("files", [])
    if not files:
        return "(no files scanned)"
    lines = []
    for f in files[:150]:   # cap at 150 files to stay within planning LLM context
        name = f.get("path") or f.get("name") or str(f)
        size = f.get("size_bytes", 0)
        kb = f"{size // 1024}KB" if size >= 1024 else f"{size}B"
        lines.append(f"  {name} ({kb})")
    if len(files) > 150:
        lines.append(f"  ... and {len(files) - 150} more files")
    return "\n".join(lines)


def _detect_stack(extensions: dict) -> str:
    """Detect primary language/stack from file extension counts."""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".java": "Java", ".go": "Go", ".rb": "Ruby", ".cs": "C#",
        ".cpp": "C++", ".rs": "Rust", ".php": "PHP", ".kt": "Kotlin",
    }
    detected = []
    for ext, lang in ext_map.items():
        if extensions.get(ext, 0) > 0:
            detected.append(lang)
    return ", ".join(detected) if detected else "Unknown"
