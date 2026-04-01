"""
Agent API Bridge
Endpoints consumed by the reviewbot-agent CLI (pip package).

POST   /api/v1/agent/scan/upload                               – receive scan metadata, create job
GET    /api/v1/agent/scan/{job_id}                             – job status
GET    /api/v1/agent/scan/{job_id}/results                     – structured results
POST   /api/v1/agent/scan/{job_id}/results/{result_id}/override – override RAG status
POST   /api/v1/agent/scan/{job_id}/file-content               – agent uploads file content
GET    /api/v1/agent/scan/{job_id}/file-requests              – server lists files it needs
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models import (
    AutonomousReviewJob, AutonomousReviewResult, AutonomousReviewOverride,
    Project, Checklist, ChecklistItem, User,
    CodebaseSnapshot, SnapshotFile,
)
from app.services.autonomous_review.agent_orchestrator import run_agent_review

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AgentFileInfo(BaseModel):
    path: str
    size_bytes: int
    language: str
    hash: str
    line_count: int


class AgentScanResult(BaseModel):
    files: List[AgentFileInfo]
    total_size_mb: float
    language_stats: Dict[str, int]


class AgentInfo(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    os_platform: Optional[str] = None
    os_version: Optional[str] = None
    username: Optional[str] = None
    agent_version: Optional[str] = None


class ScanUploadRequest(BaseModel):
    project_id: int
    checklist_id: int
    scan_result: AgentScanResult
    source_path: str = "__agent_scan__"
    agent_info: Optional[AgentInfo] = None


class ScanUploadResponse(BaseModel):
    job_id: int
    status: str
    total_items: int
    message: str


class FileContentUpload(BaseModel):
    file_path: str
    content: str


class FileRequest(BaseModel):
    file_path: str
    reason: str


class AgentOverrideRequest(BaseModel):
    new_rag_status: str
    comments: str
    reason: Optional[str] = None


# ── Transient file-request queue (in-memory, upload window only) ──────────────
# Tracks which files the server needs from the agent before /start is called.
# Intentionally not persisted — this state only lives during the upload phase.
# key: job_id, value: list of {file_path, reason}
_file_requests: Dict[int, List[Dict[str, str]]] = {}


def add_file_request(job_id: int, file_path: str, reason: str) -> None:
    if job_id not in _file_requests:
        _file_requests[job_id] = []
    existing = [r["file_path"] for r in _file_requests[job_id]]
    if file_path not in existing:
        _file_requests[job_id].append({"file_path": file_path, "reason": reason})


def get_file_requests(job_id: int) -> List[Dict[str, str]]:
    return _file_requests.get(job_id, [])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=202, response_model=ScanUploadResponse)
async def upload_scan(
    body: ScanUploadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receive file-system metadata from the local reviewbot-agent CLI.
    Creates an AutonomousReviewJob and starts analysis in the background.
    Analysis uses file paths from the metadata (no file content required for
    file-presence and metadata-check items). Pattern-scan and LLM items are
    queued as file-content requests for the agent to fulfil.
    """
    # Validate project
    project = await db.get(Project, body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate checklist + ensure it has items
    checklist_result = await db.execute(
        select(Checklist)
        .where(Checklist.id == body.checklist_id)
        .options(selectinload(Checklist.items))
    )
    checklist = checklist_result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    if not checklist.items:
        raise HTTPException(status_code=400, detail="Checklist has no items")

    # Persist a CodebaseSnapshot with file metadata stubs (content=NULL until uploaded)
    snapshot = CodebaseSnapshot(
        project_id=body.project_id,
        source_path=body.source_path or "__agent_scan__",
        total_size_mb=body.scan_result.total_size_mb,
        language_stats=body.scan_result.language_stats,
        agent_metadata=body.agent_info.model_dump() if body.agent_info else None,
        created_by=current_user.id,
    )
    db.add(snapshot)
    await db.flush()  # get snapshot.id

    for f in body.scan_result.files:
        db.add(SnapshotFile(
            snapshot_id=snapshot.id,
            path=f.path,
            size_bytes=f.size_bytes,
            language=f.language,
            hash=f.hash,
            line_count=f.line_count,
        ))

    job = AutonomousReviewJob(
        project_id=body.project_id,
        checklist_id=body.checklist_id,
        source_path=body.source_path or "__agent_scan__",
        snapshot_id=snapshot.id,
        agent_metadata=body.agent_info.model_dump() if body.agent_info else None,
        status="queued",
        total_items=len(checklist.items),
        completed_items=0,
        created_by=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # NOTE: analysis does NOT start here — caller must POST /{job_id}/start
    # after uploading all required file content via POST /{job_id}/file-content.

    return ScanUploadResponse(
        job_id=job.id,
        status="queued",
        total_items=len(checklist.items),
        message=f"Snapshot {snapshot.id} created with {len(body.scan_result.files)} files. "
                f"Upload content then POST /{job.id}/start to begin analysis.",
    )


@router.post("/{job_id}/start", status_code=202)
async def start_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start analysis for a queued agent job.
    Call this after uploading all required file content via POST /{job_id}/file-content.
    """
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "queued":
        raise HTTPException(status_code=409, detail=f"Job is already {job.status}")

    background_tasks.add_task(run_agent_review, job_id)
    return {"job_id": job_id, "status": "started", "message": "Analysis started in background"}


@router.get("/{job_id}")
async def get_job_status(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return job status — poll this until status is 'completed' or 'failed'."""
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pct = 0.0
    if job.total_items:
        pct = round(job.completed_items / job.total_items * 100, 1)

    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "checklist_id": job.checklist_id,
        "snapshot_id": job.snapshot_id,
        "status": job.status,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "progress_pct": pct,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "pending_file_requests": len(get_file_requests(job_id)),
        "agent_metadata": job.agent_metadata,
    }


@router.get("/{job_id}/results")
async def get_job_results(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the full structured results once the job is complete."""
    result = await db.execute(
        select(AutonomousReviewJob)
        .where(AutonomousReviewJob.id == job_id)
        .options(
            selectinload(AutonomousReviewJob.results).selectinload(
                AutonomousReviewResult.checklist_item
            ),
            selectinload(AutonomousReviewJob.results).selectinload(
                AutonomousReviewResult.overrides
            ),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("completed", "failed"):
        raise HTTPException(status_code=409, detail=f"Job is still {job.status}")

    items = []
    counters = {"green": 0, "amber": 0, "red": 0, "skipped": 0, "na": 0}

    for r in job.results:
        # Effective RAG: use latest override if present
        effective_rag = r.rag_status
        if r.overrides:
            latest = sorted(r.overrides, key=lambda o: o.overridden_at)[-1]
            effective_rag = latest.new_rag_status

        counters[effective_rag] = counters.get(effective_rag, 0) + 1

        items.append({
            "result_id": r.id,
            "item_id": r.checklist_item_id,
            "item_code": r.checklist_item.item_code if r.checklist_item else None,
            "area": r.checklist_item.area if r.checklist_item else None,
            "question": r.checklist_item.question if r.checklist_item else None,
            "strategy": r.strategy,
            "rag_status": r.rag_status,
            "effective_rag_status": effective_rag,
            "evidence": r.evidence,
            "confidence": r.confidence,
            "files_checked": r.files_checked or [],
            "skip_reason": r.skip_reason,
            "evidence_hint": r.evidence_hint,
            "is_overridden": bool(r.overrides),
        })

    auto_total = counters["green"] + counters["amber"] + counters["red"]
    compliance = round(counters["green"] / auto_total * 100, 1) if auto_total else 0.0

    return {
        "job_id": job_id,
        "status": job.status,
        "compliance_score": compliance,
        "summary": counters,
        "items": items,
        "pending_file_requests": get_file_requests(job_id),
    }


@router.post("/{job_id}/results/{result_id}/override", status_code=201)
async def override_result(
    job_id: int,
    result_id: int,
    body: AgentOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Override the RAG status of a specific result (with full audit trail)."""
    valid_statuses = {"green", "amber", "red", "na"}
    if body.new_rag_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"new_rag_status must be one of: {', '.join(valid_statuses)}",
        )

    result_row = await db.get(AutonomousReviewResult, result_id)
    if not result_row or result_row.job_id != job_id:
        raise HTTPException(status_code=404, detail="Result not found")

    override = AutonomousReviewOverride(
        result_id=result_id,
        new_rag_status=body.new_rag_status,
        comments=body.comments,
        reason=body.reason,
        overridden_by=current_user.id,
        overridden_at=datetime.utcnow(),
    )
    db.add(override)
    await db.commit()
    await db.refresh(override)

    return {
        "status": "success",
        "message": f"Result {result_id} overridden to {body.new_rag_status}",
        "override_id": override.id,
        "new_rag_status": body.new_rag_status,
    }


@router.post("/{job_id}/file-content", status_code=202)
async def upload_file_content(
    job_id: int,
    body: FileContentUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Agent uploads the content of a specific file the server requested.
    After uploading, the server can re-analyse skipped LLM/pattern items.
    """
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.snapshot_id:
        raise HTTPException(status_code=400, detail="No snapshot associated with this job")

    file_result = await db.execute(
        select(SnapshotFile).where(
            SnapshotFile.snapshot_id == job.snapshot_id,
            SnapshotFile.path == body.file_path,
        )
    )
    file_row = file_result.scalar_one_or_none()
    if not file_row:
        raise HTTPException(status_code=404, detail=f"File '{body.file_path}' not found in snapshot")

    file_row.content = body.content
    await db.commit()

    # Remove from transient pending-request queue
    if job_id in _file_requests:
        _file_requests[job_id] = [
            r for r in _file_requests[job_id]
            if r["file_path"] != body.file_path
        ]

    return {
        "status": "stored",
        "file_path": body.file_path,
        "snapshot_id": job.snapshot_id,
        "size_chars": len(body.content),
        "pending_requests": len(get_file_requests(job_id)),
    }


@router.get("/{job_id}/file-requests")
async def list_file_requests(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Agent polls this to learn which files the server needs content for.
    Agent should then call POST /{job_id}/file-content for each.
    """
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "pending_requests": get_file_requests(job_id),
        "count": len(get_file_requests(job_id)),
    }
