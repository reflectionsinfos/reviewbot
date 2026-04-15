# 04_create_db.ps1 - Create Cloud SQL PostgreSQL instance and user
# Reads all values from gcp_scripts/.env (DB_PASS, GCP_PROJECT, etc.)

$ErrorActionPreference = "Stop"

# ── Load .env ──────────────────────────────────────────────────────────────
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Error: .env file not found at $envFile" -ForegroundColor Red
    exit 1
}

$envVars = @{}
Get-Content $envFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' -and $_.Trim() -ne '' } | ForEach-Object {
    $line  = $_.Trim()
    $eqIdx = $line.IndexOf('=')
    if ($eqIdx -gt 0) {
        $key   = $line.Substring(0, $eqIdx).Trim()
        $value = $line.Substring($eqIdx + 1).Trim().Trim('"').Trim("'")
        $envVars[$key] = $value
    }
}

$ProjectID     = $envVars["GCP_PROJECT"]
$Region        = $envVars["GCP_REGION"]
$InstanceName  = $envVars["DB_INSTANCE_NAME"]
$DatabaseName  = $envVars["DB_NAME"]
$DatabaseUser  = $envVars["DB_USER"]
$plainPassword = $envVars["DB_PASS"]

if ([string]::IsNullOrEmpty($plainPassword)) {
    Write-Host "Error: DB_PASS is not set in .env file." -ForegroundColor Red
    exit 1
}

# ── Create SQL instance ────────────────────────────────────────────────────
Write-Host "Creating Cloud SQL PostgreSQL instance '$InstanceName'..." -ForegroundColor Cyan
Write-Host "  (Note: This can take 10-20 minutes to complete)" -ForegroundColor Yellow
gcloud config set project "$ProjectID" --quiet

$instanceExists = $false
try {
    $null = gcloud sql instances describe "$InstanceName" --project="$ProjectID" 2>$null
    $instanceExists = ($LASTEXITCODE -eq 0)
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

# ── Create Database ────────────────────────────────────────────────────────
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

# ── Create User ────────────────────────────────────────────────────────────
Write-Host "  → User: $DatabaseUser" -ForegroundColor Gray
$userExists = $false
try {
    $userList  = gcloud sql users list --instance="$InstanceName" --format="value(name)" 2>$null
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

# ── Store DATABASE_URL in Secret Manager ───────────────────────────────────
Write-Host "  → Storing DATABASE_URL in Secret Manager..." -ForegroundColor Gray
$encodedPassword = [System.Uri]::EscapeDataString($plainPassword)
$dbUrl    = "postgresql+asyncpg://${DatabaseUser}:${encodedPassword}@/${DatabaseName}?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}"
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
