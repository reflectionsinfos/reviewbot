-- ============================================================
-- ReviewBot — Dev Data Reset
-- Clears ALL data EXCEPT: users, llm_configs, system_settings,
--                          integration_configs
-- Resets all integer sequences to 1.
-- Nullifies users.organization_id (orgs are being wiped).
--
-- Usage (Docker):
--   docker exec -i reviewbot-db-1 psql -U review_user -d reviews_db \
--     < scripts/reset_dev_data.sql
--
-- Usage (local psql):
--   psql -h localhost -p 5435 -U review_user -d reviews_db \
--     -f scripts/reset_dev_data.sql
-- ============================================================

BEGIN;

-- ── 1. Deep leaf tables (audit / override / dispatch rows) ─────────────────
TRUNCATE TABLE autonomous_review_llm_audits   RESTART IDENTITY CASCADE;
TRUNCATE TABLE autonomous_review_overrides    RESTART IDENTITY CASCADE;
TRUNCATE TABLE integration_dispatches         RESTART IDENTITY CASCADE;
TRUNCATE TABLE report_approvals               RESTART IDENTITY CASCADE;
TRUNCATE TABLE checklist_recommendations      RESTART IDENTITY CASCADE;
TRUNCATE TABLE checklist_routing_rules        RESTART IDENTITY CASCADE;

-- ── 2. Review-instance children ────────────────────────────────────────────
TRUNCATE TABLE stakeholder_preparation        RESTART IDENTITY CASCADE;
TRUNCATE TABLE meeting_blocks                 RESTART IDENTITY CASCADE;
TRUNCATE TABLE reminder_queue                 RESTART IDENTITY CASCADE;
TRUNCATE TABLE consolidated_self_review_reports RESTART IDENTITY CASCADE;
TRUNCATE TABLE self_review_sessions           RESTART IDENTITY CASCADE;

-- ── 3. Project-level analytics / tracking ──────────────────────────────────
TRUNCATE TABLE gap_tracking                   RESTART IDENTITY CASCADE;
TRUNCATE TABLE review_trend_analytics         RESTART IDENTITY CASCADE;

-- ── 4. Review-instance level ───────────────────────────────────────────────
TRUNCATE TABLE review_instances               RESTART IDENTITY CASCADE;
TRUNCATE TABLE recurring_review_schedules     RESTART IDENTITY CASCADE;
TRUNCATE TABLE milestone_review_triggers      RESTART IDENTITY CASCADE;

-- ── 5. Review session children ─────────────────────────────────────────────
TRUNCATE TABLE review_responses               RESTART IDENTITY CASCADE;
TRUNCATE TABLE autonomous_review_results      RESTART IDENTITY CASCADE;

-- ── 6. Reports & autonomous jobs ───────────────────────────────────────────
TRUNCATE TABLE reports                        RESTART IDENTITY CASCADE;
TRUNCATE TABLE autonomous_review_jobs         RESTART IDENTITY CASCADE;

-- ── 7. Reviews & project members ───────────────────────────────────────────
TRUNCATE TABLE reviews                        RESTART IDENTITY CASCADE;
TRUNCATE TABLE project_members                RESTART IDENTITY CASCADE;

-- ── 8. Checklist items & checklists ───────────────────────────────────────
--    source_checklist_id is a self-FK on checklists; null it first so
--    TRUNCATE doesn't trip on the self-reference even with CASCADE.
UPDATE checklists SET source_checklist_id = NULL;
TRUNCATE TABLE checklist_items                RESTART IDENTITY CASCADE;
TRUNCATE TABLE checklists                     RESTART IDENTITY CASCADE;

-- ── 9. Projects ────────────────────────────────────────────────────────────
TRUNCATE TABLE projects                       RESTART IDENTITY CASCADE;

-- ── 10. Organizations ──────────────────────────────────────────────────────
TRUNCATE TABLE organizations                  RESTART IDENTITY CASCADE;

-- ── 11. Repair users (remove stale org FK) ────────────────────────────────
UPDATE users SET organization_id = NULL;

COMMIT;

-- ── Verify ─────────────────────────────────────────────────────────────────
SELECT 'users'            AS "table", COUNT(*) FROM users
UNION ALL
SELECT 'organizations',              COUNT(*) FROM organizations
UNION ALL
SELECT 'projects',                   COUNT(*) FROM projects
UNION ALL
SELECT 'checklists',                 COUNT(*) FROM checklists
UNION ALL
SELECT 'checklist_items',            COUNT(*) FROM checklist_items
UNION ALL
SELECT 'reviews',                    COUNT(*) FROM reviews
UNION ALL
SELECT 'reports',                    COUNT(*) FROM reports
UNION ALL
SELECT 'autonomous_review_jobs',     COUNT(*) FROM autonomous_review_jobs
UNION ALL
SELECT 'llm_configs',                COUNT(*) FROM llm_configs
UNION ALL
SELECT 'system_settings',            COUNT(*) FROM system_settings
UNION ALL
SELECT 'integration_configs',        COUNT(*) FROM integration_configs
ORDER BY "table";
