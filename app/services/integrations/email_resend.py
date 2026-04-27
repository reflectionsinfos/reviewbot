"""
Resend.com email integration.

Sends transactional emails via the Resend HTTP API.
No extra dependencies — uses httpx (already in requirements).

config_json schema:
{
    "api_key":                      "re_xxxxxxxxxxxx",
    "from_address":                 "ReviewBot <bot@yourdomain.com>",
    "recipients":                   ["team@company.com"],
    "include_project_stakeholders": true
}

The from_address must belong to a verified domain in your Resend account.
"""
import logging
from typing import Any

import httpx

from .base import DispatchItem, DispatchResult

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def _collect_recipients(cfg: dict, project: Any) -> list[str]:
    recipients = list(cfg.get("recipients") or [])
    if cfg.get("include_project_stakeholders") and project:
        stakeholders = getattr(project, "stakeholders", None) or {}
        if isinstance(stakeholders, list):
            for s in stakeholders:
                if isinstance(s, dict) and s.get("email"):
                    recipients.append(s["email"])
        elif isinstance(stakeholders, dict):
            for role_data in stakeholders.values():
                if isinstance(role_data, dict) and role_data.get("email"):
                    recipients.append(role_data["email"])
    seen: set[str] = set()
    unique = []
    for r in recipients:
        if r and r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def _rag_emoji(status: str) -> str:
    return {"red": "🔴", "amber": "🟡", "green": "🟢"}.get(status, "⚪")


async def _post_resend(api_key: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def send_summary_email(cfg: dict, job: Any, action_plan: Any) -> DispatchResult:
    """Send a review-summary email via Resend."""
    api_key = cfg.get("api_key", "")
    if not api_key:
        return DispatchResult(success=False, error_message="Resend API key not configured.")

    recipients = _collect_recipients(cfg, getattr(job, "project", None))
    if not recipients:
        return DispatchResult(success=False, error_message="No recipients configured.")

    score = getattr(job, "compliance_score", 0.0)
    project_name = job.project.name if job.project else f"Job #{job.id}"

    subject = f"[ReviewBot] Review Complete: {project_name} — {score:.1f}% compliant"

    html_lines = [
        f"<h2>ReviewBot — Autonomous Review Completed</h2>",
        f"<p><strong>Project:</strong> {project_name}<br>",
        f"<strong>Score:</strong> {score:.1f}%<br>",
        f"<strong>Red:</strong> {job.red_count} &nbsp; <strong>Amber:</strong> {job.amber_count} &nbsp; <strong>Green:</strong> {job.green_count}</p>",
    ]
    if action_plan and action_plan.critical_blockers:
        html_lines.append(f"<h3 style='color:#ef4444'>Critical Blockers ({len(action_plan.critical_blockers)})</h3><ul>")
        for b in action_plan.critical_blockers[:10]:
            html_lines.append(f"<li><strong>{b.get('item','')}</strong>: {b.get('finding','')}</li>")
        html_lines.append("</ul>")

    html_body = "\n".join(html_lines)

    items = []
    errors = []
    for addr in recipients:
        try:
            await _post_resend(api_key, {
                "from": cfg.get("from_address", "ReviewBot <noreply@reviewbot.app>"),
                "to": [addr],
                "subject": subject,
                "html": html_body,
            })
            items.append(DispatchItem(type="email", ref=addr, status="success"))
        except Exception as exc:
            logger.error("Resend send failed for %s: %s", addr, exc)
            errors.append(str(exc))
            items.append(DispatchItem(type="email", ref=addr, status="error", error=str(exc)))

    if errors and not any(i.status == "success" for i in items):
        return DispatchResult(success=False, error_message="; ".join(errors), items=items)
    return DispatchResult(success=True, items=items)


async def send_offline_review_email(
    cfg: dict,
    reviewer_email: str,
    reviewer_name: str,
    project_name: str,
    checklist_name: str,
    app_url: str,
    upload_token: str,
    due_date: Any = None,
    admin_message: str | None = None,
    item_count: int = 0,
) -> DispatchResult:
    """Send an offline-review invitation email via Resend."""
    api_key = cfg.get("api_key", "")
    if not api_key:
        return DispatchResult(success=False, error_message="Resend API key not configured.")

    review_url = f"{app_url.rstrip('/')}/offline-review?token={upload_token}"
    due_str = due_date.strftime("%A, %d %b %Y") if due_date else None

    subject = f"[ReviewBot] You've been invited to review: {project_name}"

    due_row = (
        f"<tr><td style='padding:6px 12px;color:#666'><b>Due by</b></td>"
        f"<td style='padding:6px 12px;color:#E65100;font-weight:bold'>{due_str}</td></tr>"
        if due_str else ""
    )
    msg_block = (
        f"<p style='margin:16px 0;padding:12px 16px;background:#fff8e1;border-left:4px solid #ffc107;"
        f"border-radius:4px;color:#333'><em>{admin_message}</em></p>"
        if admin_message else ""
    )

    html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e0e0e0">
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;margin:0;font-size:22px">ReviewBot</h1>
    <p style="color:#90caf9;margin:4px 0 0">Project Review Invitation</p>
  </div>
  <div style="padding:32px">
    <p style="font-size:16px;color:#333">Hi <strong>{reviewer_name}</strong>,</p>
    <p style="color:#555">You have been invited to complete a project review.</p>
    <table style="border-collapse:collapse;width:100%;margin:20px 0;background:#f9fafb;border-radius:6px">
      <tr><td style="padding:6px 12px;color:#666"><b>Project</b></td><td style="padding:6px 12px;color:#333;font-weight:600">{project_name}</td></tr>
      <tr><td style="padding:6px 12px;color:#666"><b>Checklist</b></td><td style="padding:6px 12px;color:#333">{checklist_name}</td></tr>
      <tr><td style="padding:6px 12px;color:#666"><b>Items</b></td><td style="padding:6px 12px;color:#333">{item_count}</td></tr>
      {due_row}
    </table>
    {msg_block}
    <p style="color:#555">Click the button below to access the review portal, download the checklist, fill in your responses, and upload it back.</p>
    <div style="text-align:center;margin:32px 0">
      <a href="{review_url}" style="background:#1e3a5f;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:16px">Open Review Portal</a>
    </div>
    <p style="font-size:12px;color:#999">Or copy this link: <a href="{review_url}" style="color:#1e3a5f">{review_url}</a></p>
    <p style="font-size:12px;color:#bbb">This link expires in 30 days. This is an automated message — do not reply.</p>
  </div>
</div>
"""

    try:
        await _post_resend(api_key, {
            "from": cfg.get("from_address", "ReviewBot <noreply@reviewbot.app>"),
            "to": [reviewer_email],
            "subject": subject,
            "html": html_body,
        })
        return DispatchResult(
            success=True,
            items=[DispatchItem(type="email", ref=reviewer_email, status="success")],
        )
    except Exception as exc:
        logger.error("Resend offline review email failed: %s", exc)
        return DispatchResult(success=False, error_message=str(exc))


async def test_connection(cfg: dict) -> tuple[bool, str]:
    """Verify Resend API key and from_address by sending a test request."""
    api_key = cfg.get("api_key", "")
    from_addr = cfg.get("from_address", "")
    if not api_key:
        return False, "api_key is required."
    if not from_addr:
        return False, "from_address is required."

    # Use Resend's domains endpoint to verify the key is valid without sending an email
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 401:
                return False, "Invalid Resend API key."
            if resp.status_code == 200:
                data = resp.json()
                domains = [d.get("name") for d in (data.get("data") or [])]
                return True, f"API key valid. Verified domains: {', '.join(domains) if domains else 'none yet'}"
            return False, f"Unexpected response: {resp.status_code} {resp.text[:200]}"
    except Exception as exc:
        return False, f"Connection error: {exc}"
