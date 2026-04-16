# ReviewBot

ReviewBot is a checklist-driven review platform for technical and delivery assessments. The current codebase is strongest in autonomous code review: it can scan a codebase, classify checklist items into the right review strategy, store evidence, stream progress live, preserve review history, and turn findings into action plans for teams and developers.

## Current Status

Updated against the codebase on April 17, 2026.

| Area | Status | Notes |
|---|---|---|
| Autonomous code review | Implemented | Core backend flow, WebSocket progress, history, overrides, action plans, and LLM audit are in place. |
| Project and checklist management | Implemented | Projects, global templates, project-specific checklists, clone/sync, and checklist item editing are available. |
| Admin and configuration | Implemented | JWT auth, user management, password change, LLM config management, and system settings UI are available. |
| Agent bridge for local workspaces | Implemented | `/api/v1/agent/scan` supports CLI or editor-side integrations through metadata upload plus file-content requests. |
| Conversational review | Partial | Backend routes, LangGraph agent scaffold, voice services, and report generator exist, but this is not the most mature end-to-end product flow yet. |
| Direct repository intake | Partial | UI/API support exists, but the agent-upload path is the more mature and reliable autonomous-review route right now. |
| Document review, QUIZ, self-review, scheduling, meeting integrations, analytics | Planned | Some database groundwork exists, but end-to-end product flows are not implemented yet. |

## What Works Today

### Product features

- Dashboard, AI Review, History, Projects, Global Templates, Documentation, and System Config pages in the vanilla web UI
- JWT-based login, local dev auto-login, password change, and admin user management
- Project CRUD with domain, description, tech stack, and stakeholder metadata
- Global checklist upload from Excel, project checklist cloning, sync-from-global, item CRUD, reorder, and delete protections
- Autonomous review jobs with live progress, per-item evidence, compliance scoring, and structured final reports
- Human override workflow for autonomous findings with audit history
- Action Plan generation with developer-ready prompts in generic, Cursor, and Claude Code formats
- Optional AI enhancement of action-plan prompts with cached prompt storage
- LLM configuration management, connectivity testing, activation, and LLM audit visibility controls
- Report history with detailed result breakdown, source-path updates, regeneration, and LLM trace view

### Developer-facing features

- Agent bridge for external clients such as CLI or IDE integrations
- Hybrid agent-mode orchestration with file metadata upload, server-side file requests, and staged content upload
- Multi-provider OpenAI-compatible LLM layer for OpenAI, Groq, Anthropic, Google, Azure, Qwen, and Ollama-style local models
- Strategy routing across `file_presence`, `pattern_scan`, `metadata_check`, `llm_analysis`, `human_required`, and `ai_and_human`
- GCP deployment scripts, Docker-based local development, Alembic migrations, and seed/reset scripts
- Test coverage for routing, agent upload paths, action-plan generation, and LLM audit handling

## Architecture Snapshot

- Backend: FastAPI, async SQLAlchemy, PostgreSQL, Alembic
- Frontend: server-served vanilla HTML/CSS/JS pages under `frontend_vanilla/`
- Autonomous review engine: background job orchestration plus analyzers and WebSocket progress streaming
- LLM layer: database-configured provider selection with OpenAI-compatible clients
- Reporting: persisted results, history endpoints, Markdown/PDF report generation, and action-plan generation
- Voice foundation: Whisper-based STT and TTS helpers for conversational review flows

## Key Paths

```text
app/
  api/routes/                 API surface
  agents/                     Review agent and strategy routing
  services/
    autonomous_review/        Autonomous review orchestration, analyzers, connectors
    action_plan_generator.py  Post-review action-plan generation
    checklist_service.py      Checklist lifecycle and sync logic
    report_generator.py       Markdown/PDF report generation
frontend_vanilla/             Web UI pages
docs/                         Product, design, roadmap, and operational docs
gcp_scripts/                  GCP environment setup and deploy scripts
scripts/                      Database init, seeding, resets, and utilities
tests/                        Integration and unit tests
```

## Local Development

### Prerequisites

- Python environment or Docker
- PostgreSQL 15
- At least one configured LLM provider or a local Ollama-style endpoint

### Common local workflow

```powershell
docker-compose up --build
```

Then open:

- App: `http://localhost:8000/`
- Autonomous review UI: `http://localhost:8000/ui`
- Projects UI: `http://localhost:8000/projects-ui`
- Global templates UI: `http://localhost:8000/globals`
- History UI: `http://localhost:8000/history`
- System config UI: `http://localhost:8000/system-config`
- API docs: `http://localhost:8000/docs`

Useful files:

- `env.local` for local development values
- `env.non-prod.gcp` for Cloud Run deployment values
- `scripts/reset_data.sql` to reset seeded review data
- `gcp_scripts/05_deploy_app.ps1` to deploy the app to GCP

## Important API Areas

- `/api/auth` - login, register, current user, password change, local dev config
- `/api/projects` - project CRUD and checklist attachment
- `/api/checklists` - checklist templates, clone, sync, item management
- `/api/autonomous-reviews` - start jobs, fetch results, overrides, action plans
- `/api/reports` - history, details, approvals, downloads, LLM audit
- `/api/v1/agent/scan` - agent upload flow for local workspace reviews
- `/api/llm-configs` - LLM provider configuration
- `/api/settings` - admin-managed system settings
- `/api/admin/users` - admin user management

## Documentation Map

- [docs/requirements.md](docs/requirements.md) - current functional scope and status
- [docs/design.md](docs/design.md) - current implementation design
- [docs/REVIEWBOT_DETAILED_OVERVIEW.md](docs/REVIEWBOT_DETAILED_OVERVIEW.md) - customer and developer overview for demos or video generation
- [docs/ROAD_MAP.md](docs/ROAD_MAP.md) - broader roadmap and planned phases
- [docs/AUTONOMOUS_CODE_REVIEW.md](docs/AUTONOMOUS_CODE_REVIEW.md) - deeper autonomous-review background
- [DEVELOPER_NOTES.md](DEVELOPER_NOTES.md) - local development notes

## Known Gaps

- Direct repository intake exists in the product surface but still needs stabilization compared with the agent-upload workflow.
- Conversational review is present as backend foundation, not as the primary polished product flow.
- Several v2 tables for self-review, reminders, meeting blocking, and trend analytics are modeled in the database but are not yet wired into APIs and UI.
- Document review, knowledge quiz, meeting participation, and advanced analytics are still roadmap features.
