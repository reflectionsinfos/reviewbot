import pytest

from app.models import (
    AutonomousReviewJob,
    AutonomousReviewLLMAudit,
    AutonomousReviewResult,
    ChecklistItem,
    SystemSetting,
)
from app.services.autonomous_review.llm_audit import is_llm_audit_enabled, record_llm_audit


async def _seed_job_with_result(db_session, project, checklist):
    item = ChecklistItem(
        checklist_id=checklist.id,
        item_code="ARCH-001",
        area="Architecture",
        question="Is the architecture documented?",
        category="technical",
        is_review_mandatory=True,
        order=1,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    job = AutonomousReviewJob(
        project_id=project.id,
        checklist_id=checklist.id,
        source_path="c:/projects/sample",
        status="completed",
        total_items=1,
        completed_items=1,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    result = AutonomousReviewResult(
        job_id=job.id,
        checklist_item_id=item.id,
        strategy="llm_analysis",
        rag_status="amber",
        evidence="Architecture notes exist but decision records are incomplete.",
        confidence=0.78,
        files_checked=["README.md", "docs/architecture.md"],
    )
    db_session.add(result)
    await db_session.commit()
    await db_session.refresh(result)
    return job, result, item


@pytest.mark.asyncio
async def test_record_llm_audit_redacts_sensitive_values(
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    user, _ = await create_test_user("admin")
    project = await project_factory(user.id)
    checklist = await checklist_factory(is_global=False, project_id=project.id)
    job, result, item = await _seed_job_with_result(db_session, project, checklist)

    await record_llm_audit(
        db_session,
        enabled=True,
        job_id=job.id,
        result_id=result.id,
        checklist_item_id=item.id,
        item_code=item.item_code,
        item_area=item.area,
        item_question=item.question,
        phase="item_analysis",
        prompt_summary="Prompt summary",
        response_summary="Response summary",
        prompt_text="api_key='abcdef123456'\n-----BEGIN PRIVATE KEY-----\nshh\n-----END PRIVATE KEY-----",
        response_text="Authorization: Bearer super-secret-token",
    )
    await db_session.commit()

    stored = (
        await db_session.execute(
            AutonomousReviewLLMAudit.__table__.select().where(AutonomousReviewLLMAudit.job_id == job.id)
        )
    ).mappings().first()

    assert stored is not None
    assert "[REDACTED]" in stored["prompt_text"]
    assert "abcdef123456" not in stored["prompt_text"]
    assert "[REDACTED_PRIVATE_KEY]" in stored["prompt_text"]
    assert "[REDACTED_TOKEN]" in stored["response_text"]


@pytest.mark.asyncio
async def test_report_llm_audit_respects_role_visibility(
    async_client,
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    reviewer, reviewer_headers = await create_test_user("reviewer")
    admin, admin_headers = await create_test_user("admin")
    project = await project_factory(admin.id)
    checklist = await checklist_factory(is_global=False, project_id=project.id)
    job, result, item = await _seed_job_with_result(db_session, project, checklist)

    db_session.add(
        AutonomousReviewLLMAudit(
            job_id=job.id,
            result_id=result.id,
            checklist_item_id=item.id,
            phase="item_analysis",
            status="completed",
            provider="ollama",
            model_name="qwen2.5-coder:7b",
            config_name="Local Ollama",
            item_code=item.item_code,
            item_area=item.area,
            item_question=item.question,
            prompt_summary="Evaluate checklist item against docs/architecture.md.",
            response_summary="Returned AMBER because ADR coverage is incomplete.",
            prompt_text="SYSTEM\nEvaluate architecture",
            response_text='{"rag":"amber"}',
        )
    )
    await db_session.commit()

    reviewer_response = await async_client.get(f"/api/reports/{job.id}/llm-audit", headers=reviewer_headers)
    assert reviewer_response.status_code == 200
    reviewer_payload = reviewer_response.json()
    assert reviewer_payload["can_view_full"] is False
    assert reviewer_payload["entries"][0]["prompt_text"] is None
    assert reviewer_payload["entries"][0]["response_text"] is None
    assert reviewer_payload["entries"][0]["prompt_summary"]

    admin_response = await async_client.get(f"/api/reports/{job.id}/llm-audit", headers=admin_headers)
    assert admin_response.status_code == 200
    admin_payload = admin_response.json()
    assert admin_payload["can_view_full"] is True
    assert "Evaluate architecture" in admin_payload["entries"][0]["prompt_text"]
    assert admin_payload["entries"][0]["response_text"] == '{"rag":"amber"}'


@pytest.mark.asyncio
async def test_report_history_includes_llm_audit_count(
    async_client,
    db_session,
    create_test_user,
    project_factory,
    checklist_factory,
):
    user, headers = await create_test_user("admin")
    project = await project_factory(user.id)
    checklist = await checklist_factory(is_global=False, project_id=project.id)
    job, result, item = await _seed_job_with_result(db_session, project, checklist)

    db_session.add(
        AutonomousReviewLLMAudit(
            job_id=job.id,
            result_id=result.id,
            checklist_item_id=item.id,
            phase="planning",
            status="completed",
            prompt_summary="Plan routing for one item.",
            response_summary="Planned one llm_analysis item.",
        )
    )
    await db_session.commit()

    response = await async_client.get("/api/reports/history", headers=headers)
    assert response.status_code == 200
    reports = response.json()["reports"]
    row = next(r for r in reports if r["job_id"] == job.id)
    assert row["llm_audit_count"] == 1


@pytest.mark.asyncio
async def test_is_llm_audit_enabled_reads_system_setting(db_session):
    db_session.add(
        SystemSetting(
            key="LLM_AUDIT_ENABLED",
            value="false",
            description="toggle",
            category="Agent",
            is_mandatory=False,
        )
    )
    await db_session.commit()

    assert await is_llm_audit_enabled(db_session) is False
