"""
Reviews API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.db.session import get_db
from app.models import Review, ReviewResponse, Checklist, ChecklistItem, Project
from app.agents.review_agent import get_review_agent
from sqlalchemy.orm import selectinload
from app.services.voice_interface import get_voice_interface

router = APIRouter()


@router.get("/")
async def list_reviews(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all reviews"""
    query = select(Review).options(selectinload(Review.project))

    if project_id:
        query = query.where(Review.project_id == project_id)
    if status:
        query = query.where(Review.status == status)

    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return {
        "reviews": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "project_name": r.project.name if r.project else "Unknown",
                "title": r.title,
                "status": r.status,
                "review_date": r.review_date.isoformat() if r.review_date else None,
                "voice_enabled": r.voice_enabled
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
