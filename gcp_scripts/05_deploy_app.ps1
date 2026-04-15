# 05_deploy_app.ps1 - Build and deploy ReviewBot to Cloud Run
param (
    [string]$ProjectID = "reviewbot-493320",
    [string]$Region = "us-central1",
    [string]$ImageName = "reviewbot",
    [string]$RepoName = "reviewbot-repo",
    [string]$ServiceName = "reviewbot-web",
    [string]$SA_NAME = "reviewbot-runtime",
    [string]$InstanceName = "reviewbot-db"
)

$ErrorActionPreference = "Stop"

# ── LOAD .env FILE ──────────────────────────────────────────────────────
Write-Host "  1. Loading deployment variables from .env..." -ForegroundColor Gray
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' -and $_.Trim() -ne '' } | ForEach-Object {
        $line = $_.Trim()
        $eqIdx = $line.IndexOf('=')
        if ($eqIdx -gt 0) {
            $varName  = $line.Substring(0, $eqIdx).Trim()
            $varValue = $line.Substring($eqIdx + 1).Trim().Trim('"').Trim("'")
            Set-Variable -Name "ENV_$varName" -Value $varValue -Scope Script
        }
    }
} else {
    Write-Error ".env file not found at $envFile - copy .env.example or create it first."
    return
}

# Values for constructing DATABASE_URL and seeding secrets
$dbUser       = $ENV_DB_USER
$dbPass       = $ENV_DB_PASS
$dbName       = $ENV_DB_NAME
$secretKey    = $ENV_SECRET_KEY

# Override params with .env values if the caller didn't pass them explicitly
if ($ProjectID   -eq "reviewbot-493320")  { $ProjectID   = $ENV_GCP_PROJECT }
if ($Region      -eq "us-central1")       { $Region      = $ENV_GCP_REGION }
if ($RepoName    -eq "reviewbot-repo")    { $RepoName    = $ENV_REPO_NAME }
if ($ServiceName -eq "reviewbot-web")     { $ServiceName = $ENV_SERVICE_NAME }
if ($SA_NAME     -eq "reviewbot-runtime") { $SA_NAME     = $ENV_SA_NAME }
if ($InstanceName -eq "reviewbot-db")     { $InstanceName = $ENV_DB_INSTANCE_NAME }

# ── PUSH secrets to Secret Manager so --set-secrets has versions to resolve ──
Write-Host "  2. Syncing secrets to Secret Manager..." -ForegroundColor Gray
$dbUrl = "postgresql+asyncpg://${dbUser}:${dbPass}@/${dbName}?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}"
$secretsToSync = @{
    "DATABASE_URL" = $dbUrl
    "SECRET_KEY"   = $secretKey
}
foreach ($entry in $secretsToSync.GetEnumerator()) {
    $val = $entry.Value
    if ([string]::IsNullOrWhiteSpace($val)) {
        $val = "NOT_SET"
    }
    $tempFile = [System.IO.Path]::GetTempFileName()
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $False
        [System.IO.File]::WriteAllText($tempFile, $val, $utf8NoBom)
        gcloud secrets versions add $entry.Key --data-file="$tempFile" --project="$ProjectID" --quiet
        Write-Host "    → $($entry.Key) updated." -ForegroundColor Gray
    } finally {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "  3. Project: $ProjectID" -ForegroundColor Gray
Write-Host "  4. Region: $Region" -ForegroundColor Gray

$imageTag = "${Region}-docker.pkg.dev/${ProjectID}/${RepoName}/${ImageName}:latest"

# 0. Rebuild reviewbot-cli .whl so the download link on the UI stays current
Write-Host "  5. Rebuilding reviewbot-cli .whl..." -ForegroundColor Gray
# $PSScriptRoot = c:\projects\reviewbot\gcp_scripts
# reviewbot-cli sits at   c:\projects\reviewbot-cli
$repoRoot      = Split-Path -Parent $PSScriptRoot
$agentPath     = Join-Path (Split-Path -Parent $repoRoot) "reviewbot-cli"
$downloadsPath = Join-Path $repoRoot "frontend_vanilla\downloads"

$pythonCmd = "python"
$venvPython = Join-Path (Split-Path -Parent $repoRoot) ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonCmd = $venvPython
}

if (Test-Path $agentPath) {
    Push-Location $agentPath
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    & $pythonCmd -m ensurepip 2>&1 | Out-Null
    & $pythonCmd -m pip install build --quiet
    & $pythonCmd -m build --wheel --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python build failed with exit code $LASTEXITCODE."
        exit $LASTEXITCODE
    }
    $whl = Get-ChildItem "dist\reviewbot_cli-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not (Test-Path $downloadsPath)) {
        New-Item -ItemType Directory -Path $downloadsPath -Force | Out-Null
    }
    if ($whl) {
        Copy-Item $whl.FullName "$downloadsPath\" -Force
        Write-Host "    OK: Copied $($whl.Name) to frontend_vanilla/downloads/" -ForegroundColor Gray
    }
    # Regenerate source zip from repo contents (excludes build artefacts)
    $zipDest = Join-Path $downloadsPath "reviewbot-cli.zip"
    $tempDir = Join-Path $env:TEMP "reviewbot-cli-zip"
    if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
    Copy-Item $agentPath $tempDir -Recurse -Exclude @("dist","build","*.egg-info","__pycache__",".git","venv",".venv")
    Compress-Archive -Path "$tempDir\*" -DestinationPath $zipDest -Force
    Remove-Item $tempDir -Recurse -Force
    Write-Host "    OK: Regenerated reviewbot-cli.zip in frontend_vanilla/downloads/" -ForegroundColor Gray
    Pop-Location
} else {
    Write-Host "    WARNING: reviewbot-cli not found at $agentPath - skipping .whl rebuild." -ForegroundColor Yellow
}

# 1. Build and push image via Cloud Build
Write-Host "  → Building image via Cloud Build..." -ForegroundColor Gray
gcloud builds submit --tag "$imageTag" . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cloud Build failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# 2. Delete existing Cloud Run service (fresh install)
Write-Host "  → Deleting existing service '$ServiceName' (if present)..." -ForegroundColor Gray
$existing = $null
try {
    $ErrorActionPreference = "Continue"
    $existing = gcloud run services describe "$ServiceName" --region="$Region" --project="$ProjectID" --format="value(metadata.name)" 2>$null
    $ErrorActionPreference = "Stop"
} catch {
    $existing = $null
    $ErrorActionPreference = "Stop"
}
if ($existing -eq $ServiceName) {
    gcloud run services delete "$ServiceName" --region="$Region" --project="$ProjectID" --quiet
    Write-Host "    → Service deleted." -ForegroundColor Gray
} else {
    Write-Host "    → Service not found, skipping delete." -ForegroundColor Gray
}

# 3. Deploy to Cloud Run
Write-Host "  → Deploying service: $ServiceName..." -ForegroundColor Gray
gcloud run deploy "$ServiceName" `
    --image "$imageTag" `
    --region "$Region" `
    --service-account "$SA_NAME@$ProjectID.iam.gserviceaccount.com" `
    --port 8000 `
    --allow-unauthenticated `
    --add-cloudsql-instances "${ProjectID}:${Region}:${InstanceName}" `
    --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" `
    --set-env-vars="DEBUG=false" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cloud Run deployment failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "App deployment complete." -ForegroundColor Green
$url = gcloud run services describe "$ServiceName" --region="$Region" --format='value(status.url)'
Write-Host "   URL: $url" -ForegroundColor Cyan
