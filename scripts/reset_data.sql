-- ============================================================
-- ReviewBot - Reset all data except users
-- Preserves: users
-- Clears: all project, checklist, review, report and
--         autonomous-review tables in FK-safe order
-- Safe to run multiple times (TRUNCATE is idempotent)
-- ============================================================

BEGIN;

TRUNCATE TABLE
    -- Autonomous review tables (deepest dependents first)
    autonomous_review_overrides,
    autonomous_review_llm_audits,
    autonomous_review_results,
    autonomous_review_jobs,

    -- Scheduling / recurring reviews
    review_instances,
    milestone_review_triggers,
    recurring_review_schedules,

    -- Report approval chain
    report_approvals,
    reports,

    -- Review session data
    review_responses,
    reviews,

    -- Checklist metadata
    checklist_recommendations,
    checklist_routing_rules,
    checklist_items,
    checklists,

    -- Project membership & projects
    project_members,
    projects

CASCADE;

COMMIT;

-- ============================================================
-- Verification — shows row counts for every table
-- ============================================================
SELECT
    table_name,
    (xpath(
        '/row/c/text()',
        query_to_xml(
            format('SELECT count(*) AS c FROM %I', table_name),
            FALSE, TRUE, ''
        )
    ))[1]::text::int AS rows
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type  = 'BASE TABLE'
ORDER BY table_name;
