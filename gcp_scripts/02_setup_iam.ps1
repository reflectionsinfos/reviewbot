# 02_setup_iam.ps1 - Create Service Account and assign IAM roles for ReviewBot
param (
    [string]$ProjectID = "reviewbot-493320"
)

$ErrorActionPreference = "Stop"
$SA_NAME = "reviewbot-runtime"

Write-Host "🚀 Creating Service Account: $SA_NAME in $ProjectID..." -ForegroundColor Cyan
gcloud config set project "$ProjectID" --quiet

$saEmail = "$SA_NAME@$ProjectID.iam.gserviceaccount.com"
$existingSA = gcloud iam service-accounts list --filter="email:$saEmail" --format="value(email)"

if ($null -ne $existingSA -and $existingSA -eq $saEmail) {
    Write-Host "  → Service Account already exists." -ForegroundColor Gray
} else {
    gcloud iam service-accounts create "$SA_NAME" `
        --display-name="ReviewBot Runtime Service Account" --quiet
    Write-Host "  → Service Account created." -ForegroundColor Gray
}

$roles = @(
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
)

foreach ($role in $roles) {
    Write-Host "  → Assigning $role..." -ForegroundColor Gray
    gcloud projects add-iam-policy-binding "$ProjectID" `
        --member="serviceAccount:$saEmail" `
        --role="$role" --quiet
}

Write-Host "✅ Service Account and IAM roles configured." -ForegroundColor Green
