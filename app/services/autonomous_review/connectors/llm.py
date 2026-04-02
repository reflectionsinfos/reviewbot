"""
Shared LLM client helpers for autonomous review flows.

Hybrid routing support:
- get_config_chain()         — ordered list of enabled configs (replaces single-active lookup)
- build_client()             — build OpenAI-compatible client from any LLMConfig
- get_planning_client()      — prefer local Ollama for the Phase 1 planning call
- get_cloud_client()         — highest-priority non-local config for complex llm_analysis
- get_local_client()         — prefer Ollama for simple llm_analysis items
- LLMChainExhaustedError     — raised when all configs in chain fail
"""
from __future__ import annotations

import logging
from typing import Optional
from openai import AsyncOpenAI
from openai import RateLimitError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import LLMConfig
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


# Provider → default base URL (used when config.base_url is empty)
_PROVIDER_BASE_URLS: dict[str, str] = {
    "groq":     "https://api.groq.com/openai/v1",
    "google":   "https://generativelanguage.googleapis.com/v1beta/openai/",
    "anthropic": "https://api.anthropic.com/v1",
    "ollama":   "http://localhost:11434/v1",
}


class LLMChainExhaustedError(Exception):
    """Raised when every config in the priority chain has been tried and failed."""
    pass


# ── Chain helpers ─────────────────────────────────────────────────────────────

async def get_config_chain(
    db: Optional[AsyncSession] = None,
    strategy: Optional[str] = None,
) -> list[LLMConfig]:
    """
    Return all enabled LLM configs ordered by priority (ascending).
    Optionally filter by strategy_affinity — configs with affinity=None handle all strategies.
    Falls back to legacy is_active lookup if no is_enabled column exists yet (pre-migration).
    """
    async def _fetch(session: AsyncSession) -> list[LLMConfig]:
        try:
            result = await session.execute(
                select(LLMConfig)
                .where(LLMConfig.is_enabled == True)
                .order_by(LLMConfig.priority)
            )
            configs = result.scalars().all()
        except Exception:
            # Pre-migration fallback — is_enabled column doesn't exist yet
            result = await session.execute(
                select(LLMConfig).where(LLMConfig.is_active == True)
            )
            configs = result.scalars().all()

        if strategy and configs:
            configs = [
                c for c in configs
                if c.strategy_affinity is None
                or strategy in (c.strategy_affinity or [])
            ]
        return list(configs)

    if db is not None:
        return await _fetch(db)
    async with AsyncSessionLocal() as session:
        return await _fetch(session)


def build_client(config: LLMConfig) -> AsyncOpenAI:
    """Build an OpenAI-compatible async client from a LLMConfig row."""
    base_url = config.base_url or _PROVIDER_BASE_URLS.get(config.provider)
    return AsyncOpenAI(
        api_key=(config.api_key or "").strip() or "ollama",
        base_url=base_url,
    )


async def get_planning_client(
    db: Optional[AsyncSession] = None,
    chain: Optional[list[LLMConfig]] = None,
) -> tuple[AsyncOpenAI, LLMConfig]:
    """
    Return the best client for the Phase 1 planning call.
    Prefers local Ollama (free, no rate limit, simple task).
    Falls back to the lowest-priority cloud config to preserve cloud quota.
    """
    if chain is None:
        chain = await get_config_chain(db)
    if not chain:
        raise LLMChainExhaustedError("No enabled LLM configs found")

    local = [c for c in chain if c.provider == "ollama"]
    target = local[0] if local else chain[-1]   # last = lowest priority = spare quota
    return build_client(target), target


async def get_cloud_client(
    db: Optional[AsyncSession] = None,
    chain: Optional[list[LLMConfig]] = None,
    skip_ids: Optional[set[int]] = None,
) -> tuple[AsyncOpenAI, LLMConfig]:
    """
    Return the highest-priority non-local (cloud) config, skipping any that
    have already failed (by id).  Used for complexity=complex llm_analysis items.
    """
    if chain is None:
        chain = await get_config_chain(db)
    skip_ids = skip_ids or set()
    cloud = [c for c in chain if c.provider != "ollama" and c.id not in skip_ids]
    if not cloud:
        raise LLMChainExhaustedError("No cloud LLM configs available")
    target = cloud[0]
    return build_client(target), target


async def get_local_client(
    db: Optional[AsyncSession] = None,
    chain: Optional[list[LLMConfig]] = None,
) -> tuple[AsyncOpenAI, LLMConfig]:
    """
    Return the local Ollama client for complexity=simple llm_analysis items.
    Falls back to lowest-priority cloud config if Ollama not configured.
    """
    if chain is None:
        chain = await get_config_chain(db)
    if not chain:
        raise LLMChainExhaustedError("No enabled LLM configs found")
    local = [c for c in chain if c.provider == "ollama"]
    target = local[0] if local else chain[-1]
    return build_client(target), target


# ── Legacy single-config helpers (kept for backwards compatibility) ────────────

async def get_active_config(db: Optional[AsyncSession] = None) -> Optional[LLMConfig]:
    """Return the single active config (legacy). Prefers is_active flag."""
    async def _fetch(session: AsyncSession) -> Optional[LLMConfig]:
        result = await session.execute(select(LLMConfig).filter(LLMConfig.is_active == True))
        return result.scalar_one_or_none()

    if db is not None:
        return await _fetch(db)
    async with AsyncSessionLocal() as session:
        return await _fetch(session)


async def get_llm_client(
    db: Optional[AsyncSession] = None,
    overriding_config: Optional[LLMConfig] = None,
) -> AsyncOpenAI:
    """Return an OpenAI-compatible client. Uses chain if available, else legacy."""
    if overriding_config:
        return build_client(overriding_config)

    chain = await get_config_chain(db)
    if chain:
        return build_client(chain[0])

    # Fallback to .env settings
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    if provider == "groq":
        return AsyncOpenAI(api_key=settings.GROQ_API_KEY,
                           base_url="https://api.groq.com/openai/v1")
    if provider == "azure":
        return AsyncOpenAI(api_key=settings.AZURE_OPENAI_API_KEY or settings.OPENAI_API_KEY)
    if provider == "qwen":
        return AsyncOpenAI(api_key=settings.QWEN_API_KEY or settings.OPENAI_API_KEY)
    if provider == "anthropic":
        return AsyncOpenAI(api_key=settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY)
    if provider == "google":
        return AsyncOpenAI(api_key=settings.GOOGLE_API_KEY or settings.OPENAI_API_KEY)
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def pick_model(
    db: Optional[AsyncSession] = None,
    overriding_config: Optional[LLMConfig] = None,
) -> str:
    """Return model name from active config or provider default."""
    config = overriding_config or await get_active_config(db)
    if config:
        return config.model_name
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    return {
        "openai":    "gpt-4o-mini",
        "groq":      "llama-3.3-70b-versatile",
        "anthropic": "claude-haiku-4-5-20251001",
        "google":    "gemini-1.5-flash",
        "azure":     "gpt-4o-mini",
        "qwen":      "qwen-turbo",
    }.get(provider, "gpt-4o-mini")


async def provider_is_configured(db: Optional[AsyncSession] = None) -> bool:
    chain = await get_config_chain(db)
    if chain:
        return bool(chain[0].api_key)
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    if provider == "groq":      return bool(settings.GROQ_API_KEY)
    if provider == "anthropic": return bool(settings.ANTHROPIC_API_KEY)
    if provider == "google":    return bool(settings.GOOGLE_API_KEY)
    if provider == "azure":     return bool(settings.AZURE_OPENAI_API_KEY)
    if provider == "qwen":      return bool(settings.QWEN_API_KEY)
    return bool(settings.OPENAI_API_KEY)


async def validate_llm_connectivity(
    db: Optional[AsyncSession] = None,
    overriding_config: Optional[LLMConfig] = None,
) -> tuple[bool, str]:
    """Pre-flight connectivity check."""
    config = overriding_config or await get_active_config(db)
    if config and hasattr(config, "id") and config.id:
        if config.max_requests_limit and config.total_requests_made >= config.max_requests_limit:
            return False, f"Config '{config.name}' has exceeded its request limit."
    try:
        client = await get_llm_client(db, overriding_config=overriding_config)
        model = await pick_model(db, overriding_config=overriding_config)
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond with 'Connectivity Verified'"}],
            max_tokens=20, timeout=15.0,
        )
        return True, resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM connectivity validation failed: %s", exc)
        return False, f"LLM validation failed: {exc}"


async def increment_llm_usage(
    tokens: int = 0,
    db: Optional[AsyncSession] = None,
    config_id: Optional[int] = None,
) -> None:
    """Increment request count and token usage for a specific config (or active config)."""
    async def _update(session: AsyncSession) -> None:
        if config_id:
            result = await session.execute(select(LLMConfig).where(LLMConfig.id == config_id))
        else:
            result = await session.execute(select(LLMConfig).where(LLMConfig.is_active == True))
        cfg = result.scalar_one_or_none()
        if cfg:
            cfg.total_requests_made += 1
            cfg.total_tokens_used += tokens
            await session.commit()

    if db is not None:
        await _update(db)
    else:
        async with AsyncSessionLocal() as session:
            await _update(session)
