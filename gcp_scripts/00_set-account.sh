#!/usr/bin/env bash
# Switch gcloud active account to mallikarjun.sh@gmail.com and configure
# Docker auth for Artifact Registry for reviewbot deployment.
#
# Usage: ./gcp_scripts/set-account.sh

set -euo pipefail

ACCOUNT="mallikarjun.sh@gmail.com"
GCP_PROJECT="reviewbot-491619"      # TODO: replace with your GCP project ID
REGION="us-central1"                   # TODO: adjust region if needed
ARTIFACT_REGISTRY_HOST="${REGION}-docker.pkg.dev"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REVIEWBOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Switching gcloud account to $ACCOUNT..."
gcloud config set account "$ACCOUNT"

echo "Setting GCP project to $GCP_PROJECT..."
gcloud config set project "$GCP_PROJECT"

echo "Fetching access token..."
TOKEN=$(gcloud auth print-access-token)

echo "Configuring Docker auth for Artifact Registry ($ARTIFACT_REGISTRY_HOST)..."
echo "$TOKEN" | docker login -u oauth2accesstoken --password-stdin "https://${ARTIFACT_REGISTRY_HOST}"

echo ""
echo "Reviewbot directory: $REVIEWBOT_DIR"
echo "Done. Active account: $(gcloud config get account 2>/dev/null)"
echo "Active project:       $(gcloud config get project 2>/dev/null)"
echo "Note: Access tokens expire in ~1 hour. Re-run this script before rebuilding Docker images."
