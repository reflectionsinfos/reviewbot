"""
Checklists API Routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Literal
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Checklist, ChecklistItem, ChecklistRecommendation, User, Project, Review, AutonomousReviewJob
from app.api.routes.auth import get_current_user
from app.services.checklist_optimizer import get_checklist_optimizer

logger = logging.getLogger(__name__)

class ChecklistItemCreate(BaseModel):
    area: str
    question: str
    category: Optional[str] = None
    weight: float = 1.0
    is_required: bool = True
    expected_evidence: Optional[str] = None
    item_code: Optional[str] = None
    order: int = 0

class ChecklistItemUpdate(BaseModel):
    area: Optional[str] = None
    question: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    is_required: Optional[bool] = None
    expected_evidence: Optional[str] = None
    item_code: Optional[str] = None
    order: Optional[int] = None

class ItemReorderReq(BaseModel):
    id: int
    order: int

class CloneChecklistResponse(BaseModel):
    id: int
    name: str
    type: str
    version: str
    project_id: Optional[int] = None
    is_global: bool
    item_count: int
    source_checklist_id: Optional[int] = None

class CloneChecklistReq(BaseModel):
    custom_name: Optional[str] = None

class SyncStrategyReq(BaseModel):
    strategy: Literal["add_new_only", "add_and_update", "full_reset"]

class SyncResult(BaseModel):
    added: int
    updated: int
    flagged_removed: int
    strategy_used: str
    flagged_items: List[str]


class GlobalChecklistCreate(BaseModel):
    """Request model for creating a global checklist"""
    name: str
    type: Literal["delivery", "technical"]
    version: Optional[str] = "1.0"


class GlobalChecklistUpdate(BaseModel):
    """Request model for updating a global checklist"""
    name: Optional[str] = None
    version: Optional[str] = None


class GlobalChecklistItemCreate(BaseModel):
    """Request model for adding an item to a global checklist"""
    item_code: Optional[str] = None
    area: str
    question: str
    category: Optional[str] = None
    weight: float = 1.0
    is_required: bool = True
    expected_evidence: Optional[str] = None
    order: int = 0


class GlobalChecklistItemUpdate(BaseModel):
    """Request model for updating an item on a global checklist"""
    item_code: Optional[str] = None
    area: Optional[str] = None
    question: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    is_required: Optional[bool] = None
    expected_evidence: Optional[str] = None
    order: Optional[int] = None


async def _generate_item_code(db: AsyncSession, checklist_id: int, area: str) -> str:
    """
    Auto-generate item_code based on area grouping.
    Format: {AREA_CODE}-{NNN}
    - AREA_CODE: 3-4 letter code for the area (e.g., SEC, TECH, GOV)
    - NNN: 3-digit sequence number within that area (e.g., 001, 002)
    
    Area codes are stored in the checklist's area_codes mapping.
    If area doesn't have a code, one is auto-generated and saved.
    """
    # Get the checklist
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Get or initialize area_codes mapping
    area_codes: dict[str, str] = checklist.area_codes or {}
    
    # Generate area code if not exists
    if area not in area_codes:
        area_codes[area] = _generate_area_code(area)
        checklist.area_codes = area_codes
        await db.flush()
    
    area_code = area_codes[area]
    
    # Get all existing items for this checklist to find max sequence
    result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.checklist_id == checklist_id)
    )
    existing_items = result.scalars().all()
    
    # Find max sequence number for this area
    max_seq = 0
    for item in existing_items:
        if item.item_code and item.item_code.startswith(f"{area_code}-"):
            try:
                seq = int(item.item_code.split("-")[1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass
    
    return f"{area_code}-{str(max_seq + 1).zfill(3)}"


def _generate_area_code(area_name: str) -> str:
    """
    Generate a 3-4 letter area code from area name.
    Uses consonants and first letter, uppercase.
    
    Examples:
        "Security" → "SEC"
        "Technical Architecture" → "TECH"
        "Governance" → "GOV"
        "Scope & Planning" → "SCOP"
    """
    # Remove special chars and split into words
    import re
    words = re.sub(r'[^a-zA-Z\s]', '', area_name).split()
    
    # Build code from first letters and consonants
    consonants = set('BCDFGHJKLMNPQRSTVWXYZ')
    code = ""
    
    for word in words:
        if len(code) >= 4:
            break
        # Add first letter
        if word:
            code += word[0].upper()
        # Add next 2-3 consonants
        for char in word[1:]:
            if char.upper() in consonants and len(code) < 4:
                code += char.upper()
    
    # Ensure at least 3 chars
    code = (code + "XXX")[:4]
    
    return code


async def _validate_item_code(db: AsyncSession, checklist_id: int, item_code: str, area: str) -> bool:
    """
    Validate manually provided item_code.
    Must match pattern: {AREA_CODE}-{NNN}
    Area code must be registered for this checklist or match the provided area.
    """
    import re
    
    # Check pattern: 3-4 letters, dash, 3 digits
    pattern = r'^[A-Z]{3,4}-\d{3}$'
    if not re.match(pattern, item_code):
        return False
    
    # Get checklist area_codes
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        return False
    
    area_codes: dict[str, str] = checklist.area_codes or {}
    
    # Extract area code from item_code
    provided_code = item_code.split("-")[0]
    
    # Check if code matches any registered area code
    registered_codes = set(area_codes.values())
    
    # Also check if it matches the area being added (auto-register if needed)
    if area in area_codes:
        registered_codes.add(area_codes[area])
    else:
        # Generate what the code would be for this area
        expected_code = _generate_area_code(area)
        registered_codes.add(expected_code)
    
    return provided_code in registered_codes


router = APIRouter()


@router.get("/globals/{checklist_id}/area-codes")
async def get_checklist_area_codes(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get area code mapping for a checklist.
    Returns: {"area_codes": {"Security": "SEC", "Technical": "TECH"}}
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    return {
        "checklist_id": checklist_id,
        "area_codes": checklist.area_codes or {}
    }


@router.get("/{checklist_id}")
async def get_checklist(
    checklist_id: int,
    include_items: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get checklist details"""
    result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.items))
        .where(Checklist.id == checklist_id)
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
        "source_checklist_id": checklist.source_checklist_id,
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
        select(Checklist)
        .options(
            selectinload(Checklist.items),
            selectinload(Checklist.project)
        )
        .where(Checklist.id == checklist_id)
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
    query = select(Checklist).options(selectinload(Checklist.items)).where(Checklist.is_global == True)
    
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
):
    """Deprecated — use POST /api/checklists/{template_id}/clone-to-project/{project_id} instead."""
    raise HTTPException(
        status_code=410,
        detail=(
            "This endpoint is deprecated. Use "
            f"POST /api/checklists/{template_id}/clone-to-project/<project_id> instead. "
            "The new endpoint requires authentication and tracks the source template for sync."
        )
    )


@router.post("/{checklist_id}/clone-to-project/{project_id}", response_model=CloneChecklistResponse)
async def clone_checklist_to_project(
    checklist_id: int,
    project_id: int,
    req: CloneChecklistReq = CloneChecklistReq(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clone a global checklist into a project-specific checklist"""
    # Validates: source checklist must exist and be is_global=True
    try:
        result = await db.execute(
            select(Checklist)
            .options(selectinload(Checklist.items))
            .where(Checklist.id == checklist_id)
        )
        source_checklist = result.scalar_one_or_none()
        
        if not source_checklist:
            raise HTTPException(status_code=404, detail="Source checklist not found")
            
        if not source_checklist.is_global:
            raise HTTPException(status_code=400, detail="Source checklist must be global")

        # Validates: project must exist and belong to current_user (or user is admin)
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        if current_user.role != "admin" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to clone to this project")
            
        # Clones: creates new Checklist... deep copies items
        checklist_name = (req.custom_name.strip() if req.custom_name and req.custom_name.strip()
                          else source_checklist.name)
        new_checklist = Checklist(
            name=checklist_name,
            type=source_checklist.type,
            version=source_checklist.version,
            project_id=project_id,
            is_global=False,
            source_checklist_id=source_checklist.id
        )
        db.add(new_checklist)
        await db.flush()
        
        items_copied = 0
        for item in source_checklist.items:
            new_item = ChecklistItem(
                checklist_id=new_checklist.id,
                item_code=item.item_code,
                area=item.area,
                question=item.question,
                category=item.category,
                weight=item.weight,
                is_required=item.is_required,
                expected_evidence=item.expected_evidence,
                suggested_for_domains=item.suggested_for_domains,
                order=item.order
            )
            db.add(new_item)
            items_copied += 1
            
        await db.commit()
        
        return CloneChecklistResponse(
            id=new_checklist.id,
            name=new_checklist.name,
            type=new_checklist.type,
            version=new_checklist.version,
            project_id=new_checklist.project_id,
            is_global=new_checklist.is_global,
            item_count=items_copied,
            source_checklist_id=new_checklist.source_checklist_id
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{checklist_id}/sync-from-global", response_model=SyncResult)
async def sync_from_global(
    checklist_id: int,
    req: SyncStrategyReq,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync a project checklist with its original global template"""
    try:
        # Load project checklist
        result = await db.execute(
            select(Checklist)
            .options(selectinload(Checklist.items))
            .where(Checklist.id == checklist_id)
        )
        project_checklist = result.scalar_one_or_none()
        
        if not project_checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if project_checklist.is_global:
            raise HTTPException(status_code=400, detail="Cannot sync a global checklist. Target must be project-specific.")
            
        if not project_checklist.source_checklist_id:
            raise HTTPException(status_code=400, detail="This checklist has no source global template to sync from.")
            
        # Permission check
        project_result = await db.execute(select(Project).where(Project.id == project_checklist.project_id))
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Associated project not found")
            
        if current_user.role != "admin" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this project's checklist")
            
        # Load global checklist
        global_result = await db.execute(
            select(Checklist)
            .options(selectinload(Checklist.items))
            .where(Checklist.id == project_checklist.source_checklist_id)
        )
        global_checklist = global_result.scalar_one_or_none()
        
        if not global_checklist:
            raise HTTPException(status_code=404, detail="Source global template no longer exists.")
            
        added = 0
        updated = 0
        flagged_removed = 0
        flagged_items = []

        if req.strategy == "full_reset":
            # Delete existing items
            for item in project_checklist.items:
                await db.delete(item)
            
            # Re-create all
            for g_item in global_checklist.items:
                new_item = ChecklistItem(
                    checklist_id=project_checklist.id,
                    item_code=g_item.item_code,
                    area=g_item.area,
                    question=g_item.question,
                    category=g_item.category,
                    weight=g_item.weight,
                    is_required=g_item.is_required,
                    expected_evidence=g_item.expected_evidence,
                    suggested_for_domains=g_item.suggested_for_domains,
                    order=g_item.order
                )
                db.add(new_item)
                added += 1
                
            await db.commit()
            return SyncResult(
                added=added,
                updated=0,
                flagged_removed=0,
                strategy_used="full_reset",
                flagged_items=[]
            )
            
        # Diff strategy
        p_dict = {item.item_code: item for item in project_checklist.items if item.item_code}
        g_dict = {item.item_code: item for item in global_checklist.items if item.item_code}
        
        # Identify new and changed
        new_items = []
        changed_items = []
        
        for g_code, g_item in g_dict.items():
            if g_code not in p_dict:
                new_items.append(g_item)
            else:
                p_item = p_dict[g_code]
                if (p_item.question != g_item.question or
                    p_item.area != g_item.area or
                    p_item.category != g_item.category or
                    p_item.weight != g_item.weight or
                    p_item.is_required != g_item.is_required or
                    p_item.expected_evidence != g_item.expected_evidence or
                    p_item.order != g_item.order):
                    changed_items.append((p_item, g_item))
                    
        # Identify removed
        for p_code in p_dict.keys():
            if p_code not in g_dict:
                flagged_removed += 1
                flagged_items.append(p_code)

        # Apply new items
        for g_item in new_items:
            new_item = ChecklistItem(
                checklist_id=project_checklist.id,
                item_code=g_item.item_code,
                area=g_item.area,
                question=g_item.question,
                category=g_item.category,
                weight=g_item.weight,
                is_required=g_item.is_required,
                expected_evidence=g_item.expected_evidence,
                suggested_for_domains=g_item.suggested_for_domains,
                order=g_item.order
            )
            db.add(new_item)
            added += 1

        # Apply updates if strategy allows
        if req.strategy == "add_and_update":
            for p_item, g_item in changed_items:
                p_item.area = g_item.area
                p_item.question = g_item.question
                p_item.category = g_item.category
                p_item.weight = g_item.weight
                p_item.is_required = g_item.is_required
                p_item.expected_evidence = g_item.expected_evidence
                p_item.order = g_item.order
                updated += 1
                
        await db.commit()
        
        return SyncResult(
            added=added,
            updated=updated,
            flagged_removed=flagged_removed,
            strategy_used=req.strategy,
            flagged_items=flagged_items
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{checklist_id}/items")
async def add_checklist_item(
    checklist_id: int,
    item_in: ChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to a project-specific checklist"""
    try:
        result = await db.execute(select(Checklist).where(Checklist.id == checklist_id))
        checklist = result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")

        project_result = await db.execute(select(Project).where(Project.id == checklist.project_id))
        project = project_result.scalar_one_or_none()
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")

        area = item_in.area.strip() if item_in.area else ""
        
        # Handle item_code: auto-generate or validate manual override
        item_code = item_in.item_code.strip() if item_in.item_code else ""
        if not item_code:
            # Auto-generate
            item_code = await _generate_item_code(db, checklist_id, area)
        else:
            # Validate manual override
            valid = await _validate_item_code(db, checklist_id, item_code, area)
            if not valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid item_code '{item_code}'. Must match pattern AREA-NNN (e.g., SEC-001) where AREA is a registered area code."
                )

        new_item = ChecklistItem(
            checklist_id=checklist_id,
            item_code=item_code,
            area=area,
            question=item_in.question.strip() if item_in.question else "",
            category=item_in.category.strip() if item_in.category else None,
            weight=item_in.weight,
            is_required=item_in.is_required,
            expected_evidence=item_in.expected_evidence.strip() if item_in.expected_evidence else None,
            order=item_in.order
        )
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)

        return {
            "id": new_item.id,
            "checklist_id": new_item.checklist_id,
            "area": new_item.area,
            "question": new_item.question,
            "category": new_item.category,
            "weight": new_item.weight,
            "is_required": new_item.is_required,
            "expected_evidence": new_item.expected_evidence,
            "item_code": new_item.item_code,
            "order": new_item.order
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    checklist_id: int,
    item_id: int,
    item_in: ChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update item on a project-specific checklist"""
    try:
        result = await db.execute(select(Checklist).where(Checklist.id == checklist_id))
        checklist = result.scalar_one_or_none()
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project_result = await db.execute(select(Project).where(Project.id == checklist.project_id))
        project = project_result.scalar_one_or_none()
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
        item_result = await db.execute(
            select(ChecklistItem).where(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        )
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
            
        update_data = item_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
            
        await db.commit()
        await db.refresh(item)
        
        return {
            "id": item.id,
            "checklist_id": item.checklist_id,
            "area": item.area,
            "question": item.question,
            "category": item.category,
            "weight": item.weight,
            "is_required": item.is_required,
            "expected_evidence": item.expected_evidence,
            "item_code": item.item_code,
            "order": item.order
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{checklist_id}/items/{item_id}")
async def delete_checklist_item(
    checklist_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete item from a project-specific checklist"""
    try:
        result = await db.execute(select(Checklist).where(Checklist.id == checklist_id))
        checklist = result.scalar_one_or_none()
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project_result = await db.execute(select(Project).where(Project.id == checklist.project_id))
        project = project_result.scalar_one_or_none()
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
        item_result = await db.execute(
            select(ChecklistItem).where(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        )
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
            
        await db.delete(item)
        await db.commit()
        return {"message": "Item deleted successfully"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{checklist_id}/items/reorder")
async def reorder_checklist_items(
    checklist_id: int,
    orders: List[ItemReorderReq],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder multiple items on a project-specific checklist"""
    try:
        result = await db.execute(select(Checklist).where(Checklist.id == checklist_id))
        checklist = result.scalar_one_or_none()
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project_result = await db.execute(select(Project).where(Project.id == checklist.project_id))
        project = project_result.scalar_one_or_none()
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
        # Build order map
        order_map = {req.id: req.order for req in orders}
        
        items_result = await db.execute(
            select(ChecklistItem).where(
                ChecklistItem.checklist_id == checklist_id,
                ChecklistItem.id.in_(order_map.keys())
            )
        )
        items = items_result.scalars().all()
        
        for item in items:
            item.order = order_map[item.id]
            
        await db.commit()
        return {"message": "Items reordered successfully"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project-specific checklist and all its items.
    Blocked if any reviews (manual or autonomous) have been run against this checklist.
    Global checklists cannot be deleted via this endpoint.
    """
    try:
        result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if checklist.is_global:
            raise HTTPException(
                status_code=403,
                detail="Global checklists cannot be deleted here. Use the admin panel."
            )

        # Ownership check
        project_result = await db.execute(
            select(Project).where(Project.id == checklist.project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this checklist")

        # Dependency check: classic review sessions
        review_count_result = await db.execute(
            select(func.count()).select_from(Review).where(Review.checklist_id == checklist_id)
        )
        review_count = review_count_result.scalar() or 0

        # Dependency check: autonomous review jobs
        job_count_result = await db.execute(
            select(func.count()).select_from(AutonomousReviewJob).where(
                AutonomousReviewJob.checklist_id == checklist_id
            )
        )
        job_count = job_count_result.scalar() or 0

        total_reviews = review_count + job_count
        if total_reviews > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot delete: this checklist has {total_reviews} review(s) on record. "
                    "Deleting it would remove historical review data. "
                    "Archive the checklist or contact an admin if deletion is required."
                )
            )

        # Safe to delete — cascade removes all ChecklistItems
        await db.delete(checklist)
        await db.commit()

        return {"message": f"Checklist '{checklist.name}' deleted successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Global Checklist Management (Admin Only)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/globals")
async def create_global_checklist(
    req: GlobalChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new global checklist (empty, no items).
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        checklist = Checklist(
            name=req.name.strip(),
            type=req.type,
            version=req.version.strip() if req.version else "1.0",
            is_global=True,
            project_id=None,
            source_checklist_id=None
        )

        db.add(checklist)
        await db.commit()
        await db.refresh(checklist)

        logger.info(f"Global checklist created: {checklist.name} (ID: {checklist.id}) by {current_user.email}")

        return {
            "id": checklist.id,
            "name": checklist.name,
            "type": checklist.type,
            "version": checklist.version,
            "is_global": True,
            "item_count": 0
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/globals/{checklist_id}")
async def update_global_checklist(
    checklist_id: int,
    req: GlobalChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rename a global checklist or update its version.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only update global checklists")

        if req.name is not None:
            if not req.name.strip():
                raise HTTPException(status_code=400, detail="Name cannot be empty")
            checklist.name = req.name.strip()

        if req.version is not None:
            checklist.version = req.version.strip() if req.version.strip() else "1.0"

        checklist.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(checklist)

        logger.info(f"Global checklist updated: {checklist.name} (ID: {checklist.id}) by {current_user.email}")

        return {
            "id": checklist.id,
            "name": checklist.name,
            "version": checklist.version
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/globals/{checklist_id}")
async def delete_global_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a global checklist.
    Requires admin role.
    Blocked if any project checklists are cloned from it or if reviews exist.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only delete global checklists")

        # Check for cloned project checklists
        cloned_count_result = await db.execute(
            select(func.count()).select_from(Checklist).where(
                Checklist.source_checklist_id == checklist_id
            )
        )
        cloned_count = cloned_count_result.scalar() or 0

        if cloned_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: {cloned_count} project checklist(s) are cloned from this template. Remove those first."
            )

        # Check for autonomous review jobs
        job_count_result = await db.execute(
            select(func.count()).select_from(AutonomousReviewJob).where(
                AutonomousReviewJob.checklist_id == checklist_id
            )
        )
        job_count = job_count_result.scalar() or 0

        if job_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: {job_count} autonomous review job(s) reference this checklist."
            )

        # Check for manual reviews
        review_count_result = await db.execute(
            select(func.count()).select_from(Review).where(
                Review.checklist_id == checklist_id
            )
        )
        review_count = review_count_result.scalar() or 0

        if review_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: {review_count} review session(s) reference this checklist."
            )

        # Safe to delete — cascade removes all ChecklistItems
        checklist_name = checklist.name
        await db.delete(checklist)
        await db.commit()

        logger.info(f"Global checklist deleted: {checklist_name} (ID: {checklist_id}) by {current_user.email}")

        return {"message": f"Global checklist '{checklist_name}' deleted successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/globals/{checklist_id}/items")
async def add_item_to_global_checklist(
    checklist_id: int,
    item_in: GlobalChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add an item to a global checklist.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only add items to global checklists")

        area = item_in.area.strip()
        
        # Handle item_code: auto-generate or validate manual override
        item_code = item_in.item_code.strip() if item_in.item_code else ""
        if not item_code:
            # Auto-generate
            item_code = await _generate_item_code(db, checklist_id, area)
        else:
            # Validate manual override
            valid = await _validate_item_code(db, checklist_id, item_code, area)
            if not valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid item_code '{item_code}'. Must match pattern AREA-NNN (e.g., SEC-001) where AREA is a registered area code for this checklist."
                )

        item = ChecklistItem(
            checklist_id=checklist_id,
            item_code=item_code,
            area=area,
            question=item_in.question.strip(),
            category=item_in.category.strip() if item_in.category else None,
            weight=item_in.weight,
            is_required=item_in.is_required,
            expected_evidence=item_in.expected_evidence.strip() if item_in.expected_evidence else None,
            order=item_in.order
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)

        logger.info(
            f"Item added to global checklist: checklist_id={checklist_id}, "
            f"item_code={item.item_code} by {current_user.email}"
        )

        return {
            "id": item.id,
            "checklist_id": item.checklist_id,
            "item_code": item.item_code,
            "area": item.area,
            "question": item.question,
            "category": item.category,
            "weight": item.weight,
            "is_required": item.is_required,
            "expected_evidence": item.expected_evidence,
            "order": item.order
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding item to global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/globals/{checklist_id}/items/{item_id}")
async def update_item_in_global_checklist(
    checklist_id: int,
    item_id: int,
    item_in: GlobalChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an item on a global checklist.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        # Verify checklist is global
        checklist_result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = checklist_result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only update items in global checklists")

        # Get the item
        item_result = await db.execute(
            select(ChecklistItem).where(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        )
        item = item_result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Update fields
        update_data = item_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if isinstance(value, str):
                    setattr(item, key, value.strip())
                else:
                    setattr(item, key, value)

        await db.commit()
        await db.refresh(item)

        logger.info(
            f"Item updated in global checklist: checklist_id={checklist_id}, item_id={item_id} by {current_user.email}"
        )

        return {
            "id": item.id,
            "checklist_id": item.checklist_id,
            "item_code": item.item_code,
            "area": item.area,
            "question": item.question,
            "category": item.category,
            "weight": item.weight,
            "is_required": item.is_required,
            "expected_evidence": item.expected_evidence,
            "order": item.order
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating item in global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/globals/{checklist_id}/items/{item_id}")
async def delete_item_from_global_checklist(
    checklist_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an item from a global checklist.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        # Verify checklist is global
        checklist_result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = checklist_result.scalar_one_or_none()

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only delete items from global checklists")

        # Get the item
        item_result = await db.execute(
            select(ChecklistItem).where(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        )
        item = item_result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        await db.delete(item)
        await db.commit()

        logger.info(
            f"Item deleted from global checklist: checklist_id={checklist_id}, item_id={item_id} by {current_user.email}"
        )

        return {"message": "Item deleted"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting item from global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
