import pytest

from app.models import (
    AutonomousReviewJob,
    AutonomousReviewResult,
    ChecklistItem,
)


async def _seed_review_job(db_session, project, checklist, items, results_payload, *, status="completed", agent_metadata=None):
    for order, item in enumerate(items, start=1):
        db_session.add(
            ChecklistItem(
                checklist_id=checklist.id,
                item_code=item["item_code"],
                area=item.get("area", "General"),
                question=item["question"],
                category="technical",
                expected_evidence=item.get("expected_evidence"),
                is_review_mandatory=True,
                order=order,
            )
        )
    await db_session.commit()

    item_rows = (
        await db_session.execute(
            ChecklistItem.__table__.select().where(ChecklistItem.checklist_id == checklist.id)
        )
    ).mappings().all()
    item_map = {row["item_code"]: row["id"] for row in item_rows}

    job = AutonomousReviewJob(
        project_id=project.id,
        checklist_id=checklist.id,
        source_path="c:/projects/sample",
        status=status,
        completed_items=len(results_payload),
        total_items=len(results_payload),
        agent_metadata=agent_metadata,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    for payload in results_payload:
        db_session.add(
            AutonomousReviewResult(
                job_id=job.id,
                checklist_item_id=item_map[payload["item_code"]],
                strategy=payload.get("strategy", "llm_analysis"),
                rag_status=payload["rag_status"],
                evidence=payload["evidence"],
                confidence=payload.get("confidence", 0.82),
                files_checked=payload.get("files_checked", []),
                needs_human_sign_off=payload.get("needs_human_sign_off", False),
            )
        )
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.mark.asyncio
async def test_action_plan_groups_by_rag(
    async_client,
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    user, headers = await create_test_user("reviewer")
    project = await project_factory(user.id)
    checklist = await checklist_factory(is_global=False, project_id=project.id, name="Technical Checklist")

    job = await _seed_review_job(
        db_session,
        project,
        checklist,
        items=[
            {"item_code": "1.1", "question": "Are auth endpoints rate limited?", "expected_evidence": "Rate limiting is enforced on login endpoints"},
            {"item_code": "1.2", "question": "Are security events logged?", "expected_evidence": "Security-relevant events are logged without secrets"},
            {"item_code": "1.3", "question": "Is JWT auth implemented?", "expected_evidence": "JWT auth is implemented and validated"},
            {"item_code": "1.4", "question": "Is backup strategy documented?", "expected_evidence": "A tested backup and restore runbook exists"},
        ],
        results_payload=[
            {"item_code": "1.1", "rag_status": "red", "evidence": "No rate limiting was found in app/api/routes/auth.py", "files_checked": ["app/api/routes/auth.py"]},
            {"item_code": "1.2", "rag_status": "amber", "evidence": "Some auth failures are logged, but no dedicated security audit log exists", "files_checked": ["app/api/routes/auth.py", "app/services/report_generator.py"]},
            {"item_code": "1.3", "rag_status": "green", "evidence": "JWT validation exists in app/api/routes/auth.py", "files_checked": ["app/api/routes/auth.py"]},
            {"item_code": "1.4", "rag_status": "red", "evidence": "No backup runbook found in docs/", "files_checked": ["docs/README.md"], "needs_human_sign_off": True},
        ],
    )

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload["critical_blockers"]) == 1
    assert payload["critical_blockers"][0]["item_code"] == "1.1"
    assert len(payload["advisories"]) == 1
    assert payload["advisories"][0]["item_code"] == "1.2"
    assert len(payload["sign_off_required"]) == 1
    assert payload["sign_off_required"][0]["item_code"] == "1.4"
    assert len(payload["compliant_summary"]) == 1
    assert payload["compliant_summary"][0]["item_code"] == "1.3"

    blocker = payload["critical_blockers"][0]
    assert blocker["priority"] == "High"
    assert blocker["what_was_found"]
    assert "WORK TO PERFORM" in blocker["ai_prompt"]["generic"]
    assert blocker["ai_prompt"]["cursor"].startswith("@workspace")
    assert blocker["ai_prompt"]["claude_code"].startswith("Task:")


@pytest.mark.asyncio
async def test_action_plan_404_for_unknown_job(async_client, create_test_user):
    _, headers = await create_test_user("reviewer")
    response = await async_client.get("/api/autonomous-reviews/99999/action-plan", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_action_plan_400_for_non_completed_job(
    async_client,
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    user, headers = await create_test_user("reviewer")
    project = await project_factory(user.id)
    checklist = await checklist_factory(is_global=False, project_id=project.id)

    job = await _seed_review_job(
        db_session,
        project,
        checklist,
        items=[
            {"item_code": "2.1", "question": "Is CI configured?", "expected_evidence": "CI pipeline is present"},
        ],
        results_payload=[
            {"item_code": "2.1", "rag_status": "red", "evidence": "No CI workflow found"},
        ],
        status="running",
    )

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_action_plan_prompt_contains_file_context_and_enhanced_prompt_override(
    async_client,
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    user, headers = await create_test_user("reviewer")
    project = await project_factory(user.id)
    project.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
    await db_session.commit()

    checklist = await checklist_factory(is_global=False, project_id=project.id)
    job = await _seed_review_job(
        db_session,
        project,
        checklist,
        items=[
            {
                "item_code": "3.1",
                "question": "Are JWT tokens validated correctly?",
                "expected_evidence": "JWT tokens must be validated with expiry check",
            },
        ],
        results_payload=[
            {
                "item_code": "3.1",
                "rag_status": "red",
                "evidence": "Token parsing exists but expiry validation is missing in auth middleware",
                "files_checked": ["src/auth.py", "src/middleware.py"],
            },
        ],
    )

    result_row = (
        await db_session.execute(
            AutonomousReviewResult.__table__.select().where(AutonomousReviewResult.job_id == job.id)
        )
    ).mappings().first()
    job.agent_metadata = {
        "action_plan_prompts": {
            str(result_row["id"]): {
                "generic": "ENHANCED GENERIC PROMPT",
                "cursor": "@workspace\nENHANCED CURSOR PROMPT",
                "claude_code": "Task:\nENHANCED CLAUDE PROMPT",
            }
        }
    }
    await db_session.commit()

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 200

    card = response.json()["critical_blockers"][0]
    assert card["ai_prompt"]["generic"] == "ENHANCED GENERIC PROMPT"
    assert card["ai_prompt"]["cursor"] == "@workspace\nENHANCED CURSOR PROMPT"
    assert card["ai_prompt"]["claude_code"] == "Task:\nENHANCED CLAUDE PROMPT"
