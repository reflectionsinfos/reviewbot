"""
Shared LLM client helpers for autonomous review flows.
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings


def get_llm_client() -> AsyncOpenAI:
    """Return an OpenAI-compatible async client for the configured provider."""
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


def pick_model() -> str:
    """Choose a default model based on the active provider."""
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


def provider_is_configured() -> bool:
    """Best-effort check for whether the selected provider has credentials."""
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
