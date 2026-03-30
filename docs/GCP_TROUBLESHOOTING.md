# 🚀 ReviewBot GCP Command Cheat Sheet

This guide provides the most frequently used commands for managing, troubleshooting, and deploying the ReviewBot infrastructure on GCP.

---

## 🏗️ 1. Cloud Run (Application Layer)

### 📋 Service Operations
```powershell
# List all services
gcloud run services list --project=reviewbot-491619 --region=us-central1

# Describe active environment variables and settings
gcloud run services describe reviewbot-web --region=us-central1 --format="value(spec.template.spec.containers[0].env)"

# Update environment variables (without redeploying code)
gcloud run services update reviewbot-web --region=us-central1 --set-env-vars="DATABASE_URL=...,SECRET_KEY=..."
```

### 🔍 Troubleshooting & Logs
```powershell
# Read last 50 logs for the service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=reviewbot-web" --limit=50 --format="value(textPayload)"

# Stream logs in real-time (Tail)
gcloud alpha run services logs tail reviewbot-web --project=reviewbot-491619 --region=us-central1

# Find why a container failed to start (Look for 'Revision is not ready' details)
gcloud run revisions list --service=reviewbot-web --region=us-central1 --limit=5
```

---

## 🗄️ 2. Cloud SQL (Database Layer)

### 📊 Database Management
```powershell
# List all databases on the instance
gcloud sql databases list --instance=reviewbot-db

# Recreate a fresh sandbox database
gcloud sql databases delete reviews_db_dev1 --instance=reviewbot-db --quiet
gcloud sql databases create reviews_db_dev1 --instance=reviewbot-db --quiet

# List database users
gcloud sql users list --instance=reviewbot-db
```

### 📥 Import / Export operations
```powershell
# Import SQL file from Cloud Storage to a specific database
gcloud sql import sql reviewbot-db gs://reviewbot-491619-artifacts/05_data.sql --database=reviews_db_dev1 --quiet

# Monitor import progress (Operation ID can be found from the result of the import command)
gcloud sql operations list --instance=reviewbot-db --limit=5
```

---

## 🪣 3. Cloud Storage (Artifacts & Backups)

### 📁 Bucket Operations
```powershell
# List all objects in the bucket
gsutil ls gs://reviewbot-491619-artifacts/

# Upload a local file to GCP for importing
gsutil cp scripts/db/02_tables.sql gs://reviewbot-491619-artifacts/

# Download a backup to local machine
gsutil cp gs://reviewbot-491619-artifacts/05_data.sql ./backup_from_gcp.sql
```

---

## 🛠️ 4. Debugging & Connectivity

### 🚦 Connectivity Testing
```powershell
# Check if the API status endpoint is responding
curl.exe -s https://reviewbot-web-128263129038.us-central1.run.app/api/status

# Check the health endpoint
curl.exe -s https://reviewbot-web-128263129038.us-central1.run.app/health
```

### 🔐 Auth & Account Management
```powershell
# List all authenticated accounts
gcloud auth list

# Login to a new account (opens browser)
gcloud auth login

# Set the active account (if multiple are logged in)
gcloud config set account 'your-email@gmail.com'

# Login for application use (local development credentials)
gcloud auth application-default login

# --- Using Named Configurations (Switching Contexts) ---

# Create a new named configuration (e.g., for work vs personal)
gcloud config configurations create reviewbot-config

# Switch to a specific configuration
gcloud config configurations activate default

# List all local configurations
gcloud config configurations list

# Delete a configuration
gcloud config configurations delete reviewbot-config
```

### 🚩 Project & Config
```powershell
# Check currently active account and project
gcloud config list

# Set default project for current session
gcloud config set project reviewbot-491619
```

---

## 💡 Quick Tips for Errors:

| Error Message | Likely Root Cause | Fix |
| :--- | :--- | :--- |
| `UndefinedTableError: relation "users" does not exist` | Connected to wrong DB or Import was skipped. | Verify `DATABASE_URL` matches the database where you imported scripts. |
| `Revision is not ready` | Startup probe failed or DB connection string is invalid. | Check `gcloud logging read ...` for Python exceptions. |
| `PostgresConnectionError` | Socket path is wrong or IAM permissions missing. | Ensure `?host=/cloudsql/...` is used for socket connections. |
| `Invalid credentials` sign-in error | mismatch in `SECRET_KEY` between local/cloud. | Run `gcloud run services update ... --set-env-vars="SECRET_KEY=..."`. |
