# ReviewBot — Architecture & Key Decisions

> Key architectural decisions and system design reference.
> Last updated: 2026-04-27

---

## System Architecture

```
Browser / Agent CLI
    │
    ▼
FastAPI Routes (auth via Depends(get_current_user))
    │
    ├── Service Layer (app/services/)
    │       │
    │       └── Async SQLAlchemy → PostgreSQL (asyncpg)
    │
    ├── Background Tasks (autonomous review jobs)
    │       └── WebSocket progress broadcast
    │
    └── LangGraph ReviewAgent (conversational reviews)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn (async) |
| AI/LLM | LangChain + LangGraph + multi-LLM (OpenAI, Anthropic, Groq, Qwen, Azure) |
| Database | PostgreSQL 15 via asyncpg (Cloud SQL / Docker) |
| ORM | SQLAlchemy async |
| Voice | OpenAI Whisper (STT) + TTS |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Reports | ReportLab (PDF) + Markdown |
| Email | SMTP (aiosmtplib) + Resend.com HTTP API |

---

## Key Architectural Decisions

### ADR-001: FastAPI (not Django/Flask)
Chosen for native async support, Pydantic integration, and automatic OpenAPI docs. All endpoints are async.

### ADR-002: PostgreSQL (not SQLite)
Production database. Docker runs on host port **5435** (internal 5432) to avoid conflicts with local PostgreSQL. In development, SQLite references in troubleshooting docs are historical — the current stack uses PostgreSQL.

### ADR-003: LangGraph for Review Agent
Stateful graph manages the conversation flow: `initialize_review` → `ask_question` → `process_response` → `assess_rag` → `generate_report`. State is a TypedDict (`ReviewState`) stored in memory during a session.

### ADR-004: Multi-LLM Support
Provider selection via `ACTIVE_LLM_PROVIDER` env var. Supported: `openai`, `anthropic`, `google`, `groq`, `qwen`, `azure`. Individual LLM configs also stored in DB (`llm_configs` table) for per-checklist routing.

### ADR-005: Human Approval Workflow
Reports go through an explicit approval step (`approval_status`: pending → approved/rejected) before being considered final. Controlled by `REQUIRE_HUMAN_APPROVAL` setting.

### ADR-006: Async DB (no Alembic)
SQLAlchemy async engine + asyncpg driver. Schema migrations managed as idempotent SQL strings in `app/db/session.py:init_db()`, not Alembic. This avoids migration files and keeps the schema source of truth in one place.

### ADR-007: JWT Auth (no sessions)
Stateless JWT tokens. Expiry: 480 minutes (8 hours). `get_current_user` FastAPI dependency used on all protected routes.

### ADR-008: RAG Status System
Three-color traffic-light: **Red** (non-compliant), **Amber** (partial), **Green** (compliant), **NA** (not applicable). Compliance score = weighted average of non-NA items.

### ADR-009: Token-Gated Offline Reviews
Offline reviews use a UUID upload_token embedded in a URL. Reviewer accesses the portal without needing a login. Token valid for `OFFLINE_REVIEW_TOKEN_DAYS` (default 30 days).

### ADR-010: Markdown + PDF Reports
Reports generated in Markdown first (for readability), then optionally converted to PDF via ReportLab for download.

### ADR-011: Org Scoping
Organizations have a `NULL` or specific org_id on shared resources. NULL = platform-wide. Filter applied in service layer with `or_(X == None, X == user_org_id)`.

### ADR-012: Dynamic URL Generation
Base URLs for shareable links derived from live HTTP request headers (`x-forwarded-proto`, `host`) to support GCP Cloud Run and other reverse-proxy deployments. Never use static `APP_BASE_URL` in route handlers.

---

## Review Types

| Type | Description |
|------|-------------|
| `online` | Conversational AI-assisted review via LangGraph agent |
| `offline` | Excel-based async review; reviewer fills spreadsheet, uploads back |
| `manual` / `self` | Team member does review via token-gated portal without Excel |
| `autonomous` | Automated code analysis via `AutonomousReviewJob` — scans source files |

---

## Compliance Score Formula

```
score = sum(item_weight * rag_points for non-NA items)
      / sum(item_weight for non-NA items)

rag_points: green=1.0, amber=0.5, red=0.0, na=excluded
```

---

## Security Notes

- JWT bearer tokens protect all authenticated routes
- Passwords hashed with bcrypt via passlib
- Integration config secrets masked in all GET responses via `_mask_config()`
- LLM audit traces stored redacted (prompt/response hashes, not full text)
- Admin-only paths enforce role check in route handler — not middleware
- Offline review portal access via upload_token (no login required)
