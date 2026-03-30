#!/bin/bash
# 05_deploy_app.sh - Build image, push to AR, and deploy to Cloud Run

set -e

PROJECT_ID="reviewbot-491619"
REGION="us-central1"
IMAGE_NAME="reviewbot"
REPO_NAME="reviewbot-repo"
SERVICE_NAME="reviewbot-web"
SA_NAME="reviewbot-runtime"
INSTANCE_NAME="reviewbot-db"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --image-name) IMAGE_NAME="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 --project <PROJECT_ID> [--region <REGION>] [--image-name <NAME>]"
    exit 1
fi

gcloud config set project "$PROJECT_ID"
echo "🚀 Deploying ReviewBot to Cloud Run in $PROJECT_ID..."

IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest"

# 1. Build and push image
echo "  → Building image: $IMAGE_TAG..."
docker build -t "$IMAGE_TAG" .

echo "  → Pushing image to Artifact Registry..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
docker push "$IMAGE_TAG"

# 2. Deploy to Cloud Run
echo "  → Deploying service: $SERVICE_NAME..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --region "$REGION" \
    --service-account "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --port 8000 \
    --allow-unauthenticated \
    --add-cloudsql-instances "$PROJECT_ID:$REGION:$INSTANCE_NAME" \
    --set-secrets="DATABASE_URL=DATABASE_URL:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest,ACTIVE_LLM_PROVIDER=ACTIVE_LLM_PROVIDER:latest" \
    --set-env-vars="DEBUG=false,VOICE_ENABLED=true,REQUIRE_HUMAN_APPROVAL=true"

echo "✅ App deployment complete."
echo "   URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')"
