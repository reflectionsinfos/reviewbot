"""
Autonomous Review API Routes
POST   /api/autonomous-reviews/          – start a new review job
GET    /api/autonomous-reviews/          – list all jobs (with optional project filter)
GET    /api/autonomous-reviews/{job_id}  – job status + results
GET    /api/autonomous-reviews/{job_id}/report – full report
DELETE /api/autonomous-reviews/{job_id}  – cancel / delete job
POST   /api/autonomous-reviews/{job_id}/results/{result_id}/override – override RAG status
GET    /api/autonomous-reviews/{job_id}/action-plan – generate action plan
POST   /api/autonomous-reviews/{job_id}/action-plan/enhance – LLM-enhance prompts
WS     /ws/autonomous-reviews/{job_id}   – real-time progress stream
"""
import os
from dataclasses import asdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import (
    AutonomousReviewJob, AutonomousReviewResult, AutonomousReviewOverride,
    Project, Checklist, ChecklistItem, User,
)
from app.api.routes.auth import get_current_user
from app.services.action_plan_generator import ActionPlanGenerator
from app.services.autonomous_review.orchestrator import run_autonomous_review
from app.services.autonomous_review.connectors.llm import (
    get_llm_client,
    pick_model,
    provider_is_configured,
)
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
    # Summary metrics (New)
    green_count: int = 0
    amber_count: int = 0
    red_count: int = 0
    skipped_count: int = 0
    na_count: int = 0
    compliance_score: float = 0.0


class OverrideRequest(BaseModel):
    """Request to override a review result"""
    new_rag_status: str  # green | amber | red | na
    comments: str
    reason: Optional[str] = None  # project_specific | not_applicable | alternative_approach | other


class OverrideResponse(BaseModel):
    """Response after override"""
    status: str
    message: str
    override_id: int
    new_rag_status: str


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
        # Summary metrics (New)
        "green_count": job.green_count or 0,
        "amber_count": job.amber_count or 0,
        "red_count": job.red_count or 0,
        "skipped_count": job.skipped_count or 0,
        "na_count": job.na_count or 0,
        "compliance_score": job.compliance_score or 0.0,
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

    # Validate source path: Local folder scanning is disabled for security/cloud-run.
    # Only allow repository-based scans (__repo__ marker).
    if not req.source_path.startswith("__repo__::"):
        raise HTTPException(
            400, 
            "Local folder scanning is deprecated. Please use the ReviewBot Agent to upload "
            "codebase metadata, or provide a Git Repository URL."
        )

    from app.services.autonomous_review.connectors.llm import validate_llm_connectivity
    
    # ── LLM Pre-flight check ──────────────────────────────
    is_ready, message = await validate_llm_connectivity(db)
    if not is_ready:
        raise HTTPException(status_code=400, detail=f"LLM not ready: {message}")

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


# ── POST /{job_id}/results/{result_id}/override — Override RAG status ─────────

@router.post(
    "/{job_id}/results/{result_id}/override",
    response_model=OverrideResponse,
    status_code=200,
)
async def override_review_result(
    job_id: int,
    result_id: int,
    override_data: OverrideRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication - for now accept any request
    # current_user: User = Depends(get_current_user),
):
    """
    Override the RAG status of a checklist item with human explanation.
    
    Use cases:
    - Project uses alternative approach not detected by AI
    - Checklist item not applicable to this project
    - Evidence exists but in non-standard location
    - Team has valid reason for deviation from standards
    
    The override creates an audit trail with:
    - Who overridden (will be added with authentication)
    - When overridden
    - Why overridden (reason + comments)
    - New RAG status
    """
    # Validate job exists
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    
    # Get the result
    result = await db.get(AutonomousReviewResult, result_id)
    if not result:
        raise HTTPException(404, f"Result {result_id} not found")
    
    # Verify result belongs to this job
    if result.job_id != job_id:
        raise HTTPException(400, f"Result {result_id} does not belong to job {job_id}")
    
    # Validate RAG status
    valid_statuses = ["green", "amber", "red", "na"]
    if override_data.new_rag_status not in valid_statuses:
        raise HTTPException(
            400, 
            f"Invalid RAG status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Create override record
    override = AutonomousReviewOverride(
        result_id=result_id,
        new_rag_status=override_data.new_rag_status,
        comments=override_data.comments,
        reason=override_data.reason,
        overridden_by=1,  # TODO: Replace with current_user.id when auth is added
        overridden_at=datetime.utcnow(),
    )
    
    db.add(override)
    await db.commit()
    await db.refresh(override)

    # RECALCULATE JOB SUMMARY (New)
    # ---------------------------
    # Load all results for this job with their overrides
    results_q = (
        select(AutonomousReviewResult)
        .where(AutonomousReviewResult.job_id == job_id)
        .options(selectinload(AutonomousReviewResult.overrides))
    )
    res_result = await db.execute(results_q)
    all_results = res_result.scalars().all()

    def get_status(r):
        if r.overrides:
            return sorted(r.overrides, key=lambda o: o.overridden_at)[-1].new_rag_status
        return r.rag_status

    # Status counts (Unified: green, amber, red, and "human required")
    green   = sum(1 for r in all_results if get_status(r) == "green")
    amber   = sum(1 for r in all_results if get_status(r) == "amber")
    red     = sum(1 for r in all_results if get_status(r) == "red")
    
    # "Human Required" includes skipped, na, and human_required
    skipped = sum(1 for r in all_results if get_status(r) in ("skipped", "na", "human_required"))
    na      = sum(1 for r in all_results if get_status(r) == "na")

    # Score calculation (based on automated items only)
    auto_total = green + amber + red
    score = round(green / auto_total * 100, 1) if auto_total else 0.0

    # Persistence
    job.green_count = green
    job.amber_count = amber
    job.red_count = red
    job.skipped_count = skipped
    job.na_count = na
    job.compliance_score = score
    await db.commit()
    
    return OverrideResponse(
        status="success",
        message="Override recorded and job summary updated",
        override_id=override.id,
        new_rag_status=override.new_rag_status,
    )


# ── GET /{job_id}/results/{result_id}/overrides — Get all overrides ──────────

@router.get("/{job_id}/results/{result_id}/overrides")
async def get_overrides(
    job_id: int,
    result_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all overrides for a specific result"""
    # Verify job exists
    job = await db.get(AutonomousReviewJob, job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    
    # Get overrides with user info
    query = (
        select(AutonomousReviewOverride)
        .where(AutonomousReviewOverride.result_id == result_id)
        .options(selectinload(AutonomousReviewOverride.user))
    )
    result = await db.execute(query)
    overrides = result.scalars().all()
    
    return {
        "result_id": result_id,
        "overrides": [
            {
                "override_id": o.id,
                "new_rag_status": o.new_rag_status,
                "comments": o.comments,
                "reason": o.reason,
                "overridden_by": o.user.full_name if o.user else "Unknown",
                "overridden_at": o.overridden_at.isoformat(),
            }
            for o in overrides
        ],
    }


# ── GET /{job_id}/action-plan — Generate action plan ────────────────────────

@router.get("/{job_id}/action-plan")
async def get_action_plan(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an action plan from autonomous review results."""
    job_result = await db.execute(
        select(AutonomousReviewJob)
        .options(
            selectinload(AutonomousReviewJob.checklist),
            selectinload(AutonomousReviewJob.project),
        )
        .where(AutonomousReviewJob.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Action plan can only be generated for completed jobs. Current status: {job.status}",
        )

    results_result = await db.execute(
        select(AutonomousReviewResult)
        .options(selectinload(AutonomousReviewResult.checklist_item))
        .where(AutonomousReviewResult.job_id == job_id)
        .order_by(AutonomousReviewResult.id)
    )
    results = results_result.scalars().all()

    checklist_items_result = await db.execute(
        select(ChecklistItem).where(ChecklistItem.checklist_id == job.checklist_id)
    )
    checklist_items_dict = {item.id: item for item in checklist_items_result.scalars().all()}

    if not job.project:
        raise HTTPException(status_code=404, detail="Project not found")

    checklist_name = job.checklist.name if job.checklist else "Unknown"

    generator = ActionPlanGenerator()
    stored_prompts = {}
    if isinstance(job.agent_metadata, dict):
        stored_prompts = job.agent_metadata.get("action_plan_prompts") or {}
    plan = generator.generate(
        job=job,
        results=results,
        checklist_items=checklist_items_dict,
        project=job.project,
        checklist_name=checklist_name,
        enhanced_prompts=stored_prompts,
    )

    return asdict(plan)


# ── POST /{job_id}/action-plan/enhance — LLM-enhance prompts ────────────────

@router.post("/{job_id}/action-plan/enhance")
async def enhance_action_plan(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enhance action plan prompts with LLM-generated codebase-specific context."""
    job_result = await db.execute(
        select(AutonomousReviewJob)
        .options(selectinload(AutonomousReviewJob.project))
        .where(AutonomousReviewJob.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Action plan can only be enhanced for completed jobs. Current status: {job.status}",
        )

    if job.agent_metadata and "action_plan_prompts" in job.agent_metadata:
        cached = job.agent_metadata.get("action_plan_prompts") or {}
        return {"status": "already_enhanced", "prompts_generated": len(cached)}

    results_result = await db.execute(
        select(AutonomousReviewResult)
        .options(selectinload(AutonomousReviewResult.checklist_item))
        .where(
            AutonomousReviewResult.job_id == job_id,
            AutonomousReviewResult.rag_status.in_(["red", "amber"]),
        )
    )
    results = results_result.scalars().all()

    if not results:
        return {"status": "enhanced", "prompts_generated": 0}

    if not await provider_is_configured(db):
        raise HTTPException(
            status_code=400,
            detail="No LLM provider configured. Set ACTIVE_LLM_PROVIDER and the corresponding API key, or configure one in the Admin UI.",
        )

    llm_client = await get_llm_client(db)
    generator = ActionPlanGenerator()

    enhanced_prompts: dict = {}
    prompts_generated = 0

    for result in results:
        item = result.checklist_item
        if not item:
            continue

        base_prompt = generator._build_prompt(result, item, job.project).generic
        enhancement_prompt = (
            "Improve the remediation prompt below so it becomes highly actionable for an engineer "
            "working in this exact repository.\n\n"
            "Requirements:\n"
            "- Reference concrete files, folders, or artifact types when the context supports it.\n"
            "- Tell the engineer whether to implement code, update configuration, add pipeline controls, "
            "or document an external/client-owned boundary.\n"
            "- Include repository-specific validation steps.\n"
            "- Keep it concise but specific.\n"
            "- Return only the upgraded prompt text, with no commentary.\n\n"
            f"{base_prompt}"
        )

        try:
            response = await llm_client.chat.completions.create(
                model=await pick_model(db),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior software engineer writing remediation prompts for AI coding tools. "
                            "Return only the final prompt text."
                        ),
                    },
                    {"role": "user", "content": enhancement_prompt},
                ],
                temperature=0.2,
                max_tokens=700,
            )
            enhanced_text = (response.choices[0].message.content or "").strip()
            if not enhanced_text:
                continue
            enhanced_prompts[str(result.id)] = {
                "generic": enhanced_text,
                "cursor": "@workspace\n"
                + enhanced_text
                + "\n\nSearch the workspace for the most relevant implementation points before making changes.",
                "claude_code": "Task:\n"
                + enhanced_text
                + "\n\nAfter making changes, run the relevant tests or verification commands and summarize the outcome.",
            }
            prompts_generated += 1
        except Exception:
            continue

    try:
        if job.agent_metadata is None:
            job.agent_metadata = {}
        job.agent_metadata["action_plan_prompts"] = enhanced_prompts
        await db.commit()
        return {"status": "enhanced", "prompts_generated": prompts_generated}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save enhanced prompts: {exc}")


# WebSocket endpoint is registered directly on the app in main.py
# to avoid prefix conflicts with the REST router.
# See: main.py  →  @app.websocket("/ws/autonomous-reviews/{job_id}")
