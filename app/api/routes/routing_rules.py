"""
Routing Rules API
Allows admins/PMs/leads to mark checklist items as human_required
so the strategy router skips automated analysis on future reviews.

POST   /api/routing-rules/items/{item_id}    – create / update rule
DELETE /api/routing-rules/items/{item_id}    – remove rule (restore auto routing)
GET    /api/routing-rules/items/{item_id}    – get current rule for an item
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.models import ChecklistRoutingRule, ChecklistItem

router = APIRouter()


class RoutingRuleRequest(BaseModel):
    strategy: str = "human_required"
    skip_reason: Optional[str] = None
    evidence_hint: Optional[str] = None


@router.get("/items/{item_id}")
async def get_routing_rule(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get the active routing rule for a checklist item, if any."""
    result = await db.execute(
        select(ChecklistRoutingRule)
        .where(ChecklistRoutingRule.checklist_item_id == item_id)
        .where(ChecklistRoutingRule.is_active == True)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return {"rule": None}
    return {
        "rule": {
            "id": rule.id,
            "strategy": rule.strategy,
            "skip_reason": rule.skip_reason,
            "evidence_hint": rule.evidence_hint,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }
    }


@router.post("/items/{item_id}")
async def set_routing_rule(
    item_id: int,
    body: RoutingRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create or replace the routing rule for a checklist item."""
    # Verify item exists
    item = await db.get(ChecklistItem, item_id)
    if not item:
        raise HTTPException(404, f"Checklist item {item_id} not found")

    valid_strategies = {"human_required", "ai_and_human", "llm_analysis", "file_presence", "pattern_scan"}
    if body.strategy not in valid_strategies:
        raise HTTPException(400, f"strategy must be one of: {', '.join(valid_strategies)}")

    # Deactivate any existing rule for this item
    existing = await db.execute(
        select(ChecklistRoutingRule)
        .where(ChecklistRoutingRule.checklist_item_id == item_id)
        .where(ChecklistRoutingRule.is_active == True)
    )
    for old in existing.scalars().all():
        old.is_active = False

    rule = ChecklistRoutingRule(
        checklist_item_id=item_id,
        strategy=body.strategy,
        skip_reason=body.skip_reason or f"Manually marked as {body.strategy} by reviewer",
        evidence_hint=body.evidence_hint,
        created_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {
        "status": "created",
        "rule": {
            "id": rule.id,
            "item_id": item_id,
            "strategy": rule.strategy,
            "skip_reason": rule.skip_reason,
            "evidence_hint": rule.evidence_hint,
        }
    }


@router.delete("/items/{item_id}")
async def delete_routing_rule(item_id: int, db: AsyncSession = Depends(get_db)):
    """Remove the routing rule — item returns to automatic strategy selection."""
    result = await db.execute(
        select(ChecklistRoutingRule)
        .where(ChecklistRoutingRule.checklist_item_id == item_id)
        .where(ChecklistRoutingRule.is_active == True)
    )
    rules = result.scalars().all()
    if not rules:
        raise HTTPException(404, "No active routing rule found for this item")

    for rule in rules:
        rule.is_active = False
    await db.commit()

    return {"status": "deleted", "item_id": item_id}
