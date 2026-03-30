#!/bin/bash
# 04_create_db.sh - Create Cloud SQL PostgreSQL instance and user

set -e

PROJECT_ID="reviewbot-491619"
REGION="us-central1"
INSTANCE_NAME="reviewbot-db"
DATABASE_NAME="reviews_db"
DATABASE_USER="review_user"
DB_PASSWORD=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --instance-name) INSTANCE_NAME="$2"; shift ;;
        --db-password) DB_PASSWORD="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Usage: $0 --project <PROJECT_ID> --db-password <DB_PASSWORD>"
    echo "  (Optional) --instance-name <NAME> --region <REGION>"
    exit 1
fi

gcloud config set project "$PROJECT_ID"
echo "🚀 Creating Cloud SQL PostgreSQL instance '$INSTANCE_NAME'..."
echo "  (⚠️ Note: This can take 10-20 minutes to complete)"

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

# Create Database if it doesn't exist
echo "  → Database: $DATABASE_NAME"
if gcloud sql databases describe "$DATABASE_NAME" --instance="$INSTANCE_NAME" >/dev/null 2>&1; then
    echo "    - Database already exists."
else
    gcloud sql databases create "$DATABASE_NAME" --instance="$INSTANCE_NAME"
    echo "    - Database created."
fi

# Create User if it doesn't exist
echo "  → User: $DATABASE_USER"
if gcloud sql users list --instance="$INSTANCE_NAME" | grep -q "$DATABASE_USER"; then
    echo "    - User already exists."
else
    gcloud sql users create "$DATABASE_USER" \
        --instance="$INSTANCE_NAME" \
        --password="$DB_PASSWORD"
    echo "    - User created."
fi

echo "✅ Cloud SQL instance and database ready."
echo "   Database URL placeholder (manual setup for Secret Manager):"
echo "   postgresql+asyncpg://$DATABASE_USER:$DB_PASSWORD@/reviews_db?unix_sock=/cloudsql/$PROJECT_ID:$REGION:$INSTANCE_NAME/.s.PGSQL.5432"
