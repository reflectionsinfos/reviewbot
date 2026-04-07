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
import os
from typing import Optional
from urllib.parse import urlparse, urlunparse
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
_LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "::1"}
_OLLAMA_DOCKER_HOST = os.getenv("OLLAMA_DOCKER_HOST", "host.docker.internal")


class LLMChainExhaustedError(Exception):
    """Raised when every config in the priority chain has been tried and failed."""
    pass


def _running_in_container() -> bool:
    """Best-effort check for Docker-style container execution."""
    return os.path.exists("/.dockerenv")


def _normalize_base_url(url: Optional[str], default_url: str) -> str:
    """Ensure provider URLs have a scheme and no trailing slash quirks."""
    candidate = (url or default_url or "").strip()
    if not candidate:
        return default_url
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    return candidate.rstrip("/")


def _swap_hostname(parsed, new_hostname: str) -> str:
    """Rebuild a URL with a different hostname while preserving credentials and port."""
    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += f":{parsed.password}"
        auth += "@"
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{auth}{new_hostname}{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _normalize_ollama_base_url(base_url: Optional[str]) -> str:
    """
    Normalize Ollama to its OpenAI-compatible endpoint.

    - Converts bare host URLs to `/v1`
    - Rewrites `/api` to `/v1` for this client's usage
    - Rewrites localhost to the Docker host alias when running in a container
    """
    candidate = _normalize_base_url(base_url, _PROVIDER_BASE_URLS["ollama"])
    parsed = urlparse(candidate)
    path = (parsed.path or "").rstrip("/")
    if path in {"", "/"}:
        parsed = parsed._replace(path="/v1")
    elif path == "/api":
        parsed = parsed._replace(path="/v1")
    elif path != "/v1":
        parsed = parsed._replace(path=path)

    normalized = urlunparse(parsed)
    parsed = urlparse(normalized)
    hostname = (parsed.hostname or "").lower()
    if _running_in_container() and hostname in _LOCALHOST_HOSTS and _OLLAMA_DOCKER_HOST:
        normalized = _swap_hostname(parsed, _OLLAMA_DOCKER_HOST)
    return normalized.rstrip("/")


def _normalize_ollama_base_url_no_rewrite(base_url: Optional[str]) -> str:
    """Normalize Ollama URLs without swapping localhost for a Docker host alias."""
    candidate = _normalize_base_url(base_url, _PROVIDER_BASE_URLS["ollama"])
    parsed = urlparse(candidate)
    path = (parsed.path or "").rstrip("/")
    if path in {"", "/"}:
        parsed = parsed._replace(path="/v1")
    elif path == "/api":
        parsed = parsed._replace(path="/v1")
    elif path != "/v1":
        parsed = parsed._replace(path=path)
    return urlunparse(parsed).rstrip("/")


def _effective_base_url(config: LLMConfig) -> Optional[str]:
    """Resolve the base URL the client should actually use."""
    default_url = _PROVIDER_BASE_URLS.get(config.provider)
    if config.provider == "ollama":
        return _normalize_ollama_base_url(config.base_url or default_url)
    if default_url or config.base_url:
        return _normalize_base_url(config.base_url, default_url or "")
    return config.base_url


def _ollama_base_url_candidates(config: LLMConfig) -> list[str]:
    """
    Return candidate Ollama endpoints to try.

    The first entry preserves existing runtime behaviour. We also keep the
    originally configured localhost form as a fallback for setups where the app
    container can actually reach Ollama via localhost (for example, sidecars or
    custom networking).
    """
    candidates: list[str] = []
    effective = _effective_base_url(config)
    direct = _normalize_ollama_base_url_no_rewrite(config.base_url or _PROVIDER_BASE_URLS["ollama"])
    for candidate in (effective, direct):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _build_client_for_base_url(config: LLMConfig, base_url: str) -> AsyncOpenAI:
    """Build an OpenAI-compatible client against a specific resolved base URL."""
    return AsyncOpenAI(
        api_key=(config.api_key or "").strip() or "ollama",
        base_url=base_url,
    )


def _format_ollama_runtime_error(config: LLMConfig, exc: Exception, *, base_url: str) -> str:
    """Explain Ollama runtime failures after connectivity has already succeeded."""
    message = str(exc)
    lowered = message.lower()

    if (
        "memory layout cannot be allocated" in lowered
        or "requires more system memory" in lowered
        or "out of memory" in lowered
    ):
        return (
            f"Ollama is reachable at `{base_url}` and model `{config.model_name}` is installed, "
            "but generation failed because the model needs more available memory. "
            "Try a smaller model such as `llama3.2:3b`, free RAM by closing apps, or restart Ollama and try again."
        )

    return (
        f"Ollama is reachable at `{base_url}` and model `{config.model_name}` is installed, "
        f"but generation failed. Original error: {exc}"
    )


def _format_ollama_error(
    config: LLMConfig,
    exc: Exception,
    *,
    tried_urls: Optional[list[str]] = None,
) -> str:
    """Turn generic Ollama connectivity failures into actionable guidance."""
    resolved_url = _effective_base_url(config) or _PROVIDER_BASE_URLS["ollama"]
    configured_url = (config.base_url or _PROVIDER_BASE_URLS["ollama"]).strip()
    hints: list[str] = []

    if configured_url.rstrip("/").endswith("/api"):
        hints.append(
            f"Use the OpenAI-compatible Ollama base URL `{resolved_url}` instead of `{configured_url}`."
        )

    parsed = urlparse(_normalize_base_url(configured_url, _PROVIDER_BASE_URLS["ollama"]))
    if _running_in_container() and (parsed.hostname or "").lower() in _LOCALHOST_HOSTS:
        hints.append(
            "ReviewBot is running in Docker, so `localhost` points to the container. "
            f"Use `{resolved_url}` or set `OLLAMA_DOCKER_HOST` if your Docker host alias differs."
        )

    if tried_urls:
        tried = ", ".join(f"`{url}`" for url in tried_urls)
        base_message = f"Could not reach Ollama. Tried {tried}."
    else:
        base_message = f"Could not reach Ollama at `{resolved_url}`."
    if hints:
        return " ".join([base_message, *hints])
    return f"{base_message} Original error: {exc}"


async def _list_ollama_models(client: AsyncOpenAI) -> list[str]:
    """Fetch available Ollama models through the OpenAI-compatible API."""
    response = await client.models.list()
    models: list[str] = []
    for model in getattr(response, "data", []) or []:
        model_id = getattr(model, "id", None)
        if model_id:
            models.append(model_id)
    return models


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
        except (AttributeError, Exception) as exc:
            # Pre-migration fallback — is_enabled/priority columns don't exist yet.
            # Only catch DB-level column errors, not programming mistakes.
            exc_str = str(exc).lower()
            if "is_enabled" not in exc_str and "priority" not in exc_str and "column" not in exc_str:
                raise
            logger.warning("is_enabled/priority columns missing — falling back to is_active (run migration)")
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
    base_url = _effective_base_url(config)
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
        primary = chain[0]
        if primary.provider == "ollama":
            return True
        return bool(primary.api_key)
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    if provider == "ollama":    return True
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
        model = await pick_model(db, overriding_config=overriding_config)
        if config and config.provider == "ollama":
            last_exc: Optional[Exception] = None
            tried_urls = _ollama_base_url_candidates(config)
            for base_url in tried_urls:
                models_listed = False
                try:
                    client = _build_client_for_base_url(config, base_url)
                    available_models = await _list_ollama_models(client)
                    models_listed = True
                    if available_models and model not in available_models:
                        available = ", ".join(sorted(available_models)[:5])
                        return (
                            False,
                            f"Ollama is reachable at `{base_url}`, but model "
                            f"'{model}' is not installed. Available models: {available}. "
                            f"Run `ollama pull {model}` or update the configured model name.",
                        )
                    resp = await client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "Respond with 'Connectivity Verified'"}],
                        max_tokens=20,
                        timeout=15.0,
                    )
                    return True, resp.choices[0].message.content.strip()
                except Exception as exc:
                    # If model listing succeeded, Ollama is reachable; classify the next error
                    # as a model/runtime failure instead of a connectivity problem.
                    if models_listed:
                        return False, _format_ollama_runtime_error(config, exc, base_url=base_url)
                    last_exc = exc
                    logger.warning("Ollama connectivity probe failed for %s: %s", base_url, exc)
            assert last_exc is not None
            return False, _format_ollama_error(config, last_exc, tried_urls=tried_urls)

        client = await get_llm_client(db, overriding_config=overriding_config)
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond with 'Connectivity Verified'"}],
            max_tokens=20, timeout=15.0,
        )
        return True, resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM connectivity validation failed: %s", exc)
        if config and config.provider == "ollama":
            return False, _format_ollama_error(config, exc)
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
