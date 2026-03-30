#!/bin/bash
# 01_enable_apis.sh - Enable required GCP APIs for ReviewBot

set -e

PROJECT_ID="reviewbot-491619"

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

echo "🚀 Enabling required APIs for project: $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

SERVICES=(
    "run.googleapis.com"
    "sqladmin.googleapis.com"
    "artifactregistry.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudbuild.googleapis.com"
    "storage.googleapis.com"
    "iam.googleapis.com"
)

for SERVICE in "${SERVICES[@]}"; do
    echo "  → Enabling $SERVICE..."
    gcloud services enable "$SERVICE"
done

echo "✅ All required APIs are enabled."
