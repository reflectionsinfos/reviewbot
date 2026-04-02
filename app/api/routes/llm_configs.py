from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models import LLMConfig, User
from app.api.routes.auth import get_current_user
from app.services.autonomous_review.connectors.llm import validate_llm_connectivity

router = APIRouter()

# --- Pydantic Schemas ---
class LLMConfigBase(BaseModel):
    name: str
    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    is_active: bool = False
    config_params: Optional[dict] = None
    max_requests_limit: Optional[int] = None
    max_tokens_limit: Optional[int] = None

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    is_active: Optional[bool] = None
    config_params: Optional[dict] = None
    max_requests_limit: Optional[int] = None
    max_tokens_limit: Optional[int] = None

class LLMConfigRead(LLMConfigBase):
    id: int
    total_tokens_used: int
    total_requests_made: int
    last_usage_reset_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.post("/test-connection")
async def test_llm_connection(
    config_in: LLMConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """Test a configuration before saving it. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to test configurations")
    
    # Create a temporary model instance (not saved to DB)
    temp_config = LLMConfig(**config_in.model_dump())
    
    # Connectivity Test
    success, message = await validate_llm_connectivity(overriding_config=temp_config)
    
    return {
        "success": success,
        "message": message
    }


@router.get("/", response_model=List[LLMConfigRead])
async def list_llm_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all LLM configurations. Only accessible by admins/managers."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")
    
    result = await db.execute(select(LLMConfig).order_by(LLMConfig.id))
    return result.scalars().all()


@router.post("/", response_model=LLMConfigRead)
async def create_llm_config(
    config_in: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new LLM configuration. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")
    
    # If this is active, deactivate others
    if config_in.is_active:
        await db.execute(update(LLMConfig).values(is_active=False))
    
    db_config = LLMConfig(**config_in.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.get("/{config_id}", response_model=LLMConfigRead)
async def get_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific LLM configuration by ID. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")

    result = await db.execute(select(LLMConfig).filter(LLMConfig.id == config_id))
    db_config = result.scalar_one_or_none()

    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return db_config


@router.patch("/{config_id}", response_model=LLMConfigRead)
async def update_llm_config(
    config_id: int,
    config_in: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing LLM configuration. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")
    
    result = await db.execute(select(LLMConfig).filter(LLMConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # If setting to active, deactivate others
    if config_in.is_active:
        await db.execute(update(LLMConfig).values(is_active=False))
    
    update_data = config_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an LLM configuration. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")
    
    result = await db.execute(select(LLMConfig).filter(LLMConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    await db.delete(db_config)
    await db.commit()
    return None


@router.post("/{config_id}/activate", response_model=LLMConfigRead)
async def activate_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set a specific LLM configuration as active. Admin only."""
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage LLM configurations")
    
    # Deactivate all
    await db.execute(update(LLMConfig).values(is_active=False))
    
    # Activate selected
    result = await db.execute(select(LLMConfig).filter(LLMConfig.id == config_id))
    db_config = result.scalar_one_or_none()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db_config.is_active = True
    await db.commit()
    await db.refresh(db_config)
    return db_config
