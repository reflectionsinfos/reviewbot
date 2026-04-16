# ReviewBot Requirements

Implementation-aligned requirements snapshot based on the codebase as of April 17, 2026.

## Product Intent

ReviewBot helps teams run structured technical and delivery reviews using reusable checklists, autonomous evidence gathering, and post-review remediation guidance. The current release is centered on autonomous code review plus checklist and review operations. Broader review modes remain on the roadmap.

## Scope Summary

### In scope now

- Autonomous code review against project or template checklists
- Project, checklist, and template lifecycle management
- Review history, overrides, action plans, and LLM audit visibility
- Admin user management and system configuration
- External agent bridge for local workspace reviews

### Partially in scope

- Direct repository intake from the web UI/API
- Conversational review and voice-assisted review foundations
- Human approval and report download workflows

### Out of scope for the current release

- End-to-end document review
- Knowledge quiz flows
- Persona-based self-review and readiness workflows
- Automated reminders, meeting blocks, and stakeholder preparation workflows
- Meeting bot integrations
- Full analytics and trend dashboards

## Functional Requirements

| ID | Requirement | Priority | Current Status | Notes |
|---|---|---|---|---|
| FR-01 | Users can authenticate with JWT and view their current profile | Must | Done | `auth.py` implements login, register, `/me`, and password change. |
| FR-02 | Admins can create, reset, update, activate/deactivate, and delete users | Must | Done | Exposed through `/api/admin/users` and shared header UI. |
| FR-03 | Local development supports auto-login without exposing dev credentials in non-local environments | Should | Done | `/api/auth/dev-config` only works when `APP_ENV=local`. |
| FR-04 | Users can create, update, delete, and list projects | Must | Done | Domain, description, tech stack, and stakeholders are stored. |
| FR-05 | Users can upload Excel-based checklists and create project checklists from global templates | Must | Done | Project upload plus global template cloning are implemented. |
| FR-06 | Admins can manage global checklist templates and their items | Must | Done | Global checklist CRUD, upload, item CRUD, and area-code support exist. |
| FR-07 | Project checklists can be synced from their source global template | Should | Done | `add_only`, `add_and_update`, and `full_reset` sync behaviors are implemented. |
| FR-08 | Checklist items can be reordered and protected from deletion when historical reviews exist | Must | Done | Delete guards check both manual reviews and autonomous jobs. |
| FR-09 | The system can start autonomous review jobs and persist per-item findings | Must | Done | `AutonomousReviewJob` and `AutonomousReviewResult` store review state and findings. |
| FR-10 | Autonomous reviews classify checklist items into the correct analysis strategy | Must | Done | Strategy routing supports deterministic rules plus human-routing overrides. |
| FR-11 | Autonomous reviews support file-presence checks, pattern scans, metadata checks, LLM analysis, and human-required items | Must | Done | These are the currently implemented analyzer types. |
| FR-12 | Autonomous reviews stream progress to the UI in real time | Must | Done | WebSocket endpoint `/ws/autonomous-reviews/{job_id}` is implemented. |
| FR-13 | Completed autonomous reviews expose structured history and detailed result views | Must | Done | History, details, counters, override counts, and LLM audit counts are exposed. |
| FR-14 | Reviewers can override autonomous findings with audit history | Must | Done | Available in both main autonomous-review routes and agent routes. |
| FR-15 | Review results can produce structured action plans for managers and developers | Must | Done | Action cards plus AI-ready prompts are implemented server-side and exposed in history UI. |
| FR-16 | Action-plan prompts can be optionally enhanced with AI and cached for reuse | Should | Done | Enhanced prompts are stored in job metadata. |
| FR-17 | The system stores a redacted LLM audit trail for planning, item analysis, and prompt enhancement | Should | Done | Visibility is role-sensitive; full text is restricted. |
| FR-18 | Admins can manage active LLM providers and test connectivity | Must | Done | Backed by `llm_configs` table and system-config page. |
| FR-19 | Admins can manage public system settings such as branding and agent controls | Should | Done | `SystemSetting` management exists; public settings endpoint is limited. |
| FR-20 | External clients can upload workspace metadata, provide requested file content, and trigger a review job | Must | Done | Agent bridge endpoints under `/api/v1/agent/scan`. |
| FR-21 | Review history allows source-path correction, report regeneration, and detailed drill-down | Should | Done | Present in report/history endpoints and history UI. |
| FR-22 | Manual conversational review sessions can be created and progressed question by question | Should | Partial | Core routes exist but the flow is still lightweight compared with autonomous review. |
| FR-23 | Voice responses can be transcribed and attached to review sessions | Could | Partial | Voice helpers exist; this is not yet a polished primary workflow. |
| FR-24 | Report approval workflow supports approve, reject, and approval history | Should | Partial | Backend endpoints exist, but the autonomous-review experience is more mature than approval UX. |
| FR-25 | Direct repository URL review from the main autonomous-review UI works across providers | Must | Partial | UI/API encoding is present, but this path still needs stabilization relative to agent mode. |
| FR-26 | Document review supports PDF, DOCX, Markdown, and Confluence sources | Must | Planned | Not implemented end to end. |
| FR-27 | Knowledge quiz supports text and voice adaptive questioning | Must | Planned | Not implemented end to end. |
| FR-28 | Persona-based self-review, recurring schedules, reminders, and meeting blocks are operational | Should | Planned | Data model groundwork exists; APIs/UI do not. |
| FR-29 | Review analytics and trend dashboards are available in product UI | Should | Planned | Trend tables exist in schema only. |

## Non-Functional Requirements

| ID | Requirement | Current Status | Notes |
|---|---|---|---|
| NFR-01 | Async API and database access | Done | FastAPI plus async SQLAlchemy are used throughout the main backend. |
| NFR-02 | Persistent relational storage | Done | PostgreSQL is the active persistence layer; Alembic migrations are present. |
| NFR-03 | Local developer setup through Docker | Done | `docker-compose.yml`, seed scripts, and local env files are present. |
| NFR-04 | Cloud deployment automation | Done | GCP setup and deploy scripts exist under `gcp_scripts/`. |
| NFR-05 | Role-based access control for admin operations | Done | Admin-only paths are enforced in user, settings, and LLM config routes. |
| NFR-06 | Redacted storage of sensitive LLM prompt/response traces | Done | LLM audit redaction is covered by tests. |
| NFR-07 | Review progress visibility during long-running jobs | Done | WebSockets plus polling fallback are implemented. |
| NFR-08 | Historical integrity of checklist-linked reviews | Done | Checklist deletion is blocked when reviews or jobs reference it. |
| NFR-09 | Comprehensive automated test coverage for the full product | Partial | Meaningful tests exist, but broad end-to-end coverage is still incomplete. |
| NFR-10 | Audit logging beyond LLM-specific traces | Planned | General audit logging is not yet implemented. |
| NFR-11 | Rate limiting and abuse protection | Planned | No production-grade rate limiting layer is wired yet. |
| NFR-12 | Multi-tenant isolation | Planned | Current data model and routing assume a single deployment context. |

## Current Release Boundaries

### Strongest current journey

1. Admin or reviewer signs in.
2. Project and checklist are selected or prepared.
3. An autonomous review is launched.
4. Progress streams live through the UI.
5. Findings are stored and reviewed in history.
6. Reviewers override findings if needed.
7. Teams export or copy the action plan and AI prompts.

### Important implementation caveats

- The agent-upload workflow is the most mature route for reviewing a local workspace.
- Conversational review APIs are available but are not yet a flagship end-to-end UX.
- Several v2 entities exist in the schema to support future review orchestration but are not yet wired into public workflows.

## Near-Term Priorities

1. Stabilize and complete direct repository intake so the web UI path is as reliable as the agent-upload path.
2. Continue maturing action-plan and remediation workflows.
3. Ship the document-review engine.
4. Build the knowledge-quiz flow.
5. Wire up self-review, scheduling, reminders, and analytics on top of the existing v2 schema foundation.
