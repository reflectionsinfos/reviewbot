# 05_deploy_app.ps1 - Deploy using env.non-prod.gcp for production secrets
param (
    [string]$ProjectID = "reviewbot-491619",
    [string]$Region = "us-central1",
    [string]$ImageName = "reviewbot",
    [string]$RepoName = "reviewbot-repo",
    [string]$ServiceName = "reviewbot-web",
    [string]$SA_NAME = "reviewbot-runtime",
    [string]$InstanceName = "reviewbot-db"
)

$ErrorActionPreference = "Stop"

# ── LOAD env.non-prod.gcp FILE ──────────────────────────────────────────
Write-Host "  → Loading GCP production variables from env.non-prod.gcp..." -ForegroundColor Gray
if (Test-Path "env.non-prod.gcp") {
    Get-Content env.non-prod.gcp | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        $line = $_.Trim()
        if ($line.Contains('=')) {
            $name, $value = $line.Split('=', 2).Trim().Replace('"', '').Replace("'", "")
            Set-Variable -Name "GCP_$name" -Value $value
        }
    }
} else {
    Write-Error "env.non-prod.gcp file not found! Deployment stopped."
    return
}

# Values for construction
$dbUser = $GCP_DB_USER
$dbPass = $GCP_DB_PASS
$dbName = $GCP_DB_NAME
$activeProvider = $GCP_ACTIVE_LLM_PROVIDER
$groqKey = $GCP_GROQ_API_KEY
$secretKey = $GCP_SECRET_KEY

Write-Host "  → Project: $ProjectID" -ForegroundColor Gray
Write-Host "  → Region: $Region" -ForegroundColor Gray

$imageTag = "${Region}-docker.pkg.dev/${ProjectID}/${RepoName}/${ImageName}:latest"

# 0. Rebuild reviewbot-cli .whl so the download link on the UI stays current
Write-Host "  -> Rebuilding reviewbot-cli .whl..." -ForegroundColor Gray
# $PSScriptRoot = c:\projects\reviewbot\gcp_scripts
# reviewbot-cli sits at   c:\projects\reviewbot-cli
$repoRoot      = Split-Path -Parent $PSScriptRoot
$agentPath     = Join-Path (Split-Path -Parent $repoRoot) "reviewbot-cli"
$downloadsPath = Join-Path $repoRoot "frontend_vanilla\downloads"
if (Test-Path $agentPath) {
    Push-Location $agentPath
    python -m build --wheel --quiet
    $whl = Get-ChildItem "dist\reviewbot_cli-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($whl) {
        Copy-Item $whl.FullName $downloadsPath -Force
        Write-Host "    OK: Copied $($whl.Name) to frontend_vanilla/downloads/" -ForegroundColor Gray
    }
    # Regenerate source zip from repo contents (excludes build artefacts)
    $zipDest = Join-Path $downloadsPath "reviewbot-cli.zip"
    $tempDir = Join-Path $env:TEMP "reviewbot-cli-zip"
    if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
    Copy-Item $agentPath $tempDir -Recurse -Exclude @("dist","build","*.egg-info","__pycache__",".git")
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

# 2. Deploy to Cloud Run
Write-Host "  → Deploying service: $ServiceName..." -ForegroundColor Gray
gcloud run deploy "$ServiceName" `
    --image "$imageTag" `
    --region "$Region" `
    --service-account "$SA_NAME@$ProjectID.iam.gserviceaccount.com" `
    --port 8000 `
    --allow-unauthenticated `
    --set-env-vars="DEBUG=false,VOICE_ENABLED=true,REQUIRE_HUMAN_APPROVAL=true" `
    --set-env-vars="ACTIVE_LLM_PROVIDER=$activeProvider" `
    --set-env-vars="SECRET_KEY=$secretKey" `
    --set-env-vars="GROQ_API_KEY=$groqKey" `
    --set-env-vars="DATABASE_URL=postgresql+asyncpg://${dbUser}:${dbPass}@/${dbName}?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}" `
    --add-cloudsql-instances "${ProjectID}:${Region}:${InstanceName}" --quiet

Write-Host "✅ App deployment complete." -ForegroundColor Green
$url = gcloud run services describe "$ServiceName" --region="$Region" --format='value(status.url)'
Write-Host "   URL: $url" -ForegroundColor Cyan
