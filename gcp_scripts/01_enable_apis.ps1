# 01_enable_apis.ps1 - Enable required GCP APIs for ReviewBot
param (
    [string]$ProjectID = "reviewbot-493320"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Enabling required APIs for project: $ProjectID..." -ForegroundColor Cyan
gcloud config set project "$ProjectID" --quiet

$services = @(
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com"
)

foreach ($service in $services) {
    Write-Host "  → Enabling $service..." -ForegroundColor Gray
    gcloud services enable "$service" --quiet
}

Write-Host "✅ All required APIs are enabled." -ForegroundColor Green
