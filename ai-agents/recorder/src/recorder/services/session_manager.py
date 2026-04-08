"""Session lifecycle management.

Session states:
  pre_meeting   → interviews running, knowledge loading, watcher activating
  in_progress   → segments arriving, agents processing, chat active
  post_meeting  → briefings generating, understanding doc co-creation active
  archived      → understanding doc finalised, briefings delivered
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from recorder.core.exceptions import SessionNotFoundError, SessionStateError
from recorder.db.models import Session

VALID_TRANSITIONS = {
    "pre_meeting": ["in_progress"],
    "in_progress": ["post_meeting"],
    "post_meeting": ["archived"],
    "archived": [],
}


async def get_session(db: AsyncSession, session_id: str) -> Session:
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise SessionNotFoundError(f"Session {session_id} not found")
    return session


async def transition_session(db: AsyncSession, session_id: str, new_status: str) -> Session:
    """Transition a session to a new status, validating the transition."""
    session = await get_session(db, session_id)
    allowed = VALID_TRANSITIONS.get(session.status, [])
    if new_status not in allowed:
        raise SessionStateError(
            f"Cannot transition {session.status} → {new_status}. Allowed: {allowed}"
        )
    session.status = new_status
    if new_status == "in_progress":
        session.start_time = datetime.now(timezone.utc)
    elif new_status == "post_meeting":
        session.end_time = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session
