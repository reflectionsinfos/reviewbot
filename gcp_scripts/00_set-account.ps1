# Switch gcloud active account to mallikarjun.sh@gmail.com and configure
# Docker auth for Artifact Registry for reviewbot deployment.
#
# Usage: .\gcp_scripts\set-account.ps1

$ErrorActionPreference = "Stop"

$ACCOUNT               = "mallikarjun.sh@gmail.com"
$GCP_PROJECT           = "reviewbot-491619"      # TODO: replace with your GCP project ID
$REGION                = "us-central1"               # TODO: adjust region if needed
$ARTIFACT_REGISTRY_HOST = "$REGION-docker.pkg.dev"

$SCRIPT_DIR    = Split-Path -Parent $MyInvocation.MyCommand.Path
$REVIEWBOT_DIR = Split-Path -Parent $SCRIPT_DIR

Write-Host "Switching gcloud account to $ACCOUNT..."
gcloud config set account $ACCOUNT

Write-Host "Setting GCP project to $GCP_PROJECT..."
gcloud config set project $GCP_PROJECT

Write-Host "Fetching access token..."
$TOKEN = gcloud auth print-access-token

Write-Host "Configuring Docker auth for Artifact Registry ($ARTIFACT_REGISTRY_HOST)..."
$TOKEN | docker login -u oauth2accesstoken --password-stdin "https://$ARTIFACT_REGISTRY_HOST"

Write-Host ""
Write-Host "Reviewbot directory: $REVIEWBOT_DIR"

$ErrorActionPreference = "Continue"
$CURRENT_ACCOUNT = gcloud config get account 2>$null
$CURRENT_PROJECT = gcloud config get project 2>$null
Write-Host "Done. Active account: $CURRENT_ACCOUNT"
Write-Host "Active project:       $CURRENT_PROJECT"
Write-Host "Note: Access tokens expire in ~1 hour. Re-run this script before rebuilding Docker images."
