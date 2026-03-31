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

The agent package is **not yet on PyPI**. Two install methods are available:

#### Option A — Install from .whl (recommended)

Download the pre-built wheel from the ReviewBot UI (AI Review page → CLI AGENT tab → **Download .whl**), then:

```bash
pip install reviewbot_agent-0.1.0-py3-none-any.whl
```

The `.whl` file is served from the ReviewBot server at:
```
/frontend_vanilla/downloads/reviewbot_agent-0.1.0-py3-none-any.whl
```

To rebuild the wheel after code changes:
```bash
cd c:\projects\reviewbot-agent
python -m build --wheel
# → dist/reviewbot_agent-0.1.0-py3-none-any.whl

# Copy to reviewbot server downloads folder
cp dist/reviewbot_agent-0.1.0-py3-none-any.whl \
   c:\projects\reviewbot\frontend_vanilla\downloads\
```

#### Option B — Install from GitHub (once repo is published)

Once `reviewbot-agent` is pushed to GitHub:
```bash
pip install git+https://github.com/reflectionsinfos/reviewbot-agent.git
```

To set up the remote (one-time, after creating the GitHub repo):
```bash
cd c:\projects\reviewbot-agent
git remote add origin https://github.com/reflectionsinfos/reviewbot-agent.git
git push -u origin main
```

#### Option C — Install from source zip

Download the zip from the ReviewBot UI → CLI AGENT tab → **Download Source (.zip)**, then:
```bash
unzip reviewbot-agent.zip && cd reviewbot-agent && pip install .
```

#### After installing

```bash
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

---

## GCP Deployment — Full Reference

### GCP Resources

| Resource | Name / ID |
|----------|-----------|
| Project ID | `reviewbot-491619` |
| Region | `us-central1` |
| Cloud Run service | `reviewbot-web` |
| Cloud SQL instance | `reviewbot-db` (PostgreSQL 15, `db-f1-micro`, 10 GB HDD) |
| Database | `reviews_db` |
| DB user | `review_user` |
| Artifact Registry | `reviewbot-repo` (Docker, `us-central1`) |
| GCS bucket | `reviewbot-491619-artifacts` |
| Service Account | `reviewbot-runtime@reviewbot-491619.iam.gserviceaccount.com` |

### IAM Roles for `reviewbot-runtime`

| Role | Purpose |
|------|---------|
| `roles/cloudsql.client` | Connect to Cloud SQL |
| `roles/storage.objectAdmin` | Read/write GCS bucket |
| `roles/secretmanager.secretAccessor` | Read secrets |
| `roles/logging.logWriter` | Write Cloud Logging |
| `roles/run.invoker` | Invoke Cloud Run (for internal calls) |

---

### First-Time Setup (run scripts in order)

All scripts are in `gcp_scripts\`. Run from PowerShell:

```powershell
cd c:\projects\reviewbot

# Step 1 — Enable required GCP APIs
.\gcp_scripts\01_enable_apis.ps1
# Enables: Cloud Run, Cloud SQL, Artifact Registry, Cloud Build,
#          Secret Manager, Cloud Storage, IAM

# Step 2 — Create service account + assign IAM roles
.\gcp_scripts\02_setup_iam.ps1

# Step 3 — Create Artifact Registry, GCS bucket, Secret Manager placeholders
.\gcp_scripts\03_create_infra.ps1
# Creates secrets: DATABASE_URL, OPENAI_API_KEY, GROQ_API_KEY,
#                  SECRET_KEY, ACTIVE_LLM_PROVIDER

# Step 4 — Create Cloud SQL instance + database + user
.\gcp_scripts\04_create_db.ps1
# Creates: PostgreSQL 15, db-f1-micro, 10 GB HDD
# Takes ~5 minutes

# Step 5 — Build & deploy to Cloud Run
.\gcp_scripts\05_deploy_app.ps1
# Reads env.non-prod.gcp, builds via Cloud Build, deploys to Cloud Run
```

---

### `env.non-prod.gcp` Configuration

This file is git-ignored. Required variables:

```env
# LLM
ACTIVE_LLM_PROVIDER=groq        # or openai, anthropic, google, etc.
GROQ_API_KEY=your-groq-key

# Database — filled by 04_create_db.ps1 output
DB_USER=review_user
DB_PASS=<your-db-password>
DB_NAME=reviews_db

# Security
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">

# IMPORTANT: do NOT set APP_ENV=local here — it would expose dev credentials
```

**Cloud SQL connection URL** (used inside Cloud Run — Unix socket, not TCP):
```
postgresql+asyncpg://review_user:<pass>@/reviews_db?host=/cloudsql/reviewbot-491619:us-central1:reviewbot-db
```

---

### Re-deploy After Code Changes

```powershell
.\gcp_scripts\05_deploy_app.ps1
```

The script:
1. Reads credentials from `env.non-prod.gcp`
2. Builds the Docker image via Cloud Build (pushes to Artifact Registry)
3. Deploys to Cloud Run with `--allow-unauthenticated`, port 8000
4. Attaches Cloud SQL instance for Unix socket connection

---

### Local Access to Cloud SQL (SQL Proxy)

To connect DBeaver or psql to the GCP database from your Windows machine:

```powershell
.\gcp_scripts\run_sql_proxy.ps1
# Runs: cloud-sql-proxy reviewbot-491619:us-central1:reviewbot-db --port 5432
```

Then connect DBeaver to: `localhost:5432 / reviews_db / review_user`

---

### gcloud Cheat Sheet

**Cloud Run**
```bash
# View service details
gcloud run services describe reviewbot-web --region us-central1

# Stream live logs
gcloud run services logs tail reviewbot-web --region us-central1

# List revisions
gcloud run revisions list --service reviewbot-web --region us-central1

# Force redeploy latest image (no code change)
gcloud run services update reviewbot-web --region us-central1 --image \
  us-central1-docker.pkg.dev/reviewbot-491619/reviewbot-repo/reviewbot:latest

# Set/update an env var
gcloud run services update reviewbot-web --region us-central1 \
  --set-env-vars ACTIVE_LLM_PROVIDER=openai
```

**Cloud SQL**
```bash
# Check instance status
gcloud sql instances describe reviewbot-db

# Connect via Cloud SQL Auth Proxy (interactive psql)
cloud-sql-proxy reviewbot-491619:us-central1:reviewbot-db --port 5432
# then: psql -h 127.0.0.1 -U review_user -d reviews_db

# Run a migration (from inside Cloud Run shell or via proxy)
docker-compose exec app alembic upgrade head   # (local)
# For GCP: gcloud run jobs create ... or exec via proxy + psql

# List databases
gcloud sql databases list --instance reviewbot-db

# Restart instance
gcloud sql instances restart reviewbot-db
```

**Artifact Registry**
```bash
# List images
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/reviewbot-491619/reviewbot-repo

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**Secret Manager**
```bash
# List secrets
gcloud secrets list --project reviewbot-491619

# View a secret value
gcloud secrets versions access latest --secret SECRET_KEY --project reviewbot-491619

# Update a secret
echo -n "new-value" | gcloud secrets versions add GROQ_API_KEY --data-file=-
```

**GCS**
```bash
# List bucket contents
gsutil ls gs://reviewbot-491619-artifacts/

# Copy a file up
gsutil cp ./report.pdf gs://reviewbot-491619-artifacts/reports/
```

**Auth / Account**
```bash
# Check active account
gcloud auth list

# Switch project
gcloud config set project reviewbot-491619

# Generate application default credentials (for local SDK calls)
gcloud auth application-default login
```

---

### Cloud Run Operations

```bash
# Check current deployed URL
gcloud run services describe reviewbot-web --region us-central1 \
  --format "value(status.url)"

# View recent logs (last 50 lines)
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=reviewbot-web" \
  --limit 50 --format "table(timestamp,textPayload)"

# Scale to zero (stop billing when idle)
gcloud run services update reviewbot-web --region us-central1 --min-instances 0

# Roll back to previous revision
gcloud run services update-traffic reviewbot-web --region us-central1 \
  --to-revisions PREV_REVISION=100
```

---

### Teardown (Destructive — Deletes Everything)

```powershell
.\gcp_scripts\cleanup_all.ps1
```

Deletes in order: Cloud Run service → Cloud SQL instance → Artifact Registry → Service Account → Secret Manager secrets. **Prompts for confirmation before each step.**

> **Warning:** Deleting the Cloud SQL instance is irreversible. All database data will be lost unless you have a backup.

---

### GCP Troubleshooting

| Error | Fix |
|-------|-----|
| `PERMISSION_DENIED` on deploy | Run `gcloud auth login` and check `reviewbot-runtime` IAM roles |
| Cloud Run can't reach Cloud SQL | Verify `--add-cloudsql-instances` flag in deploy script and SA has `cloudsql.client` role |
| `connection refused` via SQL Proxy | Check `cloud-sql-proxy` is running and using the correct instance connection name |
| Image push fails | Run `gcloud auth configure-docker us-central1-docker.pkg.dev` |
| `APP_ENV=local` accidentally set in GCP | Remove it from `env.non-prod.gcp` — it exposes dev credentials |
| Cloud Run returns 404 on all routes | Check startup logs — likely a missing env var or DB connection failure |
| Secret not found at runtime | Verify secret name matches exactly and SA has `secretmanager.secretAccessor` |

Full troubleshooting guide: `docs/GCP_TROUBLESHOOTING.md`
Full architecture plan: `docs/gcp_deployment_plan.md`

---

## Future Enhancements / Roadmap

Requirements captured here for planning. These are **not yet implemented**.

### CLI Agent Distribution

| # | Requirement | Notes |
|---|-------------|-------|
| UB-1 | Publish `reviewbot-agent` to PyPI | Enables `pip install reviewbot-agent` on any machine without downloading a file. Needs a PyPI account, API token, and version tagging workflow. |
| UB-2 | Push `reviewbot-agent` to GitHub | Create `reflectionsinfos/reviewbot-agent` repo, set remote, push. Enables `pip install git+https://github.com/reflectionsinfos/reviewbot-agent.git` and standard open-source contribution flow. |
| UB-3 | Auto-rebuild `.whl` on deploy | Add a CI/CD step in `05_deploy_app.ps1` (or a GitHub Action) to rebuild and copy the `.whl` to `frontend_vanilla/downloads/` whenever `reviewbot-agent` source changes, so the download link on the UI always serves the latest version. |
| UB-4 | Version the `.whl` download link | Instead of a hardcoded filename (`reviewbot_agent-0.1.0-py3-none-any.whl`), serve via a stable redirect URL like `/downloads/reviewbot-agent-latest.whl` so the UI never needs updating on version bumps. |

### VS Code Extension Distribution

| # | Requirement | Notes |
|---|-------------|-------|
| UB-5 | Publish VS Code extension to VS Code Marketplace | Currently distributed as a manual `.vsix` download. Marketplace publish requires an Azure DevOps publisher account. |
| UB-6 | Auto-rebuild `.vsix` on deploy | Similar to UB-3 — rebuild and copy the `.vsix` to `frontend_vanilla/downloads/` on deploy. |

### Authentication & Security

| # | Requirement | Notes |
|---|-------------|-------|
| UB-7 | OAuth / SSO login | Replace email+password with Google/Microsoft OAuth for enterprise deployments. |
| UB-8 | API key authentication | Allow service accounts (CI/CD pipelines) to authenticate with a long-lived API key instead of a short-lived JWT. |
| UB-9 | Role-based checklist access | Restrict which checklists a user/role can run reviews against. |

### Review Features

| # | Requirement | Notes |
|---|-------------|-------|
| UB-10 | Watch mode in CLI agent (`--watch`) | Re-run review automatically when source files change. Stub exists in `cli.py` but not implemented. |
| UB-11 | Incremental / diff reviews | Review only files changed since last review (git diff), not the full codebase. Reduces LLM cost and review time. |
| UB-12 | GitHub Actions integration | Pre-built Action that runs `reviewbot review` on every PR and posts results as a PR comment. |
| UB-13 | Webhook notifications | POST review completion + compliance score to a configurable webhook (Slack, Teams, Jira). |

### Platform

| # | Requirement | Notes |
|---|-------------|-------|
| UB-14 | Multi-tenancy / organisations | Isolate projects, users, and checklists by organisation. Currently all users share the same namespace. |
| UB-15 | Scheduled autonomous reviews | Cron-triggered reviews against a repo (e.g., nightly scan of main branch). |
| UB-16 | Cloud SQL to Cloud SQL Auth Proxy in production | Replace direct socket connection with Auth Proxy sidecar for better secret isolation. |
