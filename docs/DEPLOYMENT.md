# ReviewBot — Deployment Guide

## Table of Contents

1. [Local — Without Docker](#1-local--without-docker)
2. [Local — With Docker](#2-local--with-docker)
3. [Remote — GCP Cloud Run](#3-remote--gcp-cloud-run)
4. [Data Reset (Dev / Pre-Deploy)](#4-data-reset-dev--pre-deploy)
5. [Environment Variable Reference](#5-environment-variable-reference)
6. [Page & API Routes](#6-page--api-routes)

---

## 1. Local — Without Docker

Run the FastAPI app directly against a local PostgreSQL instance.
Useful for fast iteration — no image rebuild on every code change.

### 1.1 Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.11+   |
| PostgreSQL  | 15+     |

### 1.2 Create the Database

Connect to your local PostgreSQL as a superuser and run:

```sql
CREATE ROLE review_user LOGIN PASSWORD 'review_password_change_me';
CREATE DATABASE reviews_db OWNER review_user;
GRANT ALL PRIVILEGES ON DATABASE reviews_db TO review_user;
\c reviews_db
GRANT ALL ON SCHEMA public TO review_user;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### 1.3 Install Dependencies

```bash
cd reviewbot
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 1.4 Configure Environment

```bash
# Copy example and edit
cp .env.example .env
```

Minimum `.env` for local development:

```env
APP_ENV=local
DEBUG=true

DATABASE_URL=postgresql+asyncpg://review_user:review_password_change_me@localhost:5432/reviews_db

SECRET_KEY=local-dev-secret-key-change-me

# At least one LLM key required
OPENAI_API_KEY=sk-...
ACTIVE_LLM_PROVIDER=openai

VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true
```

> **Tip:** Set `APP_ENV=local` and `DEV_AUTO_LOGIN_EMAIL` / `DEV_AUTO_LOGIN_PASSWORD`
> in `.env` to skip the login screen during local testing.

### 1.5 Start the App

```bash
uvicorn main:app --reload --port 8000
```

The app creates all database tables automatically on first start via `init_db()`.

### 1.6 Verify

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Dashboard |
| `http://localhost:8000/docs` | Swagger API docs |
| `http://localhost:8000/health` | Health check |

### 1.7 DBeaver Connection (local PG)

| Field    | Value                     |
|----------|---------------------------|
| Host     | `localhost`               |
| Port     | `5432`                    |
| Database | `reviews_db`              |
| User     | `review_user`             |
| Password | `review_password_change_me` |

---

## 2. Local — With Docker

Runs the app and PostgreSQL together via Docker Compose.
Closest to production behaviour without needing a cloud account.

### 2.1 Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Compose (Linux)

### 2.2 Configure Environment

```bash
cp .env.docker .env
```

Edit `.env` and set at least your LLM key:

```env
OPENAI_API_KEY=sk-...
ACTIVE_LLM_PROVIDER=openai
SECRET_KEY=change-this-in-production
```

### 2.3 Start

```bash
docker compose up --build
```

First build takes a few minutes. Subsequent starts are fast:

```bash
docker compose up
```

### 2.4 Verify

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Dashboard |
| `http://localhost:8000/docs` | Swagger API docs |
| `http://localhost:8000/health` | Health check |

### 2.5 DBeaver Connection (Docker PG)

The DB port is **5435** (avoids conflict with any local PostgreSQL on port 5432).

| Field    | Value                     |
|----------|---------------------------|
| Host     | `localhost`               |
| Port     | `5435`                    |
| Database | `reviews_db`              |
| User     | `review_user`             |
| Password | `review_password_change_me` |

### 2.6 Common Commands

```powershell
# Stop without wiping data
docker compose down

# Full reset — destroys DB volume (fresh start)
docker compose down -v

# Tail app logs
docker logs -f reviewbot-app

# Tail DB logs
docker logs -f reviewbot-db

# Open a shell inside the app container
docker exec -it reviewbot-app bash

# Open psql inside the DB container
docker exec -it reviewbot-db psql -U review_user -d reviews_db
```

### 2.7 Rebuild After Code Changes

Source code is mounted as a volume in dev mode (`- .:/app:cached`),
so `--reload` picks up Python changes automatically.

If you change `requirements.txt` or the `Dockerfile`, rebuild:

```bash
docker compose build reviewbot-app && docker compose up -d reviewbot-app
```

---

## 3. Remote — GCP Cloud Run

ReviewBot deploys to **GCP Cloud Run** (web service) + **Cloud SQL** (PostgreSQL 15).
Automation scripts live in `gcp_scripts/`.

### 3.1 Prerequisites

- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- GCP project with billing enabled
- Docker installed locally (for image build)

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
```

### 3.2 Step-by-Step First Deployment

#### Step 1 — Enable GCP APIs

```bash
./gcp_scripts/01_enable_apis.sh --project <PROJECT_ID>
```

Enables: Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, Cloud Build, Cloud Storage.

#### Step 2 — Set Up IAM

```bash
./gcp_scripts/02_setup_iam.sh --project <PROJECT_ID>
```

Creates `reviewbot-runtime` service account with least-privilege roles.

#### Step 3 — Create Infrastructure

```bash
./gcp_scripts/03_create_infra.sh --project <PROJECT_ID> --bucket <PROJECT_ID>-reviewbot-artifacts
```

Creates Artifact Registry repo, Cloud Storage bucket, and Secret Manager placeholders.

#### Step 4 — Provision the Database

```bash
./gcp_scripts/04_create_db.sh \
  --project <PROJECT_ID> \
  --instance-name reviewbot-db \
  --db-password <SECURE_PASSWORD>
```

Creates Cloud SQL PostgreSQL 15 instance, `reviews_db` database and `review_user`.

#### Step 5 — Store Secrets in Secret Manager

```bash
# Required
gcloud secrets create DATABASE_URL   --data-file=- <<< "postgresql+asyncpg://review_user:<PASSWORD>@/<DB_NAME>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>"
gcloud secrets create SECRET_KEY     --data-file=- <<< "<generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'>"
gcloud secrets create OPENAI_API_KEY --data-file=- <<< "sk-..."

# Optional LLM providers
gcloud secrets create ANTHROPIC_API_KEY --data-file=- <<< "..."
gcloud secrets create GROQ_API_KEY      --data-file=- <<< "..."
```

#### Step 6 — Build and Deploy

```bash
./gcp_scripts/05_deploy_app.sh \
  --project <PROJECT_ID> \
  --region us-central1 \
  --image-name reviewbot
```

This builds the Docker image, pushes to Artifact Registry, and deploys to Cloud Run.

#### Step 7 — Smoke Test

```bash
curl https://<CLOUD_RUN_URL>/health
```

Expected response:
```json
{"status": "healthy", "database": "connected", "voice_enabled": true, "human_approval_required": true}
```

### 3.3 Re-Deploy (Subsequent Releases)

```bash
# Build new image
gcloud builds submit --tag us-central1-docker.pkg.dev/<PROJECT_ID>/reviewbot/reviewbot:latest

# Deploy new revision
gcloud run deploy reviewbot-web \
  --image us-central1-docker.pkg.dev/<PROJECT_ID>/reviewbot/reviewbot:latest \
  --region us-central1
```

### 3.4 Connect to Cloud SQL Locally (Proxy)

Use Cloud SQL Auth Proxy to run migrations or DBeaver against the remote DB:

```bash
./gcp_scripts/run_sql_proxy.sh --project <PROJECT_ID> --instance reviewbot-db
```

Then connect DBeaver at `localhost:5432` with the Cloud SQL credentials.

### 3.5 Tear Down All GCP Resources

```bash
./gcp_scripts/cleanup_all.sh --project <PROJECT_ID>
```

---

## 4. Data Reset (Dev / Pre-Deploy)

Use this when you need a clean slate — wiping all review data, projects,
organizations, and checklists while **preserving user accounts, LLM configs,
system settings, and integration configs**.

> This is the correct approach during development when you change the org
> model or global template structure. For a complete wipe including users,
> use `docker compose down -v` instead.

### 4.1 The Reset Script

The script lives at `scripts/reset_dev_data.sql`.

It deletes rows in strict FK-dependency order, resets all integer sequences
to 1, and nullifies `users.organization_id` (so no dangling FK after orgs
are wiped).

**What is cleared:**

| Cleared | Preserved |
|---------|-----------|
| `organizations` | `users` |
| `projects` | `llm_configs` |
| `checklists` + `checklist_items` | `system_settings` |
| `reviews` + `review_responses` | `integration_configs` |
| `reports` + `report_approvals` | |
| `autonomous_review_jobs` + results + audits | |
| `review_instances`, schedules, triggers | |
| `self_review_sessions`, gaps, analytics | |
| `integration_dispatches` | |

### 4.2 Run Against Local Docker

```powershell
# PowerShell (Windows) — note: use Get-Content pipe, not <
Get-Content scripts/reset_dev_data.sql | docker exec -i reviewbot-db psql -U review_user -d reviews_db
```

```bash
# Mac / Linux / Git Bash
docker exec -i reviewbot-db psql -U review_user -d reviews_db < scripts/reset_dev_data.sql
```

### 4.3 Run Against Local PostgreSQL (No Docker)

```bash
psql -h localhost -p 5432 -U review_user -d reviews_db -f scripts/reset_dev_data.sql
```

### 4.4 Run Against GCP Cloud SQL (Via Proxy)

Start the Cloud SQL Auth Proxy first (see §3.4), then:

```bash
psql -h localhost -p 5432 -U review_user -d reviews_db -f scripts/reset_dev_data.sql
```

Or pipe via `gcloud sql connect`:

```bash
gcloud sql connect reviewbot-db --user=review_user --database=reviews_db < scripts/reset_dev_data.sql
```

### 4.5 Verify the Reset

The script prints a row-count table at the end:

```
 table                    | count
--------------------------+-------
 autonomous_review_jobs   |     0
 checklist_items          |     0
 checklists               |     0
 integration_configs      |     2   ← preserved
 llm_configs              |     1   ← preserved
 organizations            |     0
 projects                 |     0
 reports                  |     0
 reviews                  |     0
 system_settings          |     5   ← preserved
 users                    |     3   ← preserved
```

### 4.6 Full Wipe (Including Users)

If you need to reset everything including user accounts:

```powershell
# Docker — destroys the entire DB volume and recreates
docker compose down -v
docker compose up
```

---

## 5. Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | asyncpg connection string |
| `SECRET_KEY` | ✅ | (insecure default) | JWT signing secret — rotate in production |
| `ACTIVE_LLM_PROVIDER` | ✅ | `openai` | `openai` \| `anthropic` \| `google` \| `groq` \| `qwen` \| `azure` |
| `OPENAI_API_KEY` | ✅* | — | Required if provider is `openai` |
| `ANTHROPIC_API_KEY` | ✅* | — | Required if provider is `anthropic` |
| `GROQ_API_KEY` | ✅* | — | Required if provider is `groq` |
| `GOOGLE_API_KEY` | ✅* | — | Required if provider is `google` |
| `QWEN_API_KEY` | ✅* | — | Required if provider is `qwen` |
| `AZURE_OPENAI_API_KEY` | ✅* | — | Required if provider is `azure` |
| `ELEVENLABS_API_KEY` | ❌ | — | Optional — voice TTS |
| `APP_ENV` | ❌ | `production` | `local` enables dev auto-login |
| `DEV_AUTO_LOGIN_EMAIL` | ❌ | — | Auto-login email (only when `APP_ENV=local`) |
| `DEV_AUTO_LOGIN_PASSWORD` | ❌ | — | Auto-login password (only when `APP_ENV=local`) |
| `DEBUG` | ❌ | `true` | Set `false` in production |
| `VOICE_ENABLED` | ❌ | `true` | Enable voice STT/TTS |
| `REQUIRE_HUMAN_APPROVAL` | ❌ | `true` | Require manager approval for reports |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `480` | JWT token lifetime (8 h) |
| `CHROMA_PERSIST_DIR` | ❌ | `./chroma_db` | ChromaDB vector store path |
| `UPLOAD_DIR` | ❌ | `./uploads` | File upload storage path |
| `REPORTS_DIR` | ❌ | `./reports` | Generated report storage path |

*Only one LLM key is required — the one matching `ACTIVE_LLM_PROVIDER`.

---

## 6. Page & API Routes

### Frontend Pages

| URL | Page |
|-----|------|
| `http://localhost:8000/` | Dashboard / Home |
| `http://localhost:8000/globals` | Global Templates |
| `http://localhost:8000/projects-ui` | Projects & Checklists |
| `http://localhost:8000/ui` | Autonomous Review UI |
| `http://localhost:8000/history` | Report History |
| `http://localhost:8000/documentation` | How It Works |
| `http://localhost:8000/system-config` | System Configuration |

### API

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/docs` | Swagger UI (all endpoints) |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/api/status` | JSON status |
