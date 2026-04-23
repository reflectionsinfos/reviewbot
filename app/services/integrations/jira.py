"""
Jira Cloud integration.

Uses the Jira REST API v3 with Basic Auth (email + API token).
Creates one issue per ActionCard dispatched.

config_json schema:
{
    "url":          "https://myorg.atlassian.net",
    "email":        "bot@myorg.com",
    "api_token":    "ATATT...",
    "project_key":  "PROJ",
    "issue_type":   "Task",
    "labels":       ["reviewbot"],
    "priority_map": {"red": "High", "amber": "Medium"}
}
"""
import base64
import logging
from typing import Any

import httpx

from .base import DispatchItem, DispatchResult

logger = logging.getLogger(__name__)

_DEFAULT_PRIORITY_MAP = {"red": "High", "amber": "Medium"}


def _auth_header(email: str, api_token: str) -> str:
    creds = f"{email}:{api_token}".encode()
    return "Basic " + base64.b64encode(creds).decode()


def _build_adf_doc(text: str) -> dict:
    """Wrap plain text in the minimal Atlassian Document Format structure."""
    paragraphs = []
    for para in text.split("\n\n"):
        lines = para.strip().splitlines()
        content = []
        for line in lines:
            if content:
                content.append({"type": "hardBreak"})
            content.append({"type": "text", "text": line})
        if content:
            paragraphs.append({"type": "paragraph", "content": content})
    if not paragraphs:
        paragraphs = [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    return {"type": "doc", "version": 1, "content": paragraphs}


def _build_issue_body(card: Any, cfg: dict) -> dict:
    priority_map = cfg.get("priority_map") or _DEFAULT_PRIORITY_MAP
    priority_name = priority_map.get(card.rag_status, "Medium")
    labels = cfg.get("labels") or []

    description_text = (
        f"Area: {card.area}\n\n"
        f"Finding:\n{card.what_was_found}\n\n"
        f"What to fix:\n{card.what_to_fix}\n\n"
        f"Expected outcome:\n{card.expected_outcome}"
    )

    body: dict = {
        "fields": {
            "project": {"key": cfg["project_key"]},
            "summary": f"[ReviewBot] {card.item_code} — {card.question[:120]}",
            "description": _build_adf_doc(description_text),
            "issuetype": {"name": cfg.get("issue_type", "Task")},
            "priority": {"name": priority_name},
        }
    }
    if labels:
        body["fields"]["labels"] = labels

    return body


async def create_tickets(cfg: dict, cards: list[Any]) -> DispatchResult:
    """Create one Jira issue per ActionCard. Returns a DispatchResult."""
    base_url = cfg["url"].rstrip("/")
    headers = {
        "Authorization": _auth_header(cfg["email"], cfg["api_token"]),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    items: list[DispatchItem] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for card in cards:
            payload = _build_issue_body(card, cfg)
            try:
                resp = await client.post(
                    f"{base_url}/rest/api/3/issue",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    key = data.get("key", "?")
                    url = f"{base_url}/browse/{key}"
                    items.append(DispatchItem(type="ticket", ref=key, url=url, status="success"))
                    logger.info("Jira ticket created: %s", key)
                else:
                    err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    items.append(DispatchItem(
                        type="ticket",
                        ref=card.item_code or "?",
                        status="failed",
                        error=err,
                    ))
                    logger.warning("Jira ticket failed for %s: %s", card.item_code, err)
            except Exception as exc:
                items.append(DispatchItem(
                    type="ticket",
                    ref=card.item_code or "?",
                    status="failed",
                    error=str(exc),
                ))
                logger.warning("Jira request error for %s: %s", card.item_code, exc)

    any_success = any(i.status == "success" for i in items)
    any_fail = any(i.status == "failed" for i in items)
    success = any_success and not any_fail if items else False
    return DispatchResult(success=success, items=items)


async def test_connection(cfg: dict) -> tuple[bool, str]:
    """Verify Jira credentials and project access. Returns (ok, message)."""
    try:
        base_url = cfg["url"].rstrip("/")
        headers = {
            "Authorization": _auth_header(cfg["email"], cfg["api_token"]),
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{base_url}/rest/api/3/project/{cfg['project_key']}",
                headers=headers,
            )
        if resp.status_code == 200:
            name = resp.json().get("name", cfg["project_key"])
            return True, f"Connected — project '{name}' found."
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        return False, str(exc)
