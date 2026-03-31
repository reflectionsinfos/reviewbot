# ReviewBot v2.0 — AI Tech & Delivery Review Agent

AI-powered platform for structured technical and delivery project reviews. Supports **autonomous code reviews** (AI scans your codebase against a checklist) and **conversational reviews** (LangGraph agent asks checklist questions one by one). Available via browser, VS Code extension, and CLI agent.

---

## Production (GCP)

| | |
|---|---|
| **UI** | https://reviewbot-web-128263129038.us-central1.run.app/ui |
| **API Docs** | https://reviewbot-web-128263129038.us-central1.run.app/docs |
| **Health** | https://reviewbot-web-128263129038.us-central1.run.app/health |
| **Default login** | `admin@reviewbot.com` — contact your admin for password |

---

## Features

- **Autonomous Code Review** — scan a Git repo or local directory against a checklist; streams results live via WebSocket
- **Multi-LLM Support** — OpenAI, Anthropic, Google, Groq, Qwen, Azure OpenAI (switch via `ACTIVE_LLM_PROVIDER`)
- **RAG Compliance Scoring** — Red / Amber / Green per checklist item with overall compliance %
- **Report Generation** — Markdown and PDF reports with human approval workflow
- **VS Code Extension** — review your open workspace from the editor sidebar with inline gutter decorations
- **CLI Agent** — run reviews from the terminal or CI/CD pipelines
- **Admin User Management** — add users, reset passwords, activate/deactivate, delete
- **Change Password** — users can change their own password from the header dropdown
- **Voice Interaction** — OpenAI Whisper (STT) + TTS (conversational reviews)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn (async) |
| AI/LLM | LangChain + LangGraph + configurable LLM provider |
| Database | PostgreSQL 15 (Cloud SQL / Docker) |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Vector Store | ChromaDB |
| Voice | OpenAI Whisper (STT) + TTS |
| Auth | JWT (python-jose) + bcrypt |
| Reports | ReportLab (PDF) + Markdown |

---

## Running Locally

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker + Docker Compose (Linux)
- At least one LLM API key (Groq is free: https://console.groq.com)

### Step 1 — Configure Environment

Edit `env.local` (or `.env`):

```env
# LLM — at least one required
GROQ_API_KEY=your-groq-key
ACTIVE_LLM_PROVIDER=groq   # openai | anthropic | google | groq | qwen | azure

# Security
SECRET_KEY=change-this-to-a-random-secret-key

# Database — correct for Docker, do not change host/port
DATABASE_URL="postgresql+asyncpg://review_user:review_password_change_me@db:5432/reviews_db"
```

### Step 2 — Start Docker

```bash
cd c:\projects\reviewbot
docker-compose up --build        # first time or after code changes
docker-compose up -d             # subsequent starts
```

Wait for:
```
ai-review-db     | database system is ready to accept connections
ai-review-agent  | Application startup complete
```

### Step 3 — Seed the Database

```bash
# Full seed — users, projects, global checklists
python scripts/migrate_xlsx_to_db.py

# Or via Docker SQL
docker exec ai-review-db psql -U review_user -d reviews_db -f scripts/seed_data.sql
```

Creates these users (default password: `Admin@123` — change after first login):

| Email | Role |
|-------|------|
| `admin@reviewbot.com` | admin |
| `reviewer@reviewbot.com` | reviewer |

### Step 4 — Verify

```bash
curl http://localhost:8000/health
# {"status":"healthy","database":"connected",...}
```

| Service | URL |
|---------|-----|
| UI | http://localhost:8000/ui |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

---

## Environment Files

| File | Purpose |
|------|---------|
| `env.local` | Local development (Docker) |
| `env.non-prod.gcp` | GCP Cloud Run deployment |

To deploy to GCP: fill `env.non-prod.gcp` and run `.\gcp_scripts\05_deploy_app.ps1`.

---

## API Reference

### Authentication & User Management

```
POST   /api/auth/register                 Register new user
POST   /api/auth/login                    Get JWT token
GET    /api/auth/me                       Current user info
POST   /api/auth/change-password          Change own password (requires current password)

# Admin only (role=admin)
GET    /api/admin/users                   List all users
POST   /api/admin/users                   Create user — returns generated default password
POST   /api/admin/users/{id}/reset-password   Reset password — returns new generated password
PATCH  /api/admin/users/{id}              Update role or active status
DELETE /api/admin/users/{id}              Delete user (cannot delete own account)
```

### Projects & Checklists

```
GET    /api/projects/                     List projects
POST   /api/projects/                     Create project
PUT    /api/projects/{id}                 Update project
DELETE /api/projects/{id}                 Delete project
POST   /api/projects/{id}/upload-checklist    Upload Excel checklist (.xlsx)
GET    /api/projects/{id}/checklists      List checklists for project
GET    /api/checklists/{id}               Get checklist with items
POST   /api/checklists/{id}/optimize      AI checklist recommendations
```

### Autonomous Reviews

```
POST   /api/autonomous-reviews/           Start autonomous review job
GET    /api/autonomous-reviews/           List jobs (?project_id=N to filter)
GET    /api/autonomous-reviews/{job_id}   Job status + per-item results
GET    /api/autonomous-reviews/{job_id}/report   Final structured report
DELETE /api/autonomous-reviews/{job_id}   Cancel / delete job
WS     /ws/autonomous-reviews/{job_id}    Real-time progress stream
```

### Agent Bridge (CLI + VS Code Extension)

```
POST   /api/v1/agent/scan/upload                        Upload scan metadata
POST   /api/v1/agent/scan/{job_id}/file-content         Upload file contents
POST   /api/v1/agent/scan/{job_id}/start                Start server-side analysis
GET    /api/v1/agent/scan/{job_id}                      Job status (poll)
GET    /api/v1/agent/scan/{job_id}/results              Final results
```

### Conversational Reviews

```
GET    /api/reviews/                      List reviews
POST   /api/reviews/                      Create review session
POST   /api/reviews/{id}/start            Start AI agent
POST   /api/reviews/{id}/respond          Submit text answer
POST   /api/reviews/{id}/voice-response   Submit audio (WAV)
POST   /api/reviews/{id}/complete         Complete & generate report
```

### Reports

```
GET    /api/reports/                          List reports
GET    /api/reports/{id}                      Get report details
POST   /api/reports/{id}/approve              Approve report
POST   /api/reports/{id}/reject               Reject with comments
GET    /api/reports/{id}/download/{format}    Download (markdown or pdf)
GET    /api/reports/pending/approvals         Pending approvals list
```

---

## Admin Features

### Manage Users

Accessible from the header dropdown (admin role only):

- **Add User** — enter name, email, role → system generates a secure default password to share privately with the user
- **Reset Password** — generates a new password for any user (shown once, copy before closing)
- **Activate / Deactivate** — toggle user access without deleting
- **Delete** — permanently remove a user (cannot delete your own account)

Generated passwords: 12 characters, guaranteed uppercase + lowercase + digit + special character (`!@#$^`). URL-safe — no `%` character.

### Change Password

Any logged-in user can change their own password from the header dropdown → **Change Password**:
- Must enter current password to verify identity
- New password minimum 8 characters
- Live strength meter (Weak → Very Strong)
- Show/hide toggle on all fields

---

## Client Tools

### VS Code Extension

Download from the AI Review page → **VS CODE EXTENSION** button. Reviews your local workspace directly from the editor sidebar with inline gutter decorations. See [`reviewbot-vscode/README.md`](../reviewbot-vscode/README.md).

### CLI Agent

```bash
pip install reviewbot-agent

reviewbot login --server https://reviewbot-web-128263129038.us-central1.run.app

reviewbot review \
  --project-id <id> \
  --checklist-id <id> \
  --source-path ./my-project \
  --output ./report.md
```

The AI Review page → **CLI AGENT** tab pre-fills the project and checklist IDs from the dropdowns. See [`reviewbot-agent/README.md`](../reviewbot-agent/README.md).

---

## Project Structure

```
app/
├── agents/review_agent/       # LangGraph conversational review workflow
├── api/routes/
│   ├── auth.py                # JWT auth, register, login, change-password
│   ├── users.py               # Admin user management (add, reset, delete, patch)
│   ├── projects.py            # Project CRUD + checklist upload
│   ├── checklists.py          # Checklist management + AI optimization
│   ├── reviews.py             # Conversational review sessions
│   ├── reports.py             # Report management + approval workflow
│   ├── autonomous_reviews.py  # Autonomous review jobs + WebSocket
│   └── agent.py               # CLI / VS Code extension bridge
├── core/config.py             # Pydantic settings (all env vars)
├── db/session.py              # Async engine + init_db
├── models.py                  # SQLAlchemy models
└── services/
    ├── autonomous_review/
    │   ├── connectors/        # File indexers (local folder, agent upload)
    │   ├── analyzers/         # file_presence, pattern_scan, llm_analysis, metadata_check
    │   ├── strategy_router.py
    │   ├── orchestrator.py
    │   └── progress.py        # WebSocket broadcast manager
    ├── checklist_parser.py
    ├── report_generator.py
    └── voice_interface.py
main.py
frontend_vanilla/              # Vanilla JS single-page frontend
├── components/
│   ├── header.html            # Shared header — user dropdown, change password modal, manage users modal
│   └── header_loader.js       # Header JS — auth, user management, change/reset password logic
├── index.html                 # AI Review page (autonomous reviews)
├── home.html                  # Dashboard
├── project.html               # Projects & checklists management
├── history.html               # Review history
├── globals.html               # Global templates
└── system_config.html         # System configuration
```

---

## Docker Commands

```bash
docker-compose up --build          # Start with rebuild
docker-compose up -d               # Start in background
docker-compose down                # Stop (keeps data)
docker-compose down -v             # Stop + wipe all data (WARNING: irreversible)
docker-compose restart app         # Restart app only after code change
docker-compose logs -f app         # Live app logs
docker-compose exec app bash       # Shell into app container
docker-compose exec db psql -U review_user -d reviews_db   # Database shell
docker-compose exec app alembic upgrade head               # Run migrations
```

---

## Database

| Context | Host | Port | DB | User |
|---------|------|------|----|------|
| Inside Docker (app container) | `db` | `5432` | `reviews_db` | `review_user` |
| DBeaver / external from Windows host | `localhost` | `5435` | `reviews_db` | `review_user` |

### Migrations

```bash
docker-compose exec app alembic revision --autogenerate -m "description"
docker-compose exec app alembic upgrade head
docker-compose exec app alembic current
docker-compose exec app alembic downgrade -1
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `ACTIVE_LLM_PROVIDER` | `openai` \| `anthropic` \| `google` \| `groq` \| `qwen` \| `azure` | Yes |
| `OPENAI_API_KEY` | OpenAI key | If provider=openai |
| `GROQ_API_KEY` | Groq key (free tier available) | If provider=groq |
| `ANTHROPIC_API_KEY` | Anthropic key | If provider=anthropic |
| `GOOGLE_API_KEY` | Google Gemini key | If provider=google |
| `VOICE_ENABLED` | Enable STT/TTS | No (default: true) |
| `REQUIRE_HUMAN_APPROVAL` | Reports require approval before delivery | No (default: true) |

---

## Autonomous Review Strategy Distribution

Each checklist item is routed to an analysis strategy. For the Standard Technical Checklist (103 items):

| Strategy | Approx. % | Examples |
|----------|-----------|---------|
| `human_required` | 43% | Budget, CSAT, governance, team morale |
| `llm_analysis` | 34% | Code quality, architecture review |
| `file_presence` | 13% | CI/CD config, README, HLD/LLD docs |
| `pattern_scan` | 7% | Secrets detection, HTTPS, test counts |
| `metadata_check` | 3% | Dependabot, coverage thresholds |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `password authentication failed for user "review_user"` | `docker-compose down -v && docker-compose up --build` (wipes data) |
| `User does not have a valid SCRAM secret` | Old volume with MD5 auth — `docker-compose down -v` to reset |
| Port already in use | `netstat -ano \| findstr :8000` — change `APP_PORT` in `.env` |
| `MissingGreenlet` / lazy loading crash | Add `selectinload()` before accessing SQLAlchemy relationships in async context |
| `(projects \|\| []).forEach is not a function` | Hard-refresh the browser (`Ctrl+Shift+R`) |

---

## Postman Collection

Import from `postman_collection/`:
- `ReviewBot_API.postman_collection.json` — all endpoints
- `ReviewBot_Local.postman_environment.json` — `base_url=http://localhost:8000`

The collection auto-saves `token`, `project_id`, `review_id`, and `job_id` from responses.

---

## License

Proprietary. All rights reserved. Copyright (c) 2024 Reflections Info Systems.
