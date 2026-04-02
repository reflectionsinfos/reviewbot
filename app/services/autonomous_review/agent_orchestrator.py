"""
Agent-mode Autonomous Review Orchestrator
Like orchestrator.py but uses AgentFileIndex built from uploaded metadata
instead of a LocalFolderConnector that reads the local filesystem.

Pattern-scan and LLM items that need file content are queued as file
requests; once the agent uploads those files they can be re-analysed.
"""
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import (
    AutonomousReviewJob, AutonomousReviewResult,
    ChecklistItem, Checklist,
)
from .connectors.agent_scan import AgentFileIndex
from app.agents.strategy_router_agent import StrategyRouter
from .analyzers.file_presence import FilePresenceAnalyzer
from .analyzers.pattern_scan import PatternScanAnalyzer
from .analyzers.llm_analyzer import LLMAnalyzer
from .analyzers.metadata_check import MetadataCheckAnalyzer
from .analyzers.base import AnalysisResult
from .progress import progress_manager

logger = logging.getLogger(__name__)

# Strategies that work well on metadata alone
_METADATA_CAPABLE = {"file_presence", "metadata_check"}

# Strategies that need actual file content
_CONTENT_REQUIRED = {"pattern_scan", "llm_analysis"}

_ANALYZERS = {
    "file_presence": FilePresenceAnalyzer(),
    "pattern_scan":  PatternScanAnalyzer(),
    "llm_analysis":  LLMAnalyzer(),
    "metadata_check": MetadataCheckAnalyzer(),
}


def _skipped(reason: str, hint: str = "") -> AnalysisResult:
    return AnalysisResult(
        rag_status="skipped",
        evidence=reason,
        confidence=1.0,
        files_checked=[],
        skip_reason=reason,
        evidence_hint=hint or None,
    )


async def run_agent_review(job_id: int) -> None:
    """Entry point called by the BackgroundTask in the agent upload endpoint."""
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
            await progress_manager.broadcast(job_id, {
                "type": "error", "message": str(exc),
            })


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

    # ── Load file metadata from job.agent_metadata, content from in-memory cache ─
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

    # ── Prepare items ─────────────────────────────────────────────────────────
    items = sorted(job.checklist.items, key=lambda x: x.order)
    job.total_items = len(items)
    await db.commit()

    await progress_manager.broadcast(job_id, {
        "type": "started",
        "job_id": job_id,
        "total_items": len(items),
        "project": job.project.name,
        "checklist": job.checklist.name,
        "mode": "agent",
    })

    router = StrategyRouter()
    counters = {"green": 0, "amber": 0, "red": 0, "skipped": 0, "na": 0}

    # ── Process each item ─────────────────────────────────────────────────────
    for idx, item in enumerate(items):
        strategy_cfg = router.route(item)

        await progress_manager.broadcast(job_id, {
            "type": "item_start",
            "item_id": item.id,
            "item_code": item.item_code,
            "area": item.area,
            "question": item.question[:120],
            "strategy": strategy_cfg.strategy,
            "index": idx,
            "total": len(items),
        })

        try:
            if strategy_cfg.strategy == "human_required":
                analysis = _skipped(
                    strategy_cfg.skip_reason or "Human review required",
                    strategy_cfg.evidence_hint or "",
                )

            elif strategy_cfg.strategy in _CONTENT_REQUIRED:
                # Check if any relevant file content has been uploaded
                relevant = file_index.get_relevant_files(
                    keywords=(item.area or "").split() + (item.item_code or "").split("_"),
                    max_files=5,
                )
                has_content = any(
                    get_file_content(job_id, p) is not None for p in relevant
                )

                if has_content:
                    # Run the full analyzer with whatever content we have
                    analyzer = _ANALYZERS[strategy_cfg.strategy]
                    analysis = await analyzer.analyze(item, file_index, strategy_cfg)
                else:
                    # Queue file requests and skip for now
                    hint = (
                        strategy_cfg.evidence_hint
                        or f"Upload file content to enable {strategy_cfg.strategy} analysis"
                    )
                    for p in (relevant or [])[:3]:
                        add_file_request(
                            job_id, p,
                            f"Required for {strategy_cfg.strategy} on item {item.item_code}",
                        )
                    analysis = _skipped(
                        f"agent_mode: file content not yet uploaded for {strategy_cfg.strategy}",
                        hint,
                    )

            else:
                # file_presence, metadata_check — work entirely from paths
                analyzer = _ANALYZERS[strategy_cfg.strategy]
                analysis = await analyzer.analyze(item, file_index, strategy_cfg)

        except Exception as exc:
            logger.warning("Analyzer failed for item %s: %s", item.item_code, exc)
            analysis = AnalysisResult(
                rag_status="na",
                evidence=f"Analyzer error: {exc}",
                confidence=0.0,
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
        "mode": "agent",
        "total_items": len(items),
        "green": counters["green"],
        "amber": counters["amber"],
        "red": counters["red"],
        "skipped": counters["skipped"],
        "na": counters["na"],
        "compliance_score": compliance,
        "duration_seconds": (
            datetime.utcnow() - job.started_at
        ).seconds if job.started_at else 0,
    })
