"""Persona management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from recorder.db.session import get_db
from recorder.schemas.persona import PersonaCreate, PersonaResponse

router = APIRouter()


@router.post("/", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: PersonaCreate,
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    from recorder.db.models import Persona
    persona = Persona(
        session_id=body.session_id,
        role_title=body.role_title,
        role_description=body.role_description,
        accountability_areas=body.accountability_areas,
        decision_domains=body.decision_domains,
        success_criteria=body.success_criteria,
        irrelevant_topics=body.irrelevant_topics,
        prior_open_questions=body.prior_open_questions,
        is_async=body.is_async,
        template=body.template,
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return PersonaResponse.model_validate(persona)


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str, db: AsyncSession = Depends(get_db)) -> PersonaResponse:
    from sqlalchemy import select
    from recorder.db.models import Persona
    result = await db.execute(select(Persona).where(Persona.persona_id == persona_id))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaResponse.model_validate(persona)


@router.get("/{persona_id}/briefing")
async def get_briefing(persona_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from sqlalchemy import select
    from recorder.db.models import Persona
    result = await db.execute(select(Persona).where(Persona.persona_id == persona_id))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.briefing:
        raise HTTPException(status_code=404, detail="Briefing not yet generated (post-meeting only)")
    return persona.briefing
