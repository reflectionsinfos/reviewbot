# ReviewBot Design

Current implementation design snapshot based on the codebase as of April 23, 2026, with approved near-term design direction for external review.

## System Overview

ReviewBot is a single FastAPI application that serves both backend APIs and a vanilla HTML/JS frontend. Its primary production-ready capability is autonomous code review. The system manages projects and checklists, runs asynchronous review jobs, stores evidence and history, and generates remediation-oriented action plans from completed reviews.

## High-Level Architecture

```text
Browser UI / External Agent
        |
        v
FastAPI application
  - auth and admin APIs
  - project and checklist APIs
  - autonomous review APIs
  - agent bridge APIs
  - report/history APIs
  - static frontend pages
        |
        +--> Background review orchestration
        |     - source scanning or uploaded agent metadata
        |     - strategy routing
        |     - analyzers
        |     - LLM audit capture
        |     - persisted results and summary counters
        |
        +--> PostgreSQL via async SQLAlchemy
        |
        +--> File outputs
        |     - uploads/
        |     - reports/
        |
        +--> Configured LLM providers
              - OpenAI-compatible cloud providers
              - optional local Ollama-style endpoint
```

## Runtime Surfaces

### Web pages

- `/` and `/dashboard` - home/dashboard
- `/ui` - autonomous review launcher and live progress view
- `/history` - review history, details, action plan, and AI trace view
- `/projects-ui` - project and project-checklist management
- `/globals` - global checklist template management
- `/documentation` - product and engine explanation page
- `/system-config` - LLM provider and system settings management

### Core API groups

- `/api/auth`
- `/api/organizations`
- `/api/projects`
- `/api/checklists`
- `/api/autonomous-reviews`
- `/api/reports`
- `/api/v1/agent/scan`
- `/api/llm-configs`
- `/api/settings`
- `/api/admin/users`
- `/api/integrations`
- `/api/routing-rules`

## Main Design Flows

### 1. Autonomous review through the main app

1. User selects a project, checklist, and source in the web UI.
2. `POST /api/autonomous-reviews/` creates an `AutonomousReviewJob`.
3. A background task runs the autonomous review orchestrator.
4. The source is scanned into a lightweight file index.
5. Each checklist item is routed to a strategy.
6. The relevant analyzer returns RAG status, evidence, and files checked.
7. Results are persisted immediately and progress is broadcast over WebSocket.
8. The job summary counters and compliance score are finalized at completion.
9. History, details, action plan, and LLM audit become available through report endpoints.

### 2. Autonomous review through the agent bridge

1. An external client uploads workspace metadata to `/api/v1/agent/scan/upload`.
2. The server stores metadata on an `AutonomousReviewJob` but does not start analysis yet.
3. The client polls `/file-requests` and uploads file content on demand.
4. `POST /start` begins hybrid orchestration.
5. Agent mode performs deterministic routing first, optional planning for remaining LLM items, then execution.
6. Results are stored using the same job/result models used by the main autonomous-review flow.

### 3. Post-review analysis and remediation

1. History UI loads `/api/reports/history` and `/api/reports/{job_id}/details`.
2. Reviewers can override individual results.
3. Action plans are generated on demand from stored review results and checklist metadata.
4. Optional AI enhancement enriches prompts and caches them back on the job record.
5. LLM execution traces can be viewed through `/api/reports/{job_id}/llm-audit` with role-sensitive detail.

### 4. Planned external review through scoped Excel distribution

1. An admin or reviewer selects the global master checklist and creates a project-scoped checklist.
2. The reviewer edits project-specific applicability before distribution.
3. The reviewer defines participating review teams and maps them to checklist categories.
4. ReviewBot freezes a review snapshot containing the exact item set, team mapping, and scoring rules for that review cycle.
5. ReviewBot generates one team-scoped Excel export per review team.
6. External teams submit their response files and supporting evidence against that frozen snapshot.
7. The system validates snapshot integrity, imports responses, applies scoring rules, and builds one consolidated report.

## Core Components

### API layer

- `main.py` registers routes, WebSocket progress, and static-page delivery.
- Route modules are grouped by business area rather than by frontend page.

### Domain and persistence

- `app/models.py` contains the SQLAlchemy models for users, projects, checklists, reviews, reports, autonomous jobs, overrides, LLM audit, and future v2 workflow entities.
- `app/db/session.py` manages async engine/session lifecycle and database initialization.

### Autonomous review engine

- `orchestrator.py` runs the main background autonomous-review job.
- `agent_orchestrator.py` runs the hybrid agent-upload path.
- `strategy_router_agent.py` maps checklist items to strategies.
- `connectors/local_folder.py` indexes a local source tree for the main orchestrator.
- `connectors/agent_scan.py` provides a file index view over uploaded agent metadata and content.
- `analyzers/` contains `file_presence`, `pattern_scan`, `metadata_check`, and `llm_analyzer`.
- `progress.py` manages WebSocket subscribers per review job.

### Post-review services

- `action_plan_generator.py` turns results into manager-facing action cards and developer-facing AI prompts.
- `report_generator.py` produces Markdown and PDF reports for manual or conversational review flows.
- `llm_audit.py` captures redacted prompt/response traces and usage metadata.

### Planned external review services

- A master-checklist metadata extension will add team category, guidance text, and applicability tags to checklist items.
- A project review team service will manage team definitions, named owners, and responsibility scope.
- A review snapshot service will freeze checklist content and team mappings before Excel distribution. The snapshot is represented by a `ReviewSnapshot` entity with fields: `id`, `review_id`, `revision` (integer, incrementing per distribution), `checksum` (SHA-256 of serialised item set), `frozen_at`, `status` (`active` / `superseded` / `revoked`), `item_snapshot` (JSONB), `team_snapshot` (JSONB), and `scoring_rules` (JSONB). Each time the reviewer clicks "Distribute" after editing the project checklist, a new revision is created and the previous one is marked `superseded`. Upload tokens are scoped to a specific `snapshot_id + team_id` so uploads against older revisions remain independently revocable.
- An Excel export service will generate protected team-scoped workbooks using `openpyxl` (library choice to be confirmed in Phase 0 spike). Each workbook includes: a protected metadata sheet carrying `snapshot_id`, `revision`, `team_id`, and `checksum`; locked columns for all read-only fields; data-validation dropdowns for `Response State` and `Confidence`; an instructions sheet; and visual colour differentiation between locked and editable columns.
- A response-import service implemented as `ExcelResponseParser` inside the existing `checklist_parser.py` module. The new class shares the file-reading infrastructure with the existing `ChecklistParser` but has independent column mapping, snapshot validation, and response-state parsing logic. It validates `snapshot_id`, `checksum`, and `team_id` from the metadata sheet before touching any response rows, rejects rows where locked column values differ from the snapshot, and returns structured `ParsedResponse` objects plus a list of row-level `ParseError` objects for surfacing to the reviewer.
- Distribution email notifications will route through the existing `IntegrationConfig` / dispatcher infrastructure with a new `distribution` trigger type, avoiding a second SMTP codepath. Distribution attempts are recorded in `IntegrationDispatch` audit records alongside post-review dispatch history.

### Conversational review foundation

- `review_agent.py` defines a LangGraph-based question-and-response workflow.
- `voice_interface.py` provides speech-to-text and text-to-speech helpers.
- `reviews.py` exposes review-session APIs but the overall experience is still less mature than the autonomous-review path.

### Frontend

- Frontend pages are static HTML files with embedded JavaScript.
- Shared header and footer loaders provide auth/session UI, change-password UI, and admin user-management modals.
- The history page is the richest operational screen in the current product.

### External review frontend status

- Implemented now: `/globals` supports listing, creating, uploading, renaming, editing, and deleting global checklists and their items.
- Implemented now: `/projects-ui` supports project selection, cloning a global checklist into a project, syncing from the source template, and editing/reordering project checklist items.
- Not implemented: the global checklist flow is still built around the two-template `technical` / `delivery` model rather than the single master checklist model.
- Not implemented: checklist items do not expose `team_category`, guidance, or applicability metadata in the UI or the backing schemas.
- Not implemented: there is no project review team setup surface for team names, owners, emails, or scope mapping.
- Not implemented: there is no distribution workspace for snapshot creation, team-scoped Excel generation, signed-link handling, or upload monitoring.
- Not implemented: there is no external team respondent page for token-scoped download/upload, and no reviewer dashboard for parse errors, superseded revisions, or partial-report gating.

### Planned external review frontend architecture

The external async review feature should extend the existing vanilla frontend rather than introducing a second client stack. The target interaction model is a guided reviewer workflow layered onto the existing `/globals` and `/projects-ui` pages, plus one new external-review operations surface.

1. Global master checklist workspace (`/globals`)
   The current template page becomes the master checklist library. Each item row gains `team_category`, guidance, applicability tags, and richer evidence metadata. The create flow should stop forcing `technical` versus `delivery` as the top-level information architecture.
2. Project checklist tailoring workspace (`/projects-ui`)
   The current project checklist editor remains the working copy surface, but it gains project-only overrides such as exclude/restore, reassignment of ownership category, and custom-item creation. This is where the reviewer prepares the checklist before any distribution occurs.
3. Project review team setup panel (`/projects-ui`)
   A new setup panel or tab defines participating teams, lead contacts, scope notes, and category mapping. The UI must show item counts per team and unresolved setup gaps before distribution is enabled.
4. Distribution and monitoring workspace (new reviewer surface)
   A new page should manage `ReviewSnapshot` revisions, team-scoped export generation, signed-link status, submission progress, parse warnings, and regenerate/resend actions. This surface is the operational home for the reviewer after clicking Distribute.
5. External team response page (new token-scoped surface)
   External respondents should receive a minimal download/upload page scoped to one `snapshot_id + team_id`. It should expose only the workbook, upload control, due-date/status messaging, and basic help text.

### Frontend implementation plan

1. Phase FE-1: master checklist metadata
   Extend `/globals` and checklist item forms to capture `team_category`, guidance, and applicability metadata, and remove the UI assumption that all global checklists are only `technical` or `delivery`.
2. Phase FE-2: project tailoring and team mapping
   Extend `/projects-ui` with exclude/restore controls, category reassignment, project-only custom questions, and a new review-team management panel with readiness validation.
3. Phase FE-3: snapshot distribution workflow
   Add the reviewer-facing distribution workspace that creates `ReviewSnapshot` revisions, shows revision metadata, generates team exports, and triggers distribution through the existing integration infrastructure.
4. Phase FE-4: upload monitoring and consolidation controls
   Add per-team lifecycle status, parse-error visibility, re-upload handling, revoke/reissue actions, and the partial-report gating flow before consolidated report generation.
5. Phase FE-5: external respondent and polish
   Add the token-scoped respondent download/upload page, finalize audit/status messaging, and validate the full flow against desktop browser usage plus the Excel round-trip constraints defined in Phase 0.

## Strategy Model

The autonomous-review system currently uses these strategy types:

- `file_presence` - verify required files or directories exist
- `pattern_scan` - inspect text/code for regex-detectable patterns
- `metadata_check` - evaluate metadata and config-file-driven evidence
- `llm_analysis` - use an LLM for code or design judgment
- `human_required` - mark items that require organizational or non-repository evidence
- `ai_and_human` - use AI analysis but still require human confirmation

Design intent:

- Prefer deterministic checks where possible.
- Use LLM analysis only when structural or qualitative judgment is needed.
- Preserve reviewer control through routing overrides and result overrides.

## Data Model Summary

### Core implemented entities

- `Organization` — name, slug, description, is_active; parent for users/projects/checklists
- `User` — email, hashed_password, role, is_active, organization_id (FK)
- `Project` — name, domain, tech_stack (JSON), stakeholders (JSON), organization_id (FK)
- `Checklist` — name, type, is_global, organization_id (FK); NULL org = platform-wide
- `ChecklistItem` — area, code, question, expected_evidence, weight, is_mandatory, team_category, guidance, applicability_tags (JSON), sort_order
- `Review`
- `ReviewResponse`
- `Report`
- `ReportApproval`
- `AutonomousReviewJob`
- `AutonomousReviewResult`
- `AutonomousReviewOverride`
- `AutonomousReviewLLMAudit`
- `LLMConfig`
- `SystemSetting`
- `ChecklistRoutingRule`
- `ChecklistRecommendation`
- `IntegrationConfig` — type (jira/smtp/webhook/linear/github_issues), credentials (JSON, masked on GET), trigger_condition, is_enabled
- `IntegrationDispatch` — audit record per dispatch attempt

### Future-oriented v2 entities already modeled

- `ProjectMember`
- `RecurringReviewSchedule`
- `MilestoneReviewTrigger`
- `ReviewInstance`
- `SelfReviewSession`
- `ConsolidatedSelfReviewReport`
- `ReminderQueue`
- `MeetingBlock`
- `StakeholderPreparation`
- `GapTracking`
- `ReviewTrendAnalytics`

These tables signal the intended expansion of the product, but they are not yet fully surfaced through APIs and UI.

### Planned external review entities and extensions

The approved external-review design adds a new layer between checklist management and report generation:

- `ChecklistItem` gains metadata for `team_category`, `guidance`, and optional applicability filters.
- Project-scoped checklists remain the working copy where reviewers can exclude or refine items before distribution.
- `ProjectReviewTeam` stores team name, category, lead name, lead email, and responsibility scope text per project.
- `Review` gains a `mode` field (`autonomous` / `external_async` / `live`) and a `current_snapshot_id` FK.
- `ReviewResponse` gains `team_id`, `response_state` (`answered` / `na_out_of_scope` / `delegated` / `needs_clarification` / `not_submitted`), `confidence`, `assigned_owner`, and clarification text fields.
- `ReviewSnapshot` stores the frozen item set and is the key new entity: `id`, `review_id`, `revision` (int), `checksum`, `frozen_at`, `status` (`active` / `superseded` / `revoked`), `item_snapshot` (JSONB), `team_snapshot` (JSONB), `scoring_rules` (JSONB). A distribution token table references `ReviewSnapshot.id` and `ProjectReviewTeam.id` with expiry and revocation fields.

## Organization Scoping Design

ReviewBot uses a **lightweight org-scoping layer** — not full multi-tenancy — to support multi-org deployments without a complete architectural rewrite.

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| `organization_id = NULL` means platform-wide | Zero-config default; existing data needs no migration |
| Scoping only on `User`, `Project`, `Checklist` | The minimum surface needed; reviews and results inherit context from parent |
| Admin-only writes, any-auth reads for `/api/organizations` | Orgs are reference data; listing them for dropdowns needs no privilege |
| `Organization.is_active = False` for soft-delete | Preserves referential integrity with existing users and projects |
| `GlobalChecklistCreate.type` accepts any string | Enables the planned master-checklist model (`type = "master"`) without breaking existing `delivery` / `technical` templates |

### Global checklist visibility rule

```python
# applied in ChecklistService.get_global_checklist_templates
or_(
    Checklist.organization_id == None,           # platform-wide
    Checklist.organization_id == current_user.organization_id,  # user's org
)
```

Templates created with `organization_id = NULL` are visible to every user. Templates created with an explicit org id are private to that org's users.

### `/api/organizations` endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/organizations/` | any auth | List all active organizations |
| `GET` | `/api/organizations/mine` | any auth | Return current user's organization (404 if unassigned) |
| `GET` | `/api/organizations/{id}` | any auth | Get one organization |
| `POST` | `/api/organizations/` | admin | Create organization (slug auto-generated) |
| `PUT` | `/api/organizations/{id}` | admin | Update name/description |
| `DELETE` | `/api/organizations/{id}` | admin | Soft-delete (sets is_active=False) |

## Configuration Design

### Application settings

- Pydantic settings are loaded from `.env`, `env.non-prod.gcp`, and `env.local`.
- Important runtime knobs include database URL, active LLM provider, storage paths, JWT settings, and local dev auto-login values.

### LLM configuration

- LLM providers can be driven from database rows in `llm_configs`.
- The connector layer supports cloud providers and local Ollama-style endpoints through OpenAI-compatible clients.
- Usage counters and optional request/token limits are stored on LLM config records.

### System settings

- `SystemSetting` provides runtime configuration for admin-managed toggles and public UI settings.
- `LLM_AUDIT_ENABLED` is one important current setting surfaced in the UI.

## Security Model

- JWT bearer tokens protect authenticated APIs.
- Admin-only routes enforce role checks in route handlers.
- Passwords are hashed with bcrypt through Passlib.
- LLM audit storage redacts sensitive values before persistence.
- Current implementation is not yet a full audit-logging or rate-limited platform.

## Deployment Model

### Local

- Docker Compose runs app plus PostgreSQL.
- Reports, uploads, and database data are persisted locally.
- Seed and reset scripts support local test data workflows.

### GCP

- The repo includes scripts to enable APIs, set up IAM, create infrastructure, create the database, and deploy the app.
- Cloud Run plus Cloud SQL is the intended hosted deployment model reflected in the repo tooling.

## Current Design Strengths

- Clear separation between API routes, services, and persistence
- Strong operational support for autonomous-review history and remediation
- Flexible multi-provider LLM layer
- Review strategy model that balances deterministic and LLM-based checks
- Forward-looking schema foundation for later workflow expansion
- A reusable checklist/project/report backbone that can support external review without creating a separate product silo

## Current Design Gaps

- Direct repository-intake flow is not as stable as the agent-upload workflow and needs further completion.
- Conversational review is present as a scaffolded capability rather than a flagship production path.
- General audit logging and rate limiting are not implemented. Lightweight org scoping is now in place; full row-level multi-tenant isolation remains a future concern.
- Several v2 workflow entities are modeled but not yet activated through user-facing flows.
- Frontend is functional and fast to ship, but long-term complexity may justify a richer client architecture later.
- Frontend currently exposes only template CRUD and project checklist CRUD; it does not yet expose master-checklist metadata, project review team mapping, snapshot distribution, upload-status monitoring, or consolidated external-review operations.
- External review lacks implementation of the `ReviewSnapshot` revision model, `ProjectReviewTeam`, and `ExcelResponseParser` — all designed and specified in `docs/EXCEL_TEMPLATE_REVIEW_ANALYSIS.md` but not yet built.
- Checklist ownership is not yet modeled at the item/category/team layers needed for multi-team external reviews.
- The current Excel parser (`ChecklistParser`) only handles source checklist ingestion; the planned `ExcelResponseParser` class for team response import is not yet implemented.
- Distribution email for external review has no dedicated path yet; the design calls for routing through the existing SMTP integration dispatcher with a new `distribution` trigger type.
