# 05_deploy_app.ps1 - Build image, push to AR, and deploy to Cloud Run
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

Write-Host "  → Project: $ProjectID" -ForegroundColor Gray
Write-Host "  → Region: $Region" -ForegroundColor Gray
Write-Host "  → Image: $ImageName" -ForegroundColor Gray

$imageTag = "${Region}-docker.pkg.dev/${ProjectID}/${RepoName}/${ImageName}:latest"

# 1. Build and push image via Cloud Build
Write-Host "  → Building image via Cloud Build: $imageTag..." -ForegroundColor Gray
gcloud builds submit --tag "$imageTag" . --quiet

# 2. Deploy to Cloud Run
Write-Host "  → Deploying service: $ServiceName..." -ForegroundColor Gray
gcloud run deploy "$ServiceName" `
    --image "$imageTag" `
    --region "$Region" `
    --service-account "$SA_NAME@$ProjectID.iam.gserviceaccount.com" `
    --port 8000 `
    --allow-unauthenticated `
    --set-env-vars="DEBUG=false,VOICE_ENABLED=true,REQUIRE_HUMAN_APPROVAL=true,ACTIVE_LLM_PROVIDER=openai,SECRET_KEY=DUMMY-SECRET-KEY" `
    --set-env-vars="OPENAI_API_KEY=sk-DUMMY-OPENAI-KEY-FOR-DOCS" `
    --set-env-vars="DATABASE_URL=postgresql+asyncpg://postgres:DUMMY-PASSWORD@/postgres?host=/cloudsql/${ProjectID}:${Region}:${InstanceName}" `
    --add-cloudsql-instances "${ProjectID}:${Region}:${InstanceName}" --quiet

Write-Host "✅ App deployment complete." -ForegroundColor Green
$url = gcloud run services describe "$ServiceName" --region="$Region" --format='value(status.url)'
Write-Host "   URL: $url" -ForegroundColor Cyan
