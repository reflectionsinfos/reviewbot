#!/bin/bash
# cleanup_all.sh - Delete all GCP resources created for ReviewBot

set -e

PROJECT_ID="reviewbot-491619"
REGION="us-central1"
SERVICE_NAME="reviewbot-web"
SA_NAME="reviewbot-runtime"
INSTANCE_NAME="reviewbot-db"
REPO_NAME="reviewbot-repo"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 --project <PROJECT_ID> [--region <REGION>]"
    exit 1
fi

echo "⚠️ WARNING: This will DESTRUCTIVELY delete all ReviewBot resources in $PROJECT_ID."
read -p "Are you sure you want to proceed? (y/N) " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Aborted."
    exit 1
fi

gcloud config set project "$PROJECT_ID"

# 1. Delete Cloud Run
echo "🗑️ Deleting Cloud Run service: $SERVICE_NAME..."
gcloud run services delete "$SERVICE_NAME" --region="$REGION" --quiet || true

# 2. Delete Cloud SQL
echo "🗑️ Deleting Cloud SQL instance: $INSTANCE_NAME..."
gcloud sql instances delete "$INSTANCE_NAME" --quiet || true

# 3. Delete Artifact Registry
echo "🗑️ Deleting Artifact Registry: $REPO_NAME..."
gcloud artifacts repositories delete "$REPO_NAME" --location="$REGION" --quiet || true

# 4. Delete Service Account
echo "🗑️ Deleting Service Account: $SA_NAME..."
gcloud iam service-accounts delete "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" --quiet || true

# 5. Delete Secrets
SECRETS=(
    "DATABASE_URL"
    "OPENAI_API_KEY"
    "GROQ_API_KEY"
    "SECRET_KEY"
    "ACTIVE_LLM_PROVIDER"
)
for SECRET in "${SECRETS[@]}"; do
    echo "🗑️ Deleting Secret: $SECRET..."
    gcloud secrets delete "$SECRET" --quiet || true
done

echo "✅ Cleanup complete."
