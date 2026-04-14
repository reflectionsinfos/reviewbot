# cleanup_all.ps1 - Delete all GCP resources created for ReviewBot
param (
    [string]$ProjectID = "reviewbot-493320",
    [string]$Region = "us-central1",
    [string]$ServiceName = "reviewbot-web",
    [string]$SA_NAME = "reviewbot-runtime",
    [string]$InstanceName = "reviewbot-db",
    [string]$RepoName = "reviewbot-repo",
    [string]$BucketName = "reviewbot-493320-artifacts"
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
try {
    gcloud run services delete "$ServiceName" --region="$Region" --quiet
} catch {
    Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
}

# 2. Delete Cloud SQL
Write-Host "🗑️ Deleting Cloud SQL instance: $InstanceName..." -ForegroundColor Gray
try {
    gcloud sql instances delete "$InstanceName" --quiet
} catch {
    Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
}

# 3. Delete Artifact Registry
Write-Host "🗑️ Deleting Artifact Registry: $RepoName..." -ForegroundColor Gray
try {
    gcloud artifacts repositories delete "$RepoName" --location="$Region" --quiet
} catch {
    Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
}

# 4. Delete Service Account
$saEmail = "$SA_NAME@$ProjectID.iam.gserviceaccount.com"
Write-Host "🗑️ Deleting Service Account: $saEmail..." -ForegroundColor Gray
try {
    gcloud iam service-accounts delete "$saEmail" --quiet
} catch {
    Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
}

# 5. Delete Secrets
$secrets = @(
    "DATABASE_URL",
    "SECRET_KEY"
)
foreach ($secret in $secrets) {
    Write-Host "🗑️ Deleting Secret: $secret..." -ForegroundColor Gray
    try {
        gcloud secrets delete "$secret" --quiet
    } catch {
        Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
    }
}

# 6. Delete GCS Bucket
Write-Host "🗑️ Deleting GCS Bucket: gs://$BucketName..." -ForegroundColor Gray
try {
    gsutil rm -r "gs://$BucketName"
} catch {
    Write-Host "    - Skipped (not found or already deleted)." -ForegroundColor DarkGray
}

Write-Host "✅ Cleanup complete." -ForegroundColor Green
