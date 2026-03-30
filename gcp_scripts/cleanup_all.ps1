# cleanup_all.ps1 - Delete all GCP resources created for ReviewBot
param (
    [string]$ProjectID = "reviewbot-491619",
    [string]$Region = "us-central1",
    [string]$ServiceName = "reviewbot-web",
    [string]$SA_NAME = "reviewbot-runtime",
    [string]$InstanceName = "reviewbot-db",
    [string]$RepoName = "reviewbot-repo"
)

$ErrorActionPreference = "Stop"

Write-Host "⚠️ WARNING: This will DESTRUCTIVELY delete all ReviewBot resources in $ProjectID." -ForegroundColor Red
$confirm = Read-Host "Are you sure you want to proceed? (y/N)"
if ($confirm -notmatch "^[yY](es)?$") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 1
}

gcloud config set project "$ProjectID" --quiet

# 1. Delete Cloud Run
Write-Host "🗑️ Deleting Cloud Run service: $ServiceName..." -ForegroundColor Gray
gcloud run services delete "$ServiceName" --region="$Region" --quiet

# 2. Delete Cloud SQL
Write-Host "🗑️ Deleting Cloud SQL instance: $InstanceName..." -ForegroundColor Gray
gcloud sql instances delete "$InstanceName" --quiet

# 3. Delete Artifact Registry
Write-Host "🗑️ Deleting Artifact Registry: $RepoName..." -ForegroundColor Gray
gcloud artifacts repositories delete "$RepoName" --location="$Region" --quiet

# 4. Delete Service Account
$saEmail = "$SA_NAME@$ProjectID.iam.gserviceaccount.com"
Write-Host "🗑️ Deleting Service Account: $saEmail..." -ForegroundColor Gray
gcloud iam service-accounts delete "$saEmail" --quiet

# 5. Delete Secrets
$secrets = @(
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "SECRET_KEY",
    "ACTIVE_LLM_PROVIDER"
)
foreach ($secret in $secrets) {
    Write-Host "🗑️ Deleting Secret: $secret..." -ForegroundColor Gray
    gcloud secrets delete "$secret" --quiet
}

Write-Host "✅ Cleanup complete." -ForegroundColor Green
