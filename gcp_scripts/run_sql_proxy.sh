#!/bin/bash
# run_sql_proxy.sh - Run Cloud SQL Proxy to connect to the DB from local machine

set -e

PROJECT_ID="reviewbot-491619"
REGION="us-central1"
INSTANCE_NAME="reviewbot-db"
PORT="5432"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --instance) INSTANCE_NAME="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 --project <PROJECT_ID> [--instance <NAME>] [--region <REGION>] [--port <PORT>]"
    exit 1
fi

echo "🚀 Starting Cloud SQL Proxy for $INSTANCE_NAME..."
echo "   (Make sure you have downloaded the cloud-sql-proxy binary)"
echo "   Connection string: $PROJECT_ID:$REGION:$INSTANCE_NAME"

# Check if cloud-sql-proxy exists in path
if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "❌ Error: cloud-sql-proxy not found in PATH."
    echo "   Download it from: https://cloud.google.com/sql/docs/postgres/sql-proxy#install"
    exit 1
fi

cloud-sql-proxy "$PROJECT_ID:$REGION:$INSTANCE_NAME" --port "$PORT"
