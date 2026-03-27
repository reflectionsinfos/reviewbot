"""
Autonomous Review Orchestrator
Background task that drives the full review pipeline:
  scan → route → analyze (per item) → save → broadcast → report
"""
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import (
    AutonomousReviewJob, AutonomousReviewResult,
    ChecklistItem, Checklist, ChecklistRoutingRule,
)
from .connectors.local_folder import LocalFolderConnector
from .strategy_router import StrategyRouter, build_strategy_config_from_db
from .analyzers.file_presence import FilePresenceAnalyzer
from .analyzers.pattern_scan import PatternScanAnalyzer
from .analyzers.llm_analyzer import LLMAnalyzer
from .analyzers.metadata_check import MetadataCheckAnalyzer
from .analyzers.base import AnalysisResult
from .progress import progress_manager

logger = logging.getLogger(__name__)

_ANALYZERS = {
    "file_presence": FilePresenceAnalyzer(),
    "pattern_scan":  PatternScanAnalyzer(),
    "llm_analysis":  LLMAnalyzer(),
    "metadata_check": MetadataCheckAnalyzer(),
}


def _skipped_result(config) -> AnalysisResult:
    return AnalysisResult(
        rag_status="skipped",
        evidence=config.skip_reason or "Human review required",
        confidence=1.0,
        files_checked=[],
        skip_reason=config.skip_reason,
        evidence_hint=config.evidence_hint,
    )


async def run_autonomous_review(job_id: int) -> None:
    """
    Entry point for the background task.
    Creates its own DB session (safe for BackgroundTasks / Celery).
    """
    async with AsyncSessionLocal() as db:
        try:
            await _execute_review(job_id, db)
        except Exception as exc:
            logger.exception("Autonomous review job %s crashed: %s", job_id, exc)
            # Best-effort status update
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
                "type": "error",
                "message": str(exc),
            })


def _resolve_source_path(path: str) -> str:
    """
    Normalise source paths entered by users so common mistakes work:
      C:\\projects\\foo     → /host-projects/foo
      C:/projects/foo      → /host-projects/foo
      /projects/foo        → /host-projects/foo  (missing the 'host-' prefix)
    All other paths are returned as-is.
    """
    import re
    p = path.replace("\\", "/")
    # Windows drive letter: C:/projects/... or C:/anything/...
    m = re.match(r"^[A-Za-z]:/(.*)", p)
    if m:
        rest = m.group(1)
        # Map the top-level "projects" folder to the Docker mount point
        rest = re.sub(r"^projects/", "host-projects/", rest)
        return "/" + rest
    # /projects/... → /host-projects/...
    if p.startswith("/projects/"):
        return "/host-" + p[1:]
    return path


async def _execute_review(job_id: int, db) -> None:
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

    # ── Scan source folder ────────────────────────────────────────────────────
    source_path = _resolve_source_path(job.source_path)

    await progress_manager.broadcast(job_id, {
        "type": "scanning",
        "message": f"Scanning project folder: {source_path}",
    })

    connector = LocalFolderConnector(source_path)
    file_index = connector.scan()
    fs = file_index.summary()

    await progress_manager.broadcast(job_id, {
        "type": "scan_complete",
        "total_files": fs["total_files"],
        "text_files": fs["text_files"],
        "extensions": fs["extensions"],
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
    })

    # ── Load DB routing rules for this checklist ──────────────────────────────
    item_ids = [item.id for item in items]
    db_rules_result = await db.execute(
        select(ChecklistRoutingRule)
        .where(ChecklistRoutingRule.checklist_item_id.in_(item_ids))
        .where(ChecklistRoutingRule.is_active == True)
    )
    db_rules = {
        rule.checklist_item_id: build_strategy_config_from_db(rule)
        for rule in db_rules_result.scalars().all()
    }

    router = StrategyRouter(db_rules=db_rules)
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
                analysis = _skipped_result(strategy_cfg)
            else:
                analyzer = _ANALYZERS[strategy_cfg.strategy]
                analysis = await analyzer.analyze(item, file_index, strategy_cfg)
        except Exception as exc:
            logger.warning("Analyzer failed for item %s: %s", item.item_code, exc)
            analysis = AnalysisResult(
                rag_status="na",
                evidence=f"Analyzer error: {exc}",
                confidence=0.0,
            )

        # Save result
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
            "files_checked": analysis.files_checked[:5],
            "evidence_hint": analysis.evidence_hint,
            "index": idx + 1,
            "total": len(items),
            "counters": dict(counters),
        })

    # ── Finalise ──────────────────────────────────────────────────────────────
    job.status = "completed"
    job.completed_at = datetime.utcnow()
    await db.commit()

    auto_total = counters["green"] + counters["amber"] + counters["red"]
    compliance = round(counters["green"] / auto_total * 100, 1) if auto_total else 0.0

    await progress_manager.broadcast(job_id, {
        "type": "completed",
        "job_id": job_id,
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
