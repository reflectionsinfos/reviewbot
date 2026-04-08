"""Chat and understanding document endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from recorder.db.session import get_db

router = APIRouter()


@router.get("/sessions/{session_id}/understanding")
async def get_understanding_doc(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from sqlalchemy import select
    from recorder.db.models import UnderstandingDocument
    result = await db.execute(
        select(UnderstandingDocument)
        .where(UnderstandingDocument.session_id == session_id)
        .order_by(UnderstandingDocument.version.desc())
    )
    doc = result.scalar_one_or_none()
    if not doc:
        return {"session_id": session_id, "version": 0, "content": {}}
    return {"session_id": session_id, "version": doc.version, "content": doc.content}


@router.get("/sessions/{session_id}/conflicts")
async def get_conflicts(session_id: str, db: AsyncSession = Depends(get_db)) -> list:
    from sqlalchemy import select
    from recorder.db.models import Conflict
    result = await db.execute(
        select(Conflict).where(Conflict.session_id == session_id)
    )
    return [
        {
            "conflict_id": c.conflict_id,
            "topic": c.topic,
            "agents_involved": c.agents_involved,
            "agent_positions": c.agent_positions,
            "conflict_type": c.conflict_type,
            "resolution_status": c.resolution_status,
        }
        for c in result.scalars().all()
    ]
