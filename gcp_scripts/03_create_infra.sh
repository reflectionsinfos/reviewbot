#!/bin/bash
# 03_create_infra.sh - Setup Artifact Registry, GCS Bucket, and Secret Manager

set -e

PROJECT_ID="reviewbot-491619"
REGION="us-central1"
BUCKET_NAME="reviewbot-491619-artifacts"
REPO_NAME="reviewbot-repo"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --bucket) BUCKET_NAME="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ] || [ -z "$BUCKET_NAME" ]; then
    echo "Usage: $0 --project <PROJECT_ID> --bucket <BUCKET_NAME>"
    exit 1
fi

gcloud config set project "$PROJECT_ID"
echo "🚀 Initializing GCP Infrastructure in $PROJECT_ID..."

# 1. Artifact Registry
echo "  → Artifact Registry: $REPO_NAME"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
    echo "    - Repository already exists."
else
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for ReviewBot"
    echo "    - Repository created."
fi

# 2. Cloud Storage Bucket
echo "  → Cloud Storage Bucket: $BUCKET_NAME"
if gsutil ls -b "gs://$BUCKET_NAME" >/dev/null 2>&1; then
    echo "    - Bucket already exists."
else
    gsutil mb -l "$REGION" "gs://$BUCKET_NAME"
    echo "    - Bucket created."
fi

# 3. Secret Manager placeholders
SECRETS=(
    "DATABASE_URL"
    "OPENAI_API_KEY"
    "GROQ_API_KEY"
    "SECRET_KEY"
    "ACTIVE_LLM_PROVIDER"
)

for SECRET in "${SECRETS[@]}"; do
    echo "  → Secret Manager: $SECRET"
    if gcloud secrets describe "$SECRET" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "    - Secret '$SECRET' already exists."
    else
        gcloud secrets create "$SECRET" \
            --replication-policy="automatic" \
            --project="$PROJECT_ID"
        echo "    - Secret '$SECRET' created. (Populate manually)"
    fi
done

echo "✅ All infrastructure components are ready."
