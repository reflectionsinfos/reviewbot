# ReviewBot — Claude Code Reference

## Project Overview

AI-powered project review platform that conducts structured technical and delivery reviews via a conversational agent. Features LangGraph workflows, voice interaction, RAG compliance scoring, and a mandatory human approval workflow.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn (async) |
| AI/LLM | LangChain + LangGraph + OpenAI GPT-4o |
| Database | PostgreSQL 15 via asyncpg (Cloud SQL / Docker) |
| Vector Store | ChromaDB |
| Voice | OpenAI Whisper (STT) + TTS |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Reports | ReportLab (PDF) + Markdown |

## Project Structure

```
app/
├── agents/review_agent/    # LangGraph state machine workflow
│   ├── agent.py            # ReviewAgent class + node functions
│   └── states.py           # ReviewState TypedDict
├── api/routes/             # FastAPI endpoints
│   ├── auth.py             # JWT auth, register, login
│   ├── projects.py         # Project CRUD + checklist upload
│   ├── checklists.py       # Checklist management + AI optimization
│   ├── reviews.py          # Review sessions + voice responses
│   └── reports.py          # Report management + approval workflow
├── core/config.py          # Pydantic settings (all env vars)
├── db/session.py           # Async engine, get_db dependency, init_db
├── models.py               # SQLAlchemy models
└── services/
    ├── checklist_parser.py     # Excel (.xlsx) parsing
    ├── checklist_optimizer.py  # AI-powered checklist enhancements
    ├── report_generator.py     # Markdown + PDF report generation
    ├── template_manager.py     # Template management
    └── voice_interface.py      # STT/TTS integration
main.py                     # FastAPI app entry point + lifespan
```

## Key Models

- `User` — auth with roles: `reviewer`, `manager`, `admin`
- `Project` — domain, tech_stack (JSON), stakeholders (JSON)
- `Checklist` — type: `delivery` or `technical`, global or project-specific
- `ChecklistItem` — questions with area, weight, expected_evidence
- `Review` — session linking project + checklist, tracks status
- `ReviewResponse` — per-item answer + RAG status (red/amber/green/na)
- `Report` — compliance score, gaps, recommendations, approval_status
- `ReportApproval` — approval decision trail

## Environment Variables

All vars defined in `app/core/config.py` (Pydantic Settings). Key ones:

```env
# Required
DATABASE_URL=postgresql+asyncpg://review_user:review_password_change_me@db:5432/reviews_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# LLM (at least one required)
OPENAI_API_KEY=
ACTIVE_LLM_PROVIDER=openai   # openai | anthropic | google | groq | qwen | azure
ANTHROPIC_API_KEY=
GROQ_API_KEY=
QWEN_API_KEY=

# Optional
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true
ELEVENLABS_API_KEY=
```

## Running the App

```bash
# Development (requires a running PostgreSQL instance)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Docker (recommended)
docker-compose up --build
# App: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Docker Architecture

- **app** — FastAPI (waits for db health check before starting)
- **db** — PostgreSQL 15, initialized via `scripts/init-db-simple.sql`
- Database host port: **5435** (not 5432 — avoids conflict with local PostgreSQL on Windows)
- Database credentials: user=`review_user`, db=`reviews_db`, password=`review_password_change_me`

**DBeaver connection:** host=`localhost`, port=`5435`, db=`reviews_db`, user=`review_user`

## API Endpoints

```
POST   /api/auth/register          Register user
POST   /api/auth/login             Get JWT token

GET    /api/projects/              List projects
POST   /api/projects/              Create project
POST   /api/projects/{id}/upload-checklist   Upload Excel checklist
GET    /api/projects/{id}/checklists

GET    /api/reviews/               List reviews
POST   /api/reviews/               Create review session
POST   /api/reviews/{id}/start     Start AI agent
POST   /api/reviews/{id}/respond   Submit text response
POST   /api/reviews/{id}/voice-response  Submit audio
POST   /api/reviews/{id}/complete  Complete review

GET    /api/reports/               List reports
POST   /api/reports/{id}/approve   Approve report
POST   /api/reports/{id}/reject    Reject with comments
GET    /api/reports/{id}/download/{format}  markdown or pdf

GET    /api/checklists/{id}
POST   /api/checklists/{id}/optimize   AI recommendations
GET    /health
```

## Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Coding Conventions

- **All DB queries must use eager loading** — use `selectinload()` when accessing relationships to avoid `MissingGreenlet` errors with async SQLAlchemy
- **Async everywhere** — use `async def` + `await` for all I/O
- **Error handling** — wrap DB operations in try/except, rollback on error
- **Validation** — use Pydantic models for request bodies; validate at route level
- **Secrets** — always via `settings.*`, never hardcoded
- Type hints required on all functions

## Common Pitfalls

1. **Lazy loading crashes** — always add `selectinload(Model.relationship)` before accessing related objects in async context
2. **DB not ready on Docker start** — `depends_on: db: condition: service_healthy` ensures the app waits
3. **Agent `generate_report`** — parameter must be named `state`, not `ReviewState` (the class)
4. **reportlab `Heading`** — not a valid platypus class; use `Paragraph` with heading styles instead
5. **`declarative_base`** — import from `sqlalchemy.orm`, not `sqlalchemy.ext.declarative` (deprecated)

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=app
```
