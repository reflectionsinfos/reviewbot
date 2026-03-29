"""
Reports API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from app.db.session import get_db
from app.models import (
    Report, ReportApproval, Review, User,
    Project, Checklist, AutonomousReviewJob,
    AutonomousReviewResult, ChecklistItem, AutonomousReviewOverride,
)
from app.core.config import settings
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_reports(
    project_id: Optional[int] = None,
    approval_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all reports"""
    query = select(Report).join(Review).options(
        selectinload(Report.review).selectinload(Review.project)
    )

    if project_id:
        query = query.where(Review.project_id == project_id)
    if approval_status:
        query = query.where(Report.approval_status == approval_status)

    query = query.order_by(Report.created_at.desc())

    result = await db.execute(query)
    reports = result.scalars().all()
    
    return {
        "reports": [
            {
                "id": r.id,
                "review_id": r.review_id,
                "project_name": r.review.project.name if r.review else "Unknown",
                "overall_rag_status": r.overall_rag_status,
                "compliance_score": r.compliance_score,
                "approval_status": r.approval_status,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ]
    }


@router.get("/history")
async def get_report_history(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List autonomous review job history for the Report History page"""
    query = (
        select(AutonomousReviewJob)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist),
            selectinload(AutonomousReviewJob.results).selectinload(
                AutonomousReviewResult.overrides
            ),
        )
        .order_by(AutonomousReviewJob.created_at.desc())
    )
    if project_id:
        query = query.where(AutonomousReviewJob.project_id == project_id)

    result = await db.execute(query)
    jobs = result.scalars().all()

    def eff(r) -> str:
        if r.overrides:
            return sorted(r.overrides, key=lambda o: o.overridden_at)[-1].new_rag_status
        return r.rag_status

    reports = []
    for job in jobs:
        green  = sum(1 for r in job.results if eff(r) == "green")
        amber  = sum(1 for r in job.results if eff(r) == "amber")
        red    = sum(1 for r in job.results if eff(r) == "red")
        skipped = sum(1 for r in job.results if eff(r) in ("skipped", "na"))
        overrides = sum(len(r.overrides) for r in job.results)
        auto = green + amber + red
        score = round(green / auto * 100, 1) if auto else 0.0

        reports.append({
            "id": job.id,
            "job_id": job.id,
            "project_name": job.project.name if job.project else "—",
            "checklist_name": job.checklist.name if job.checklist else "—",
            "source_path": job.source_path,
            "status": job.status,
            "compliance_score": score,
            "green_count": green,
            "amber_count": amber,
            "red_count": red,
            "skipped_count": skipped,
            "override_count": overrides,
            "total_items": job.total_items,
            "generated_at": job.completed_at.isoformat() if job.completed_at else (
                job.created_at.isoformat() if job.created_at else None
            ),
        })

    return {"reports": reports}


@router.get("/{report_id}")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get report details"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "review_id": report.review_id,
        "summary": report.summary,
        "overall_rag_status": report.overall_rag_status,
        "compliance_score": report.compliance_score,
        "areas_followed": report.areas_followed,
        "gaps_identified": report.gaps_identified,
        "recommendations": report.recommendations,
        "action_items": report.action_items,
        "approval_status": report.approval_status,
        "requires_approval": report.requires_approval,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "approved_at": report.approved_at.isoformat() if report.approved_at else None
    }


@router.get("/{report_id}/download/{format}")
async def download_report(
    report_id: int,
    format: str,
    db: AsyncSession = Depends(get_db)
):
    """Download report in specified format (markdown or pdf)"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format == "markdown":
        file_path = report.markdown_path
    elif format == "pdf":
        file_path = report.pdf_path
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'pdf'")
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.{format}",
        media_type="application/octet-stream"
    )


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: int,
    approver_id: int,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Approve a report (human approval workflow)"""
    # Verify report exists
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Verify approver exists
    approver_result = await db.execute(
        select(User).where(User.id == approver_id)
    )
    approver = approver_result.scalar_one_or_none()
    
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")
    
    # Check if approval already exists
    existing_result = await db.execute(
        select(ReportApproval).where(
            ReportApproval.report_id == report_id,
            ReportApproval.approver_id == approver_id
        )
    )
    existing_approval = existing_result.scalar_one_or_none()
    
    if existing_approval:
        # Update existing
        existing_approval.status = "approved"
        existing_approval.comments = comments
        existing_approval.decided_at = datetime.utcnow()
    else:
        # Create new approval
        approval = ReportApproval(
            report_id=report_id,
            approver_id=approver_id,
            status="approved",
            comments=comments,
            decided_at=datetime.utcnow()
        )
        db.add(approval)
    
    # Update report status
    report.approval_status = "approved"
    report.approved_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Report approved successfully",
        "report_id": report_id,
        "approved_by": approver.full_name,
        "approved_at": report.approved_at.isoformat()
    }


@router.post("/{report_id}/reject")
async def reject_report(
    report_id: int,
    approver_id: int,
    comments: str,
    db: AsyncSession = Depends(get_db)
):
    """Reject a report with comments for revision"""
    # Verify report exists
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.review))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Create rejection
    approval = ReportApproval(
        report_id=report_id,
        approver_id=approver_id,
        status="rejected",
        comments=comments,
        decided_at=datetime.utcnow()
    )
    db.add(approval)
    
    # Update report status
    report.approval_status = "revision_requested"
    report.approved_at = datetime.utcnow()
    
    # Update associated review
    if report.review:
        report.review.status = "pending_approval"
    
    await db.commit()
    
    return {
        "message": "Report rejected - revision requested",
        "report_id": report_id,
        "rejected_by": approver_id,
        "comments": comments,
        "next_step": "Review needs to be revised and resubmitted"
    }


@router.get("/{report_id}/approvals")
async def get_report_approvals(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get approval history for a report"""
    result = await db.execute(
        select(ReportApproval)
        .options(selectinload(ReportApproval.approver))
        .where(ReportApproval.report_id == report_id)
        .order_by(ReportApproval.created_at.desc())
    )
    approvals = result.scalars().all()
    
    return {
        "report_id": report_id,
        "approvals": [
            {
                "id": appr.id,
                "approver_id": appr.approver_id,
                "approver_name": appr.approver.full_name if appr.approver else "Unknown",
                "status": appr.status,
                "comments": appr.comments,
                "decided_at": appr.decided_at.isoformat() if appr.decided_at else None
            }
            for appr in approvals
        ]
    }


@router.get("/pending/approvals")
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db)
):
    """Get all reports pending approval"""
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.review).selectinload(Review.project))
        .where(Report.approval_status == "pending")
    )
    reports = result.scalars().all()
    
    return {
        "pending_reports": [
            {
                "id": r.id,
                "review_id": r.review_id,
                "project_name": r.review.project.name if r.review else "Unknown",
                "compliance_score": r.compliance_score,
                "overall_rag": r.overall_rag_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "requires_approval": r.requires_approval
            }
            for r in reports
        ],
        "total_pending": len(reports)
    }


@router.post("/{report_id}/regenerate")
async def regenerate_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Regenerate report from review data"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Reset approval status
    report.approval_status = "pending"
    report.approved_at = None
    report.created_at = datetime.utcnow()

    # In production: regenerate the actual report files
    # For now, just reset status

    await db.commit()

    return {
        "message": "Report regenerated and sent for approval",
        "report_id": report_id,
        "approval_status": "pending"
    }


# ──────────────────────────────────────────────────────────────────────────────
# Report History & Management Endpoints (NEW)
# ──────────────────────────────────────────────────────────────────────────────

# Pydantic schemas
class SourcePathUpdate(BaseModel):
    source_path: str


class RegenerateRequest(BaseModel):
    use_updated_source_path: bool = True
    include_overrides: bool = True


class ReportHistoryItem(BaseModel):
    id: int
    project_id: int
    project_name: str
    checklist_id: int
    checklist_name: str
    source_path: str
    generated_at: str
    total_items: int
    green_count: int
    amber_count: int
    red_count: int
    compliance_score: float
    override_count: int
    adjusted_score: float
    status: str


@router.put("/{report_id}/source-path")
async def update_source_path(
    report_id: int,
    source_path_data: SourcePathUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update source path for a report
    
    This allows users to correct the source path if it was wrong
    or if the project has moved to a different location.
    """
    # Get report with job
    result = await db.execute(
        select(Report)
        .options(joinedload(Report.autonomous_review_job))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.autonomous_review_job:
        raise HTTPException(
            status_code=400, 
            detail="Report is not linked to an autonomous review job"
        )
    
    old_path = report.autonomous_review_job.source_path
    report.autonomous_review_job.source_path = source_path_data.source_path
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Source path updated successfully",
        "report_id": report_id,
        "job_id": report.autonomous_review_job.id,
        "old_path": old_path,
        "new_path": source_path_data.source_path
    }


@router.get("/{report_id}/details")
async def get_report_details(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full details for an autonomous review job (report_id == job_id).
    Returns all checklist items with RAG status and override history.
    """
    # report_id from the history page is the AutonomousReviewJob.id
    job_result = await db.execute(
        select(AutonomousReviewJob)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist),
        )
        .where(AutonomousReviewJob.id == report_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")

    # Load all results with their overrides and the linked checklist item
    results_query = (
        select(AutonomousReviewResult)
        .options(
            selectinload(AutonomousReviewResult.overrides).selectinload(AutonomousReviewOverride.user),
            selectinload(AutonomousReviewResult.checklist_item),
        )
        .where(AutonomousReviewResult.job_id == job.id)
        .order_by(AutonomousReviewResult.id)
    )
    results_result = await db.execute(results_query)
    results = results_result.scalars().all()

    # Load active routing rules so the UI can show the toggle state
    from app.models import ChecklistRoutingRule
    ci_ids = [r.checklist_item_id for r in results if r.checklist_item_id]
    rr_result = await db.execute(
        select(ChecklistRoutingRule)
        .where(ChecklistRoutingRule.checklist_item_id.in_(ci_ids))
        .where(ChecklistRoutingRule.is_active == True)
    )
    # {checklist_item_id: strategy_string}  e.g. "human_required" | "ai_and_human"
    routing_rule_map = {rr.checklist_item_id: rr.strategy for rr in rr_result.scalars().all()}

    items = []
    override_count = 0

    for r in results:
        ci = r.checklist_item
        is_overridden = len(r.overrides) > 0
        if is_overridden:
            override_count += 1
        items.append({
            "item_id": r.id,
            "checklist_item_id": r.checklist_item_id,
            "item_code": ci.item_code if ci else "",
            "area": ci.area if ci else "",
            "question": ci.question if ci else r.evidence,
            "rag_status": r.rag_status,
            "evidence": r.evidence,
            "confidence": r.confidence,
            "strategy": r.strategy,
            "routing_rule": routing_rule_map.get(r.checklist_item_id),  # None | "human_required" | "ai_and_human"
            "needs_human_sign_off": getattr(r, 'needs_human_sign_off', False),
            "is_overridden": is_overridden,
            "overrides": [
                {
                    "override_id": o.id,
                    "new_rag_status": o.new_rag_status,
                    "comments": o.comments,
                    "reason": o.reason,
                    "overridden_by": o.user.full_name if o.user else "Unknown",
                    "overridden_at": o.overridden_at.isoformat(),
                }
                for o in r.overrides
            ],
        })

    def effective_status(r) -> str:
        """Return the latest override status if overridden, else original."""
        if r.overrides:
            return sorted(r.overrides, key=lambda o: o.overridden_at)[-1].new_rag_status
        return r.rag_status

    green_count  = sum(1 for r in results if effective_status(r) == "green")
    amber_count  = sum(1 for r in results if effective_status(r) == "amber")
    red_count    = sum(1 for r in results if effective_status(r) == "red")
    auto = green_count + amber_count + red_count
    adjusted_score = round(green_count / auto * 100, 1) if auto else 0.0

    return {
        "report": {
            "id": job.id,
            "project_name": job.project.name if job.project else "—",
            "checklist_name": job.checklist.name if job.checklist else "—",
            "source_path": job.source_path,
            "generated_at": (job.completed_at or job.created_at).isoformat(),
            "compliance_score": adjusted_score,
            "override_count": override_count,
            "adjusted_score": adjusted_score,
            "agent_metadata": job.agent_metadata,
        },
        "summary": {
            "total": len(results),
            "green": green_count,
            "amber": amber_count,
            "red": red_count,
            "human_required": sum(1 for r in results if effective_status(r) == "skipped"),
            "na": sum(1 for r in results if effective_status(r) == "na"),
        },
        "items": items,
    }
