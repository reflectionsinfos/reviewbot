# ============================================
# ReviewBot v2.0 - Database Setup Script
# ============================================
# Run this after starting Docker containers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ReviewBot v2.0 - Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerStatus = docker ps
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "[2/4] Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "✗ .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.docker" ".env"
    Write-Host "✓ Created .env from .env.docker" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠ IMPORTANT: Edit .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host "⚠ Also change SECRET_KEY to a random value" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to continue after editing .env..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Start Docker containers
Write-Host ""
Write-Host "[3/4] Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d db

# Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "[4/4] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Start-Sleep -Seconds 2
    try {
        $result = docker-compose exec -T db pg_isready -U review_user 2>&1
        if ($result -like "*accepting connections*") {
            $ready = $true
            Write-Host "✓ PostgreSQL is ready (attempt $attempt/$maxAttempts)" -ForegroundColor Green
        } else {
            Write-Host "  Waiting... (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Waiting... (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
    }
}

if (-not $ready) {
    Write-Host "✗ PostgreSQL did not become ready in time" -ForegroundColor Red
    Write-Host "  Check logs: docker-compose logs db" -ForegroundColor Yellow
    exit 1
}

# Show connection info
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Database Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connection Info:" -ForegroundColor Yellow
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host "  Database: reviews_db" -ForegroundColor White
Write-Host "  User: review_user" -ForegroundColor White
Write-Host "  Password: review_password_change_me" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env and add your OPENAI_API_KEY" -ForegroundColor White
Write-Host "  2. Change SECRET_KEY to a random value" -ForegroundColor White
Write-Host "  3. Run: docker-compose up -d" -ForegroundColor White
Write-Host "  4. Run migrations: docker-compose exec app alembic upgrade head" -ForegroundColor White
Write-Host ""
Write-Host "Connect with DBeaver:" -ForegroundColor Yellow
Write-Host "  - Host: localhost" -ForegroundColor White
Write-Host "  - Port: 5432" -ForegroundColor White
Write-Host "  - Database: reviews_db" -ForegroundColor White
Write-Host "  - Username: review_user" -ForegroundColor White
Write-Host "  - Password: review_password_change_me" -ForegroundColor White
Write-Host ""
