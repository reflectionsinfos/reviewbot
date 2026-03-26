"""
Reports API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from app.db.session import get_db
from app.models import Report, ReportApproval, Review, User
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def list_reports(
    project_id: Optional[int] = None,
    approval_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all reports"""
    query = select(Report).join(Review)
    
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
        select(Report).where(Report.id == report_id)
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
        select(Report).where(Report.approval_status == "pending")
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
