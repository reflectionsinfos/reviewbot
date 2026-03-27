# ReviewBot v2.0 — AI Tech & Delivery Review Agent

An AI-powered platform for conducting structured technical and delivery project reviews. Supports both **conversational reviews** (human Q&A via API) and **autonomous code reviews** (AI crawls your codebase against a checklist without human input).

---

## Features

- **Autonomous Code Review** — Point ReviewBot at a local folder; it scans files and evaluates each checklist item automatically with real-time WebSocket progress
- **Conversational Review** — LangGraph-based agent asks checklist questions one by one; supports text and voice responses
- **Multi-LLM Support** — OpenAI, Anthropic, Google, Groq, Qwen, Azure OpenAI (switch via `ACTIVE_LLM_PROVIDER`)
- **RAG Compliance Scoring** — Automatic Red/Amber/Green status per item with compliance percentage
- **Report Generation** — Markdown and PDF reports with recommendations and human approval workflow
- **Voice Interaction** — OpenAI Whisper (STT) + TTS support
- **Live UI** — Single-page frontend at `/ui` for autonomous reviews

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn (async) |
| AI/LLM | LangChain + LangGraph + configurable LLM provider |
| Database | PostgreSQL 15 (Docker) / SQLite (local dev) |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Vector Store | ChromaDB |
| Voice | OpenAI Whisper (STT) + TTS |
| Auth | JWT (python-jose) + bcrypt |
| Reports | ReportLab (PDF) + Markdown |

---

## Quick Start (Docker)

### 1. Configure environment

```bash
# Edit .env — the file already exists, just verify/update API keys
notepad .env
```

Key variables:
```env
# At least one LLM key required
GROQ_API_KEY=your-key-here
ACTIVE_LLM_PROVIDER=groq          # openai | anthropic | google | groq | qwen | azure

# Security (change in production)
SECRET_KEY=change-this-to-a-random-secret-key
```

### 2. Start

```bash
docker-compose up --build
```

### 3. Access

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Autonomous Review UI | http://localhost:8000/ui |
| Health Check | http://localhost:8000/health |

**DBeaver connection:** host=`localhost`, port=`5435`, db=`reviews_db`, user=`review_user`, password=`review_password_change_me`

---

## Default Credentials

There is no built-in auto-seeded admin user. Use one of these approaches:

### Option A — Register via API
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@reviewbot.com", "password": "Password123!", "full_name": "Admin User", "role": "admin"}'
```

### Option B — Run the seed script (requires psycopg2, runs against host port 5435)
```bash
python scripts/db_test.py
```
This creates three users, all with password **`Password123!`**:

| Email | Role |
|-------|------|
| admin@reviewbot.com | admin |
| manager@reviewbot.com | manager |
| reviewer@reviewbot.com | reviewer |

### Option C — Run the full migration (imports xlsx checklists + seed data)
```bash
python scripts/migrate_xlsx_to_db.py
```

---

## Docker Commands

```bash
# Start
docker-compose up --build

# Start in background
docker-compose up -d --build

# Stop (KEEPS all data)
docker-compose down

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Shell into app container
docker-compose exec app bash

# Run migrations manually
docker-compose exec app alembic upgrade head

# DANGER — Stop AND delete all data (volumes wiped)
docker-compose down -v
```

> **WARNING**: `docker-compose down -v` deletes the `postgres_data` volume and all database content. Use `docker-compose down` to stop without losing data.

---

## Database Config

Inside Docker containers, the app connects to PostgreSQL at `db:5432` (internal Docker network port).
The host-side mapping is `5435:5432` — port `5435` is only for external tools like DBeaver.

```
# Correct DATABASE_URL (used inside the container)
postgresql+asyncpg://review_user:review_password_change_me@db:5432/reviews_db

# For DBeaver / external tools connecting from your Windows host
host=localhost  port=5435
```

---

## API Overview

### Authentication
```
POST /api/auth/register    Register user
POST /api/auth/login       Get JWT token
```

### Projects & Checklists
```
GET  /api/projects/                           List projects
POST /api/projects/                           Create project
POST /api/projects/{id}/upload-checklist      Upload Excel checklist (.xlsx)
GET  /api/checklists/{id}                     Get checklist with items
POST /api/checklists/{id}/optimize            AI checklist recommendations
```

### Conversational Reviews
```
POST /api/reviews/                  Create review session
POST /api/reviews/{id}/start        Start AI agent
POST /api/reviews/{id}/respond      Submit text answer
POST /api/reviews/{id}/voice-response  Submit audio (WAV)
POST /api/reviews/{id}/complete     Complete & generate report
```

### Autonomous Reviews
```
POST   /api/autonomous-reviews/           Start autonomous review job
GET    /api/autonomous-reviews/           List jobs (optional ?project_id=N)
GET    /api/autonomous-reviews/{job_id}   Job status + per-item results
GET    /api/autonomous-reviews/{job_id}/report  Final structured report
DELETE /api/autonomous-reviews/{job_id}   Cancel / delete job
WS     /ws/autonomous-reviews/{job_id}    Real-time progress stream
```

### Reports
```
GET  /api/reports/                          List reports
POST /api/reports/{id}/approve              Approve report
POST /api/reports/{id}/reject               Reject with comments
GET  /api/reports/{id}/download/{format}    Download (markdown or pdf)
GET  /api/reports/pending/approvals         Pending approvals
```

---

## Autonomous Review

The autonomous review feature scans a local folder against a checklist without human Q&A.

### How it works

1. POST to `/api/autonomous-reviews/` with `project_id`, `checklist_id`, and `source_path` (path on the server machine)
2. ReviewBot scans up to 2000 files (skipping `node_modules`, `.git`, `venv`, etc.)
3. Each checklist item is routed to an analyzer strategy:
   - **file_presence** — checks if expected files/dirs exist (architecture docs, CI config, etc.)
   - **pattern_scan** — regex scans for code patterns (secrets, HTTPS, test counts, error handling)
   - **llm_analysis** — top 3 relevant files sent to LLM for evaluation
   - **metadata_check** — dependency scanning config, coverage thresholds
   - **human_required** — financial/people items flagged for manual evidence
4. Results stream in real-time via WebSocket
5. Final report at `GET /api/autonomous-reviews/{job_id}/report`

### Strategy distribution (152 checklist items)
| Strategy | % of items | Example items |
|----------|-----------|---------------|
| human_required | 43% | Budget, CSAT, team morale, governance |
| llm_analysis | 34% | Code quality, architecture, documentation |
| file_presence | 13% | CI/CD config, README, HLD/LLD docs |
| pattern_scan | 7% | Secrets detection, test count, HTTPS |
| metadata_check | 3% | Dependency scanning, coverage config |

### Quick start via UI
1. Go to http://localhost:8000/ui
2. Login with your credentials
3. Select project, checklist, enter source path
4. Click **Start Autonomous Review**
5. Watch results stream in real time

---

## Postman Collection

Import both files from `postman_collection/`:
- `ReviewBot_API.postman_collection.json` — 25 requests across all endpoints
- `ReviewBot_Local.postman_environment.json` — environment with `base_url=http://localhost:8000`

The collection auto-saves `token`, `project_id`, `review_id`, and `job_id` from responses.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│  API Routes                                                  │
│  ├── /api/auth              Authentication & Users           │
│  ├── /api/projects          Project CRUD + xlsx upload       │
│  ├── /api/checklists        Checklist management + AI opt    │
│  ├── /api/reviews           Conversational review sessions   │
│  ├── /api/reports           Reports + approval workflow      │
│  └── /api/autonomous-reviews  Autonomous code review jobs    │
│  WS /ws/autonomous-reviews/{job_id}  Real-time progress      │
├─────────────────────────────────────────────────────────────┤
│  Services                                                    │
│  ├── ReviewAgent (LangGraph)    Conversational AI workflow   │
│  ├── AutonomousReview           Folder scan + analysis       │
│  │   ├── LocalFolderConnector   File indexing                │
│  │   ├── StrategyRouter         Routes items to analyzers    │
│  │   ├── FilePresenceAnalyzer                                │
│  │   ├── PatternScanAnalyzer                                 │
│  │   ├── LLMAnalyzer                                         │
│  │   └── MetadataCheckAnalyzer                               │
│  ├── ChecklistParser            Excel (.xlsx) parsing        │
│  ├── ReportGenerator            Markdown + PDF               │
│  └── VoiceInterface             STT/TTS                      │
├─────────────────────────────────────────────────────────────┤
│  Database (PostgreSQL 15)                                    │
│  ├── Users, Projects, Checklists, ChecklistItems             │
│  ├── Reviews, ReviewResponses                                │
│  ├── Reports, ReportApprovals                                │
│  └── AutonomousReviewJobs, AutonomousReviewResults           │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
app/
├── agents/review_agent/    # LangGraph conversational review workflow
├── api/routes/             # FastAPI route handlers
│   ├── auth.py
│   ├── projects.py
│   ├── checklists.py
│   ├── reviews.py
│   ├── reports.py
│   └── autonomous_reviews.py
├── core/config.py          # Pydantic settings (all env vars)
├── db/session.py           # Async engine + init_db
├── models.py               # SQLAlchemy models
└── services/
    ├── autonomous_review/
    │   ├── connectors/local_folder.py
    │   ├── analyzers/
    │   ├── strategy_router.py
    │   ├── orchestrator.py
    │   └── progress.py
    ├── checklist_parser.py
    ├── report_generator.py
    └── voice_interface.py
main.py                     # App entry point
static/index.html           # Autonomous review frontend UI
scripts/
├── init-db-simple.sql      # PostgreSQL init (creates review_user)
├── db_test.py              # Seed data script (users + sample project)
└── migrate_xlsx_to_db.py   # Full migration from xlsx checklists
```

---

## Environment Variables

All defined in `app/core/config.py`. Full list in `.env`:

| Variable | Description | Required |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `ACTIVE_LLM_PROVIDER` | `openai` \| `anthropic` \| `google` \| `groq` \| `qwen` \| `azure` | Yes |
| `OPENAI_API_KEY` | OpenAI key | If provider=openai |
| `GROQ_API_KEY` | Groq key | If provider=groq |
| `ANTHROPIC_API_KEY` | Anthropic key | If provider=anthropic |
| `VOICE_ENABLED` | Enable STT/TTS | No (default true) |
| `REQUIRE_HUMAN_APPROVAL` | Require approval before reports sent | No (default true) |

---

## Database Migrations

```bash
# Generate migration after model changes
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec app alembic upgrade head

# Check current version
docker-compose exec app alembic current
```

---

## Troubleshooting

**`password authentication failed for user "review_user"`**
The `postgres_data` volume may have been initialized before the init SQL ran, or the password was stored with the wrong encryption method. Fix:
```bash
docker-compose down -v   # WARNING: deletes all data
docker-compose up --build
```
Then re-seed data via `python scripts/db_test.py` or register via API.

**`User does not have a valid SCRAM secret`**
PostgreSQL 15 requires `scram-sha-256`. The `init-db-simple.sql` no longer sets `password_encryption = 'md5'`. If you hit this, the volume has stale user data — run `docker-compose down -v` to reset.

**Port already in use**
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :5435
# Change APP_PORT or DB_PORT in .env
```

**`MissingGreenlet` errors in SQLAlchemy**
All relationship access must use `selectinload()`. Never access `.relationship` attributes without eager loading in async context.

---

## Local Python Dev (without Docker)

```bash
pip install -r requirements.txt

# SQLite for local dev — no PostgreSQL needed
# In .env:
DATABASE_URL=sqlite+aiosqlite:///./reviews.db

uvicorn main:app --reload --port 8000
```

---

## License

Proprietary. All rights reserved.
