"""
SMTP email notification integration.

Sends one summary email per completed review job.
Uses smtplib (stdlib) via asyncio.to_thread — no extra dependencies.

config_json schema:
{
    "host":                         "smtp.gmail.com",
    "port":                         587,
    "username":                     "bot@gmail.com",
    "password":                     "app-password",
    "from_address":                 "ReviewBot <bot@gmail.com>",
    "use_tls":                      true,
    "recipients":                   ["team@company.com"],
    "include_project_stakeholders": true
}
"""
import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .base import DispatchItem, DispatchResult

logger = logging.getLogger(__name__)


def _collect_recipients(cfg: dict, project: Any) -> list[str]:
    recipients = list(cfg.get("recipients") or [])
    if cfg.get("include_project_stakeholders") and project:
        stakeholders = getattr(project, "stakeholders", None) or {}
        # stakeholders can be a list of dicts or a dict of role→{name, email}
        if isinstance(stakeholders, list):
            for s in stakeholders:
                if isinstance(s, dict) and s.get("email"):
                    recipients.append(s["email"])
        elif isinstance(stakeholders, dict):
            for role_data in stakeholders.values():
                if isinstance(role_data, dict) and role_data.get("email"):
                    recipients.append(role_data["email"])
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for r in recipients:
        if r and r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def _rag_emoji(status: str) -> str:
    return {"red": "🔴", "amber": "🟡", "green": "🟢"}.get(status, "⚪")


def _build_email(cfg: dict, job: Any, action_plan: Any, recipients: list[str]) -> MIMEMultipart:
    score = getattr(job, "compliance_score", 0.0)
    project_name = job.project.name if job.project else f"Job #{job.id}"

    subject = (
        f"[ReviewBot] Review Complete: {project_name} — "
        f"{score:.1f}% compliant"
    )

    # ── Plain text body ────────────────────────────────────────────────────────
    lines = [
        f"ReviewBot — Autonomous Review Completed",
        f"{'=' * 50}",
        f"Project:   {project_name}",
        f"Checklist: {getattr(action_plan, 'checklist', '')}",
        f"Score:     {score:.1f}%",
        f"Red:       {job.red_count}   Amber: {job.amber_count}   Green: {job.green_count}",
        "",
    ]

    if action_plan.critical_blockers:
        lines += [f"CRITICAL BLOCKERS ({len(action_plan.critical_blockers)})", "-" * 40]
        for card in action_plan.critical_blockers:
            lines += [
                f"  {card.item_code}  {card.area}",
                f"  {card.question[:120]}",
                f"  Finding: {card.what_was_found[:200]}",
                "",
            ]

    if action_plan.advisories:
        lines += [f"ADVISORIES ({len(action_plan.advisories)})", "-" * 40]
        for card in action_plan.advisories[:10]:  # cap to avoid huge emails
            lines += [
                f"  {card.item_code}  {card.area}",
                f"  {card.question[:120]}",
                "",
            ]

    if len(action_plan.advisories) > 10:
        lines.append(f"  ... and {len(action_plan.advisories) - 10} more advisories.")

    lines += [
        "",
        "View full results in ReviewBot.",
        "This is an automated message — do not reply.",
    ]
    plain_text = "\n".join(lines)

    # ── HTML body ──────────────────────────────────────────────────────────────
    def card_rows(cards: list, limit: int = 999) -> str:
        rows = []
        for card in cards[:limit]:
            emoji = _rag_emoji(card.rag_status)
            rows.append(
                f"<tr>"
                f"<td style='padding:4px 8px;white-space:nowrap'>{emoji} {card.item_code}</td>"
                f"<td style='padding:4px 8px'><b>{card.area}</b><br/>"
                f"<span style='color:#555'>{card.question[:120]}</span></td>"
                f"<td style='padding:4px 8px;color:#333;font-size:0.9em'>"
                f"{card.what_was_found[:200]}</td>"
                f"</tr>"
            )
        return "".join(rows)

    blockers_html = ""
    if action_plan.critical_blockers:
        blockers_html = f"""
        <h3 style='color:#c0392b'>🔴 Critical Blockers ({len(action_plan.critical_blockers)})</h3>
        <table border='0' cellspacing='0' style='width:100%;border-collapse:collapse'>
          <thead><tr style='background:#f5f5f5'>
            <th style='padding:4px 8px;text-align:left'>Item</th>
            <th style='padding:4px 8px;text-align:left'>Question</th>
            <th style='padding:4px 8px;text-align:left'>Finding</th>
          </tr></thead>
          <tbody>{card_rows(action_plan.critical_blockers)}</tbody>
        </table>"""

    advisories_html = ""
    if action_plan.advisories:
        extra = len(action_plan.advisories) - 10
        advisories_html = f"""
        <h3 style='color:#e67e22'>🟡 Advisories ({len(action_plan.advisories)})</h3>
        <table border='0' cellspacing='0' style='width:100%;border-collapse:collapse'>
          <thead><tr style='background:#f5f5f5'>
            <th style='padding:4px 8px;text-align:left'>Item</th>
            <th style='padding:4px 8px;text-align:left'>Question</th>
            <th style='padding:4px 8px;text-align:left'>Finding</th>
          </tr></thead>
          <tbody>{card_rows(action_plan.advisories, 10)}</tbody>
        </table>
        {"<p style='color:#777'><em>... and " + str(extra) + " more advisories.</em></p>" if extra > 0 else ""}"""

    html = f"""<html><body style='font-family:Arial,sans-serif;max-width:800px;margin:auto'>
    <h2 style='border-bottom:2px solid #2c3e50;padding-bottom:8px'>
      ReviewBot — Autonomous Review Completed
    </h2>
    <table style='margin-bottom:16px'>
      <tr><td><b>Project:</b></td><td>{project_name}</td></tr>
      <tr><td><b>Checklist:</b></td><td>{getattr(action_plan, 'checklist', '')}</td></tr>
      <tr><td><b>Score:</b></td>
          <td><b style='font-size:1.2em'>{score:.1f}%</b></td></tr>
      <tr><td><b>Summary:</b></td>
          <td>🔴 {job.red_count} critical &nbsp;
              🟡 {job.amber_count} advisory &nbsp;
              🟢 {job.green_count} compliant</td></tr>
    </table>
    {blockers_html}
    {advisories_html}
    <hr/>
    <p style='color:#999;font-size:0.85em'>
      Automated message from ReviewBot — do not reply.
    </p>
    </body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.get("from_address", cfg.get("username", "reviewbot@noreply"))
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def _send_sync(cfg: dict, msg: MIMEMultipart, recipients: list[str]) -> None:
    """Blocking SMTP send — runs in a thread via asyncio.to_thread."""
    host = cfg["host"]
    port = int(cfg.get("port", 587))
    use_tls = cfg.get("use_tls", True)

    if use_tls:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(cfg["username"], cfg["password"])
            server.sendmail(msg["From"], recipients, msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            server.login(cfg["username"], cfg["password"])
            server.sendmail(msg["From"], recipients, msg.as_string())


async def send_summary_email(
    cfg: dict,
    job: Any,
    action_plan: Any,
) -> DispatchResult:
    """Send a review-summary email to all configured recipients."""
    recipients = _collect_recipients(cfg, getattr(job, "project", None))
    if not recipients:
        return DispatchResult(
            success=False,
            error_message="No recipients configured.",
        )

    msg = _build_email(cfg, job, action_plan, recipients)
    try:
        await asyncio.to_thread(_send_sync, cfg, msg, recipients)
        logger.info("Review summary email sent to %d recipient(s)", len(recipients))
        items = [
            DispatchItem(type="email", ref=addr, status="success")
            for addr in recipients
        ]
        return DispatchResult(success=True, items=items)
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return DispatchResult(success=False, error_message=str(exc))


async def test_connection(cfg: dict) -> tuple[bool, str]:
    """Verify SMTP credentials by opening a connection. Returns (ok, message)."""
    try:
        def _probe() -> str:
            host = cfg["host"]
            port = int(cfg.get("port", 587))
            use_tls = cfg.get("use_tls", True)
            if use_tls:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(host, port) as s:
                    s.ehlo()
                    s.starttls(context=ctx)
                    s.login(cfg["username"], cfg["password"])
            else:
                with smtplib.SMTP(host, port) as s:
                    s.login(cfg["username"], cfg["password"])
            return f"Connected to {host}:{port}"

        message = await asyncio.to_thread(_probe)
        return True, message
    except Exception as exc:
        return False, str(exc)
