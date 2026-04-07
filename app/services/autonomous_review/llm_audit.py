"""Helpers for redacted LLM audit capture during autonomous reviews."""
from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AutonomousReviewLLMAudit, SystemSetting, User

_MAX_FULL_TEXT_CHARS = 6000
_MAX_SUMMARY_CHARS = 320

_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)
_TOKEN_RE = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([a-z0-9._\-]+)")
_ASSIGNMENT_SECRET_RE = re.compile(
    r"""(?ix)
    \b(api[_-]?key|token|secret|password|passwd|client_secret|access_key)\b
    (\s*[:=]\s*)
    (["']?)
    ([^"'\s,]{6,})
    \3
    """
)


def user_can_view_full_llm_audit(user: User) -> bool:
    """Only admins and managers can inspect stored redacted prompt/response bodies."""
    return getattr(user, "role", "") in {"admin", "manager"}


async def is_llm_audit_enabled(db: AsyncSession, default: bool = True) -> bool:
    """Read the runtime switch for LLM audit capture from system settings."""
    result = await db.execute(
        select(SystemSetting.value).where(SystemSetting.key == "LLM_AUDIT_ENABLED")
    )
    raw = result.scalar_one_or_none()
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def build_summary(text: Optional[str], limit: int = _MAX_SUMMARY_CHARS) -> Optional[str]:
    """Collapse multiline text into a short human-readable summary."""
    if not text:
        return None
    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def redact_text(text: Optional[str], max_chars: int = _MAX_FULL_TEXT_CHARS) -> Optional[str]:
    """Apply lightweight secret redaction before persistence."""
    if not text:
        return None

    redacted = str(text)
    redacted = _PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", redacted)
    redacted = _TOKEN_RE.sub(r"\1[REDACTED_TOKEN]", redacted)
    redacted = _ASSIGNMENT_SECRET_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}[REDACTED]{m.group(3)}", redacted)

    if len(redacted) <= max_chars:
        return redacted
    return redacted[:max_chars].rstrip() + "\n...[truncated]"


def usage_counts(usage: Any) -> dict[str, Optional[int]]:
    """Normalize token usage objects across compatible providers."""
    if usage is None:
        return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


async def record_llm_audit(
    db: AsyncSession,
    *,
    enabled: bool,
    job_id: int,
    phase: str,
    status: str = "completed",
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    config_name: Optional[str] = None,
    result_id: Optional[int] = None,
    checklist_item_id: Optional[int] = None,
    item_code: Optional[str] = None,
    item_area: Optional[str] = None,
    item_question: Optional[str] = None,
    prompt_summary: Optional[str] = None,
    response_summary: Optional[str] = None,
    prompt_text: Optional[str] = None,
    response_text: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    latency_ms: Optional[int] = None,
    metadata_json: Optional[dict[str, Any]] = None,
) -> Optional[AutonomousReviewLLMAudit]:
    """Persist one audit record when capture is enabled."""
    if not enabled:
        return None

    entry = AutonomousReviewLLMAudit(
        job_id=job_id,
        result_id=result_id,
        checklist_item_id=checklist_item_id,
        phase=phase,
        status=status,
        provider=provider,
        model_name=model_name,
        config_name=config_name,
        item_code=item_code,
        item_area=item_area,
        item_question=build_summary(item_question, limit=600),
        prompt_summary=build_summary(prompt_summary),
        response_summary=build_summary(response_summary),
        prompt_text=redact_text(prompt_text),
        response_text=redact_text(response_text),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        metadata_json=metadata_json or None,
    )
    db.add(entry)
    await db.flush()
    return entry
