# ReviewBot Design

Current implementation design snapshot based on the codebase as of April 17, 2026.

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
- `/api/projects`
- `/api/checklists`
- `/api/autonomous-reviews`
- `/api/reports`
- `/api/v1/agent/scan`
- `/api/llm-configs`
- `/api/settings`
- `/api/admin/users`

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

### Conversational review foundation

- `review_agent.py` defines a LangGraph-based question-and-response workflow.
- `voice_interface.py` provides speech-to-text and text-to-speech helpers.
- `reviews.py` exposes review-session APIs but the overall experience is still less mature than the autonomous-review path.

### Frontend

- Frontend pages are static HTML files with embedded JavaScript.
- Shared header and footer loaders provide auth/session UI, change-password UI, and admin user-management modals.
- The history page is the richest operational screen in the current product.

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

- `User`
- `Project`
- `Checklist`
- `ChecklistItem`
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

## Current Design Gaps

- Direct repository-intake flow is not as stable as the agent-upload workflow and needs further completion.
- Conversational review is present as a scaffolded capability rather than a flagship production path.
- General audit logging, rate limiting, and multi-tenant boundaries are not implemented.
- Several v2 workflow entities are modeled but not yet activated through user-facing flows.
- Frontend is functional and fast to ship, but long-term complexity may justify a richer client architecture later.
