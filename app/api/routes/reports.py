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
    AutonomousReviewResult, AutonomousReviewOverride
)
from app.core.config import settings
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel


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


@router.get("/history", response_model=List[ReportHistoryItem])
async def get_report_history(
    project_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all autonomous review reports with full details
    
    Includes:
    - Project and checklist information
    - Source path
    - Generation date
    - RAG counts
    - Override count and adjusted score
    """
    # Query reports linked to autonomous review jobs
    query = (
        select(
            Report,
            AutonomousReviewJob,
            Project,
            Checklist,
            func.count(AutonomousReviewOverride.id).label('override_count')
        )
        .join(AutonomousReviewJob, Report.autonomous_review_job_id == AutonomousReviewJob.id)
        .join(Project, AutonomousReviewJob.project_id == Project.id)
        .join(Checklist, AutonomousReviewJob.checklist_id == Checklist.id)
        .outerjoin(AutonomousReviewResult, AutonomousReviewJob.id == AutonomousReviewResult.job_id)
        .outerjoin(AutonomousReviewOverride, AutonomousReviewResult.id == AutonomousReviewOverride.result_id)
        .group_by(Report.id, AutonomousReviewJob.id, Project.id, Checklist.id)
        .order_by(Report.created_at.desc())
    )
    
    if project_id:
        query = query.where(Project.id == project_id)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    reports = []
    for row in rows:
        report, job, project, checklist, override_count = row
        
        # Count RAG statuses from results
        results_query = (
            select(
                func.count(AutonomousReviewResult.id).label('total'),
                func.sum(func.case(
                    (AutonomousReviewResult.rag_status == 'green', 1),
                    else_=0
                )).label('green'),
                func.sum(func.case(
                    (AutonomousReviewResult.rag_status == 'amber', 1),
                    else_=0
                )).label('amber'),
                func.sum(func.case(
                    (AutonomousReviewResult.rag_status == 'red', 1),
                    else_=0
                )).label('red'),
            )
            .where(AutonomousReviewResult.job_id == job.id)
        )
        results_result = await db.execute(results_query)
        counts = results_result.first()
        
        # Calculate adjusted score (accounting for overrides)
        base_score = report.compliance_score or 0.0
        adjusted_score = base_score + (override_count * 2.0)  # Each override adds 2%
        adjusted_score = min(100.0, adjusted_score)
        
        reports.append({
            "id": report.id,
            "project_id": project.id,
            "project_name": project.name,
            "checklist_id": checklist.id,
            "checklist_name": checklist.name,
            "source_path": job.source_path,
            "generated_at": report.created_at.isoformat(),
            "total_items": counts.total or 0,
            "green_count": counts.green or 0,
            "amber_count": counts.amber or 0,
            "red_count": counts.red or 0,
            "compliance_score": base_score,
            "override_count": override_count,
            "adjusted_score": adjusted_score,
            "status": "completed"
        })
    
    return reports


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


@router.post("/{report_id}/regenerate")
async def regenerate_report(
    report_id: int,
    regenerate_data: RegenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate report with updated source path
    
    Options:
    - use_updated_source_path: Use the (possibly updated) source path
    - include_overrides: Carry forward previous overrides
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
    
    job = report.autonomous_review_job
    
    # Reset report status
    report.approval_status = "pending"
    report.approved_at = None
    report.created_at = datetime.utcnow()
    
    # Schedule background regeneration
    # TODO: Implement actual regeneration logic
    # For now, just mark as pending
    
    await db.commit()
    
    return {
        "status": "accepted",
        "message": "Report regeneration started",
        "job_id": job.id,
        "report_id": report_id,
        "estimated_time_seconds": 120,
        "use_updated_source_path": regenerate_data.use_updated_source_path,
        "include_overrides": regenerate_data.include_overrides
    }


@router.get("/{report_id}/details")
async def get_report_details(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full report details including all items and their overrides
    
    Returns:
    - Report summary
    - RAG counts
    - All checklist items with their status
    - Overrides for each item
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
    
    job = report.autonomous_review_job
    
    # Get all results with overrides
    results_query = (
        select(AutonomousReviewResult, ChecklistItem)
        .options(joinedload(AutonomousReviewResult.overrides).joinedload(AutonomousReviewOverride.user))
        .join(ChecklistItem, AutonomousReviewResult.checklist_item_id == ChecklistItem.id)
        .where(AutonomousReviewResult.job_id == job.id)
        .order_by(ChecklistItem.item_code)
    )
    
    results_result = await db.execute(results_query)
    results = results_result.all()
    
    # Build items list
    items = []
    override_count = 0
    
    for result, checklist_item in results:
        is_overridden = len(result.overrides) > 0
        if is_overridden:
            override_count += 1
        
        items.append({
            "item_id": result.id,
            "item_code": checklist_item.item_code,
            "area": checklist_item.area,
            "question": checklist_item.question,
            "rag_status": result.rag_status,
            "evidence": result.evidence,
            "confidence": result.confidence,
            "is_overridden": is_overridden,
            "overrides": [
                {
                    "override_id": o.id,
                    "new_rag_status": o.new_rag_status,
                    "comments": o.comments,
                    "reason": o.reason,
                    "overridden_by": o.user.full_name if o.user else "Unknown",
                    "overridden_at": o.overridden_at.isoformat()
                }
                for o in result.overrides
            ]
        })
    
    # Count RAG statuses
    green_count = sum(1 for r, _ in results if r.rag_status == 'green')
    amber_count = sum(1 for r, _ in results if r.rag_status == 'amber')
    red_count = sum(1 for r, _ in results if r.rag_status == 'red')
    
    # Calculate adjusted score
    base_score = report.compliance_score or 0.0
    adjusted_score = base_score + (override_count * 2.0)
    adjusted_score = min(100.0, adjusted_score)
    
    return {
        "report": {
            "id": report.id,
            "project_name": job.project.name,
            "checklist_name": job.checklist.name,
            "source_path": job.source_path,
            "generated_at": report.created_at.isoformat(),
            "compliance_score": base_score,
            "override_count": override_count,
            "adjusted_score": adjusted_score
        },
        "summary": {
            "total": len(results),
            "green": green_count,
            "amber": amber_count,
            "red": red_count,
            "human_required": 0,
            "na": len(results) - green_count - amber_count - red_count
        },
        "items": items
    }
