from typing import Optional, List, Dict, Any, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
import logging
from datetime import datetime

from app.models import (
    Checklist, ChecklistItem, ChecklistRecommendation, Project, Review,
    AutonomousReviewJob, ChecklistRoutingRule, User
)
from app.services.checklist_optimizer import get_checklist_optimizer
from app.schemas.checklist import (
    ChecklistItemCreate, ChecklistItemUpdate, ItemReorderReq,
    CloneChecklistReq, SyncStrategyReq, GlobalChecklistCreate,
    GlobalChecklistUpdate, GlobalChecklistItemCreate, GlobalChecklistItemUpdate
)

logger = logging.getLogger(__name__)


def _generate_area_code(area_name: str) -> str:
    """
    Generate a 3-4 letter area code from area name.
    Uses consonants and first letter, uppercase.
    """
    import re
    words = re.sub(r'[^a-zA-Z\s]', '', area_name).split()
    
    consonants = set('BCDFGHJKLMNPQRSTVWXYZ')
    code = ""
    
    for word in words:
        if len(code) >= 4:
            break
        if word:
            code += word[0].upper()
        for char in word[1:]:
            if char.upper() in consonants and len(code) < 4:
                code += char.upper()
    
    code = (code + "XXX")[:4]
    return code


async def _generate_item_code(db: AsyncSession, checklist_id: int, area: str) -> str:
    """Auto-generate item_code based on area grouping."""
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    area_codes: dict[str, str] = checklist.area_codes or {}
    
    if area not in area_codes:
        area_codes[area] = _generate_area_code(area)
        checklist.area_codes = area_codes
        await db.flush()
    
    area_code = area_codes[area]
    
    result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.checklist_id == checklist_id)
    )
    existing_items = result.scalars().all()
    
    max_seq = 0
    for item in existing_items:
        if item.item_code and item.item_code.startswith(f"{area_code}-"):
            try:
                seq = int(item.item_code.split("-")[1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass
    
    return f"{area_code}-{str(max_seq + 1).zfill(3)}"


async def _validate_item_code(db: AsyncSession, checklist_id: int, item_code: str, area: str) -> bool:
    """Validate manually provided item_code."""
    import re
    
    pattern = r'^[A-Z]{3,4}-\d{3}$'
    if not re.match(pattern, item_code):
        return False
    
    checklist_result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    
    if not checklist:
        return False
    
    area_codes: dict[str, str] = checklist.area_codes or {}
    provided_code = item_code.split("-")[0]
    registered_codes = set(area_codes.values())
    
    if area in area_codes:
        registered_codes.add(area_codes[area])
    else:
        expected_code = _generate_area_code(area)
        registered_codes.add(expected_code)
    
    return provided_code in registered_codes


class ChecklistService:
    @staticmethod
    async def list_checklists(
        db: AsyncSession,
        is_global: Optional[bool] = None,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = select(Checklist).options(selectinload(Checklist.items))
        
        if is_global is not None:
            query = query.where(Checklist.is_global == is_global)
        if project_id is not None:
            query = query.where(Checklist.project_id == project_id)
            
        result = await db.execute(query)
        checklists = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "version": c.version,
                "is_global": c.is_global,
                "project_id": c.project_id,
                "items_count": len(c.items)
            }
            for c in checklists
        ]

    @staticmethod
    async def get_checklist_area_codes(db: AsyncSession, checklist_id: int) -> dict:
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

    @staticmethod
    async def get_checklist(db: AsyncSession, checklist_id: int, include_items: bool) -> dict:
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
            item_ids = [item.id for item in checklist.items]
            strategy_map = {}
            if item_ids:
                rule_result = await db.execute(
                    select(ChecklistRoutingRule)
                    .where(ChecklistRoutingRule.checklist_item_id.in_(item_ids))
                    .where(ChecklistRoutingRule.is_active == True)
                )
                strategy_map = {
                    rule.checklist_item_id: rule.strategy
                    for rule in rule_result.scalars().all()
                }

            response["items"] = [
                {
                    "id": item.id,
                    "item_code": item.item_code,
                    "area": item.area,
                    "question": item.question,
                    "category": item.category,
                    "weight": item.weight,
                    "is_review_mandatory": item.is_review_mandatory,
                    "expected_evidence": item.expected_evidence,
                    "order": item.order,
                    "strategy": strategy_map.get(item.id, "auto"),
                }
                for item in checklist.items
            ]
            response["items_count"] = len(checklist.items)
        
        return response

    @staticmethod
    async def get_checklist_recommendations(db: AsyncSession, checklist_id: int) -> dict:
        result = await db.execute(
            select(Checklist).where(Checklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        
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

    @staticmethod
    async def optimize_checklist(db: AsyncSession, checklist_id: int) -> dict:
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
        
        project_domain = "general"
        if checklist.project:
            project_domain = checklist.project.domain or "general"
        
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
        
        optimizer = get_checklist_optimizer()
        recommendations = await optimizer.analyze_and_recommend(
            project_domain=project_domain,
            current_checklist=current_checklist,
            project_context={
                "project_name": checklist.project.name if checklist.project else None,
                "domain": project_domain
            }
        )
        
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
        
        await db.commit()
        
        return {
            "message": f"Generated {len(recommendations)} recommendations",
            "checklist_id": checklist_id,
            "domain": project_domain,
            "recommendations_count": len(recommendations)
        }

    @staticmethod
    async def get_global_checklist_templates(db: AsyncSession, type: Optional[str]) -> dict:
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

    @staticmethod
    async def clone_checklist_to_project(db: AsyncSession, checklist_id: int, project_id: int, req: CloneChecklistReq, current_user: User) -> Checklist:
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

        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        if current_user.role != "admin" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to clone to this project")
            
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
        
        for item in source_checklist.items:
            new_item = ChecklistItem(
                checklist_id=new_checklist.id,
                item_code=item.item_code,
                area=item.area,
                question=item.question,
                category=item.category,
                weight=item.weight,
                is_review_mandatory=item.is_review_mandatory,
                expected_evidence=item.expected_evidence,
                suggested_for_domains=item.suggested_for_domains,
                order=item.order
            )
            db.add(new_item)
            
        await db.commit()
        result = await db.execute(
            select(Checklist)
            .options(selectinload(Checklist.items))
            .where(Checklist.id == new_checklist.id)
        )
        return result.scalar_one()

    @staticmethod
    async def sync_from_global(db: AsyncSession, checklist_id: int, req: SyncStrategyReq, current_user: User) -> dict:
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
            
        project_result = await db.execute(select(Project).where(Project.id == project_checklist.project_id))
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Associated project not found")
            
        if current_user.role != "admin" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this project's checklist")
            
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
            for item in project_checklist.items:
                await db.delete(item)
            
            for g_item in global_checklist.items:
                new_item = ChecklistItem(
                    checklist_id=project_checklist.id,
                    item_code=g_item.item_code,
                    area=g_item.area,
                    question=g_item.question,
                    category=g_item.category,
                    weight=g_item.weight,
                    is_review_mandatory=g_item.is_review_mandatory,
                    expected_evidence=g_item.expected_evidence,
                    suggested_for_domains=g_item.suggested_for_domains,
                    order=g_item.order
                )
                db.add(new_item)
                added += 1
                
            await db.commit()
            return {
                "added": added,
                "updated": 0,
                "flagged_removed": 0,
                "strategy_used": "full_reset",
                "flagged_items": []
            }
            
        p_dict = {item.item_code: item for item in project_checklist.items if item.item_code}
        g_dict = {item.item_code: item for item in global_checklist.items if item.item_code}
        
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
                    p_item.is_review_mandatory != g_item.is_review_mandatory or
                    p_item.expected_evidence != g_item.expected_evidence or
                    p_item.order != g_item.order):
                    changed_items.append((p_item, g_item))
                    
        for p_code in p_dict.keys():
            if p_code not in g_dict:
                flagged_removed += 1
                flagged_items.append(p_code)

        for g_item in new_items:
            new_item = ChecklistItem(
                checklist_id=project_checklist.id,
                item_code=g_item.item_code,
                area=g_item.area,
                question=g_item.question,
                category=g_item.category,
                weight=g_item.weight,
                is_review_mandatory=g_item.is_review_mandatory,
                expected_evidence=g_item.expected_evidence,
                suggested_for_domains=g_item.suggested_for_domains,
                order=g_item.order
            )
            db.add(new_item)
            added += 1

        if req.strategy == "add_and_update":
            for p_item, g_item in changed_items:
                p_item.area = g_item.area
                p_item.question = g_item.question
                p_item.category = g_item.category
                p_item.weight = g_item.weight
                p_item.is_review_mandatory = g_item.is_review_mandatory
                p_item.expected_evidence = g_item.expected_evidence
                p_item.order = g_item.order
                updated += 1
                
        await db.commit()
        
        return {
            "added": added,
            "updated": updated,
            "flagged_removed": flagged_removed,
            "strategy_used": req.strategy,
            "flagged_items": flagged_items
        }

    @staticmethod
    async def add_checklist_item(db: AsyncSession, checklist_id: int, item_in: ChecklistItemCreate, current_user: User) -> ChecklistItem:
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")

        project = await db.get(Project, checklist.project_id)
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")

        area = item_in.area.strip() if item_in.area else ""
        
        item_code = item_in.item_code.strip() if item_in.item_code else ""
        if not item_code:
            item_code = await _generate_item_code(db, checklist_id, area)
        else:
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
            is_review_mandatory=item_in.is_review_mandatory,
            expected_evidence=item_in.expected_evidence.strip() if item_in.expected_evidence else None,
            order=item_in.order
        )
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item

    @staticmethod
    async def update_checklist_item(db: AsyncSession, checklist_id: int, item_id: int, item_in: ChecklistItemUpdate, current_user: User) -> ChecklistItem:
        checklist = await db.get(Checklist, checklist_id)
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project = await db.get(Project, checklist.project_id)
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
        item = await db.get(ChecklistItem, item_id)
        
        if not item or item.checklist_id != checklist_id:
            raise HTTPException(status_code=404, detail="Item not found")
            
        update_data = item_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
            
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_checklist_item(db: AsyncSession, checklist_id: int, item_id: int, current_user: User):
        checklist = await db.get(Checklist, checklist_id)
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project = await db.get(Project, checklist.project_id)
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
        item = await db.get(ChecklistItem, item_id)
        
        if not item or item.checklist_id != checklist_id:
            raise HTTPException(status_code=404, detail="Item not found")
            
        await db.delete(item)
        await db.commit()

    @staticmethod
    async def reorder_checklist_items(db: AsyncSession, checklist_id: int, orders: List[ItemReorderReq], current_user: User):
        checklist = await db.get(Checklist, checklist_id)
        
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
            
        if checklist.is_global:
            raise HTTPException(status_code=403, detail="Cannot modify global checklist")
            
        project = await db.get(Project, checklist.project_id)
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this checklist")
            
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

    @staticmethod
    async def delete_checklist(db: AsyncSession, checklist_id: int, current_user: User):
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if checklist.is_global:
            raise HTTPException(
                status_code=403,
                detail="Global checklists cannot be deleted here. Use the admin panel."
            )

        project = await db.get(Project, checklist.project_id)
        if not project or (current_user.role != "admin" and project.owner_id != current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this checklist")

        review_count_result = await db.execute(
            select(func.count()).select_from(Review).where(Review.checklist_id == checklist_id)
        )
        review_count = review_count_result.scalar() or 0

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

        await db.delete(checklist)
        await db.commit()
        logger.info(f"Checklist '{checklist.name}' deleted successfully by {current_user.email}")

    @staticmethod
    async def create_global_checklist(db: AsyncSession, req: GlobalChecklistCreate) -> Checklist:
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
        return checklist

    @staticmethod
    async def update_global_checklist(db: AsyncSession, checklist_id: int, req: GlobalChecklistUpdate) -> Checklist:
        checklist = await db.get(Checklist, checklist_id)

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
        return checklist

    @staticmethod
    async def delete_global_checklist(db: AsyncSession, checklist_id: int):
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only delete global checklists")

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

        await db.delete(checklist)
        await db.commit()

    @staticmethod
    async def add_item_to_global_checklist(db: AsyncSession, checklist_id: int, item_in: GlobalChecklistItemCreate) -> ChecklistItem:
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only add items to global checklists")

        area = item_in.area.strip()
        
        item_code = item_in.item_code.strip() if item_in.item_code else ""
        if not item_code:
            item_code = await _generate_item_code(db, checklist_id, area)
        else:
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
            is_review_mandatory=item_in.is_review_mandatory,
            expected_evidence=item_in.expected_evidence.strip() if item_in.expected_evidence else None,
            order=item_in.order
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def update_item_in_global_checklist(db: AsyncSession, checklist_id: int, item_id: int, item_in: GlobalChecklistItemUpdate) -> ChecklistItem:
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only update items in global checklists")

        item = await db.get(ChecklistItem, item_id)

        if not item or item.checklist_id != checklist_id:
            raise HTTPException(status_code=404, detail="Item not found")

        update_data = item_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if isinstance(value, str):
                setattr(item, key, value.strip())
            else:
                setattr(item, key, value)

        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_item_from_global_checklist(db: AsyncSession, checklist_id: int, item_id: int):
        checklist = await db.get(Checklist, checklist_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if not checklist.is_global:
            raise HTTPException(status_code=400, detail="Can only delete items from global checklists")

        item = await db.get(ChecklistItem, item_id)

        if not item or item.checklist_id != checklist_id:
            raise HTTPException(status_code=404, detail="Item not found")

        await db.delete(item)
        await db.commit()