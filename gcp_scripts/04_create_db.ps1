# 04_create_db.ps1 - Create Cloud SQL PostgreSQL instance and user
param (
    [string]$ProjectID = "reviewbot-493320",
    [string]$Region = "us-central1",
    [string]$InstanceName = "reviewbot-db",
    [string]$DatabaseName = "reviews_db",
    [string]$DatabaseUser = "review_user",
    [SecureString]$DatabasePassword = $null
)

if ($null -eq $DatabasePassword -or $DatabasePassword.Length -eq 0) {
    Write-Host "Error: --DatabasePassword is required." -ForegroundColor Red
    exit 1
}

# Convert SecureString to plain text for gcloud CLI usage
$plainPassword = [System.Net.NetworkCredential]::new("", $DatabasePassword).Password

$ErrorActionPreference = "Stop"

Write-Host "Creating Cloud SQL PostgreSQL instance '$InstanceName'..." -ForegroundColor Cyan
Write-Host "  (Note: This can take 10-20 minutes to complete)" -ForegroundColor Yellow
gcloud config set project "$ProjectID" --quiet

$instanceExists = $false
try {
    $null = gcloud sql instances describe "$InstanceName" --project="$ProjectID" 2>$null
    $instanceExists = $?
} catch {
    $instanceExists = $false
}

if ($instanceExists) {
    Write-Host "  → Instance already exists." -ForegroundColor Gray
} else {
    gcloud sql instances create "$InstanceName" `
        --database-version=POSTGRES_15 `
        --tier=db-f1-micro `
        --region="$Region" `
        --root-password="$plainPassword" `
        --storage-type=HDD `
        --storage-size=10GB `
        --backup-start-time=00:00 --quiet
    Write-Host "  → Instance created." -ForegroundColor Gray
}

# Create Database if it doesn't exist
Write-Host "  → Database: $DatabaseName" -ForegroundColor Gray
$dbExists = $false
try {
    $null = gcloud sql databases describe "$DatabaseName" --instance="$InstanceName" 2>$null
    $dbExists = ($LASTEXITCODE -eq 0)
} catch {
    $dbExists = $false
}
if ($dbExists) {
    Write-Host "    - Database already exists." -ForegroundColor Gray
} else {
    gcloud sql databases create "$DatabaseName" --instance="$InstanceName" --quiet
    Write-Host "    - Database created." -ForegroundColor Gray
}

# Create User if it doesn't exist
Write-Host "  → User: $DatabaseUser" -ForegroundColor Gray
$userExists = $false
try {
    $userList = gcloud sql users list --instance="$InstanceName" --format="value(name)" 2>$null
    $userExists = ($userList -contains $DatabaseUser)
} catch {
    $userExists = $false
}
if ($userExists) {
    Write-Host "    - User already exists." -ForegroundColor Gray
} else {
    gcloud sql users create "$DatabaseUser" `
        --instance="$InstanceName" `
        --password="$plainPassword" --quiet
    Write-Host "    - User created." -ForegroundColor Gray
}

Write-Host "Cloud SQL instance and database ready." -ForegroundColor Green

# Populate DATABASE_URL secret via temp file (avoids plaintext in logs/history)
Write-Host "  → Storing DATABASE_URL in Secret Manager..." -ForegroundColor Gray
$dbUrl = "postgresql+asyncpg://${DatabaseUser}:${plainPassword}@/${DatabaseName}?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}"
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $False
    [System.IO.File]::WriteAllText($tempFile, $dbUrl, $utf8NoBom)
    gcloud secrets versions add DATABASE_URL --data-file="$tempFile" --project="$ProjectID" --quiet
    Write-Host "  → DATABASE_URL secret updated in Secret Manager." -ForegroundColor Gray
} finally {
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
}
Write-Host ""
Write-Host "   DATABASE_URL saved to Secret Manager as 'DATABASE_URL:latest'." -ForegroundColor Green
Write-Host "   Connection: postgresql+asyncpg://${DatabaseUser}:***@/${DatabaseName}?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}" -ForegroundColor Gray
