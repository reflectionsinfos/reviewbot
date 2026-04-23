"""
Integration Dispatcher

Called by the autonomous review orchestrator after a job completes.
Reads enabled IntegrationConfig rows, decides whether to fire based on
trigger_on / compliance state, generates the action plan, then fans
out to each integration handler.

All errors are caught and logged — dispatch failure never affects job status.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import (
    AutonomousReviewJob,
    AutonomousReviewResult,
    ChecklistItem,
    IntegrationConfig,
    IntegrationDispatch,
)
from app.services.action_plan_generator import ActionPlanGenerator
from .base import DispatchResult

logger = logging.getLogger(__name__)


async def dispatch_review_results(job_id: int) -> None:
    """
    Entry point called by the orchestrator after job completion.
    Creates its own DB session — completely isolated from the review session.
    """
    async with AsyncSessionLocal() as db:
        try:
            await _run_dispatch(job_id, db)
        except Exception as exc:
            logger.exception("Integration dispatch crashed for job %s: %s", job_id, exc)


async def _should_dispatch(integration: IntegrationConfig, job: AutonomousReviewJob) -> bool:
    if not integration.is_enabled:
        return False
    trigger = integration.trigger_on or "red_only"
    if trigger == "manual":
        return False
    if trigger == "red_only":
        return (job.red_count or 0) > 0
    return True  # "always"


async def _run_dispatch(job_id: int, db) -> None:
    # ── Load job with relationships ───────────────────────────────────────────
    result = await db.execute(
        select(AutonomousReviewJob)
        .where(AutonomousReviewJob.id == job_id)
        .options(
            selectinload(AutonomousReviewJob.project),
            selectinload(AutonomousReviewJob.checklist),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        logger.warning("Dispatch: job %s not found", job_id)
        return

    # ── Load enabled integrations ─────────────────────────────────────────────
    int_result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.is_enabled == True)  # noqa: E712
    )
    integrations = int_result.scalars().all()
    if not integrations:
        return

    # Determine which integrations actually need to fire
    active = [i for i in integrations if await _should_dispatch(i, job)]
    if not active:
        logger.info("Dispatch: no integrations triggered for job %s", job_id)
        return

    logger.info("Dispatch: job %s — %d integration(s) will fire", job_id, len(active))

    # ── Generate action plan once for all integrations ────────────────────────
    action_plan = await _build_action_plan(job, db)

    # ── Fan out ───────────────────────────────────────────────────────────────
    for integration in active:
        await _run_single(integration, job, action_plan, db)


async def _build_action_plan(job: AutonomousReviewJob, db):
    """Build an ActionPlanResponse from stored results (same logic as the API route)."""
    results_q = await db.execute(
        select(AutonomousReviewResult)
        .where(AutonomousReviewResult.job_id == job.id)
        .options(selectinload(AutonomousReviewResult.checklist_item))
    )
    results = results_q.scalars().all()

    item_ids = [r.checklist_item_id for r in results]
    items_q = await db.execute(
        select(ChecklistItem).where(ChecklistItem.id.in_(item_ids))
    )
    checklist_items = {item.id: item for item in items_q.scalars().all()}

    generator = ActionPlanGenerator()
    return await generator.generate(
        job=job,
        results=results,
        checklist_items=checklist_items,
        project=job.project,
        checklist_name=job.checklist.name if job.checklist else "",
        enhanced_prompts={},
    )


async def _run_single(
    integration: IntegrationConfig,
    job: AutonomousReviewJob,
    action_plan,
    db,
) -> None:
    """Run one integration and persist the dispatch log."""
    dispatch = IntegrationDispatch(
        integration_id=integration.id,
        job_id=job.id,
        triggered_by="auto",
        status="pending",
        dispatched_at=datetime.utcnow(),
    )
    db.add(dispatch)
    await db.flush()  # get dispatch.id

    try:
        result = await _call_handler(integration, job, action_plan)
        dispatch.status = (
            "success" if result.success
            else "partial" if result.dispatched > 0
            else "failed"
        )
        dispatch.items_dispatched = result.dispatched
        dispatch.items_failed = result.failed
        dispatch.results_json = result.to_json()
        if result.error_message:
            dispatch.error_message = result.error_message
    except Exception as exc:
        logger.error(
            "Integration %s (%s) raised unexpectedly for job %s: %s",
            integration.name, integration.type, job.id, exc,
        )
        dispatch.status = "failed"
        dispatch.error_message = str(exc)

    await db.commit()
    logger.info(
        "Dispatch log saved — integration=%s status=%s dispatched=%d failed=%d",
        integration.name, dispatch.status,
        dispatch.items_dispatched, dispatch.items_failed,
    )


async def _call_handler(
    integration: IntegrationConfig,
    job: AutonomousReviewJob,
    action_plan,
) -> DispatchResult:
    cfg = integration.config_json or {}
    cards = list(action_plan.critical_blockers)
    if integration.include_advisories:
        cards += list(action_plan.advisories)

    if integration.type == "jira":
        from .jira import create_tickets
        return await create_tickets(cfg, cards)

    if integration.type == "smtp":
        from .email_smtp import send_summary_email
        return await send_summary_email(cfg, job, action_plan)

    if integration.type == "linear":
        return await _linear_stub(cfg, cards)

    if integration.type == "github_issues":
        return await _github_issues_stub(cfg, cards)

    if integration.type == "webhook":
        return await _webhook(cfg, job, action_plan)

    raise ValueError(f"Unknown integration type: {integration.type!r}")


# ── Future integration stubs ──────────────────────────────────────────────────
# These follow the same httpx pattern as jira.py — implement when needed.

async def _linear_stub(cfg: dict, cards: list) -> DispatchResult:
    """
    Linear GraphQL integration placeholder.

    config_json: {api_key, team_id, priority_map}
    Endpoint: https://api.linear.app/graphql
    Auth: Authorization: <api_key>
    Mutation: issueCreate(input: {teamId, title, description, priority})
    """
    from .base import DispatchResult
    return DispatchResult(
        success=False,
        error_message="Linear integration is not yet implemented.",
    )


async def _github_issues_stub(cfg: dict, cards: list) -> DispatchResult:
    """
    GitHub Issues integration placeholder.

    config_json: {token, owner, repo, labels, priority_map}
    Endpoint: https://api.github.com/repos/{owner}/{repo}/issues
    Auth: Authorization: Bearer <token>
    """
    from .base import DispatchResult
    return DispatchResult(
        success=False,
        error_message="GitHub Issues integration is not yet implemented.",
    )


async def _webhook(cfg: dict, job, action_plan) -> DispatchResult:
    """Generic outbound webhook — POST JSON payload to a configured URL."""
    import httpx
    from .base import DispatchItem, DispatchResult

    url = cfg.get("url")
    if not url:
        return DispatchResult(success=False, error_message="webhook.url is required")

    headers = dict(cfg.get("headers") or {})
    headers.setdefault("Content-Type", "application/json")
    method = (cfg.get("method") or "POST").upper()

    payload = {
        "job_id": job.id,
        "project": job.project.name if job.project else None,
        "compliance_score": job.compliance_score,
        "red_count": job.red_count,
        "amber_count": job.amber_count,
        "green_count": job.green_count,
        "critical_blockers": [
            {"item_code": c.item_code, "area": c.area, "question": c.question,
             "what_was_found": c.what_was_found}
            for c in action_plan.critical_blockers
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=headers, json=payload)
        if resp.status_code < 300:
            return DispatchResult(
                success=True,
                items=[DispatchItem(type="webhook", ref=url, status="success")],
            )
        err = f"HTTP {resp.status_code}: {resp.text[:200]}"
        return DispatchResult(
            success=False,
            items=[DispatchItem(type="webhook", ref=url, status="failed", error=err)],
            error_message=err,
        )
    except Exception as exc:
        return DispatchResult(success=False, error_message=str(exc))


async def run_manual_dispatch(job_id: int, integration_id: int) -> DispatchResult:
    """
    Trigger a specific integration for a specific job on demand.
    Used by the manual dispatch API endpoint.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AutonomousReviewJob)
            .where(AutonomousReviewJob.id == job_id)
            .options(
                selectinload(AutonomousReviewJob.project),
                selectinload(AutonomousReviewJob.checklist),
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return DispatchResult(success=False, error_message=f"Job {job_id} not found")

        int_result = await db.execute(
            select(IntegrationConfig).where(IntegrationConfig.id == integration_id)
        )
        integration = int_result.scalar_one_or_none()
        if not integration:
            return DispatchResult(
                success=False,
                error_message=f"Integration {integration_id} not found",
            )

        action_plan = await _build_action_plan(job, db)

        dispatch = IntegrationDispatch(
            integration_id=integration.id,
            job_id=job.id,
            triggered_by="manual",
            status="pending",
            dispatched_at=datetime.utcnow(),
        )
        db.add(dispatch)
        await db.flush()

        try:
            dispatch_result = await _call_handler(integration, job, action_plan)
            dispatch.status = (
                "success" if dispatch_result.success
                else "partial" if dispatch_result.dispatched > 0
                else "failed"
            )
            dispatch.items_dispatched = dispatch_result.dispatched
            dispatch.items_failed = dispatch_result.failed
            dispatch.results_json = dispatch_result.to_json()
            if dispatch_result.error_message:
                dispatch.error_message = dispatch_result.error_message
        except Exception as exc:
            dispatch.status = "failed"
            dispatch.error_message = str(exc)
            dispatch_result = DispatchResult(success=False, error_message=str(exc))

        await db.commit()
        return dispatch_result
