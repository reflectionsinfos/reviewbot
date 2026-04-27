# ReviewBot — Codebase Knowledge File

> Maintained by Claude Code. Read this before exploring the repo to avoid re-deriving context.
> Last updated: 2026-04-27

---

## Project Layout

```
reviewbot/
├── main.py                          # FastAPI entry point + lifespan startup
├── app/
│   ├── api/routes/
│   │   ├── auth.py                  # JWT login/register; get_current_user dependency
│   │   ├── projects.py              # Project CRUD + checklist upload
│   │   ├── checklists.py            # Checklist CRUD; GET /templates/global
│   │   ├── reviews.py               # Review sessions, offline flow, voice, uploads
│   │   ├── reports.py               # Report management + approval workflow
│   │   └── integrations.py          # Admin CRUD for IntegrationConfig + test/dispatch
│   ├── agents/review_agent/
│   │   ├── agent.py                 # LangGraph ReviewAgent class + node functions
│   │   └── states.py                # ReviewState TypedDict
│   ├── core/config.py               # Pydantic Settings (all env vars, including APP_BASE_URL)
│   ├── db/session.py                # Async engine, get_db, init_db
│   ├── models.py                    # All SQLAlchemy ORM models
│   └── services/
│       ├── checklist_parser.py
│       ├── checklist_optimizer.py
│       ├── excel_offline_exporter.py
│       ├── excel_response_parser.py
│       ├── report_generator.py
│       ├── template_manager.py
│       ├── voice_interface.py
│       └── integrations/
│           ├── base.py              # DispatchItem, DispatchResult, mask_secret
│           ├── dispatcher.py        # run_auto_dispatch, run_manual_dispatch
│           ├── email_smtp.py        # SMTP email via aiosmtplib; send_offline_review_email, send_summary_email, test_connection
│           ├── email_resend.py      # Resend.com HTTP API; same send_* / test_connection signature
│           ├── jira.py
│           ├── linear.py
│           ├── github_issues.py
│           └── webhook.py
├── frontend_vanilla/
│   ├── project.html                 # Project detail page (checklist tabs, reviews, offline flow)
│   ├── system_config.html           # AI Models + System Settings + Email/SMTP tabs
│   ├── offline-review.html          # Token-gated reviewer portal
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
| `User` | `role` ∈ {reviewer, manager, admin} |
| `Project` | `domain`, `tech_stack` (JSON), `stakeholders` (JSON), `org_id` |
| `Checklist` | `type` ∈ {delivery, technical}, `is_global`, `project_id` (null = global template) |
| `ChecklistItem` | `area`, `weight`, `expected_evidence` |
| `Review` | `review_type` ∈ {online, offline}, `status`, `upload_token`, `due_date`, `assigned_reviewer_email` |
| `ReviewResponse` | `rag_status` ∈ {red, amber, green, na} |
| `Report` | `compliance_score`, `approval_status` |
| `IntegrationConfig` | `type`, `is_enabled`, `trigger_on`, `config_json` (JSON), `include_advisories` |
| `IntegrationDispatch` | dispatch log per job+integration |

---

## Integration System

### Supported Types (`integrations.py`)
```python
_SUPPORTED_TYPES = {"jira", "smtp", "resend", "linear", "github_issues", "webhook"}
_TRIGGER_OPTIONS = {"always", "red_only", "manual"}
```

### Email dispatch pattern in `reviews.py`
Two private helpers centralise email routing:
```python
async def _get_email_integration(db) -> IntegrationConfig | None:
    # Returns first enabled smtp or resend (resend preferred alphabetically)

async def _send_offline_review_email(integration, **kwargs) -> DispatchResult:
    # Dispatches to email_resend or email_smtp based on integration.type
```

### email_resend.py config schema
```json
{
  "api_key": "re_xxxx",
  "from_address": "ReviewBot <bot@yourdomain.com>",
  "recipients": ["team@company.com"],
  "include_project_stakeholders": true
}
```

### email_smtp.py config schema
```json
{
  "host": "smtp.example.com",
  "port": 587,
  "username": "user@example.com",
  "password": "secret",
  "use_tls": true,
  "from_address": "ReviewBot <noreply@example.com>",
  "recipients": ["team@example.com"]
}
```

---

## Frontend Patterns (vanilla JS)

- Auth token: `localStorage.getItem('rb_token')` → `Authorization: Bearer <token>` header
- API helper: `api(url, options)` in project.html; `apiFetch(url, options)` in system_config.html
- Tab switching: `showTab(id)` — adds/removes `.active` class; each tab has a lazy-load trigger
- Modal pattern: `.classList.add('active')` / `.classList.remove('active')` (system_config modals use `.modal-overlay.active`)  
- Toast/notif: `showNotif(msg, type)` in system_config; `toast(msg, type)` in project.html

### project.html state variables
| Variable | Purpose |
|----------|---------|
| `currentProjectId` | Selected project |
| `currentChecklistId` | Active checklist tab |
| `globalTemplates` | Cached global templates (loaded lazily in `openAddModal`) |
| `pendingDeleteChecklistId` | ID awaiting confirmation in delete modal |

---

## API Routes Summary

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/auth/login` | Returns `{access_token}` |
| GET/POST | `/api/projects/` | List / create projects |
| POST | `/api/projects/{id}/upload-checklist` | Excel import |
| GET | `/api/checklists/templates/global` | Global template list |
| GET/DELETE | `/api/checklists/{id}` | Get / soft-delete checklist |
| GET/POST | `/api/reviews/` | List / create reviews |
| POST | `/api/reviews/{id}/start` | Start AI agent |
| POST | `/api/reviews/{id}/resend-email` | Resend offline invitation |
| GET | `/api/integrations/` | List all integrations (admin) |
| POST | `/api/integrations/` | Create integration (admin) |
| PATCH | `/api/integrations/{id}` | Update integration (admin) |
| DELETE | `/api/integrations/{id}` | Delete integration (admin) |
| POST | `/api/integrations/{id}/test` | Test connectivity |
| POST | `/api/integrations/{id}/dispatch/{job_id}` | Manual dispatch |

---

## Docker / Config

- Docker host port for DB: **5435** (internal 5432)
- DB credentials: user=`review_user`, db=`reviews_db`, password=`review_password_change_me`
- App runs on port **8000** (`http://localhost:8000`)
- Env var `APP_BASE_URL` used for offline review deep-link generation

---

## Common Gotchas

1. **`selectinload()` required** on every SQLAlchemy relationship in async context — omitting causes `MissingGreenlet`
2. **Delete checklist** (`DELETE /api/checklists/{id}`) is blocked if reviews reference the checklist
3. **Resend.com** test uses `GET https://api.resend.com/domains` — does not send an email
4. **SMTP** uses `aiosmtplib` via `asyncio.to_thread` wrapper pattern
5. **`globalTemplates`** in project.html is loaded lazily inside `openAddModal()` — not at page load
