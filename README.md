# ReviewBot

ReviewBot is a checklist-driven review platform for technical and delivery assessments. The current codebase is strongest in autonomous code review: it can scan a codebase, classify checklist items into the right review strategy, store evidence, stream progress live, preserve review history, turn findings into action plans for teams and developers, automatically create JIRA tickets or send email summaries on review completion, and detect known CVEs and dependency vulnerabilities using local scanning tools.

## Current Status

Updated against the codebase on April 23, 2026.

| Area | Status | Notes |
|---|---|---|
| Autonomous code review | Implemented | Core backend flow, WebSocket progress, history, overrides, action plans, and LLM audit are in place. |
| Project and checklist management | Implemented | Projects, global templates, project-specific checklists, clone/sync, and checklist item editing are available. |
| Admin and configuration | Implemented | JWT auth, user management, password change, LLM config management, and system settings UI are available. |
| Agent bridge for local workspaces | Implemented | `/api/v1/agent/scan` supports CLI or editor-side integrations through metadata upload plus file-content requests. |
| Outbound integrations | Implemented | Configurable JIRA ticket creation, SMTP email summaries, and generic webhooks auto-dispatch after review completion. Linear and GitHub Issues are stubbed. |
| Dependency / CVE security scanning | Implemented | `security_scan` strategy auto-detects Trivy → OSV Scanner → pip-audit → npm-audit and maps CVE severity to RAG status. No API keys required. |
| Conversational review | Partial | Backend routes, LangGraph agent scaffold, voice services, and report generator exist, but this is not the most mature end-to-end product flow yet. |
| Direct repository intake | Partial | UI/API support exists, but the agent-upload path is the more mature and reliable autonomous-review route right now. |
| Document review, quiz, self-review, scheduling, meeting integrations, analytics | Planned | Some database groundwork exists, but end-to-end product flows are not implemented yet. |

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
- **Outbound integrations**: JIRA ticket creation per action card, HTML+text email summaries to project stakeholders, and generic JSON webhooks — all configurable with per-integration trigger conditions (`always`, `red_only`, `manual`) and audit dispatch history
- **Dependency / CVE scanning**: checklist items about known vulnerabilities automatically route to the `security_scan` strategy, which runs the best available local tool and maps CRITICAL/HIGH → red, MEDIUM/LOW → amber, clean → green

### Developer-facing features

- Agent bridge for external clients such as CLI or IDE integrations
- Hybrid agent-mode orchestration with file metadata upload, server-side file requests, and staged content upload
- Multi-provider OpenAI-compatible LLM layer for OpenAI, Groq, Anthropic, Google, Azure, Qwen, and Ollama-style local models
- Strategy routing across `file_presence`, `pattern_scan`, `metadata_check`, `llm_analysis`, `security_scan`, `human_required`, and `ai_and_human`
- Security scan analyzer auto-detects Trivy, OSV Scanner, pip-audit, and npm-audit in PATH; produces normalised CVE evidence with package, version, fix version, and CVSS severity
- Integration dispatcher runs in a fully isolated async session after job completion — failures never affect review job status
- GCP deployment scripts, Docker-based local development, Alembic migrations, and seed/reset scripts
- Test coverage for routing, agent upload paths, action-plan generation, and LLM audit handling

## Architecture Snapshot

- **Backend**: FastAPI, async SQLAlchemy, PostgreSQL, Alembic
- **Frontend**: server-served vanilla HTML/CSS/JS pages under `frontend_vanilla/`
- **Autonomous review engine**: background job orchestration, per-strategy analyzers (file_presence, pattern_scan, metadata_check, llm_analysis, security_scan), and WebSocket progress streaming
- **Outbound integrations**: `IntegrationConfig` table stores per-provider credentials and trigger rules; `IntegrationDispatch` table records every dispatch attempt; dispatcher fires in an isolated session after job completion
- **Security scan**: `SecurityScanAnalyzer` shells out to the first available tool (Trivy preferred), parses structured JSON, and converts severity counts to RAG status
- **LLM layer**: database-configured provider selection with OpenAI-compatible clients
- **Reporting**: persisted results, history endpoints, Markdown/PDF report generation, and action-plan generation
- **Voice foundation**: Whisper-based STT and TTS helpers for conversational review flows

## Key Paths

```text
app/
  api/routes/
    integrations.py             Integrations CRUD, test connectivity, manual dispatch, dispatch history
    autonomous_reviews.py       Review jobs, results, overrides, action plans
    ...                         auth, projects, checklists, reports, agent, settings
  agents/
    strategy_router_agent/      LLM batch classification + deterministic keyword routing
  services/
    autonomous_review/
      orchestrator.py           Background job driver — scan → route → analyze → save → broadcast → dispatch
      analyzers/
        file_presence.py
        pattern_scan.py
        llm_analyzer.py
        metadata_check.py
        security_scan.py        CVE / dependency vulnerability scanner (Trivy, OSV, pip-audit, npm-audit)
      connectors/               Local folder + agent-upload connectors
    integrations/
      dispatcher.py             Auto-dispatch to JIRA / SMTP / Webhook after job completion
    action_plan_generator.py    Post-review action-plan generation
    checklist_service.py        Checklist lifecycle and sync logic
    report_generator.py         Markdown/PDF report generation
frontend_vanilla/               Web UI pages
docs/                           Product, design, roadmap, and operational docs
gcp_scripts/                    GCP environment setup and deploy scripts
scripts/                        Database init, seeding, resets, and utilities
tests/                          Integration and unit tests
```

## Local Development

### Prerequisites

| Requirement | Notes |
|---|---|
| Docker Desktop | Recommended — runs the app and PostgreSQL together |
| Python 3.11+ | Only needed if running without Docker |
| At least one LLM API key | Groq is free and fast; OpenAI, Anthropic, Google, Azure, Qwen also supported |
| (Optional) Trivy / pip-audit | For CVE dependency scanning — see [Security scan tools](#security-scan-tools-optional) |

---

### Option A — Docker (recommended)

This is the fastest path. Docker Compose starts the app and a PostgreSQL database together.

#### Step 1 — Copy the environment file

```bash
cp env.local .env
```

Open `.env` and set at minimum one LLM provider key:

```env
# Choose one provider and set its key
ACTIVE_LLM_PROVIDER=groq          # groq | openai | anthropic | google | qwen | azure
GROQ_API_KEY=your-groq-key-here   # free at console.groq.com

# Auto-login is enabled in env.local (APP_ENV=local)
# Leave DEV_AUTO_LOGIN_EMAIL and DEV_AUTO_LOGIN_PASSWORD as-is for local use
```

> Groq is recommended for local development — it is free, fast, and requires no billing setup.

#### Step 2 — Build and start

```bash
# First time (builds the Docker image — takes ~2–3 minutes)
docker-compose up --build

# Subsequent starts (image already built)
docker-compose up -d
```

#### Step 3 — Apply database migrations

On first run the database schema is created by Alembic automatically. If you are pulling a new version that added tables (e.g. the integrations tables), run:

```bash
docker-compose exec reviewbot-app alembic upgrade head
```

#### Step 4 — Open the app

| URL | Page |
|---|---|
| `http://localhost:8000/` | Dashboard (auto-login active) |
| `http://localhost:8000/ui` | Autonomous Review |
| `http://localhost:8000/projects-ui` | Projects & Checklists |
| `http://localhost:8000/globals` | Global Templates |
| `http://localhost:8000/history` | Review History |
| `http://localhost:8000/system-config` | System Config (LLM, settings, users) |
| `http://localhost:8000/docs` | Swagger API docs |

When `APP_ENV=local` is set (default in `env.local`) the login form auto-fills and submits on every page load — no manual login needed. Default credentials: `admin@reviewbot.com` / `Reflect@123`.

#### Day-to-day Docker commands

```bash
# Start in background
docker-compose up -d

# View live logs
docker-compose logs -f reviewbot-app

# Stop (keeps data volumes)
docker-compose stop

# Stop and wipe all data (fresh start)
docker-compose down -v

# Rebuild after requirements.txt or Dockerfile changes
docker-compose build reviewbot-app
docker-compose up -d

# Open a shell inside the running app container
docker-compose exec reviewbot-app bash

# Run a migration after changing models.py
docker-compose exec reviewbot-app alembic revision --autogenerate -m "description"
docker-compose exec reviewbot-app alembic upgrade head

# Check current migration version
docker-compose exec reviewbot-app alembic current
```

#### Database access (DBeaver / psql)

The PostgreSQL port is exposed on the host at **5435** (not 5432 — avoids conflict with a local PostgreSQL install).

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5435` |
| Database | `reviews_db` |
| User | `review_user` |
| Password | `review_password_change_me` |

---

### Option B — Local Python (no Docker)

Use this if you want faster reload cycles or are debugging without containers. You still need a PostgreSQL 15 instance running somewhere.

#### Step 1 — Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

#### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

#### Step 3 — Configure environment

```bash
cp env.local .env
```

Edit `.env` and update `DATABASE_URL` to point to your local PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://review_user:review_password_change_me@localhost:5432/reviews_db
ACTIVE_LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here
APP_ENV=local
SECRET_KEY=change-this-to-a-random-secret-key
```

#### Step 4 — Create the database (first time only)

```bash
# Connect to PostgreSQL and create the user + database
psql -U postgres -c "CREATE USER review_user WITH PASSWORD 'review_password_change_me';"
psql -U postgres -c "CREATE DATABASE reviews_db OWNER review_user;"

# Apply the schema via Alembic
alembic upgrade head
```

#### Step 5 — Run the server

```bash
uvicorn main:app --reload --port 8000
```

App is at `http://localhost:8000/`.

---

### Seeding data

To populate the database with sample projects and checklists:

```bash
# Inside Docker
docker-compose exec reviewbot-app python scripts/migrate_xlsx_to_db.py

# Local Python
python scripts/migrate_xlsx_to_db.py

# Reset only review results (keep projects/checklists)
# Inside Docker
docker-compose exec reviewbot-db psql -U review_user -d reviews_db -f /scripts/reset_data.sql
```

---

### Security scan tools (optional)

The `security_scan` review strategy auto-detects and uses the first available tool from PATH. Install any one:

```bash
# Trivy — recommended (covers all ecosystems, containers, IaC, secrets)
# Windows
winget install aquasecurity.trivy
# macOS
brew install trivy
# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# pip-audit — Python projects only
pip install pip-audit

# OSV Scanner — Google OSV database, multi-ecosystem
# https://google.github.io/osv-scanner/
```

If none are installed, checklist items routed to `security_scan` return a `na` result with installation instructions.

---

### Common issues

| Problem | Fix |
|---|---|
| Auto-login not working | Check `APP_ENV=local` is in `.env` and the container restarted after the change |
| `401 Unauthorized` on all requests | Token expired — refresh the page; auto-login will re-authenticate |
| Port `8000` already in use | `netstat -ano \| findstr :8000` on Windows, then change `APP_PORT` in `.env` |
| Port `5435` already in use | Change `DB_PORT` in `.env` |
| `MissingGreenlet` error | Add `selectinload()` before accessing a SQLAlchemy relationship in async context |
| DB data wiped after `down -v` | Re-run `python scripts/migrate_xlsx_to_db.py` to re-seed |
| `alembic upgrade head` fails | Check `DATABASE_URL` in `.env` matches running PostgreSQL; run inside Docker with `docker-compose exec` |
| LLM calls failing | Confirm the right `ACTIVE_LLM_PROVIDER` is set and the matching API key is non-empty |

## Important API Areas

- `/api/auth` - login, register, current user, password change, local dev config
- `/api/projects` - project CRUD and checklist attachment
- `/api/checklists` - checklist templates, clone, sync, item management
- `/api/autonomous-reviews` - start jobs, fetch results, overrides, action plans
- `/api/reports` - history, details, approvals, downloads, LLM audit
- `/api/v1/agent/scan` - agent upload flow for local workspace reviews
- `/api/integrations` - CRUD, test connectivity, manual dispatch, dispatch history
- `/api/llm-configs` - LLM provider configuration
- `/api/settings` - admin-managed system settings
- `/api/admin/users` - admin user management

### Integration API quick reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/integrations/` | List all integrations (secrets masked) |
| `POST` | `/api/integrations/` | Create integration |
| `PATCH` | `/api/integrations/{id}` | Update integration |
| `DELETE` | `/api/integrations/{id}` | Delete integration |
| `POST` | `/api/integrations/{id}/test` | Test connectivity without dispatching |
| `POST` | `/api/integrations/{id}/dispatch/{job_id}` | Manual dispatch for a completed job |
| `GET` | `/api/integrations/dispatches/{job_id}` | Dispatch audit history for a job |

Supported types: `jira` · `smtp` · `webhook` · `linear` (stub) · `github_issues` (stub)

Trigger conditions: `red_only` (default) · `always` · `manual`

## Documentation Map

- [docs/requirements.md](docs/requirements.md) - current functional scope and status (FR-01 to FR-45)
- [docs/design.md](docs/design.md) - current implementation design
- [docs/REVIEWBOT_DETAILED_OVERVIEW.md](docs/REVIEWBOT_DETAILED_OVERVIEW.md) - customer and developer overview for demos or video generation
- [docs/ROAD_MAP.md](docs/ROAD_MAP.md) - broader roadmap and planned phases
- [docs/AUTONOMOUS_CODE_REVIEW.md](docs/AUTONOMOUS_CODE_REVIEW.md) - deeper autonomous-review background
- [DEVELOPER_NOTES.md](DEVELOPER_NOTES.md) - local development notes

## Known Gaps

- Direct repository intake exists in the product surface but still needs stabilization compared with the agent-upload workflow.
- Conversational review is present as backend foundation, not as the primary polished product flow.
- No frontend UI panel for managing integrations yet — the backend API at `/api/integrations` is complete but there is no admin page for it in the web UI.
- Linear and GitHub Issues integration handlers are stubbed in the dispatcher and not yet implemented.
- Several v2 tables for self-review, reminders, meeting blocking, and trend analytics are modeled in the database but are not yet wired into APIs and UI.
- Document review, knowledge quiz, meeting participation, and advanced analytics are still roadmap features.
