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

## Deploy & Run

### Prerequisites

- **Docker Desktop** (Windows/Mac) or Docker + Docker Compose (Linux)
- At least one LLM API key (Groq is free and recommended for getting started)

---

### Step 1 — Configure Environment

Edit `.env` (already exists in the project root):

```bash
notepad .env        # Windows
# or
code .env           # VS Code
```

Minimum required settings:
```env
# LLM — at least one required (Groq is free: https://console.groq.com)
GROQ_API_KEY=your-groq-key-here
ACTIVE_LLM_PROVIDER=groq        # openai | anthropic | google | groq | qwen | azure

# Security — change this before going to production
SECRET_KEY=change-this-to-a-random-secret-key

# Database — already correct for Docker, do not change the host/port
DATABASE_URL="postgresql+asyncpg://review_user:review_password_change_me@db:5432/reviews_db"
```

> **Important**: Inside Docker, the database host is `db:5432` (internal network).
> The port `5435` is only for external tools like DBeaver connecting from your Windows host.

---

### Step 2 — Start Docker

```bash
cd c:\projects\reviewbot

# First time or after code changes
docker-compose up --build

# Subsequent starts (no code changes)
docker-compose up -d
```

Wait for both containers to be healthy:
```
ai-review-db     | database system is ready to accept connections
ai-review-agent  | Application startup complete
```

---

### Step 3 — Seed the Database

The database starts empty. Run one of these to populate it:

#### Option A — Full seed from xlsx checklists (recommended)
Reads `data/projects/` and `data/templates/` xlsx files. Creates users, projects, checklists, reviews, and reports.

```bash
# Requires: pip install psycopg2-binary pandas openpyxl
python scripts/migrate_xlsx_to_db.py
```

Creates these users (password: **`Admin@123`**):

| Email | Role |
|-------|------|
| admin@reviewbot.com | admin |
| reviewer@reviewbot.com | reviewer |

#### Option B — Run a pre-generated SQL seed file

SQL seed files can be run without Python. They connect directly to PostgreSQL via Docker.

```bash
# Full seed (all projects + global checklists + users)
docker exec ai-review-db psql -U review_user -d reviews_db -c "$(cat scripts/seed_data.sql)"

# Hatch Pay project only (copies NeUMoney delivery + technical data)
docker exec ai-review-db psql -U review_user -d reviews_db -c "$(cat scripts/seed_hatchpay.sql)"
```

> **Note**: `seed_hatchpay.sql` is idempotent — it checks if Hatch Pay exists and skips if so.
> `seed_data.sql` uses `ON CONFLICT DO NOTHING` / `ON CONFLICT DO UPDATE` so it is also safe to re-run.

#### Option C — Run via DBeaver

1. Open DBeaver → connect to `localhost:5435`, db=`reviews_db`, user=`review_user`
2. Open the SQL file: `scripts/seed_data.sql` or `scripts/seed_hatchpay.sql`
3. Execute (F5 or Run Script button)

#### Option D — Register manually via Swagger

1. Go to http://localhost:8000/docs
2. Find `POST /api/auth/register`
3. Click "Try it out" and submit:
```json
{
  "email": "admin@reviewbot.com",
  "password": "Admin@123",
  "full_name": "Admin User",
  "role": "admin"
}
```

---

### Step 4 — Verify

```bash
# Health check
curl http://localhost:8000/health

# Expected
{"status":"healthy","database":"connected","voice_enabled":true,...}
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger / API Docs | http://localhost:8000/docs |
| Autonomous Review UI | http://localhost:8000/ui |
| Health Check | http://localhost:8000/health |

---

## Seed SQL Files Reference

| File | Purpose | When to use |
|------|---------|-------------|
| `scripts/seed_data.sql` | Full dataset — users, global checklists, AAA PDH + NeUMoney projects | After a fresh `docker-compose down -v` reset |
| `scripts/seed_hatchpay.sql` | Hatch Pay project only — copies NeUMoney delivery + technical checklist | Add Hatch Pay to an existing database |
| `scripts/migrate_xlsx_to_db.py` | Python script that reads xlsx files directly — generates the same data as seed_data.sql | When xlsx source files have changed |
| `scripts/generate_seed.py` | Re-generates `seed_data.sql` from current xlsx files | Run this if xlsx files are updated, then commit the new seed_data.sql |

### Regenerating seed_data.sql after xlsx changes

```bash
python scripts/generate_seed.py
# Output: scripts/seed_data.sql (re-generated)
git add scripts/seed_data.sql && git commit -m "chore: regenerate seed data"
```

---

## Autonomous Code Review

The autonomous review feature scans a source folder against a checklist — no human Q&A needed.

### How it works

1. User selects project + checklist + source path in the UI (or via API)
2. ReviewBot scans up to 2,000 files (skipping `node_modules`, `.git`, `target`, `venv`, etc.)
3. Each checklist item is routed to an analysis strategy:
   - **file_presence** — checks if expected files/dirs exist (architecture docs, CI config, README, etc.)
   - **pattern_scan** — regex scans for code patterns (secrets, HTTPS, test counts, error handling)
   - **llm_analysis** — top 3 relevant files sent to LLM for contextual evaluation
   - **metadata_check** — inspects dependency scanning config, coverage thresholds
   - **human_required** — financial/people/governance items flagged for manual evidence
4. Results stream live via WebSocket
5. Final report available at `GET /api/autonomous-reviews/{job_id}/report`

### Strategy distribution (152 checklist items)

| Strategy | Items | Examples |
|----------|-------|---------|
| human_required | 43% | Budget, CSAT, team morale, governance, escalations |
| llm_analysis | 34% | Code quality, architecture, documentation completeness |
| file_presence | 13% | CI/CD config, README, HLD/LLD docs, Dockerfile |
| pattern_scan | 7% | Secrets detection, test count, HTTPS usage |
| metadata_check | 3% | Dependabot/Snyk config, coverage thresholds |

---

## Microservices & Large Codebases

### Current Support Status

| Scenario | Supported | Notes |
|----------|-----------|-------|
| Single service / module | ✅ Full support | Best results — full context within one service |
| Monolithic project | ✅ Full support | Works as long as total files < 2,000 |
| Microservices — one service at a time | ✅ Supported | Point source path at individual service folder |
| Microservices — entire fleet in one job | ❌ Not yet | File limit hit; no per-service result axis |

### Scanning a microservices project (one service at a time)

ReviewBot runs inside Docker. To scan code on your Windows host, the `C:\projects` folder is mounted into the container as `/host-projects` (read-only).

**Source path format in the UI:**
```
/host-projects/<relative-path-from-C:\projects>
```

**Examples:**
```
# Single microservice
/host-projects/hatch-pay/backend/hatch-pay-auth-management-service

# Another service
/host-projects/hatch-pay/backend/hatch-pay-payment-adapter-service

# Monolithic project
/host-projects/my-monolith/src
```

**Recommended workflow for microservices fleet:**
1. Create one ReviewBot project per microservice (or one per team)
2. Run a separate autonomous review job per service
3. Each job produces its own RAG report for that service
4. Compare results across jobs manually (fleet-level reporting is on the roadmap)

### Path mount configuration

`docker-compose.yml` mounts `C:\projects` → `/host-projects` (already configured):
```yaml
volumes:
  - C:\projects:/host-projects:ro
```

If your projects are in a different drive or folder, edit `docker-compose.yml` and restart:
```bash
docker-compose up -d --force-recreate app
```

### Roadmap: Full microservices fleet support

See [docs/MICROSERVICES_REVIEW_PLAN.md](docs/MICROSERVICES_REVIEW_PLAN.md) for the full plan.

| Phase | What | Status |
|-------|------|--------|
| Phase 1 | Docker volume mount for host path access | ✅ Done |
| Phase 2 | Multi-service job mode (per-service result axis) | Planned |
| Phase 3 | Java/Spring Boot LLM context quality | Planned |
| Phase 4 | Microservices-specific checklist rules | Planned |
| Phase 5 | Fleet heat-map UI (services × checklist areas) | Planned |

---

## Docker Commands Reference

```bash
# Start (with rebuild)
docker-compose up --build

# Start in background
docker-compose up -d --build

# Stop — KEEPS all data
docker-compose down

# Restart app only (after code changes, no DB rebuild)
docker-compose restart app

# Force recreate app container (after docker-compose.yml changes)
docker-compose up -d --force-recreate app

# View live logs
docker-compose logs -f app
docker-compose logs -f db

# Shell into app container
docker-compose exec app bash

# Shell into database
docker-compose exec db psql -U review_user -d reviews_db

# Run database migrations
docker-compose exec app alembic upgrade head

# DANGER — wipes ALL data (postgres_data volume deleted)
docker-compose down -v
```

> **WARNING**: `docker-compose down -v` permanently deletes all database content.
> Use `docker-compose down` (no `-v`) to stop containers while keeping data intact.

---

## Database Connection

| Context | Host | Port | DB | User | Password |
|---------|------|------|----|------|---------|
| Inside Docker (app container) | `db` | `5432` | `reviews_db` | `review_user` | `review_password_change_me` |
| DBeaver / external tool from Windows host | `localhost` | `5435` | `reviews_db` | `review_user` | `review_password_change_me` |

---

## API Overview

### Authentication
```
POST /api/auth/register    Register new user
POST /api/auth/login       Get JWT token
GET  /api/auth/me          Current user info
```

### Projects & Checklists
```
GET  /api/projects/                           List projects
POST /api/projects/                           Create project
PUT  /api/projects/{id}                       Update project
DELETE /api/projects/{id}                     Delete project
POST /api/projects/{id}/upload-checklist      Upload Excel checklist (.xlsx)
GET  /api/projects/{id}/checklists            List checklists for project
GET  /api/checklists/{id}                     Get checklist with items
POST /api/checklists/{id}/optimize            AI checklist recommendations
```

### Conversational Reviews
```
GET  /api/reviews/                     List reviews
POST /api/reviews/                     Create review session
POST /api/reviews/{id}/start           Start AI agent
POST /api/reviews/{id}/respond         Submit text answer
POST /api/reviews/{id}/voice-response  Submit audio (WAV)
POST /api/reviews/{id}/complete        Complete & generate report
```

### Autonomous Reviews
```
POST   /api/autonomous-reviews/              Start autonomous review job
GET    /api/autonomous-reviews/              List jobs (?project_id=N to filter)
GET    /api/autonomous-reviews/{job_id}      Job status + per-item results
GET    /api/autonomous-reviews/{job_id}/report   Final structured report
DELETE /api/autonomous-reviews/{job_id}      Cancel / delete job
WS     /ws/autonomous-reviews/{job_id}       Real-time progress stream
```

### Reports
```
GET  /api/reports/                           List reports
GET  /api/reports/{id}                       Get report details
POST /api/reports/{id}/approve               Approve report
POST /api/reports/{id}/reject                Reject with comments
GET  /api/reports/{id}/download/{format}     Download (markdown or pdf)
GET  /api/reports/pending/approvals          Pending approvals
```

---

## Postman Collection

Import both files from `postman_collection/`:
- `ReviewBot_API.postman_collection.json` — 25 requests across all endpoints
- `ReviewBot_Local.postman_environment.json` — environment preset (`base_url=http://localhost:8000`)

The collection auto-saves `token`, `project_id`, `review_id`, and `job_id` from responses into environment variables.

---

## Project Structure

```
app/
├── agents/review_agent/       # LangGraph conversational review workflow
├── api/routes/                # FastAPI route handlers
│   ├── auth.py
│   ├── projects.py
│   ├── checklists.py
│   ├── reviews.py
│   ├── reports.py
│   └── autonomous_reviews.py
├── core/config.py             # Pydantic settings (all env vars)
├── db/session.py              # Async engine + init_db
├── models.py                  # SQLAlchemy models
└── services/
    ├── autonomous_review/
    │   ├── connectors/local_folder.py   # File indexer
    │   ├── analyzers/                   # file_presence, pattern_scan, llm, metadata
    │   ├── strategy_router.py           # Routes checklist items to analyzers
    │   ├── orchestrator.py              # Background job runner
    │   └── progress.py                  # WebSocket broadcast manager
    ├── checklist_parser.py    # Excel (.xlsx) parsing
    ├── report_generator.py    # Markdown + PDF generation
    └── voice_interface.py     # STT/TTS integration
main.py                        # FastAPI app entry point
static/index.html              # Autonomous review frontend (served at /ui)
data/
├── templates/                 # Global xlsx checklists (standard-delivery.xlsx, standard-technical.xlsx)
└── projects/                  # Per-project xlsx files (aaa-pdh/, neumoney/)
scripts/
├── init-db-simple.sql         # PostgreSQL init script (creates review_user + reviews_db)
├── migrate_xlsx_to_db.py      # Full migration: reads xlsx → inserts all data
├── generate_seed.py           # Re-generates seed_data.sql from current xlsx files
├── seed_data.sql              # Pre-generated SQL: users + all projects (safe to re-run)
├── seed_hatchpay.sql          # Pre-generated SQL: Hatch Pay project only (safe to re-run)
└── db_test.py                 # Minimal seed: 3 users + 1 sample project
docs/
└── MICROSERVICES_REVIEW_PLAN.md   # Roadmap for microservices fleet scanning
postman_collection/
├── ReviewBot_API.postman_collection.json
└── ReviewBot_Local.postman_environment.json
```

---

## Environment Variables

All defined in `app/core/config.py`. See `.env` for the full list.

| Variable | Description | Required |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | Yes |
| `SECRET_KEY` | JWT signing key — change in production | Yes |
| `ACTIVE_LLM_PROVIDER` | `openai` \| `anthropic` \| `google` \| `groq` \| `qwen` \| `azure` | Yes |
| `OPENAI_API_KEY` | OpenAI key | If provider=openai |
| `GROQ_API_KEY` | Groq key (free tier available) | If provider=groq |
| `ANTHROPIC_API_KEY` | Anthropic key | If provider=anthropic |
| `GOOGLE_API_KEY` | Google Gemini key | If provider=google |
| `VOICE_ENABLED` | Enable STT/TTS features | No (default: true) |
| `REQUIRE_HUMAN_APPROVAL` | Reports require approval before delivery | No (default: true) |

---

## Database Migrations

```bash
# Generate a new migration after changing models.py
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply all pending migrations
docker-compose exec app alembic upgrade head

# Check current migration version
docker-compose exec app alembic current

# Roll back one migration
docker-compose exec app alembic downgrade -1
```

---

## Local Python Dev (without Docker)

```bash
pip install -r requirements.txt

# Use SQLite — no PostgreSQL needed
# Edit .env:
DATABASE_URL=sqlite+aiosqlite:///./reviews.db

uvicorn main:app --reload --port 8000
```

---

## Troubleshooting

**`password authentication failed for user "review_user"`**
The Postgres volume exists but `review_user` wasn't created (or was created with wrong auth method). Fix:
```bash
docker-compose down -v    # WARNING: wipes all data
docker-compose up --build
# Then re-seed:
python scripts/migrate_xlsx_to_db.py
```

**`User does not have a valid SCRAM secret`**
PostgreSQL 15 requires `scram-sha-256`. Old volumes created with `password_encryption = 'md5'` fail.
Fix: `docker-compose down -v` to reset the volume, then restart.

**`Source path does not exist: C:\projects\...`**
The app runs inside Docker and cannot see Windows host paths directly.
Use the `/host-projects/` prefix which maps to your `C:\projects\` folder:
```
# Wrong
C:\projects\hatch-pay\backend\hatch-pay-auth-management-service

# Correct
/host-projects/hatch-pay/backend/hatch-pay-auth-management-service
```
If the mount isn't working, restart the app container:
```bash
docker-compose up -d --force-recreate app
```

**Port already in use**
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :5435
# Change APP_PORT or DB_PORT in .env, then restart
```

**`(projects || []).forEach is not a function`**
The projects API returns `{"projects": [...]}` not a plain array. The UI handles this — if you see this error, hard-refresh the browser (Ctrl+Shift+R).

**`MissingGreenlet` / lazy loading crash**
All SQLAlchemy relationship access in async context must use `selectinload()`. Never access `.relationship` attributes without eager loading.

---

## License

Proprietary. All rights reserved.
