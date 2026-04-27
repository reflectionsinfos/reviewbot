# ReviewBot — Codebase Reference

> Auto-loaded by Claude Code. Read this before exploring the repo.
> Last updated: 2026-04-27

---

## Project Layout

```
reviewbot/
├── main.py                              # FastAPI entry point + lifespan startup + route registration
├── app/
│   ├── api/routes/
│   │   ├── auth.py                      # JWT login/register; get_current_user dependency
│   │   ├── organizations.py             # Organization CRUD (admin write, any-auth read)
│   │   ├── projects.py                  # Project CRUD + checklist upload
│   │   ├── checklists.py                # Checklist CRUD; GET /templates/global
│   │   ├── reviews.py                   # Review sessions, offline flow, voice, uploads
│   │   ├── reports.py                   # Report management + approval workflow
│   │   ├── autonomous_reviews.py        # Autonomous job lifecycle, results, overrides, action plans
│   │   ├── agent.py                     # Agent bridge upload/start/file-request
│   │   ├── integrations.py              # Admin CRUD for IntegrationConfig + test/dispatch
│   │   ├── routing_rules.py             # LLM routing rules for checklist strategy
│   │   ├── llm_configs.py               # LLM provider CRUD + connectivity test
│   │   ├── settings.py                  # System settings CRUD
│   │   └── users.py                     # Admin user management
│   ├── agents/review_agent/
│   │   ├── agent.py                     # LangGraph ReviewAgent class + node functions
│   │   └── states.py                    # ReviewState TypedDict
│   ├── core/config.py                   # Pydantic Settings (all env vars, including APP_BASE_URL)
│   ├── db/session.py                    # Async engine, get_db, init_db (migrations array)
│   ├── models.py                        # All SQLAlchemy ORM models
│   ├── schemas/
│   │   └── checklist.py                 # Pydantic request/response models for checklists
│   └── services/
│       ├── checklist_service.py         # Checklist business logic + org-scoped template filtering
│       ├── checklist_parser.py          # Excel .xlsx ingestion
│       ├── checklist_optimizer.py       # AI-powered checklist enhancements
│       ├── report_generator.py          # Markdown + PDF report generation
│       ├── template_manager.py          # Template management
│       ├── voice_interface.py           # STT/TTS integration
│       └── integrations/
│           ├── base.py                  # DispatchItem, DispatchResult, mask_secret
│           ├── dispatcher.py            # run_auto_dispatch, run_manual_dispatch
│           ├── email_smtp.py            # SMTP email via aiosmtplib
│           ├── email_resend.py          # Resend.com HTTP API
│           ├── jira.py
│           ├── linear.py
│           ├── github_issues.py
│           └── webhook.py
├── frontend_vanilla/
│   ├── index.html                       # Autonomous review launcher / landing
│   ├── home.html / dashboard.html       # Home / dashboard
│   ├── history.html                     # Review history, details, action plan, AI trace
│   ├── project.html                     # Project + project-checklist management + Manual/Offline reviews
│   ├── globals.html                     # Global checklist template management (org-scoped)
│   ├── documentation.html               # Product documentation
│   ├── system_config.html               # LLM + system settings management
│   └── components/
│       ├── header_loader.js
│       └── footer-loader.js
└── scripts/
    └── init-db-simple.sql
```

---

## Key Models (models.py)

| Model | Notable fields |
|-------|---------------|
| `Organization` | `id`, `name`, `slug`, `description`, `is_active` |
| `User` | `role` ∈ {reviewer, manager, admin}, `organization_id` (FK) |
| `Project` | `domain`, `tech_stack` (JSON), `stakeholders` (JSON), `organization_id` |
| `Checklist` | `type` (free-form string), `is_global`, `organization_id` (NULL=platform-wide), `source_global_id`, `version` |
| `ChecklistItem` | `area`, `code`, `question`, `expected_evidence`, `weight`, `is_mandatory`, `team_category`, `guidance`, `applicability_tags` (JSON), `sort_order` |
| `Review` | `review_type` ∈ {online, offline}, `status`, `upload_token`, `due_date`, `assigned_reviewer_email` |
| `ReviewResponse` | `rag_status` ∈ {red, amber, green, na} |
| `Report` | `compliance_score`, `approval_status` |
| `AutonomousReviewJob` | `status`, `source_path`, `red_count`, `amber_count`, `green_count`, `na_count`, `compliance_score`, `metadata` (JSON) |
| `AutonomousReviewResult` | `rag_status`, `evidence`, `files_checked`, `strategy_used`, `llm_used` |
| `LlmConfig` | `provider`, `model`, `api_key` (encrypted), `base_url`, `is_active`, `is_default` |
| `IntegrationConfig` | `type`, `is_enabled`, `trigger_on`, `config_json` (JSON), `include_advisories` |
| `IntegrationDispatch` | dispatch log per job+integration |

---

## Coding Conventions

### Async everywhere
- `async def` + `await` for all DB and I/O operations
- `selectinload()` is **mandatory** when accessing any SQLAlchemy relationship in async context (omitting causes `MissingGreenlet`)
- Never use blocking calls in route handlers

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
Add SQL strings to the `migrations` array in `app/db/session.py:init_db()`. Always use `IF NOT EXISTS`.
```python
migrations = [
    # ... existing ...
    "ALTER TABLE my_table ADD COLUMN IF NOT EXISTS new_col VARCHAR(200)",
    "CREATE INDEX IF NOT EXISTS idx_my_table_col ON my_table(new_col)",
]
```

### Config — never os.getenv()
```python
from app.core.config import settings
key = settings.OPENAI_API_KEY   # ✅
# os.getenv("OPENAI_API_KEY")  # ❌
```

### Service layer pattern
Do not execute raw DB queries inside route functions. Delegate to `app/services/`.
```python
@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    return await ItemService.list_all(db)
```

---

## Org Scoping Rule

`organization_id = NULL` → platform-wide (visible to all users).
`organization_id = X` → visible only to users with matching `organization_id`.

Apply filter in service layer (not route handlers):
```python
from sqlalchemy import or_
query = query.where(or_(
    Checklist.organization_id == None,
    Checklist.organization_id == current_user.organization_id,
))
```

---

## Integration System

```python
_SUPPORTED_TYPES = {"jira", "smtp", "resend", "linear", "github_issues", "webhook"}
_TRIGGER_OPTIONS = {"always", "red_only", "manual"}
```

Two private helpers in `reviews.py` centralise email routing:
- `_get_email_integration(db)` — returns first enabled smtp or resend
- `_send_offline_review_email(integration, **kwargs)` — dispatches based on type

---

## Frontend Patterns (vanilla JS)

- Auth token: `localStorage.getItem('rb_token')` → `Authorization: Bearer <token>` header
- API helper: `api(url, options)` in project.html; `apiFetch(url, options)` in system_config.html
- Tab switching: `showTab(id)` — adds/removes `.active` class
- Modal pattern: `.classList.add('active')` / `.classList.remove('active')`
- Toast: `toast(msg, type)` in project.html; `showNotif(msg, type)` in system_config.html

---

## Docker / Config

- Docker host port for DB: **5435** (internal 5432)
- DB credentials: user=`review_user`, db=`reviews_db`, password=`review_password_change_me`
- App runs on port **8000**
- Env var `APP_BASE_URL` kept for non-request contexts only (CLI, background tasks)
- **In route handlers: always derive base URL from `Request` headers** (see design guidelines)

---

## Common Gotchas

1. **`selectinload()` required** on every SQLAlchemy relationship in async context
2. **Delete checklist** blocked if reviews reference it
3. **Resend.com** test uses `GET https://api.resend.com/domains` — does not send email
4. **`declarative_base`** — import from `sqlalchemy.orm`, not deprecated `sqlalchemy.ext.declarative`
5. **ReportLab `Heading`** — not valid; use `Paragraph` with heading styles
6. **Agent `generate_report` node** — parameter must be named `state`, not the class type name
7. **`globalTemplates`** in project.html loaded lazily inside `openAddModal()` — not at page load

---

## Syntax Check Before Completing Tasks

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
