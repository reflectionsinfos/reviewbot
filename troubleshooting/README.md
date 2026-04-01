# ReviewBot — Troubleshooting & Support Guide

Quick index for support and ops staff. Start here, then jump to the relevant section.

## Key Reference

| Item | Value |
|------|-------|
| GCP Project | `reviewbot-491619` |
| Region | `us-central1` |
| Cloud Run Service | `reviewbot-web` |
| Cloud SQL Instance | `reviewbot-db` |
| Database | `reviews_db` |
| DB User | `review_user` |
| Artifact Registry | `reviewbot-repo` |
| Service Account | `reviewbot-runtime` |
| App Port | `8000` |
| Local DB Port | `5435` (Docker maps here to avoid conflict with local PostgreSQL) |

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Local development overrides |
| `env.local` | Local-specific settings (APP_ENV=local enables dev auto-login) |
| `env.non-prod.gcp` | GCP non-prod environment settings |

## Secrets in GCP Secret Manager

| Secret Name | Description |
|------------|-------------|
| `DATABASE_URL` | Cloud SQL connection string (unix socket) |
| `OPENAI_API_KEY` | OpenAI API key |
| `GROQ_API_KEY` | Groq API key |
| `SECRET_KEY` | JWT signing secret |
| `ACTIVE_LLM_PROVIDER` | Active LLM: `openai`, `anthropic`, `groq`, `google`, `qwen`, `azure` |

## Guides

| Guide | When to Use |
|-------|-------------|
| [docker.md](docker.md) | Local Docker Desktop — logs, restart, exec, cleanup |
| [local-dev.md](local-dev.md) | Run without Docker, env setup, log file locations |
| [gcp.md](gcp.md) | Cloud Run logs, Cloud SQL access, Secret Manager, redeploy |
| [database.md](database.md) | SQL queries for diagnosing users, reviews, reports, checklists |
| [api.md](api.md) | Health check, auth, and curl examples for all major endpoints |
| [known-issues.md](known-issues.md) | Common errors with root causes and fixes |

## Quick Health Check

```bash
# Local Docker
curl http://localhost:8000/health

# GCP (get URL first)
gcloud run services describe reviewbot-web --region=us-central1 \
  --format='value(status.url)' --project=reviewbot-491619
curl https://<URL>/health
```

Expected response: `{"status": "healthy"}`
