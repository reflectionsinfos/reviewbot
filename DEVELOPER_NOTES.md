# ReviewBot — Developer Notes

Practical reference for day-to-day local development. See [README.md](README.md) for full deployment and API docs.

---

## Quick Start (Local)

```bash
cd c:\projects\reviewbot
docker-compose up --build       # first time
docker-compose up -d            # subsequent starts
```

App: http://localhost:8000/ui — auto-logs in as `admin@reviewbot.com` (see below).

---

## Auto-Login in Local Development

When `APP_ENV=local` (already set in `env.local`), all pages auto-fill and auto-submit the login form on load. No credentials to type.

**How it works:**
1. Frontend calls `GET /api/auth/dev-config` on page load
2. Server returns email + password from `env.local` (only when `APP_ENV=local`)
3. Frontend fills the form and calls `login()` automatically
4. The endpoint returns `404` in production — nothing leaks

**Credentials (in `env.local` only — never in code):**
```env
APP_ENV=local
DEV_AUTO_LOGIN_EMAIL=admin@reviewbot.com
DEV_AUTO_LOGIN_PASSWORD=Reflect@123
```

**To disable auto-login locally:** remove or comment out `APP_ENV=local` in `env.local`.

---

## Environment Files

| File | Purpose | Committed? |
|------|---------|-----------|
| `env.local` | Local Docker development | No (git-ignored) |
| `env.non-prod.gcp` | GCP Cloud Run deployment | No (git-ignored) |
| `.env` | Fallback (legacy) | No (git-ignored) |

Load order: `.env` → `env.non-prod.gcp` → `env.local` (later files win).

**Never set `APP_ENV=local` in `env.non-prod.gcp`** — it would expose dev credentials.

---

## User Management

Admin users can manage all accounts from the header dropdown → **Manage Users**:

| Action | Details |
|--------|---------|
| Add User | Enter name, email, role → auto-generates a 12-char password to share privately |
| Reset Password | Generates a new password shown once — copy before closing |
| Activate / Deactivate | Toggle access without deleting |
| Delete | Permanent — cannot delete your own account |

### Change your own password

Header dropdown → **Change Password** — requires current password, min 8 chars, live strength meter.

### Reset a password via SQL (emergency)

```bash
# 1. Generate bcrypt hash for new password
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('NewPassword123!'))"

# 2. Update in DB
docker-compose exec db psql -U review_user -d reviews_db -c \
  "UPDATE users SET hashed_password = '<hash>' WHERE email = 'user@example.com';"
```

Passwords are stored as **bcrypt hashes** in the `hashed_password` column — they cannot be reversed.

---

## Database

| Context | Host | Port | DB | User | Password |
|---------|------|------|----|------|---------|
| Inside Docker (app) | `db` | `5432` | `reviews_db` | `review_user` | `review_password_change_me` |
| DBeaver / external | `localhost` | `5435` | `reviews_db` | `review_user` | `review_password_change_me` |

### Useful queries

```sql
-- List all users
SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC;

-- Check autonomous review jobs
SELECT id, project_id, status, compliance_score, created_at FROM autonomous_review_jobs ORDER BY created_at DESC LIMIT 20;

-- See checklist item counts per checklist
SELECT c.id, c.name, COUNT(ci.id) as items FROM checklists c
LEFT JOIN checklist_items ci ON ci.checklist_id = c.id
GROUP BY c.id, c.name ORDER BY c.id;
```

### Migrations

```bash
# After changing models.py
docker-compose exec app alembic revision --autogenerate -m "description"
docker-compose exec app alembic upgrade head

# Check current version
docker-compose exec app alembic current

# Roll back one step
docker-compose exec app alembic downgrade -1
```

---

## API Routes Overview

| Router | Prefix | File |
|--------|--------|------|
| Auth + user self-service | `/api/auth` | `app/api/routes/auth.py` |
| Admin user management | `/api/admin` | `app/api/routes/users.py` |
| Projects & checklists | `/api/projects`, `/api/checklists` | `projects.py`, `checklists.py` |
| Conversational reviews | `/api/reviews` | `reviews.py` |
| Autonomous reviews | `/api/autonomous-reviews` | `autonomous_reviews.py` |
| CLI + VS Code bridge | `/api/v1/agent/scan` | `agent.py` |
| Reports | `/api/reports` | `reports.py` |
| LLM config | `/api/llm-configs` | `llm_configs.py` |
| System settings | `/api/settings` | `settings.py` |

### Auth endpoints

```
POST  /api/auth/register            Register new user
POST  /api/auth/login               Get JWT token (OAuth2 form)
GET   /api/auth/me                  Current user info
POST  /api/auth/change-password     Change own password
GET   /api/auth/dev-config          Dev auto-login creds (APP_ENV=local only)
```

### Admin endpoints (role=admin required)

```
GET    /api/admin/users                    List all users
POST   /api/admin/users                    Create user + return generated password
POST   /api/admin/users/{id}/reset-password   Reset password + return new generated password
PATCH  /api/admin/users/{id}               Update role or is_active
DELETE /api/admin/users/{id}               Delete user (not self)
```

---

## Password Generation

Admin-created and reset passwords use `secrets.choice()` with:

```python
alphabet = string.ascii_letters + string.digits + "!@#$^"
```

- 12 characters
- Guaranteed: 1 uppercase, 1 lowercase, 1 digit, 1 special char
- No `%` (URL-safe — avoids issues with form-encoded submissions)
- Example: `Xk9@mP2vRt7!`

---

## Frontend Structure

All pages share:
- `frontend_vanilla/components/header.html` — sticky nav, user dropdown, Change Password modal, Manage Users modal (admin only)
- `frontend_vanilla/components/header_loader.js` — header JS, `updateSharedUserInfo()`, `tryDevAutoLogin()`, all modal logic

| Page | Route | File |
|------|-------|------|
| Dashboard | `/` or `/ui` | `home.html` or `index.html` |
| AI Review | `/ui` | `index.html` |
| Projects | `/projects-ui` | `project.html` |
| History | `/history` | `history.html` |
| Global Templates | `/globals` | `globals.html` |
| System Config | `/system-config` | `system_config.html` |
| How It Works | `/documentation` | `documentation.html` |

---

## LLM Provider Switching

Set `ACTIVE_LLM_PROVIDER` in your env file:

| Provider | Env var | Free tier? |
|----------|---------|-----------|
| `openai` | `OPENAI_API_KEY` | No |
| `anthropic` | `ANTHROPIC_API_KEY` | No |
| `groq` | `GROQ_API_KEY` | Yes |
| `google` | `GOOGLE_API_KEY` | Yes (limited) |
| `qwen` | `QWEN_API_KEY` | Yes (limited) |
| `azure` | `AZURE_OPENAI_API_KEY` | No |

Groq is recommended for local development (free, fast).

---

## Client Tools

### VS Code Extension

Download from the AI Review page → **VS CODE EXTENSION** button. Install via:
```bash
code --install-extension reviewbot-vscode-0.0.1.vsix
```
Server URL: `https://reviewbot-web-128263129038.us-central1.run.app` (or `http://localhost:8000` locally).

### CLI Agent

```bash
pip install reviewbot-agent

# Login (no prior auth needed — this IS the auth step)
reviewbot login --server http://localhost:8000

# Run a review (IDs pre-filled on the AI Review page when you select project+checklist)
reviewbot review \
  --project-id <id> \
  --checklist-id <id> \
  --source-path ./my-project \
  --output ./report.md

reviewbot status   # check login state
reviewbot logout   # clear token
```

Token stored at `~/.reviewbot/config.json`, expires after 8 hours.

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Auto-login not working locally | Check `APP_ENV=local` is set in `env.local` and the container has restarted |
| `401 Unauthorized` on all requests | Token expired — re-login (or auto-login will trigger on page refresh) |
| `MissingGreenlet` crash | Add `selectinload()` before accessing SQLAlchemy relationships in async context |
| Port `8000` or `5435` in use | `netstat -ano \| findstr :8000` — change `APP_PORT` in env file |
| DB data wiped | You ran `docker-compose down -v` — re-seed with `python scripts/migrate_xlsx_to_db.py` |
| `%` in generated password causes login issue | Fixed — generator now uses `!@#$^` (no `%`) |

---

## Production (GCP)

| | |
|---|---|
| URL | https://reviewbot-web-128263129038.us-central1.run.app |
| Deploy | `.\gcp_scripts\05_deploy_app.ps1` |
| Config | `env.non-prod.gcp` |
| DB | Cloud SQL (PostgreSQL 15) — `reviewbot-db` instance |
| `APP_ENV` | Not set (defaults to `production`) — auto-login disabled |
