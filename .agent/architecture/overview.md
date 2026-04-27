# Architecture Overview

*Last Updated: 2026-04-26*

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌─────────────┐  ┌───────────────────┐  ┌───────────────────┐ │
│  │ Vanilla JS  │  │  ReviewBot CLI /  │  │  External agents  │ │
│  │  Web UI     │  │  VSCode extension │  │  (agent bridge)   │ │
│  └─────────────┘  └───────────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (main.py)                │
│                                                                 │
│  /api/auth          /api/organizations   /api/projects          │
│  /api/checklists    /api/autonomous-reviews                     │
│  /api/reports       /api/v1/agent/scan   /api/integrations      │
│  /api/llm-configs   /api/settings        /api/admin             │
│  /api/routing-rules                                             │
│                                                                 │
│  WebSocket: /ws/autonomous-reviews/{job_id}                     │
│  Static pages: / /ui /history /projects-ui /globals etc.        │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  Background     │  │  Services    │  │  Outbound            │
│  Review Jobs    │  │  layer       │  │  Integrations        │
│                 │  │              │  │                      │
│  Orchestrator   │  │  Checklist   │  │  JIRA (REST v3)      │
│  Agent orch.    │  │  Service     │  │  SMTP email          │
│  Strategy router│  │  Report gen  │  │  Webhook (httpx)     │
│  Analyzers      │  │  Action plan │  │  Linear (stub)       │
│  Progress mgr   │  │  LLM audit   │  │  GitHub Issues (stub)│
└─────────────────┘  └──────────────┘  └──────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PostgreSQL via async SQLAlchemy                 │
│                                                                 │
│  organizations → users → projects → checklists → items         │
│  autonomous_review_jobs → results → overrides → llm_audit       │
│  integration_configs → integration_dispatches                   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Web Framework | FastAPI + Uvicorn | REST API + WebSocket |
| Database ORM | SQLAlchemy (async) + asyncpg | Data access |
| Migrations | Custom migration array in `db/session.py` init_db() | Schema evolution (no Alembic) |
| AI Orchestration | LangChain + LangGraph | Agent workflows |
| LLM | OpenAI / Anthropic / Groq / Qwen / Azure / local Ollama | Multi-provider intelligence |
| Voice STT | OpenAI Whisper | Speech-to-text |
| Voice TTS | OpenAI TTS | Text-to-speech |
| Auth | JWT (python-jose) + bcrypt (passlib) | Security |
| Reports | ReportLab (PDF) + Markdown | Report generation |
| File Parsing | openpyxl / pandas | Excel checklist ingestion |
| HTTP client | httpx (async) | Outbound integrations |
| Vulnerability scan | Trivy, OSV Scanner, pip-audit, npm-audit | CVE detection (local CLI) |

## Key Design Decisions

See: [decisions.md](decisions.md)

## Organization Scoping

ReviewBot uses lightweight org scoping — not full multi-tenancy:

- `Organization` model: id, name, slug, description, is_active
- `organization_id` FK on `User`, `Project`, `Checklist` (nullable)
- `NULL` = platform-wide (visible to all); non-null = org-private
- Global checklist visibility: `WHERE is_global=true AND (org_id IS NULL OR org_id = user.org_id)`
- `/api/organizations` — admin write, any-auth read
- Free-form checklist type (not locked to `delivery`/`technical`)

## Core Data Flow (Autonomous Review)

1. User submits `POST /api/autonomous-reviews/` with project + checklist + source path
2. FastAPI creates `AutonomousReviewJob` (status=pending), starts background task
3. Orchestrator indexes source files → routes each checklist item to an analyzer strategy
4. Each analyzer stores `AutonomousReviewResult` with RAG status and evidence
5. Progress is broadcast via WebSocket to subscribed UI clients
6. On completion: job counters updated, outbound integrations auto-dispatched if configured
7. History UI polls `/api/reports/history` and loads detail + action plan on demand

## Project Structure

```
app/
  api/routes/           One file per domain area
  core/config.py        Pydantic Settings — all config here
  db/session.py         Async engine, get_db, init_db (migration array)
  models.py             All SQLAlchemy models
  schemas/              Pydantic request/response models
  services/             Business logic layer
    autonomous_review/  Orchestrator, analyzers, connectors, progress, action-plan
frontend_vanilla/       Static HTML + vanilla JS (served by FastAPI)
main.py                 App entry, route registration, lifespan
```
