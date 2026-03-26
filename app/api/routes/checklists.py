"""
Checklists API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models import Checklist, ChecklistItem, ChecklistRecommendation
from app.services.checklist_optimizer import get_checklist_optimizer

router = APIRouter()


@router.get("/{checklist_id}")
async def get_checklist(
    checklist_id: int,
    include_items: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get checklist details"""
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    response = {
        "id": checklist.id,
        "name": checklist.name,
        "type": checklist.type,
        "version": checklist.version,
        "is_global": checklist.is_global,
        "project_id": checklist.project_id,
        "created_at": checklist.created_at.isoformat() if checklist.created_at else None
    }
    
    if include_items:
        response["items"] = [
            {
                "id": item.id,
                "item_code": item.item_code,
                "area": item.area,
                "question": item.question,
                "category": item.category,
                "weight": item.weight,
                "is_required": item.is_required,
                "expected_evidence": item.expected_evidence,
                "order": item.order
            }
            for item in checklist.items
        ]
        response["items_count"] = len(checklist.items)
    
    return response


@router.get("/{checklist_id}/recommendations")
async def get_checklist_recommendations(
    checklist_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated recommendations for checklist improvement"""
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Get existing recommendations
    rec_result = await db.execute(
        select(ChecklistRecommendation).where(
            ChecklistRecommendation.checklist_id == checklist_id
        )
    )
    recommendations = rec_result.scalars().all()
    
    return {
        "checklist_id": checklist_id,
        "recommendations": [
            {
                "id": rec.id,
                "type": rec.suggestion_type,
                "description": rec.description,
                "rationale": rec.rationale,
                "priority": rec.priority,
                "confidence_score": rec.confidence_score,
                "status": rec.status,
                "created_at": rec.created_at.isoformat() if rec.created_at else None
            }
            for rec in recommendations
        ]
    }


@router.post("/{checklist_id}/optimize")
async def optimize_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI recommendations for checklist optimization"""
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Get project domain if available
    project_domain = "general"
    if checklist.project:
        project_domain = checklist.project.domain or "general"
    
    # Prepare current checklist data
    current_checklist = {
        checklist.type: [
            {
                "id": item.id,
                "area": item.area,
                "question": item.question,
                "category": item.category
            }
            for item in checklist.items
        ]
    }
    
    # Get optimizer and generate recommendations
    optimizer = get_checklist_optimizer()
    recommendations = await optimizer.analyze_and_recommend(
        project_domain=project_domain,
        current_checklist=current_checklist,
        project_context={
            "project_name": checklist.project.name if checklist.project else None,
            "domain": project_domain
        }
    )
    
    # Save recommendations to database
    saved_recommendations = []
    for rec_data in recommendations:
        rec = ChecklistRecommendation(
            checklist_id=checklist_id,
            suggestion_type=rec_data.get("type", "add_item"),
            description=str(rec_data.get("item", {})),
            rationale=rec_data.get("rationale", ""),
            priority=rec_data.get("priority", "medium"),
            based_on_domain=project_domain,
            confidence_score=rec_data.get("confidence", 0.7)
        )
        db.add(rec)
        saved_recommendations.append(rec)
    
    await db.commit()
    
    return {
        "message": f"Generated {len(recommendations)} recommendations",
        "checklist_id": checklist_id,
        "domain": project_domain,
        "recommendations_count": len(recommendations)
    }


@router.get("/templates/global")
async def get_global_checklist_templates(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get global checklist templates"""
    query = select(Checklist).where(Checklist.is_global == True)
    
    if type:
        query = query.where(Checklist.type == type)
    
    result = await db.execute(query)
    checklists = result.scalars().all()
    
    return {
        "templates": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "version": c.version,
                "items_count": len(c.items)
            }
            for c in checklists
        ]
    }


@router.post("/templates/use/{template_id}")
async def use_global_template(
    template_id: int,
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Copy a global template to a project"""
    # Get template
    result = await db.execute(
        select(Checklist).where(Checklist.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create copy for project
    project_checklist = Checklist(
        name=template.name,
        type=template.type,
        version=template.version,
        project_id=project_id,
        is_global=False
    )
    
    db.add(project_checklist)
    await db.flush()
    
    # Copy items
    for item in template.items:
        new_item = ChecklistItem(
            checklist_id=project_checklist.id,
            item_code=item.item_code,
            area=item.area,
            question=item.question,
            category=item.category,
            weight=item.weight,
            is_required=item.is_required,
            expected_evidence=item.expected_evidence,
            order=item.order
        )
        db.add(new_item)
    
    await db.commit()
    
    return {
        "message": "Template applied successfully",
        "new_checklist_id": project_checklist.id,
        "items_copied": len(template.items)
    }
