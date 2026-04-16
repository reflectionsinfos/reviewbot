"""
Checklists API Routes
"""
import logging
import os
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.models import Checklist, ChecklistItem, User
from app.api.routes.auth import get_current_user
from app.services.checklist_parser import parse_excel_checklist
from app.services.checklist_service import ChecklistService, _generate_item_code
from app.schemas.checklist import (
    ChecklistItemCreate, ChecklistItemUpdate, ItemReorderReq,
    CloneChecklistResponse, CloneChecklistReq, SyncStrategyReq, SyncResult,
    GlobalChecklistCreate, GlobalChecklistUpdate,
    GlobalChecklistItemCreate, GlobalChecklistItemUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_checklists(
    is_global: Optional[bool] = None,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List checklists with optional filters."""
    return await ChecklistService.list_checklists(db, is_global=is_global, project_id=project_id)


@router.get("/globals/{checklist_id}/area-codes")
async def get_checklist_area_codes(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get area code mapping for a checklist. Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return await ChecklistService.get_checklist_area_codes(db, checklist_id)
    
@router.get("/{checklist_id}")
async def get_checklist(
    checklist_id: int,
    include_items: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get checklist details"""
    return await ChecklistService.get_checklist(db, checklist_id, include_items)


@router.get("/{checklist_id}/recommendations")
async def get_checklist_recommendations(
    checklist_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated recommendations for checklist improvement"""
    return await ChecklistService.get_checklist_recommendations(db, checklist_id)


@router.post("/{checklist_id}/optimize")
async def optimize_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI recommendations for checklist optimization"""
    return await ChecklistService.optimize_checklist(db, checklist_id)


@router.get("/templates/global")
async def get_global_checklist_templates(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get global checklist templates"""
    return await ChecklistService.get_global_checklist_templates(db, type)


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
    try:
        new_checklist = await ChecklistService.clone_checklist_to_project(
            db, checklist_id, project_id, req, current_user
        )
        
        return CloneChecklistResponse(
            id=new_checklist.id,
            name=new_checklist.name,
            type=new_checklist.type,
            version=new_checklist.version,
            project_id=new_checklist.project_id,
            is_global=new_checklist.is_global,
            item_count=len(new_checklist.items),
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
        sync_data = await ChecklistService.sync_from_global(db, checklist_id, req, current_user)
        return SyncResult(
            added=sync_data["added"],
            updated=sync_data["updated"],
            flagged_removed=sync_data["flagged_removed"],
            strategy_used=sync_data["strategy_used"],
            flagged_items=sync_data["flagged_items"]
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
        new_item = await ChecklistService.add_checklist_item(db, checklist_id, item_in, current_user)

        return {
            "id": new_item.id,
            "checklist_id": new_item.checklist_id,
            "area": new_item.area,
            "question": new_item.question,
            "category": new_item.category,
            "weight": new_item.weight,
            "is_review_mandatory": new_item.is_review_mandatory,
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
        item = await ChecklistService.update_checklist_item(db, checklist_id, item_id, item_in, current_user)
        
        return {
            "id": item.id,
            "checklist_id": item.checklist_id,
            "area": item.area,
            "question": item.question,
            "category": item.category,
            "weight": item.weight,
            "is_review_mandatory": item.is_review_mandatory,
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
        await ChecklistService.delete_checklist_item(db, checklist_id, item_id, current_user)
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
        await ChecklistService.reorder_checklist_items(db, checklist_id, orders, current_user)
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
        await ChecklistService.delete_checklist(db, checklist_id, current_user)
        return {"message": f"Checklist deleted successfully"}

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
        checklist = await ChecklistService.create_global_checklist(db, req)
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
        checklist = await ChecklistService.update_global_checklist(db, checklist_id, req)
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
        await ChecklistService.delete_global_checklist(db, checklist_id)
        logger.info(f"Global checklist (ID: {checklist_id}) deleted by {current_user.email}")
        return {"message": f"Global checklist deleted successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/globals/upload")
async def upload_global_checklist(
    file: UploadFile = File(..., description="Excel checklist file (.xlsx)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an Excel checklist file and create one or more global templates.
    Parses sheets named 'Delivery Check List V 1.0' and/or 'Technical Check List V 1.0'.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xlsm files are supported")

    # Validate file size (25 MB limit)
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 25 MB)")

    # Save to temp file and parse
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        parsed = await parse_excel_checklist(tmp_path)
        checklists_data = parsed.get("checklists", {})

        if not checklists_data:
            raise HTTPException(status_code=422, detail="No recognisable checklist sheets found in this file")

        created = []
        for checklist_type, items in checklists_data.items():
            if not items:
                continue

            # Derive a name from the original filename (strip extension)
            base_name = os.path.splitext(filename)[0]
            checklist_name = f"{base_name} ({checklist_type.capitalize()})"

            checklist = Checklist(
                name=checklist_name,
                type=checklist_type,
                version="1.0",
                is_global=True,
                project_id=None,
            )
            db.add(checklist)
            await db.flush()  # get checklist.id

            for order, item_data in enumerate(items):
                area = item_data.get("area", "General")
                # Generate AREA-NNN code (registers area abbreviation on checklist.area_codes)
                item_code = await _generate_item_code(db, checklist.id, area)
                item = ChecklistItem(
                    checklist_id=checklist.id,
                    item_code=item_code,
                    area=area,
                    question=item_data.get("question", ""),
                    category=item_data.get("category", checklist_type),
                    weight=item_data.get("weight", 1.0),
                    is_review_mandatory=item_data.get("is_review_mandatory", True),
                    expected_evidence=item_data.get("expected_evidence"),
                    order=order,
                )
                db.add(item)

            await db.flush()
            created.append({
                "id": checklist.id,
                "name": checklist.name,
                "type": checklist.type,
                "version": checklist.version,
                "item_count": len(items),
            })

        await db.commit()
        logger.info(
            f"Global checklist(s) uploaded from '{filename}' by {current_user.email}: "
            f"{[c['name'] for c in created]}"
        )
        return {"created": created}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading global checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse Excel file: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
        item = await ChecklistService.add_item_to_global_checklist(db, checklist_id, item_in)
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
            "is_review_mandatory": item.is_review_mandatory,
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
        item = await ChecklistService.update_item_in_global_checklist(db, checklist_id, item_id, item_in)
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
            "is_review_mandatory": item.is_review_mandatory,
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
        await ChecklistService.delete_item_from_global_checklist(db, checklist_id, item_id)
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
