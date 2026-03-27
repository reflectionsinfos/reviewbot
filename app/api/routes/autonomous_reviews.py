"""
Autonomous Review API Routes
POST   /api/autonomous-reviews/          – start a new review job
GET    /api/autonomous-reviews/          – list all jobs (with optional project filter)
GET    /api/autonomous-reviews/{job_id}  – job status + results
GET    /api/autonomous-reviews/{job_id}/report – full report
DELETE /api/autonomous-reviews/{job_id}  – cancel / delete job
WS     /ws/autonomous-reviews/{job_id}   – real-time progress stream
"""
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import (
    AutonomousReviewJob, AutonomousReviewResult,
    Project, Checklist, ChecklistItem,
)
from app.services.autonomous_review.orchestrator import run_autonomous_review
from app.services.autonomous_review.progress import progress_manager

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class StartReviewRequest(BaseModel):
    project_id: int
    checklist_id: int
    source_path: str


class JobStatusResponse(BaseModel):
    job_id: int
    project_id: int
    checklist_id: int
    source_path: str
    status: str
    total_items: int
    completed_items: int
    progress_pct: float
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def _job_to_status(job: AutonomousReviewJob) -> dict:
    pct = 0.0
    if job.total_items and job.total_items > 0:
        pct = round(job.completed_items / job.total_items * 100, 1)
    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "checklist_id": job.checklist_id,
        "source_path": job.source_path,
        "status": job.status,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "progress_pct": pct,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat(),
    }


# ── POST /  — Start a new autonomous review ───────────────────────────────────

@router.post("/", status_code=202)
async def start_autonomous_review(
    req: StartReviewRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start an autonomous review for a project checklist against a local folder.
    Returns immediately with job_id; subscribe to WS for live progress.
    """
    # Validate project
    project = await db.get(Project, req.project_id)
    if not project:
        raise HTTPException(404, f"Project {req.project_id} not found")

    # Validate checklist
    checklist = await db.get(Checklist, req.checklist_id,
                             options=[selectinload(Checklist.items)])
    if not checklist:
        raise HTTPException(404, f"Checklist {req.checklist_id} not found")
    if not checklist.items:
        raise HTTPException(400, "Checklist has no items to review")

    # Validate source path
    if not os.path.exists(req.source_path):
        raise HTTPException(400, f"Source path does not exist: {req.source_path}")
    if not os.path.isdir(req.source_path):
        raise HTTPException(400, f"Source path is not a directory: {req.source_path}")

    # Create job
    job = AutonomousReviewJob(
        project_id=req.project_id,
        checklist_id=req.checklist_id,
        source_path=req.source_path,
        status="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Kick off background task
    background_tasks.add_task(run_autonomous_review, job.id)

    return {
        "job_id": job.id,
        "status": "queued",
        "message": f"Autonomous review started. Connect to WS /ws/autonomous-reviews/{job.id} for live progress.",
        "total_checklist_items": len(checklist.items),
        "project": project.name,
        "checklist": checklist.name,
    }


# ── GET /  — List all jobs ────────────────────────────────────────────────────

@router.get("/")
async def list_jobs(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List autonomous review jobs, optionally filtered by project."""
    q = select(AutonomousReviewJob).order_by(AutonomousReviewJob.created_at.desc())
    if project_id:
        q = q.where(AutonomousReviewJob.project_id == project_id)
    result = await db.execute(q)
    jobs = result.scalars().all()
    return [_job_to_status(j) for j in jobs]


# ── GET /{job_id}  — Job status + all results ─────────────────────────────────

@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get job status and all per-item results."""
    result = await db.execute(
        select(AutonomousReviewJob)
        .where(AutonomousReviewJob.id == job_id)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist),
            selectinload(AutonomousReviewJob.results)
            .selectinload(AutonomousReviewResult.checklist_item),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    item_results = []
    for r in sorted(job.results, key=lambda x: x.checklist_item.order if x.checklist_item else 0):
        ci = r.checklist_item
        item_results.append({
            "result_id": r.id,
            "item_id": ci.id if ci else None,
            "item_code": ci.item_code if ci else None,
            "area": ci.area if ci else None,
            "question": ci.question if ci else None,
            "strategy": r.strategy,
            "rag_status": r.rag_status,
            "evidence": r.evidence,
            "confidence": r.confidence,
            "files_checked": r.files_checked,
            "skip_reason": r.skip_reason,
            "evidence_hint": r.evidence_hint,
        })

    status_data = _job_to_status(job)
    status_data["project_name"] = job.project.name if job.project else None
    status_data["checklist_name"] = job.checklist.name if job.checklist else None
    status_data["results"] = item_results

    return status_data


# ── GET /{job_id}/report  — Structured final report ──────────────────────────

@router.get("/{job_id}/report")
async def get_report(job_id: int, db: AsyncSession = Depends(get_db)):
    """Return a structured final report for a completed job."""
    result = await db.execute(
        select(AutonomousReviewJob)
        .where(AutonomousReviewJob.id == job_id)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist),
            selectinload(AutonomousReviewJob.results)
            .selectinload(AutonomousReviewResult.checklist_item),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status not in ("completed", "failed"):
        raise HTTPException(400, f"Job is still {job.status} — report not ready yet")

    red, amber, green, skipped, na = [], [], [], [], []
    for r in sorted(job.results, key=lambda x: x.checklist_item.order if x.checklist_item else 0):
        ci = r.checklist_item
        entry = {
            "item_code": ci.item_code if ci else "?",
            "area": ci.area if ci else "Unknown",
            "question": ci.question if ci else "",
            "strategy": r.strategy,
            "evidence": r.evidence,
            "confidence": r.confidence,
            "files_checked": r.files_checked,
            "evidence_hint": r.evidence_hint,
        }
        if r.rag_status == "red":
            red.append(entry)
        elif r.rag_status == "amber":
            amber.append(entry)
        elif r.rag_status == "green":
            green.append(entry)
        elif r.rag_status == "skipped":
            skipped.append(entry)
        else:
            na.append(entry)

    auto_total = len(red) + len(amber) + len(green)
    compliance = round(len(green) / auto_total * 100, 1) if auto_total else 0.0
    overall_rag = (
        "green" if compliance >= 75 else
        "amber" if compliance >= 50 else
        "red"
    )

    return {
        "job_id": job_id,
        "project": job.project.name if job.project else None,
        "checklist": job.checklist.name if job.checklist else None,
        "source_path": job.source_path,
        "reviewed_at": job.completed_at.isoformat() if job.completed_at else None,
        "summary": {
            "total_items": job.total_items,
            "auto_reviewed": auto_total,
            "human_required": len(skipped),
            "na": len(na),
            "green": len(green),
            "amber": len(amber),
            "red": len(red),
            "compliance_score": compliance,
            "overall_rag": overall_rag,
        },
        "red_items": red,
        "amber_items": amber,
        "green_items": green,
        "human_required_items": skipped,
        "na_items": na,
        "recommendations": _generate_recommendations(red, amber, skipped),
    }


def _generate_recommendations(red: list, amber: list, skipped: list) -> list[dict]:
    recs = []
    for item in red[:10]:
        recs.append({
            "priority": "HIGH",
            "area": item["area"],
            "item_code": item["item_code"],
            "recommendation": f"Address failing check: {item['question'][:100]}",
            "evidence": item["evidence"][:200],
        })
    for item in amber[:5]:
        recs.append({
            "priority": "MEDIUM",
            "area": item["area"],
            "item_code": item["item_code"],
            "recommendation": f"Improve: {item['question'][:100]}",
            "evidence": item["evidence"][:200],
        })
    if skipped:
        recs.append({
            "priority": "INFO",
            "area": "Human Review Required",
            "item_code": "—",
            "recommendation": f"{len(skipped)} items require manual evidence from the team",
            "evidence": "See human_required_items section for details",
        })
    return recs


# ── DELETE /{job_id}  — Cancel / delete job ───────────────────────────────────

@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status == "running":
        # Mark as cancelled (the background task will hit a failure on next DB commit)
        job.status = "cancelled"
        await db.commit()
    else:
        await db.delete(job)
        await db.commit()


# WebSocket endpoint is registered directly on the app in main.py
# to avoid prefix conflicts with the REST router.
# See: main.py  →  @app.websocket("/ws/autonomous-reviews/{job_id}")
