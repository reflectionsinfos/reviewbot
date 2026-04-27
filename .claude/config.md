# Claude AI Agent - Configuration & Standards

> Configuration and behavioral standards for Claude AI assistant in this project

*Last updated: 2026-04-26*

---

## Project Context

**Project Name:** ReviewBot — AI Tech & Delivery Review Agent
**Location:** `c:\projects\nexus-ai\reviewbot` (git submodule of `nexus-ai`)
**Type:** Autonomous code review platform + external async review tooling
**Tech Stack:** FastAPI, SQLAlchemy (async), PostgreSQL, LangGraph, LangChain, OpenAI / multi-LLM

**Key capabilities:**
- Autonomous code review jobs with LLM-powered item analysis and real-time WebSocket progress
- Multi-provider LLM configuration (OpenAI, Anthropic, Groq, Qwen, Azure, local Ollama)
- Structured checklist management with global templates and project-specific copies
- Org-scoped global checklist templates (platform-wide vs. org-private)
- Outbound integrations: JIRA ticket creation, SMTP email, generic webhooks
- CVE/dependency vulnerability scanning via Trivy, OSV Scanner, pip-audit, npm-audit
- Agent bridge for local workspace review (`/api/v1/agent/scan`)
- Human approval workflow for completed review reports
- Action-plan generation with AI-enhanced prompt caching
- JWT auth with role-based access (reviewer / manager / admin)

---

## Architecture

### Runtime layout

```
main.py                         FastAPI entry point, route registration, lifespan DB init
app/
  api/routes/                   Route modules (one file per domain area)
    auth.py                     JWT auth, register, login, /me, change-password, dev-config
    organizations.py            Organization CRUD (new 2026-04-26)
    projects.py                 Project CRUD, org_id support
    checklists.py               Checklist and item CRUD, global templates, sync
    reviews.py                  Conversational review sessions
    reports.py                  Report approval, download, history
    autonomous_reviews.py       Autonomous job lifecycle, results, overrides, action plans
    agent.py                    Agent bridge upload/start/file-request
    integrations.py             Outbound integration CRUD, test, manual dispatch
    routing_rules.py            LLM routing rules for checklist strategy
    llm_configs.py              LLM provider CRUD + connectivity test
    settings.py                 System settings CRUD
    organizations.py            Organization CRUD (admin write, any-auth read)
    users.py                    Admin user management
  core/
    config.py                   Pydantic Settings — all env vars live here, never os.getenv()
  db/
    session.py                  Async engine, get_db, AsyncSessionLocal, init_db (with migrations array)
  models.py                     All SQLAlchemy models
  schemas/
    checklist.py                Pydantic request/response models for checklists
  services/
    checklist_service.py        Checklist business logic + org-scoped template filtering
    checklist_parser.py         Excel .xlsx ingestion (ChecklistParser class)
    checklist_optimizer.py      AI-powered checklist item recommendations
    report_generator.py         Markdown + PDF report generation
    template_manager.py         Template management
    voice_interface.py          STT / TTS helpers
    autonomous_review/          Orchestrator, analyzers, connectors, progress, action-plan generator
frontend_vanilla/               Static HTML + vanilla JS pages served by FastAPI
  index.html                    Autonomous review launcher
  history.html                  Review history, details, action plan, AI trace
  project.html                  Project + project-checklist management
  globals.html                  Global checklist template management (org-scoped)
  home.html / dashboard         Home / dashboard
  documentation.html            Product documentation
  system_config.html            LLM + system settings management
```

### Request flow

```
Browser / Agent
    → FastAPI route (auth via Depends(get_current_user))
    → Service / inline query (async SQLAlchemy)
    → PostgreSQL (asyncpg)
    → Background tasks (autonomous review jobs)
    → WebSocket progress broadcast
```

---

## Data Model

### Core entities

| Table | Key columns | Notes |
|-------|-------------|-------|
| `organizations` | id, name, slug, description, is_active, created_at, updated_at | Soft-delete via is_active |
| `users` | id, email, hashed_password, full_name, role, is_active, organization_id | roles: reviewer/manager/admin |
| `projects` | id, name, domain, description, tech_stack (JSON), stakeholders (JSON), organization_id | |
| `checklists` | id, name, type, is_global, organization_id, source_global_id, version | NULL org_id = platform-wide global |
| `checklist_items` | id, checklist_id, area, code, question, expected_evidence, weight, is_mandatory, team_category, guidance, applicability_tags (JSON), sort_order | team_category/guidance/applicability_tags added 2026-04 |
| `reviews` | id, project_id, checklist_id, reviewer_id, status, review_type | |
| `review_responses` | id, review_id, checklist_item_id, rag_status, answer, notes | |
| `reports` | id, review_id, job_id, compliance_score, gaps, recommendations, approval_status | |
| `report_approvals` | id, report_id, user_id, decision, comments | |
| `autonomous_review_jobs` | id, project_id, checklist_id, status, source_path, red_count, amber_count, green_count, na_count, compliance_score, metadata (JSON) | |
| `autonomous_review_results` | id, job_id, checklist_item_id, rag_status, evidence, files_checked, strategy_used, llm_used | |
| `autonomous_review_overrides` | id, result_id, user_id, previous_rag, new_rag, justification | |
| `autonomous_review_llm_audit` | id, job_id, item_id, stage, prompt_hash, response_hash, model_used, input_tokens, output_tokens | redacted storage |
| `llm_configs` | id, name, provider, model, api_key (encrypted), base_url, is_active, is_default | |
| `system_settings` | id, key, value, description | runtime toggles |
| `checklist_routing_rules` | id, checklist_id, item_id, strategy_override, created_by | |
| `checklist_recommendations` | id, job_id, checklist_id, recommendations (JSON) | |
| `integration_configs` | id, name, type, config (JSON, secrets masked in GET), trigger_condition, include_advisories, is_enabled | types: jira/smtp/webhook/linear/github_issues |
| `integration_dispatches` | id, integration_id, job_id, status, dispatched_at, items_dispatched, result_detail, error_message | |

### Org-scoping rule

```
organization_id = NULL  →  platform-wide, visible to all users
organization_id = X     →  private to users with organization_id = X
```

Applied via:
```python
from sqlalchemy import or_
query = query.where(or_(
    Checklist.organization_id == None,
    Checklist.organization_id == current_user.organization_id,
))
```

---

## API Endpoint Inventory

### Auth `/api/auth`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | — | Register new user (accepts organization_id) |
| POST | `/api/auth/login` | — | Get JWT access token |
| GET | `/api/auth/me` | any | Current user info including organization_id |
| POST | `/api/auth/change-password` | any | Change own password |
| GET | `/api/auth/dev-config` | — | Dev credentials (local env only) |

### Organizations `/api/organizations`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/organizations/` | any | List active organizations |
| GET | `/api/organizations/mine` | any | Get current user's organization |
| GET | `/api/organizations/{id}` | any | Get one organization |
| POST | `/api/organizations/` | admin | Create organization |
| PUT | `/api/organizations/{id}` | admin | Update organization |
| DELETE | `/api/organizations/{id}` | admin | Soft-delete organization |

### Projects `/api/projects`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/projects/` | any | List projects |
| POST | `/api/projects/` | any | Create project (accepts organization_id) |
| GET | `/api/projects/{id}` | any | Get project |
| PUT | `/api/projects/{id}` | any | Update project |
| DELETE | `/api/projects/{id}` | any | Delete project |
| GET | `/api/projects/{id}/checklists` | any | List project checklists |
| POST | `/api/projects/{id}/upload-checklist` | any | Upload Excel checklist |
| POST | `/api/projects/{id}/clone-template/{template_id}` | any | Clone global template |

### Checklists `/api/checklists`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/checklists/templates/global` | any | List global templates (org-scoped) |
| POST | `/api/checklists/templates/global` | admin | Create global template (accepts organization_id) |
| POST | `/api/checklists/templates/global/upload` | admin | Upload global template from Excel |
| GET | `/api/checklists/{id}` | any | Get checklist with items |
| PUT | `/api/checklists/{id}` | any | Update checklist metadata |
| DELETE | `/api/checklists/{id}` | any | Delete checklist |
| GET | `/api/checklists/{id}/items` | any | List items |
| POST | `/api/checklists/{id}/items` | any | Create item (accepts team_category, guidance, applicability_tags) |
| PUT | `/api/checklists/{id}/items/{item_id}` | any | Update item |
| DELETE | `/api/checklists/{id}/items/{item_id}` | any | Delete item |
| POST | `/api/checklists/{id}/sync` | any | Sync from source template |
| POST | `/api/checklists/{id}/optimize` | any | AI recommendations |
| PUT | `/api/checklists/{id}/items/reorder` | any | Reorder items |

### Autonomous Reviews `/api/autonomous-reviews`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/autonomous-reviews/` | any | Start job |
| GET | `/api/autonomous-reviews/` | any | List jobs |
| GET | `/api/autonomous-reviews/{id}` | any | Get job |
| GET | `/api/autonomous-reviews/{id}/results` | any | Get results |
| POST | `/api/autonomous-reviews/{id}/results/{result_id}/override` | any | Override finding |

### Integrations `/api/integrations`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/integrations/` | admin | List (secrets masked) |
| POST | `/api/integrations/` | admin | Create |
| GET | `/api/integrations/{id}` | admin | Get one |
| PATCH | `/api/integrations/{id}` | admin | Update |
| DELETE | `/api/integrations/{id}` | admin | Delete |
| POST | `/api/integrations/{id}/test` | admin | Test connectivity |
| POST | `/api/integrations/{id}/dispatch/{job_id}` | admin/manager | Manual dispatch |
| GET | `/api/integrations/dispatches/{job_id}` | any | Dispatch history |

---

## Coding Conventions

### Async everywhere
- `async def` + `await` for all DB and I/O operations
- `selectinload()` is **mandatory** when accessing any SQLAlchemy relationship in async context (omitting it causes `MissingGreenlet`)
- Never use blocking calls (requests, time.sleep) in route handlers

### Database access pattern
```python
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@router.get("/items/{id}")
async def get_item(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChecklistItem)
        .options(selectinload(ChecklistItem.checklist))
        .where(ChecklistItem.id == id)
    )
    return result.scalar_one_or_none()
```

### DB migrations — no Alembic
Migrations run at startup inside `init_db()` in `app/db/session.py`. Add new migrations as strings in the `migrations` list:
```python
migrations = [
    # ... existing ...
    "ALTER TABLE my_table ADD COLUMN IF NOT EXISTS new_col VARCHAR(200)",
]
```
Never use `alembic revision` for this project — the migration array is the single source of schema truth.

### Config — never os.getenv()
```python
# ✅ Always
from app.core.config import settings
key = settings.OPENAI_API_KEY

# ❌ Never
import os
key = os.getenv("OPENAI_API_KEY")
```

### Auth dependency injection
```python
from app.api.routes.auth import get_current_user
from app.models import User

@router.get("/protected")
async def endpoint(current_user: User = Depends(get_current_user)):
    # current_user.organization_id is available for org scoping
    ...
```

### Role check pattern
```python
if current_user.role != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
```

### Syntax check before completing any task
```bash
python -c "
import ast, sys
files = ['app/models.py', 'app/db/session.py', 'main.py']
for f in files:
    try:
        ast.parse(open(f).read())
        print('OK ', f)
    except SyntaxError as e:
        print('ERR', f, e)
        sys.exit(1)
"
```

---

## Org Scoping Rules

1. **NULL = platform-wide.** Never set `organization_id = NULL` intentionally on user-created org-scoped content — only explicitly pass `None` for platform content.
2. **Filter in service layer.** Apply org filter in `ChecklistService`, not in route handlers.
3. **Admin bypass.** Admins see everything regardless of their own `organization_id`. Apply only for regular users.
4. **Free-form type.** `GlobalChecklistCreate.type` accepts any string — do not revert to `Literal["delivery", "technical"]`.
5. **Slug auto-generation.** Organization slug is derived from name: `re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")`.

---

## Security Notes

- JWT bearer tokens protect all authenticated routes
- Passwords hashed with bcrypt via passlib
- Integration config secrets masked in all GET responses via `_mask_config()`
- LLM audit traces are stored redacted (prompt/response hashes, not full text)
- Admin-only paths enforce role check in route handler — not middleware

---

## Common Pitfalls

1. **Missing `selectinload`** — async SQLAlchemy will raise `MissingGreenlet` if you access a relationship attribute without eager loading
2. **`declarative_base` import** — use `from sqlalchemy.orm import declarative_base`, not the deprecated `sqlalchemy.ext.declarative`
3. **ReportLab `Heading`** — not a valid class; use `Paragraph` with heading styles
4. **Agent `generate_report` node** — parameter must be named `state`, not the class type name
5. **DB port conflict** — Docker PostgreSQL runs on host port `5435`, not 5432, to avoid local PostgreSQL conflicts
6. **`init_db` migrations** — adding `ADD COLUMN IF NOT EXISTS` is idempotent; always use IF NOT EXISTS
