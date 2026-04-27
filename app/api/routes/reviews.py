"""
Reviews API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import io
import os
import secrets

from app.db.session import get_db
from app.models import Review, ReviewResponse, Checklist, ChecklistItem, Project, Report, IntegrationConfig
from app.agents.review_agent import get_review_agent
from sqlalchemy.orm import selectinload
from app.services.voice_interface import get_voice_interface
from app.services.excel_offline_exporter import generate_offline_excel
from app.services.excel_response_parser import parse_response_excel
from app.services.integrations import email_smtp as _smtp_svc
from app.services.integrations import email_resend as _resend_svc
from app.api.routes.auth import get_current_user
from app.core.config import settings

router = APIRouter()


async def _get_email_integration(db: AsyncSession):
    """Return the first enabled smtp or resend integration (resend preferred)."""
    from sqlalchemy import or_
    result = await db.execute(
        select(IntegrationConfig).where(
            or_(IntegrationConfig.type == "resend", IntegrationConfig.type == "smtp"),
            IntegrationConfig.is_enabled == True,
        ).order_by(IntegrationConfig.type)  # "resend" < "smtp" alphabetically
    )
    return result.scalars().first()


async def _send_offline_review_email(integration: IntegrationConfig, **kwargs):
    """Dispatch offline review email via the configured provider."""
    if integration.type == "resend":
        return await _resend_svc.send_offline_review_email(
            cfg=integration.config_json, **kwargs
        )
    return await _smtp_svc.send_offline_review_email(
        cfg=integration.config_json, **kwargs
    )


@router.get("/")
async def list_reviews(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    review_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all reviews"""
    query = select(Review).options(
        selectinload(Review.project),
        selectinload(Review.checklist),
    )

    if project_id:
        query = query.where(Review.project_id == project_id)
    if status:
        query = query.where(Review.status == status)
    if review_type:
        query = query.where(Review.review_type == review_type)

    result = await db.execute(query)
    reviews = result.scalars().all()

    return {
        "reviews": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "project_name": r.project.name if r.project else "Unknown",
                "checklist_id": r.checklist_id,
                "checklist_name": r.checklist.name if r.checklist else None,
                "title": r.title,
                "status": r.status,
                "review_type": getattr(r, "review_type", "online"),
                "review_date": r.review_date.isoformat() if r.review_date else None,
                "voice_enabled": r.voice_enabled,
                "assigned_reviewer_email": getattr(r, "assigned_reviewer_email", None),
                "assigned_reviewer_name": getattr(r, "assigned_reviewer_name", None),
                "excel_sent_at": r.excel_sent_at.isoformat() if getattr(r, "excel_sent_at", None) else None,
                "excel_uploaded_at": r.excel_uploaded_at.isoformat() if getattr(r, "excel_uploaded_at", None) else None,
                "due_date": r.due_date.isoformat() if getattr(r, "due_date", None) else None,
                "upload_token": getattr(r, "upload_token", None),
            }
            for r in reviews
        ]
    }


@router.get("/{review_id}")
async def get_review(
    review_id: int,
    include_responses: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get review details"""
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.responses).selectinload(ReviewResponse.checklist_item)
        )
        .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    response = {
        "id": review.id,
        "project_id": review.project_id,
        "checklist_id": review.checklist_id,
        "title": review.title,
        "status": review.status,
        "conducted_by": review.conducted_by,
        "participants": review.participants,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "voice_enabled": review.voice_enabled,
        "notes": review.notes,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "completed_at": review.completed_at.isoformat() if review.completed_at else None
    }
    
    if include_responses:
        response["responses"] = [
            {
                "id": resp.id,
                "question": resp.checklist_item.question if resp.checklist_item else None,
                "answer": resp.answer,
                "comments": resp.comments,
                "rag_status": resp.rag_status,
                "transcript": resp.transcript
            }
            for resp in review.responses
        ]
    
    return response


@router.post("/")
async def create_review(
    project_id: int,
    checklist_id: int,
    title: Optional[str] = None,
    voice_enabled: bool = True,
    participants: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new review session"""
    import json
    
    # Verify project and checklist exist
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Create review
    review = Review(
        project_id=project_id,
        checklist_id=checklist_id,
        title=title or f"Review - {project.name}",
        voice_enabled=voice_enabled,
        participants=json.loads(participants) if participants else None,
        status="draft"
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    return {
        "message": "Review created successfully",
        "review_id": review.id,
        "project_name": project.name,
        "checklist_name": checklist.name
    }


@router.post("/{review_id}/start")
async def start_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Start a review session with AI agent"""
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.checklist).selectinload(Checklist.items)
        )
        .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Load checklist items
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == review.checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Get project info
    project = review.project
    
    # Initialize agent state
    initial_state = {
        "project_id": project.id,
        "project_name": project.name,
        "project_domain": project.domain or "general",
        "project_context": {
            "description": project.description,
            "tech_stack": project.tech_stack,
            "stakeholders": project.stakeholders,
            "participants": review.participants or []
        },
        "checklist_id": checklist.id,
        "checklist_items": [
            {
                "id": item.id,
                "item_code": item.item_code,
                "area": item.area,
                "question": item.question,
                "category": item.category,
                "weight": item.weight
            }
            for item in checklist.items
        ],
        "review_id": review.id,
        "responses": [],
        "session_status": "draft",
        "voice_enabled": review.voice_enabled,
        "last_transcript": None,
        "last_voice_response": None,
        "conversation_history": [],
        "current_question": None,
        "user_answer": None,
        "report_data": None,
        "compliance_score": 0.0,
        "overall_rag": "na",
        "requires_approval": True,
        "approval_status": "pending",
        "approver_id": None,
        "approval_comments": None,
        "errors": [],
        "warnings": [],
        "metadata": {}
    }
    
    # Run agent
    agent = get_review_agent()
    # For demo, just initialize - actual run would be interactive
    review.status = "in_progress"
    await db.commit()
    
    return {
        "message": "Review session started",
        "review_id": review.id,
        "checklist_items_count": len(checklist.items),
        "voice_enabled": review.voice_enabled,
        "first_question": checklist.items[0].question if checklist.items else None
    }


@router.post("/{review_id}/respond")
async def submit_response(
    review_id: int,
    question_index: int,
    answer: str,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Submit response to a review question"""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Get checklist item
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == review.checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist or question_index >= len(checklist.items):
        raise HTTPException(status_code=404, detail="Question not found")
    
    item = checklist.items[question_index]
    
    # Determine RAG status from answer
    answer_lower = answer.lower()
    if any(word in answer_lower for word in ["yes", "yeah", "yep", "done"]):
        rag_status = "green"
    elif any(word in answer_lower for word in ["no", "nope", "missing"]):
        rag_status = "red"
    elif any(word in answer_lower for word in ["partial", "in progress", "working"]):
        rag_status = "amber"
    else:
        rag_status = "na"
    
    # Create response
    response = ReviewResponse(
        review_id=review_id,
        checklist_item_id=item.id,
        answer=answer,
        comments=comments or "",
        rag_status=rag_status
    )
    
    db.add(response)
    await db.commit()
    
    # Get next question
    next_question = None
    next_index = question_index + 1
    if next_index < len(checklist.items):
        next_question = {
            "index": next_index,
            "question": checklist.items[next_index].question,
            "area": checklist.items[next_index].area
        }
    
    return {
        "message": "Response recorded",
        "rag_status": rag_status,
        "next_question": next_question,
        "progress": f"{next_index}/{len(checklist.items)}"
    }


@router.post("/{review_id}/voice-response")
async def submit_voice_response(
    review_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Submit voice response (audio file)"""
    # Verify review exists
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if not review.voice_enabled:
        raise HTTPException(status_code=400, detail="Voice not enabled for this review")
    
    # Save audio file
    upload_dir = "./uploads/voice"
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"review_{review_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Transcribe
    voice_interface = get_voice_interface()
    transcript = await voice_interface.speech_to_text(file_path)
    
    if not transcript:
        return {
            "message": "Audio saved but transcription failed",
            "file_path": file_path,
            "transcript": None
        }
    
    # Process voice intent
    voice_result = await voice_interface.process_voice_input(file_path)
    
    return {
        "message": "Voice response processed",
        "file_path": file_path,
        "transcript": transcript,
        "intent": voice_result.get("intent"),
        "answer": transcript  # Use transcript as answer
    }


@router.post("/{review_id}/complete")
async def complete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Complete the review and generate report"""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = "completed"
    review.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Review completed",
        "review_id": review_id,
        "status": "pending_approval",
        "next_step": "Report generated and awaiting human approval"
    }


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a review"""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await db.delete(review)
    await db.commit()

    return {"message": "Review deleted successfully"}


# ──────────────────────────────────────────────────────────────────────────────
# Offline Review Endpoints
# ──────────────────────────────────────────────────────────────────────────────

class OfflineReviewCreate(BaseModel):
    project_id: int
    checklist_id: int
    assigned_reviewer_email: str
    assigned_reviewer_name: str
    offline_message: Optional[str] = None
    due_date: Optional[str] = None  # ISO format: "2026-05-09"


async def _process_offline_upload(review: Review, file: UploadFile, db: AsyncSession):
    """Parse uploaded response Excel, upsert ReviewResponse rows, create/update Report."""
    content = await file.read()

    # Load checklist items for item_code → id mapping
    checklist_result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.items))
        .where(Checklist.id == review.checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    try:
        parsed = parse_response_excel(content, checklist.items)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not parsed:
        raise HTTPException(status_code=422, detail="No responses found in the uploaded file.")

    # Save the uploaded file for audit trail
    upload_dir = os.path.join(settings.UPLOAD_DIR, "offline_responses")
    os.makedirs(upload_dir, exist_ok=True)
    response_path = os.path.join(upload_dir, f"{review.id}_response.xlsx")
    with open(response_path, "wb") as f:
        f.write(content)

    # Upsert ReviewResponse rows
    existing_result = await db.execute(
        select(ReviewResponse).where(ReviewResponse.review_id == review.id)
    )
    existing_map = {r.checklist_item_id: r for r in existing_result.scalars().all()}

    rag_scores = {"green": 100, "amber": 50, "red": 0}
    rag_counts: Dict[str, int] = {"green": 0, "amber": 0, "red": 0, "na": 0}

    for item_data in parsed:
        cid = item_data["checklist_item_id"]
        rag = item_data["rag_status"]
        rag_counts[rag] = rag_counts.get(rag, 0) + 1

        if cid in existing_map:
            resp = existing_map[cid]
            resp.answer = item_data["answer"]
            resp.rag_status = rag
            resp.comments = item_data.get("comments") or ""
            resp.evidence_links = item_data.get("evidence_links") or []
        else:
            resp = ReviewResponse(
                review_id=review.id,
                checklist_item_id=cid,
                answer=item_data["answer"],
                rag_status=rag,
                comments=item_data.get("comments") or "",
                evidence_links=item_data.get("evidence_links") or [],
            )
            db.add(resp)

    # Compliance score: N/A items excluded from denominator
    scored = [r for r in parsed if r["rag_status"] != "na"]
    compliance_score = (
        sum(rag_scores.get(r["rag_status"], 0) for r in scored) / len(scored)
        if scored else 0.0
    )

    overall_rag = (
        "red" if rag_counts["red"] > 0
        else "amber" if rag_counts["amber"] > 0
        else "green" if rag_counts["green"] > 0
        else "na"
    )

    # Update review fields
    now = datetime.utcnow()
    review.excel_uploaded_at = now
    review.excel_response_path = response_path
    review.status = "completed"
    review.completed_at = now

    # Create or update Report
    existing_report_result = await db.execute(
        select(Report).where(Report.review_id == review.id)
    )
    report = existing_report_result.scalar_one_or_none()

    gaps = [
        {
            "item_code": r["item_code"],
            "rag_status": r["rag_status"],
            "answer": r["answer"],
            "comments": r.get("comments") or "",
        }
        for r in parsed if r["rag_status"] in ("red", "amber")
    ]
    green_items = [r["item_code"] for r in parsed if r["rag_status"] == "green"]

    if report:
        report.compliance_score = compliance_score
        report.overall_rag_status = overall_rag
        report.gaps_identified = gaps
        report.areas_followed = green_items
        report.approval_status = "pending"
        report.created_at = now
    else:
        report = Report(
            review_id=review.id,
            compliance_score=compliance_score,
            overall_rag_status=overall_rag,
            gaps_identified=gaps,
            areas_followed=green_items,
            recommendations=[],
            action_items=[],
            approval_status="pending",
            requires_approval=True,
        )
        db.add(report)

    await db.commit()

    return {
        "review_id": review.id,
        "responses_recorded": len(parsed),
        "compliance_score": round(compliance_score, 1),
        "rag_summary": rag_counts,
        "report_status": "pending_approval",
    }


@router.post("/offline")
async def create_offline_review(
    request: OfflineReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an offline review and optionally send an invitation email to the reviewer."""
    # Verify project and checklist exist
    project_result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    checklist_result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.items))
        .where(Checklist.id == request.checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    due_dt = None
    if request.due_date:
        try:
            due_dt = datetime.fromisoformat(request.due_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid due_date. Use ISO format: YYYY-MM-DD")

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(days=settings.OFFLINE_REVIEW_TOKEN_DAYS)

    review = Review(
        project_id=request.project_id,
        checklist_id=request.checklist_id,
        title=f"Offline Review — {project.name}",
        review_type="offline",
        status="in_progress",
        assigned_reviewer_email=request.assigned_reviewer_email,
        assigned_reviewer_name=request.assigned_reviewer_name,
        upload_token=token,
        upload_token_expiry=expiry,
        offline_message=request.offline_message,
        due_date=due_dt,
        voice_enabled=False,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Send invitation email if an email integration (smtp or resend) is configured
    email_sent = False
    email_error = None
    email_cfg_row = await _get_email_integration(db)

    if email_cfg_row:
        try:
            dispatch = await _send_offline_review_email(
                integration=email_cfg_row,
                reviewer_email=request.assigned_reviewer_email,
                reviewer_name=request.assigned_reviewer_name,
                project_name=project.name,
                checklist_name=checklist.name,
                app_url=settings.APP_BASE_URL,
                upload_token=token,
                due_date=due_dt,
                admin_message=request.offline_message,
                item_count=len(checklist.items),
            )
            email_sent = dispatch.success
            if dispatch.success:
                review.excel_sent_at = datetime.utcnow()
                await db.commit()
            else:
                email_error = dispatch.error_message
        except Exception as exc:
            email_error = str(exc)

    review_url = f"{settings.APP_BASE_URL.rstrip('/')}/offline-review?token={token}"

    return {
        "message": "Offline review created",
        "review_id": review.id,
        "upload_token": token,
        "review_url": review_url,
        "email_sent": email_sent,
        "email_error": email_error,
        "reviewer_email": request.assigned_reviewer_email,
        "project_name": project.name,
        "checklist_name": checklist.name,
        "item_count": len(checklist.items),
        "token_expires_at": expiry.isoformat(),
    }


@router.get("/offline/pending")
async def get_pending_offline_reviews(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List offline reviews assigned to the current user that haven't been uploaded yet."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.project), selectinload(Review.checklist))
        .where(
            Review.review_type == "offline",
            Review.assigned_reviewer_email == current_user.email,
            Review.excel_uploaded_at == None,
            Review.upload_token_expiry > now,
        )
    )
    reviews = result.scalars().all()

    return {
        "pending_reviews": [
            {
                "review_id": r.id,
                "project_name": r.project.name if r.project else "Unknown",
                "checklist_name": r.checklist.name if r.checklist else "Unknown",
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "sent_at": r.excel_sent_at.isoformat() if r.excel_sent_at else None,
                "review_url": f"{settings.APP_BASE_URL.rstrip('/')}/offline-review?token={r.upload_token}",
            }
            for r in reviews
        ]
    }


@router.get("/upload-info/{token}")
async def get_upload_info(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get review metadata by upload token (no authentication required)."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.checklist).selectinload(Checklist.items)
        )
        .where(Review.upload_token == token)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Invalid or expired review link")

    if review.upload_token_expiry and review.upload_token_expiry < now:
        raise HTTPException(
            status_code=410,
            detail="This review link has expired. Please contact your ReviewBot administrator."
        )

    if not review.first_accessed_at:
        review.first_accessed_at = now
        await db.commit()

    return {
        "review_id": review.id,
        "project_name": review.project.name if review.project else "Unknown",
        "checklist_name": review.checklist.name if review.checklist else "Unknown",
        "reviewer_name": review.assigned_reviewer_name or "Reviewer",
        "admin_message": review.offline_message,
        "due_date": review.due_date.isoformat() if review.due_date else None,
        "sent_at": review.excel_sent_at.isoformat() if review.excel_sent_at else None,
        "token_expires_at": review.upload_token_expiry.isoformat() if review.upload_token_expiry else None,
        "item_count": len(review.checklist.items) if review.checklist else 0,
        "already_submitted": review.excel_uploaded_at is not None,
        "submitted_at": review.excel_uploaded_at.isoformat() if review.excel_uploaded_at else None,
    }


@router.get("/download-checklist/{token}")
async def download_checklist_by_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate and download the review checklist Excel by upload token (no authentication required)."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.checklist).selectinload(Checklist.items)
        )
        .where(Review.upload_token == token)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Invalid review link")

    if review.upload_token_expiry and review.upload_token_expiry < now:
        raise HTTPException(status_code=410, detail="This review link has expired.")

    if not review.checklist or not review.checklist.items:
        raise HTTPException(status_code=404, detail="No checklist items found for this review")

    project_name = review.project.name if review.project else "Project"
    checklist_name = review.checklist.name if review.checklist else "Checklist"

    excel_bytes = generate_offline_excel(
        project_name=project_name,
        checklist_name=checklist_name,
        reviewer_name=review.assigned_reviewer_name or "Reviewer",
        items=review.checklist.items,
        due_date=review.due_date,
        admin_message=review.offline_message,
    )

    review.excel_downloaded_at = now
    await db.commit()

    safe_project = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    filename = f"ReviewBot_{safe_project}_Checklist.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/upload/{token}")
async def upload_response_by_token(
    token: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a completed response Excel by upload token (no authentication required)."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Review).where(Review.upload_token == token)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Invalid review link")

    if review.upload_token_expiry and review.upload_token_expiry < now:
        raise HTTPException(status_code=410, detail="This review link has expired.")

    if review.excel_uploaded_at:
        raise HTTPException(
            status_code=409,
            detail="A response has already been submitted for this review."
        )

    return await _process_offline_upload(review, file, db)


@router.post("/{review_id}/upload-response")
async def upload_response_by_id(
    review_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Upload a completed response Excel by review ID (authentication required)."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.review_type != "offline":
        raise HTTPException(status_code=400, detail="This endpoint is only for offline reviews.")

    return await _process_offline_upload(review, file, db)


@router.post("/{review_id}/resend-email")
async def resend_offline_invitation(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Resend the offline review invitation email (authentication required)."""
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.checklist).selectinload(Checklist.items)
        )
        .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.review_type != "offline":
        raise HTTPException(status_code=400, detail="This is not an offline review.")

    if not review.assigned_reviewer_email:
        raise HTTPException(status_code=400, detail="No reviewer email assigned to this review.")

    email_cfg_row = await _get_email_integration(db)

    if not email_cfg_row:
        raise HTTPException(
            status_code=503,
            detail="No active email integration (SMTP or Resend) configured. Set one up in Settings > Integrations."
        )

    project_name = review.project.name if review.project else "Project"
    checklist_name = review.checklist.name if review.checklist else "Checklist"

    dispatch = await _send_offline_review_email(
        integration=email_cfg_row,
        reviewer_email=review.assigned_reviewer_email,
        reviewer_name=review.assigned_reviewer_name or "Reviewer",
        project_name=project_name,
        checklist_name=checklist_name,
        app_url=settings.APP_BASE_URL,
        upload_token=review.upload_token,
        due_date=review.due_date,
        admin_message=review.offline_message,
        item_count=len(review.checklist.items) if review.checklist else 0,
    )

    if dispatch.success:
        review.excel_sent_at = datetime.utcnow()
        await db.commit()

    return {
        "message": "Email resent successfully" if dispatch.success else "Failed to send email",
        "email_sent": dispatch.success,
        "error": dispatch.error_message if not dispatch.success else None,
        "reviewer_email": review.assigned_reviewer_email,
    }
