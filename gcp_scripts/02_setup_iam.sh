#!/bin/bash
# 02_setup_iam.sh - Create Service Account and assign IAM roles for ReviewBot

set -e

PROJECT_ID="reviewbot-491619"
SA_NAME="reviewbot-runtime"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 --project <PROJECT_ID>"
    exit 1
fi

echo "🚀 Creating Service Account: $SA_NAME in $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

if gcloud iam service-accounts describe "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1; then
    echo "  → Service Account already exists."
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="ReviewBot Runtime Service Account"
    echo "  → Service Account created."
fi

ROLES=(
    "roles/cloudsql.client"
    "roles/secretmanager.secretAccessor"
    "roles/storage.objectAdmin"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

for ROLE in "${ROLES[@]}"; do
    echo "  → Assigning $ROLE..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="$ROLE"
done

echo "✅ Service Account and IAM roles configured."
