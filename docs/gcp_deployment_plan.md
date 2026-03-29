# ReviewBot GCP Deployment Plan

## 1. Objective

Deploy ReviewBot web application and PostgreSQL database on GCP with production-grade reliability.

This plan assumes:
- You already have a GCP account.
- The "server filesystem access for project scanning" feature is removed.
- Autonomous review uses agent upload mode (API-driven), not local folder mounts.

## 2. Target Architecture

- **Cloud Run (Web API)**: FastAPI app serving UI, REST, and WebSocket endpoints.
- **Cloud Run (Worker)**: Background job processor for autonomous reviews (triggered asynchronously).
- **Cloud SQL for PostgreSQL**: Primary relational database.
- **Cloud Storage**: Persistent storage for uploads, reports, and voice artifacts.
- **Cloud Tasks**: Reliable async job queue from API -> worker.
- **Artifact Registry**: Container image storage.
- **Secret Manager**: Secrets and API keys.
- **Cloud Logging + Monitoring + Alerting**: Observability and incident response.

## 3. Current-State Constraints to Address Before Go-Live

1. Local-folder scanning path must be disabled/removed:
   - `/api/autonomous-reviews/` currently uses local path scanning in orchestrator.
   - Keep and prioritize `/api/v1/agent/scan/*` flow for cloud-safe scans.

2. In-memory caches are not multi-instance safe:
   - `agent.py` uses in-memory `_file_cache` and `_file_requests`.
   - Replace with Redis (Memorystore) or database tables.

3. Local file writes are not durable in Cloud Run:
   - Current report/upload/voice paths are local disk based.
   - Move artifacts to Cloud Storage and store object URIs in DB.

4. Migration workflow is incomplete:
   - Repo contains `alembic/versions` but no `alembic.ini`/`env.py`.
   - Define a single production schema migration mechanism before launch.

## 4. Required Application Changes

### 4.1 Autonomous Review Flow

- Disable local source-path scan endpoint behavior (or return `410 Gone` for deprecated mode).
- Route autonomous scans through agent-upload API only.
- Replace path-based UI messaging (`/host-projects/...`) with agent workflow instructions.

### 4.2 Async Processing

- Replace request-lifecycle `BackgroundTasks` with Cloud Tasks.
- Add worker endpoint/service to consume queue messages and run review jobs.
- Add idempotency checks to avoid duplicate processing.

### 4.3 Persistent File Storage

- Introduce storage abstraction layer:
  - `put_object`, `get_signed_url`, `delete_object`.
- Store `gs://bucket/key` (or object key) in DB instead of local file paths.
- Update report download endpoint to stream from GCS or return signed URL.

### 4.4 Shared State for Agent Upload Mode

- Move agent file-content cache + pending requests to:
  - Option A (recommended): Postgres tables (simple, durable).
  - Option B: Redis (fast, ephemeral + TTL).

### 4.5 Configuration and Runtime

- Ensure server starts with Cloud Run port:
  - `uvicorn main:app --host 0.0.0.0 --port ${PORT}`.
- Production defaults:
  - `DEBUG=false`
  - Restrict CORS to actual frontend domains
  - Rotate strong `SECRET_KEY`

### 4.6 Database Migration Strategy

- Add missing Alembic runtime config (`alembic.ini`, `alembic/env.py`) or define equivalent migration runner.
- Deploy migration as a controlled pre-deploy step (Cloud Run Job recommended).
- Keep `init_db()` only for non-destructive bootstrap safeguards, not main schema evolution.

## 5. GCP Resource Plan

## 5.1 Project and Region

- Project ID: `<PROJECT_ID>`
- Region: `us-central1` (recommended baseline; adjust for latency/compliance).

## 5.2 APIs to Enable

- `run.googleapis.com` (Cloud Run)
- `sqladmin.googleapis.com` (Cloud SQL)
- `artifactregistry.googleapis.com` (Artifact Registry)
- `secretmanager.googleapis.com` (Secret Manager)
- `cloudbuild.googleapis.com` (Cloud Build)
- `cloudtasks.googleapis.com` (Cloud Tasks)
- `vpcaccess.googleapis.com` (Serverless VPC Access, if private networking used)
- `storage.googleapis.com` (Cloud Storage)
- `monitoring.googleapis.com` and `logging.googleapis.com`

## 5.3 Service Accounts and IAM

### Runtime service account (`reviewbot-runtime@...`)

- `roles/cloudsql.client`
- `roles/secretmanager.secretAccessor`
- `roles/storage.objectAdmin` (or finer-grained bucket IAM)
- `roles/logging.logWriter`
- `roles/monitoring.metricWriter`
- `roles/cloudtasks.enqueuer` (web service only)

### Deploy service account (`reviewbot-deployer@...`)

- `roles/run.admin`
- `roles/artifactregistry.writer`
- `roles/iam.serviceAccountUser` (on runtime SA)
- `roles/cloudbuild.builds.editor`

### Worker invocation

- Restrict worker endpoint to authenticated internal callers only.
- Allow only Cloud Tasks service identity to invoke worker.

## 5.4 Cloud SQL (PostgreSQL)

- Create PostgreSQL instance (`POSTGRES_15+`).
- Configure:
  - Automatic backups enabled
  - Point-in-time recovery enabled
  - Deletion protection enabled
  - HA optional for phase 1, recommended for phase 2
- Create DB/user:
  - DB: `reviews_db`
  - User: `review_user`
- Use strong generated password in Secret Manager.

## 5.5 Cloud Storage

- Bucket: `<PROJECT_ID>-reviewbot-artifacts`
- Suggested folder prefixes:
  - `uploads/`
  - `reports/markdown/`
  - `reports/pdf/`
  - `voice/`
- Enable object lifecycle policy (delete old temp audio, stale uploads).

## 5.6 Cloud Tasks

- Queue: `reviewbot-jobs`
- Configure retry + exponential backoff:
  - Max attempts: 5-10
  - Max retry duration: 1-2 hours
- Dead-letter queue recommended for failed tasks.

## 6. Environment and Secrets

Store as Secret Manager secrets (not plain env files):

- `DATABASE_URL` (Cloud SQL connection)
- `SECRET_KEY`
- `OPENAI_API_KEY` (and/or other LLM provider keys)
- `ELEVENLABS_API_KEY` (if used)
- `ACTIVE_LLM_PROVIDER`

Non-secret env variables:

- `DEBUG=false`
- `VOICE_ENABLED=true|false`
- `REQUIRE_HUMAN_APPROVAL=true|false`
- `UPLOAD_DIR`, `REPORTS_DIR` (logical values only if abstraction layer still references them)
- `GCS_BUCKET=<bucket-name>`
- `APP_NAME`, `APP_VERSION`

## 7. CI/CD and Release Pipeline

## 7.1 Build and Push

1. Build container image from `Dockerfile`.
2. Push to Artifact Registry:
   - `us-central1-docker.pkg.dev/<PROJECT_ID>/reviewbot/reviewbot:<git-sha>`

## 7.2 Deploy Sequence

1. Run DB migration job (Cloud Run Job) against Cloud SQL.
2. Deploy worker service (no public traffic).
3. Deploy web service.
4. Smoke test health and critical APIs.
5. Shift traffic to latest revision (or canary rollout 10% -> 100%).

## 7.3 Rollback

- Cloud Run rollback to previous stable revision.
- DB changes must be backward-compatible for at least one release window.
- Keep migration downgrade scripts where safe.

## 8. Networking and Security

- Use Cloud SQL connector integration from Cloud Run.
- Restrict ingress:
  - Web service: `all` or `internal-and-cloud-load-balancing` depending on exposure model.
  - Worker service: `internal` + IAM-authenticated invoke only.
- Use HTTPS only (managed by Cloud Run and optional Load Balancer/custom domain).
- Enable Cloud Armor if exposed through load balancer.
- Add rate limiting and auth hardening for public endpoints.

## 9. Observability and SRE Baseline

- Structured JSON logging with correlation IDs:
  - `request_id`, `job_id`, `project_id`
- Monitoring dashboards:
  - Request latency/p95
  - Error rate
  - Cloud SQL CPU/connections
  - Task queue depth and failure count
- Alerts:
  - 5xx rate threshold
  - Worker failure spike
  - Queue age > threshold
  - Cloud SQL storage or CPU alerts

## 10. Validation and Test Plan

## 10.1 Pre-Deployment Checks

- Unit + integration tests passing.
- Migration dry-run in staging.
- Artifact upload/download integration test with GCS.
- Agent-mode autonomous review E2E in staging.

## 10.2 Post-Deployment Smoke Tests

- `GET /health` returns healthy.
- Auth login/register flows.
- Project/checklist CRUD.
- Agent upload flow:
  - upload metadata
  - upload file-content
  - start job
  - retrieve results
- Report download works from GCS-backed artifacts.

## 10.3 Non-Functional Validation

- Cold start acceptable.
- Concurrent jobs process correctly.
- Restart/redeploy does not lose job state or file pointers.

## 11. Phased Execution Plan

### Phase 1: Cloud Foundation
- Create GCP resources (Cloud SQL, Artifact Registry, Storage, Secrets, baseline Cloud Run).
- Deploy web app with DB connectivity.

### Phase 2: Cloud-Safe App Refactor
- Remove local filesystem scan path.
- Move caches to shared persistence.
- Move file artifacts to GCS.
- Add migration runner.

### Phase 3: Async Worker Reliability
- Integrate Cloud Tasks + worker service.
- Add retries/idempotency/dead-letter handling.

### Phase 4: Hardening and Go-Live
- Observability, alerts, CORS/auth tightening.
- Load tests and failure drills.
- Production cutover.

## 12. Production Readiness Exit Criteria

- No feature depends on server local filesystem.
- No critical state kept in process memory only.
- All DB schema changes are migration-controlled and repeatable.
- Artifacts persist in Cloud Storage and remain downloadable across deploys.
- Async jobs are queue-backed and resilient to restarts.
- Monitoring + alerting + rollback path validated.

## 13. Suggested Naming Convention

- Cloud Run web service: `reviewbot-web`
- Cloud Run worker service: `reviewbot-worker`
- Cloud SQL instance: `reviewbot-pg`
- Artifact Registry repo: `reviewbot`
- Cloud Tasks queue: `reviewbot-jobs`
- Storage bucket: `<PROJECT_ID>-reviewbot-artifacts`

