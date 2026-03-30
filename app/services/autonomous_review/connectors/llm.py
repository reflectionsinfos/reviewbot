"""
Shared LLM client helpers for autonomous review flows.
"""
from __future__ import annotations

import logging
from typing import Optional
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import LLMConfig
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Cache for the active config to avoid DB hits on every item
_active_config_cache: Optional[LLMConfig] = None


async def get_active_config(db: Optional[AsyncSession] = None) -> Optional[LLMConfig]:
    """Fetch the active LLM configuration from the database."""
    global _active_config_cache
    
    if db is None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(LLMConfig).filter(LLMConfig.is_active == True))
            _active_config_cache = result.scalar_one_or_none()
    else:
        result = await db.execute(select(LLMConfig).filter(LLMConfig.is_active == True))
        _active_config_cache = result.scalar_one_or_none()
    
    return _active_config_cache


async def get_llm_client(db: Optional[AsyncSession] = None, overriding_config: Optional[LLMConfig] = None) -> AsyncOpenAI:
    """Return an OpenAI-compatible async client for the dynamic or configured provider."""
    config = overriding_config or await get_active_config(db)
    
    if config:
        logger.info(f"Using{' overriding' if overriding_config else ' dynamic'} LLM config: {config.name} ({config.provider})")
        
        # Determine base URL based on provider if not explicitly set
        base_url = config.base_url
        if not base_url:
            if config.provider == "groq":
                base_url = "https://api.groq.com/openai/v1"
            elif config.provider == "google" or config.provider == "google-gemini":
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            elif config.provider == "anthropic":
                base_url = "https://api.anthropic.com/v1/messages" # Note: requires proxy usually
        
        return AsyncOpenAI(
            api_key=config.api_key.strip() if config.api_key else config.api_key,
            base_url=base_url
        )

    # Fallback to .env settings
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()

    if provider == "groq":
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

    if provider == "azure":
        return AsyncOpenAI(api_key=settings.AZURE_OPENAI_API_KEY or settings.OPENAI_API_KEY)

    if provider == "qwen":
        return AsyncOpenAI(api_key=settings.QWEN_API_KEY or settings.OPENAI_API_KEY)

    if provider == "anthropic":
        return AsyncOpenAI(api_key=settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY)

    if provider == "google":
        return AsyncOpenAI(api_key=settings.GOOGLE_API_KEY or settings.OPENAI_API_KEY)

    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def pick_model(db: Optional[AsyncSession] = None, overriding_config: Optional[LLMConfig] = None) -> str:
    """Choose a model based on the active dynamic config or provider."""
    config = overriding_config or await get_active_config(db)
    if config:
        return config.model_name

    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    models = {
        "openai": "gpt-4o-mini",
        "groq": "llama-3.3-70b-versatile",
        "anthropic": "claude-haiku-4-5-20251001",
        "google": "gemini-1.5-flash",
        "azure": "gpt-4o-mini",
        "qwen": "qwen-turbo",
    }
    return models.get(provider, "gpt-4o-mini")


async def provider_is_configured(db: Optional[AsyncSession] = None) -> bool:
    """Check if any configuration is active (DB or .env)."""
    config = await get_active_config(db)
    if config:
        return bool(config.api_key)

    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()

    if provider == "groq":
        return bool(settings.GROQ_API_KEY)
    if provider == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY)
    if provider == "google":
        return bool(settings.GOOGLE_API_KEY or settings.OPENAI_API_KEY)
    if provider == "azure":
        return bool(settings.AZURE_OPENAI_API_KEY or settings.OPENAI_API_KEY)
    if provider == "qwen":
        return bool(settings.QWEN_API_KEY or settings.OPENAI_API_KEY)
    return bool(settings.OPENAI_API_KEY)


async def validate_llm_connectivity(db: Optional[AsyncSession] = None, overriding_config: Optional[LLMConfig] = None) -> tuple[bool, str]:
    """
    Perform a 'pre-flight' check or test a specific configuration:
    1. Check if configured.
    2. Check if within limits (if from DB).
    3. Try a tiny 'hello' request to verify key & quota.
    """
    config = overriding_config or await get_active_config(db)
    
    # 1. Quota Check (Database-side) - Only if it's already in DB (has an ID)
    if config and hasattr(config, "id") and config.id:
        # Check if limits exceeded
        if config.max_requests_limit and config.total_requests_made >= config.max_requests_limit:
            return False, f"LLM configuration '{config.name}' has exceeded its request limit ({config.max_requests_limit})."
            
    # 2. Connectivity Check (API-side)
    try:
        client = await get_llm_client(db, overriding_config=overriding_config)
        model = await pick_model(db, overriding_config=overriding_config)
        
        # Fast "hello" test
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond with 'Connectivity Verified'"}],
            max_tokens=20,
            timeout=15.0
        )
        ai_response = resp.choices[0].message.content.strip()
        return True, ai_response
    except Exception as exc:
        logger.error(f"LLM connectivity validation failed: {exc}")
        return False, f"LLM validation failed: {str(exc)}"


async def increment_llm_usage(tokens: int = 0, db: Optional[AsyncSession] = None) -> None:
    """Increment request count and token usage for the active LLM configuration."""
    config = await get_active_config(db)
    if not config:
        return

    if db is None:
        async with AsyncSessionLocal() as session:
            # Re-fetch to ensure we are in a session
            result = await session.execute(select(LLMConfig).filter(LLMConfig.id == config.id))
            db_config = result.scalar_one_or_none()
            if db_config:
                db_config.total_requests_made += 1
                db_config.total_tokens_used += tokens
                await session.commit()
    else:
        config.total_requests_made += 1
        config.total_tokens_used += tokens
        await db.commit()
