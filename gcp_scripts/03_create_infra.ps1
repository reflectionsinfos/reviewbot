# 03_create_infra.ps1 - Setup Artifact Registry, GCS Bucket, and Secret Manager
param (
    [string]$ProjectID = "reviewbot-493320",
    [string]$Region = "us-central1",
    [string]$BucketName = "reviewbot-493320-artifacts",
    [string]$RepoName = "reviewbot-repo"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Initializing GCP Infrastructure in $ProjectID..." -ForegroundColor Cyan
gcloud config set project "$ProjectID" --quiet

# 1. Artifact Registry
Write-Host "  → Artifact Registry: $RepoName" -ForegroundColor Gray
$repoExists = gcloud artifacts repositories list --filter="name:$RepoName" --location="$Region" --format="value(name)"
if ($null -ne $repoExists -and $repoExists.Contains($RepoName)) {
    Write-Host "    - Repository already exists." -ForegroundColor Gray
} else {
    gcloud artifacts repositories create "$RepoName" `
        --repository-format=docker `
        --location="$Region" `
        --description="Docker repository for ReviewBot" --quiet
    Write-Host "    - Repository created." -ForegroundColor Gray
}

# 2. Cloud Storage Bucket
Write-Host "  → Cloud Storage Bucket: $BucketName" -ForegroundColor Gray
$bucketExists = $false
try {
    $null = gsutil ls -b "gs://$BucketName" 2>&1
    $bucketExists = $true
} catch {
    $bucketExists = $false
}

if ($bucketExists) {
    Write-Host "    - Bucket already exists." -ForegroundColor Gray
} else {
    gsutil mb -l "$Region" "gs://$BucketName"
    Write-Host "    - Bucket created." -ForegroundColor Gray
}

# 3. Secret Manager placeholders
$secrets = @(
    "DATABASE_URL",
    "SECRET_KEY",
    "OPENAI_API_KEY",
    "ACTIVE_LLM_PROVIDER"
)

foreach ($secret in $secrets) {
    Write-Host "  → Secret Manager: $secret" -ForegroundColor Gray
    $secretExists = $false
    try {
        $null = gcloud secrets describe "$secret" --project="$ProjectID" 2>$null
        $secretExists = $?
    } catch {
        $secretExists = $false
    }

    if ($secretExists) {
        Write-Host "    - Secret '$secret' already exists." -ForegroundColor Gray
    } else {
        gcloud secrets create "$secret" `
            --replication-policy="automatic" `
            --project="$ProjectID" --quiet
        Write-Host "    - Secret '$secret' created. (Populate manually)" -ForegroundColor Gray
    }
}

Write-Host "✅ All infrastructure components are ready." -ForegroundColor Green
