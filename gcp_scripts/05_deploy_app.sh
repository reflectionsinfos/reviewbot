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

# 0. Rebuild reviewbot-cli .whl so the download link on the UI stays current
echo "  -> Rebuilding reviewbot-cli .whl..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_PATH="$(dirname "$REPO_ROOT")/reviewbot-cli"
DOWNLOADS_PATH="$REPO_ROOT/frontend_vanilla/downloads"
if [ -d "$AGENT_PATH" ]; then
    pushd "$AGENT_PATH" > /dev/null
    python -m build --wheel --quiet
    WHL=$(ls dist/reviewbot_cli-*.whl 2>/dev/null | sort -t_ -k3 -V | tail -1)
    if [ -n "$WHL" ]; then
        cp "$WHL" "$DOWNLOADS_PATH/"
        echo "    OK: Copied $(basename "$WHL") to frontend_vanilla/downloads/"
    fi
    # Regenerate source zip (exclude build artefacts)
    ZIP_DEST="$DOWNLOADS_PATH/reviewbot-cli.zip"
    TEMP_DIR=$(mktemp -d)
    rsync -a --exclude=dist --exclude=build --exclude='*.egg-info' --exclude=__pycache__ --exclude=.git \
        "$AGENT_PATH/" "$TEMP_DIR/reviewbot-cli/"
    (cd "$TEMP_DIR" && zip -qr "$ZIP_DEST" reviewbot-cli/)
    rm -rf "$TEMP_DIR"
    echo "    OK: Regenerated reviewbot-cli.zip in frontend_vanilla/downloads/"
    popd > /dev/null
else
    echo "    WARNING: reviewbot-cli not found at $AGENT_PATH - skipping .whl rebuild."
fi

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
    --set-secrets="DATABASE_URL=DATABASE_URL:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,GROQ_API_KEY=GROQ_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest,ACTIVE_LLM_PROVIDER=ACTIVE_LLM_PROVIDER:latest" \
    --set-env-vars="DEBUG=false,VOICE_ENABLED=true,REQUIRE_HUMAN_APPROVAL=true"

echo "✅ App deployment complete."
echo "   URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')"
