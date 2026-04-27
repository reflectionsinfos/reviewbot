# ReviewBot — Claude Code Reference

> **Context is auto-loaded** from `.claude/rules/` — no manual reads needed before coding.
> Key rules files: `reviewbot-00-codebase.md`, `reviewbot-01-design-guidelines.md`, `reviewbot-02-architecture.md`, `reviewbot-03-api-reference.md`, `reviewbot-04-agent-workflow.md`

## Project Overview

AI-powered project review platform that conducts structured technical and delivery reviews via a conversational agent. Features LangGraph workflows, voice interaction, RAG compliance scoring, autonomous code review, and a mandatory human approval workflow.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn (async) |
| AI/LLM | LangChain + LangGraph + multi-LLM (OpenAI, Anthropic, Groq, Qwen, Azure) |
| Database | PostgreSQL 15 via asyncpg (Cloud SQL / Docker) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Reports | ReportLab (PDF) + Markdown |
| Email | SMTP (aiosmtplib) + Resend.com |

## Running the App

```bash
# Development (requires PostgreSQL)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Docker (recommended)
docker-compose up --build
# App: http://localhost:8000  |  Docs: http://localhost:8000/docs
```

## Docker Architecture

- **app** — FastAPI (waits for db health check)
- **db** — PostgreSQL 15 on host port **5435** (not 5432 — avoids conflict with local PostgreSQL)
- DB credentials: user=`review_user`, db=`reviews_db`, password=`review_password_change_me`
- DBeaver: host=`localhost`, port=`5435`, db=`reviews_db`, user=`review_user`

## Environment Variables

All vars in `app/core/config.py` (Pydantic Settings). Key ones:

```env
DATABASE_URL=postgresql+asyncpg://review_user:review_password_change_me@db:5432/reviews_db
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">

# LLM (at least one required)
OPENAI_API_KEY=
ACTIVE_LLM_PROVIDER=openai   # openai | anthropic | google | groq | qwen | azure
ANTHROPIC_API_KEY=
GROQ_API_KEY=

# Optional
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true
ELEVENLABS_API_KEY=
```

## Critical Coding Rules

1. **selectinload() mandatory** — every SQLAlchemy relationship access in async context requires eager loading
2. **No Alembic** — schema changes go in the `migrations` array in `app/db/session.py:init_db()`
3. **No os.getenv()** — always use `settings.*` from `app/core/config.py`
4. **Service layer** — DB queries go in `app/services/`, not in route handlers
5. **Dynamic URLs** — use `_get_base_url(http_request: Request)` in route handlers, never `settings.APP_BASE_URL`
6. **Org scoping** — apply `or_(org_id == None, org_id == user.organization_id)` filter in services

See `.claude/rules/reviewbot-01-design-guidelines.md` for full guidelines with code examples.

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=app
```
