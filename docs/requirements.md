# ReviewBot Requirements

Implementation-aligned requirements snapshot based on the codebase as of April 23, 2026, including the approved near-term external review design direction.

## Product Intent

ReviewBot helps teams run structured technical and delivery reviews using reusable checklists, autonomous evidence gathering, and post-review remediation guidance. The current release is centered on autonomous code review plus checklist and review operations. Broader review modes remain on the roadmap, with external async review via scoped Excel distribution now defined as an approved near-term design.

## Scope Summary

### In scope now

- Autonomous code review against project or template checklists
- Project, checklist, and template lifecycle management
- Review history, overrides, action plans, and LLM audit visibility
- Admin user management and system configuration
- External agent bridge for local workspace reviews
- Configurable outbound integrations: JIRA ticket creation, SMTP email notifications, and generic webhooks triggered automatically on review completion
- Dependency vulnerability scanning via local CLI tools (Trivy, OSV Scanner, pip-audit, npm audit) with CVE-to-RAG mapping

### Partially in scope

- Direct repository intake from the web UI/API
- Conversational review and voice-assisted review foundations
- Human approval and report download workflows
- External review foundations through existing checklist, manual review, report, and file-upload building blocks, but not yet the full team-scoped Excel distribution flow

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
| FR-30 | Admins can configure outbound integrations (JIRA, SMTP email, Generic Webhook, Linear, GitHub Issues) with per-integration credentials, trigger conditions, and enable/disable state | Must | Done | `IntegrationConfig` table and full CRUD API at `/api/integrations`. Secrets are masked in all GET responses. |
| FR-31 | When an autonomous review job completes, the system automatically dispatches to all enabled integrations based on each integration's trigger condition | Must | Done | Dispatcher runs in a fully isolated session after job completion; failure never affects job status. |
| FR-32 | Integration trigger conditions control when auto-dispatch fires: `always` (every completed job), `red_only` (only when red findings exist), or `manual` (never auto-dispatches) | Must | Done | Evaluated per integration in `_should_dispatch()` against the job's `red_count`. |
| FR-33 | The JIRA integration creates one issue per dispatched ActionCard using Jira REST API v3 with configurable project key, issue type, labels, and priority mapping | Must | Done | ADF-formatted descriptions; config includes `url`, `email`, `api_token`, `project_key`, `issue_type`, `labels`, `priority_map`. |
| FR-34 | The SMTP email integration sends a single summary email per job with HTML and plain-text parts covering score, critical blockers, and advisories to a configurable recipient list | Must | Done | Supports `include_project_stakeholders` flag that also emails contacts stored in the project's stakeholders JSON. |
| FR-35 | The generic webhook integration POSTs a structured JSON payload (job summary + critical blockers) to any configured URL with custom headers and configurable HTTP method | Must | Done | Implemented in `dispatcher._webhook()` using `httpx`. |
| FR-36 | Admins can test connectivity for each integration before enabling it without triggering a real dispatch | Must | Done | `POST /api/integrations/{id}/test` routes to provider-specific `test_connection()` implementations. |
| FR-37 | Admins and managers can manually trigger a specific integration for any completed review job | Must | Done | `POST /api/integrations/{id}/dispatch/{job_id}` calls `run_manual_dispatch()`. |
| FR-38 | Every dispatch attempt (auto and manual) is persisted as an audit record with status, item counts, result details, and error message | Must | Done | `IntegrationDispatch` table; retrievable via `GET /api/integrations/dispatches/{job_id}`. |
| FR-39 | An integration can optionally include amber advisory findings (in addition to red critical blockers) in its dispatch payload | Should | Done | `include_advisories` flag on `IntegrationConfig`; evaluated when building the card list in `_call_handler()`. |
| FR-40 | The autonomous review engine can detect known CVEs and dependency vulnerabilities in a project's source tree using local scanning tools | Must | Done | `SecurityScanAnalyzer` tries Trivy → OSV Scanner → pip-audit → npm-audit in order; maps findings to RAG status. |
| FR-41 | Security scanning uses no external API keys or accounts; all tools run locally against the source path | Must | Done | Trivy, OSV Scanner, pip-audit, and npm-audit are all open-source CLI tools requiring no credentials. |
| FR-42 | CRITICAL or HIGH severity CVEs produce a red RAG finding; MEDIUM or LOW produce amber; clean dependencies produce green | Must | Done | Severity mapping in `_rag_from_counts()` inside `security_scan.py`. |
| FR-43 | Security scan findings list the top CVEs with package name, installed version, available fix version, and CVSS severity | Must | Done | `_summarise()` builds structured evidence showing CVE ID, package, installed/fixed versions, and title. |
| FR-44 | Checklist items about known CVEs and dependency vulnerabilities are automatically routed to the security scan strategy without manual configuration | Must | Done | Deterministic keyword rules in `_SECURITY_SCAN_RULES` route CVE-related questions before falling back to LLM classification; LLM prompt also includes `security_scan` as a strategy option. |
| FR-45 | If no scanning tool is found in PATH the finding is marked `na` with installation instructions for each supported tool | Should | Done | `SecurityScanAnalyzer.analyze()` returns `AnalysisResult(rag_status="na", ...)` with links to Trivy, OSV Scanner, pip-audit, and npm. |
| FR-46 | Admins can maintain a single global master checklist whose items include `team_category`, guidance text, expected evidence, and applicability metadata | Must | Planned | This is the target replacement for the long-term two-template model used today. |
| FR-47 | Reviewers can derive a project-scoped checklist from the global master checklist and edit, exclude, delete, or reassign items before external review distribution | Must | Planned | Project-level overrides happen before distribution, not on the frozen review snapshot. |
| FR-48 | Projects can define one or more review teams with category, lead, email, and responsibility scope | Must | Planned | Teams are used to map checklist ownership and distribution targets. |
| FR-49 | ReviewBot can freeze a review snapshot before external distribution and reject uploads that do not match that snapshot version | Must | Planned | Snapshot integrity is required for safe Excel generation and parsing. |
| FR-50 | ReviewBot can generate one team-scoped Excel template per participating review team from a frozen review snapshot | Must | Planned | Team-scoped export is the recommended Milestone 1 distribution model. |
| FR-51 | Team-scoped Excel templates support protected columns plus editable fields for response state, answer, confidence, notes, clarification questions, and evidence references | Must | Planned | Protected fields must include snapshot and item identifiers. |
| FR-52 | External async review uploads can be parsed into `ReviewResponse` records with explicit response states such as `answered`, `na_out_of_scope`, `delegated`, `needs_clarification`, and `not_submitted` | Must | Planned | This replaces ambiguous free-form NA handling. |
| FR-53 | Out-of-scope items are excluded from the scoring denominator and unresolved mandatory items block completion by default unless the reviewer explicitly proceeds with a partial report | Must | Planned | Scoring and completion behavior must be deterministic and auditable. |
| FR-54 | Consolidated external review reports group findings by team or owner and show missing teams, delegated items, and out-of-scope items explicitly | Must | Planned | Reports must remain trustworthy when responses are distributed across multiple teams. |
| FR-55 | Async external review templates provide built-in clarification support through guidance text and a Questions / Doubts field | Should | Planned | This addresses the offline clarification gap seen in the NeuMoney-iOS session. |
| FR-56 | Live external review can reuse the same frozen snapshot and support an `explain` interaction plus optional STT-based responses | Should | Planned | Live review is a later extension of the same external review data model. |
| FR-57 | Distributed external review links or upload surfaces can be revoked and time-limited per team | Should | Planned | External distribution must not rely on open-ended access. |
| FR-58 | Each external review distribution cycle is versioned as a `ReviewSnapshot` revision so that post-distribution checklist changes produce a new revision rather than mutating the active one | Must | Planned | Snapshot revision model prevents upload mismatch when the reviewer iterates after distribution. Each revision carries an immutable item set, team mapping, scoring rules, and a SHA-256 checksum. Previous revisions are marked `superseded` but their upload tokens remain independently revocable. |
| FR-59 | Distribution emails to external team leads are sent through the existing outbound integration infrastructure (`IntegrationConfig` / dispatcher) rather than a separate email path | Should | Planned | Avoids a second SMTP codepath; distribution attempts are automatically recorded in `IntegrationDispatch` audit records with a new `distribution` trigger type. |
| FR-60 | The upload parser for team response files is implemented as `ExcelResponseParser` within the existing `checklist_parser.py` module, sharing file-reading infrastructure with the existing `ChecklistParser` class but with independent column mapping and snapshot validation logic | Must | Planned | Keeps the working source-ingestion path intact while adding response-import capability; the two classes are independently testable. |
| FR-61 | Team-scoped Excel templates include an instructions sheet, a protected metadata sheet, data-validation dropdowns for Response State and Confidence, and visual differentiation (colour) between locked and editable columns | Must | Planned | Without dropdowns, teams enter free-text response states that break the parser. Without an instructions sheet, external teams have no context for filling the file correctly. |
| FR-62 | A short technical spike (Phase 0) must validate that the chosen Excel library (`openpyxl` or `xlsxwriter`) produces worksheet-protected, dropdown-validated workbooks that survive round-trips through Microsoft Excel, LibreOffice, and Google Sheets before Phase 4 begins | Must | Planned | Protection and dropdown behaviour differ across libraries and spreadsheet applications; discovering incompatibilities in Phase 0 costs a day rather than a sprint. |

## Frontend Requirements

This section translates the approved external async review design into reviewer-facing and respondent-facing UI requirements. It focuses on what must change in `/globals`, `/projects-ui`, and the new distribution/upload surfaces.

| ID | Requirement | Priority | Current Status | Notes |
|---|---|---|---|---|
| FE-01 | The global checklist management UI must support a single master checklist model and allow each item to capture `team_category`, guidance text, expected evidence, and applicability metadata | Must | Planned | The current `/globals` screen only edits code, area, question, expected evidence, weight, and review-mandatory flag. |
| FE-02 | The global template create flow must stop assuming only `technical` and `delivery` checklist types and instead support the master-checklist library model | Must | Planned | The current create modal still forces a `delivery` or `technical` selection. |
| FE-03 | The project checklist workspace must support project-specific tailoring before distribution: exclude/restore, inline wording edits, mandatory toggle, team-category reassignment, and project-only custom questions | Must | Planned | Existing project checklist editing covers add/edit/delete/reorder only. |
| FE-04 | The project review setup UI must allow reviewers to define review teams with team name, category, lead name, lead email, and responsibility scope | Must | Planned | This is the missing ownership layer between checklist categories and external recipients. |
| FE-05 | The project review setup UI must show per-team item counts, uncategorized items, unassigned categories, and other readiness warnings before distribution is allowed | Must | Planned | Distribution should be blocked until the reviewer resolves or explicitly accepts key setup gaps. |
| FE-06 | Reviewers must be able to create a distribution revision from the UI and see the generated snapshot ID, revision number, checksum status, and generated team exports | Must | Planned | This is the reviewer-facing control surface for `ReviewSnapshot`. |
| FE-07 | A reviewer dashboard must show the distribution lifecycle for each team: generated, sent, downloaded, submitted, parse warning, superseded, or revoked | Must | Planned | The reviewer needs one place to monitor progress after distribution. |
| FE-08 | The UI must surface row-level parse/import errors for uploaded team files and support re-upload, token reissue, and token revocation flows per team | Should | Planned | Without this, reviewers cannot recover cleanly from malformed uploads. |
| FE-09 | The consolidated external review UI must show missing teams, delegated items, out-of-scope items, unresolved mandatory items, and the explicit partial-report override path | Must | Planned | The report screen must make incompleteness visible before approval and export. |
| FE-10 | The frontend must provide revision history for external review runs, including superseded snapshots and regenerate/resend actions when the project checklist changes after distribution | Should | Planned | This keeps post-distribution edits auditable and understandable. |
| FE-11 | External team-facing download/upload pages must be token-scoped, response-only, and must not expose admin navigation, unrelated teams, or other project data | Must | Planned | The external participant experience should be minimal and least-privilege by default. |
| FE-12 | New external review screens must preserve the current ReviewBot visual language and shared shell while adding a guided multi-step workflow for setup, distribution, monitoring, and consolidation | Should | Planned | The new flow should feel like an extension of the current product, not a separate tool. |

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
| NFR-10 | Audit logging beyond LLM-specific traces | Partial | General audit logging is not yet implemented, but integration dispatch history is stored per-attempt in `integration_dispatches`. |
| NFR-13 | Outbound integration credentials are never returned in plaintext via the API | Done | `_mask_config()` masks `api_token`, `password`, `api_key`, and `token` fields in all GET responses using a four-character visible suffix. |
| NFR-14 | Integration dispatch failures are isolated from review job state | Done | Dispatcher opens its own `AsyncSessionLocal` session; exceptions are caught and logged without affecting the completed job record. |
| NFR-15 | External review uploads must validate snapshot identity and protected checklist fields before importing any responses | Planned | Prevents tampered or stale Excel files from corrupting review state. |
| NFR-16 | External review scoring rules must treat out-of-scope, delegated, unresolved, and partial-submission states deterministically | Planned | Required for score trust and report auditability. |
| NFR-17 | External review distribution and upload access must support expiry, revocation, and audit visibility per team | Planned | External participants should receive least-privilege access only. |
| NFR-18 | Evidence binding for distributed external reviews must use stable server-side identifiers rather than filename text alone | Planned | Filename-only binding is too fragile for production workflows. |
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
8. Configured integrations automatically create JIRA tickets and/or send email summaries to responsible stakeholders when the job completes.

### Important implementation caveats

- The agent-upload workflow is the most mature route for reviewing a local workspace.
- Conversational review APIs are available but are not yet a flagship end-to-end UX.
- Several v2 entities exist in the schema to support future review orchestration but are not yet wired into public workflows.
- The approved external review design assumes a single global master checklist, project-level checklist tailoring, frozen review snapshots, and team-scoped Excel distribution, but those pieces are not implemented yet.

## Near-Term Priorities

1. Run Phase 0 spike (FR-62): validate `openpyxl` / `xlsxwriter` Excel round-trip with protection and dropdowns before committing to Phase 4 implementation.
2. Implement the external async review foundation (FR-46 through FR-62): master checklist metadata, project team mapping, `ReviewSnapshot` revision model, `ExcelResponseParser`, distribution via existing SMTP integration, and team-scoped Excel export.
3. Stabilize and complete direct repository intake so the web UI path is as reliable as the agent-upload path.
4. Continue maturing action-plan and remediation workflows.
5. Add a UI panel for managing integrations (CRUD + connection test + dispatch history) - backend is complete.
6. Implement the Linear and GitHub Issues stubs in the dispatcher.
7. Ship the document-review engine.
8. Build the knowledge-quiz flow.
9. Wire up self-review, scheduling, reminders, and analytics on top of the existing v2 schema foundation.

## Integration Feature Reference

The outbound integration system (FR-30 through FR-39) delivers configurable post-review notifications and ticket creation.

### Supported integration types

| Type | Capability | Status |
|---|---|---|
| `jira` | Creates one Jira Cloud issue per ActionCard via REST API v3 | Done |
| `smtp` | Sends a single HTML+text summary email per job | Done |
| `webhook` | POSTs a JSON payload to any configured URL | Done |
| `linear` | Linear GraphQL issue creation | Stub (pending) |
| `github_issues` | GitHub Issues REST API | Stub (pending) |

### Trigger conditions

| Value | Behaviour |
|---|---|
| `red_only` | Auto-dispatches only when the completed job has at least one red finding (default) |
| `always` | Auto-dispatches for every completed job regardless of results |
| `manual` | Never auto-dispatches; can still be triggered via `POST /api/integrations/{id}/dispatch/{job_id}` |

### Config schemas

**JIRA (`jira`)**
```json
{
  "url": "https://myorg.atlassian.net",
  "email": "bot@myorg.com",
  "api_token": "ATATT...",
  "project_key": "PROJ",
  "issue_type": "Task",
  "labels": ["reviewbot"],
  "priority_map": {"red": "High", "amber": "Medium"}
}
```

**SMTP email (`smtp`)**
```json
{
  "host": "smtp.gmail.com",
  "port": 587,
  "username": "bot@gmail.com",
  "password": "app-password",
  "from_address": "ReviewBot <bot@gmail.com>",
  "use_tls": true,
  "recipients": ["team@company.com"],
  "include_project_stakeholders": true
}
```

**Webhook (`webhook`)**
```json
{
  "url": "https://hooks.example.com/reviewbot",
  "method": "POST",
  "headers": {"X-Secret": "token123"}
}
```

### API endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| `GET` | `/api/integrations/` | admin | List all integrations (secrets masked) |
| `POST` | `/api/integrations/` | admin | Create integration |
| `GET` | `/api/integrations/{id}` | admin | Get one integration |
| `PATCH` | `/api/integrations/{id}` | admin | Update integration |
| `DELETE` | `/api/integrations/{id}` | admin | Delete integration |
| `POST` | `/api/integrations/{id}/test` | admin | Test connectivity |
| `POST` | `/api/integrations/{id}/dispatch/{job_id}` | admin, manager | Manual dispatch |
| `GET` | `/api/integrations/dispatches/{job_id}` | any auth | Dispatch history for a job |

### Database migration

After pulling this change, generate and apply the Alembic migration:

```bash
alembic revision --autogenerate -m "add integration configs and dispatches"
alembic upgrade head
```
