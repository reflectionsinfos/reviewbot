#!/bin/bash
# 04_create_db.sh - Create Cloud SQL PostgreSQL instance and user
# Reads all values from gcp_scripts/.env (DB_PASS, GCP_PROJECT, etc.)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Parse .env (skip comments and blank lines)
while IFS='=' read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    value="${value%%#*}"   # strip inline comments
    value="${value%"${value##*[![:space:]]}"}"  # rtrim whitespace
    export "$key=$value"
done < "$ENV_FILE"

PROJECT_ID="${GCP_PROJECT}"
REGION="${GCP_REGION}"
INSTANCE_NAME="${DB_INSTANCE_NAME}"
DATABASE_NAME="${DB_NAME}"
DATABASE_USER="${DB_USER}"
DB_PASSWORD="${DB_PASS}"

if [ -z "$PROJECT_ID" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Error: GCP_PROJECT and DB_PASS must be set in .env"
    exit 1
fi

gcloud config set project "$PROJECT_ID"
echo "Creating Cloud SQL PostgreSQL instance '$INSTANCE_NAME'..."
echo "  (Note: This can take 10-20 minutes to complete)"

if gcloud sql instances describe "$INSTANCE_NAME" >/dev/null 2>&1; then
    echo "  → Instance already exists."
else
    gcloud sql instances create "$INSTANCE_NAME" \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --root-password="$DB_PASSWORD" \
        --storage-type=HDD \
        --storage-size=10GB \
        --backup-start-time=00:00
    echo "  → Instance created."
fi

# Create Database
echo "  → Database: $DATABASE_NAME"
if gcloud sql databases describe "$DATABASE_NAME" --instance="$INSTANCE_NAME" >/dev/null 2>&1; then
    echo "    - Database already exists."
else
    gcloud sql databases create "$DATABASE_NAME" --instance="$INSTANCE_NAME"
    echo "    - Database created."
fi

# Create User
echo "  → User: $DATABASE_USER"
if gcloud sql users list --instance="$INSTANCE_NAME" | grep -q "^$DATABASE_USER$"; then
    echo "    - User already exists."
else
    gcloud sql users create "$DATABASE_USER" \
        --instance="$INSTANCE_NAME" \
        --password="$DB_PASSWORD"
    echo "    - User created."
fi

echo "Cloud SQL instance and database ready."

# Store DATABASE_URL in Secret Manager
echo "  → Storing DATABASE_URL in Secret Manager..."
DB_URL="postgresql+asyncpg://${DATABASE_USER}:${DB_PASSWORD}@/${DATABASE_NAME}?host=/cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
printf '%s' "$DB_URL" | gcloud secrets versions add DATABASE_URL --data-file=- --project="$PROJECT_ID"
echo "  → DATABASE_URL secret updated in Secret Manager."
echo ""
echo "   DATABASE_URL saved to Secret Manager as 'DATABASE_URL:latest'."
echo "   Connection: postgresql+asyncpg://${DATABASE_USER}:***@/${DATABASE_NAME}?host=/cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
