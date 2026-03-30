from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
from pydantic import BaseModel

from app.db.session import get_db
from app.models import SystemSetting, User
from app.api.routes.auth import get_current_user

router = APIRouter()

class SettingUpdate(BaseModel):
    value: str

class SettingRead(BaseModel):
    key: str
    value: str
    category: str
    is_mandatory: bool
    description: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SettingRead])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all system settings. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage settings")
    
    result = await db.execute(select(SystemSetting))
    return result.scalars().all()

@router.patch("/{key}", response_model=SettingRead)
async def update_setting(
    key: str,
    setting_in: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a system setting. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage settings")
    
    result = await db.execute(select(SystemSetting).filter(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    setting.value = setting_in.value
    await db.commit()
    await db.refresh(setting)
    return setting

@router.get("/public")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """Public settings for UI branding (no auth required)"""
    keys = ["APP_NAME", "DEFAULT_LANGUAGE"]
    result = await db.execute(select(SystemSetting).filter(SystemSetting.key.in_(keys)))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}
