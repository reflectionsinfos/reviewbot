# ============================================
# ReviewBot v2.0 - Database Setup Script
# ============================================
# This script helps you setup the PostgreSQL database
# Run this after starting Docker containers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ReviewBot v2.0 - Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$envFile = ".env"
$dockerComposeFile = "docker-compose.yml"

# Check if Docker is running
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerStatus = docker ps
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "[2/5] Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path $envFile) {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "✗ .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.docker") {
        Copy-Item ".env.docker" $envFile
        Write-Host "✓ Created .env from .env.docker" -ForegroundColor Green
        Write-Host "⚠ Please update .env with your configuration" -ForegroundColor Yellow
        Write-Host "  Required: OPENAI_API_KEY, SECRET_KEY, DATABASE_URL" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "✗ .env.docker not found" -ForegroundColor Red
        exit 1
    }
}

# Start Docker containers
Write-Host ""
Write-Host "[3/5] Starting Docker containers..." -ForegroundColor Yellow
docker-compose --profile tools up -d db pgadmin

# Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "[4/5] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
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

# Run database migrations
Write-Host ""
Write-Host "[5/5] Running database migrations..." -ForegroundColor Yellow
docker-compose exec app alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Migration failed" -ForegroundColor Red
    Write-Host "  Check logs: docker-compose logs app" -ForegroundColor Yellow
    exit 1
}

# Verify setup
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check tables
Write-Host ""
Write-Host "Database Tables:" -ForegroundColor Yellow
docker-compose exec -T db psql -U review_user -d reviews_db -c "\dt"

# Show connection info
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database Connection:" -ForegroundColor Yellow
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host "  Database: reviews_db" -ForegroundColor White
Write-Host "  User: review_user" -ForegroundColor White
Write-Host "  Password: review_password_change_me" -ForegroundColor White
Write-Host ""
Write-Host "pgAdmin Access:" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:5050" -ForegroundColor White
Write-Host "  Email: admin@example.com" -ForegroundColor White
Write-Host "  Password: admin_change_me" -ForegroundColor White
Write-Host ""
Write-Host "Application:" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Update .env with your OPENAI_API_KEY" -ForegroundColor White
Write-Host "  2. Change SECRET_KEY in .env" -ForegroundColor White
Write-Host "  3. Change database password in .env" -ForegroundColor White
Write-Host "  4. Start the application: docker-compose up app" -ForegroundColor White
Write-Host ""
