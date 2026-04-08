"""Session management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from recorder.db.session import get_db
from recorder.schemas.session import QueryRequest, QueryResponse, SessionCreate, SessionResponse
from recorder.services.session_manager import transition_session

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    from recorder.db.models import Session
    session = Session(
        project_id=body.project_id,
        title=body.title,
        meeting_focus=body.meeting_focus,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionResponse]:
    from sqlalchemy import select
    from recorder.db.models import Session
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    return [SessionResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/{session_id}/start")
async def start_session(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Activate OBS watcher and initialise agents. Transitions to in_progress."""
    session = await transition_session(db, session_id, "in_progress")
    return {"session_id": session_id, "status": session.status}


@router.post("/{session_id}/complete")
async def complete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """End meeting. Transitions to post_meeting and triggers briefing generation."""
    session = await transition_session(db, session_id, "post_meeting")
    return {"session_id": session_id, "status": session.status, "note": "briefing generation queued"}


@router.post("/{session_id}/query", response_model=QueryResponse)
async def submit_query(
    session_id: str,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Submit a text query. Orchestrator routes to best agent. Phase 1 (Default Expert only)."""
    # Phase 1: route to Default Expert agent
    # Phase 4+: orchestrator routes to specialist agents
    return QueryResponse(
        session_id=session_id,
        question=body.text,
        answer="[Phase 1 MVP — agent implementation pending]",
        responding_agent="Default Expert",
        citations=[],
        conflicts_detected=[],
    )


@router.get("/{session_id}/transcript")
async def get_transcript(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from recorder.db.models import Session
    result = await db.execute(
        select(Session)
        .where(Session.session_id == session_id)
        .options(selectinload(Session.transcript_chunks))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    chunks = [
        {"chunk_id": c.chunk_id, "start_time": c.start_time, "end_time": c.end_time, "text": c.text}
        for c in sorted(session.transcript_chunks, key=lambda x: x.start_time)
    ]
    return {"session_id": session_id, "chunks": chunks}
