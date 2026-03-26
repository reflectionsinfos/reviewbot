# ============================================
# ReviewBot v2.0 - Complete Reset & Setup
# ============================================
# Run this to completely reset and setup fresh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ReviewBot v2.0 - Complete Reset" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all containers
Write-Host "[1/6] Stopping all containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "✓ Containers stopped" -ForegroundColor Green

# Step 2: Remove old volumes (this deletes old database!)
Write-Host ""
Write-Host "[2/6] Removing old database volumes..." -ForegroundColor Yellow
docker-compose down -v
Write-Host "✓ Old volumes removed" -ForegroundColor Green

# Step 3: Check .env file
Write-Host ""
Write-Host "[3/6] Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
    
    # Check if OPENAI_API_KEY is set
    $envContent = Get-Content ".env"
    $openAiKey = $envContent | Where-Object { $_ -like "OPENAI_API_KEY=*" }
    if ([string]::IsNullOrWhiteSpace($openAiKey) -or $openAiKey -like "OPENAI_API_KEY=`"``"") {
        Write-Host "⚠ OPENAI_API_KEY is not set in .env" -ForegroundColor Yellow
        Write-Host "  Please edit .env and add your OpenAI API key" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key after adding your API key..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
    # Check if SECRET_KEY is changed
    $secretKey = $envContent | Where-Object { $_ -like "SECRET_KEY=*" }
    if ($secretKey -like "*change-this*") {
        Write-Host "⚠ SECRET_KEY still has default value" -ForegroundColor Yellow
        Write-Host "  Please change SECRET_KEY in .env" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key after changing SECRET_KEY..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} else {
    Write-Host "✗ .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.docker" ".env"
    Write-Host "✓ Created .env from .env.docker" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠ IMPORTANT: Edit .env now!" -ForegroundColor Red
    Write-Host "  1. Add your OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host "  2. Change SECRET_KEY to a random value" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key after editing .env..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Step 4: Start PostgreSQL only
Write-Host ""
Write-Host "[4/6] Starting PostgreSQL database..." -ForegroundColor Yellow
docker-compose up -d db

# Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "[5/6] Waiting for PostgreSQL to initialize..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Start-Sleep -Seconds 2
    try {
        $result = docker-compose exec -T db pg_isready -U review_user -d reviews_db 2>&1
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
    docker-compose logs db
    exit 1
}

# Step 6: Verify database was created correctly
Write-Host ""
Write-Host "[6/6] Verifying database setup..." -ForegroundColor Yellow
try {
    $dbCheck = docker-compose exec -T db psql -U review_user -d reviews_db -c "SELECT current_database();" 2>&1
    if ($dbCheck -like "*reviews_db*") {
        Write-Host "✓ Database 'reviews_db' created successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Database check failed" -ForegroundColor Red
        Write-Host "  Output: $dbCheck" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Database verification error" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Yellow
}

# Show success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Database Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database Connection:" -ForegroundColor Yellow
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host "  Database: reviews_db" -ForegroundColor White
Write-Host "  User: review_user" -ForegroundColor White
Write-Host "  Password: review_password_change_me" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start the application:" -ForegroundColor White
Write-Host "     docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Run database migrations:" -ForegroundColor White
Write-Host "     docker-compose exec app alembic upgrade head" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Check application logs:" -ForegroundColor White
Write-Host "     docker-compose logs -f app" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Test health endpoint:" -ForegroundColor White
Write-Host "     curl http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connect with DBeaver:" -ForegroundColor Yellow
Write-Host "  - Host: localhost" -ForegroundColor White
Write-Host "  - Port: 5432" -ForegroundColor White
Write-Host "  - Database: reviews_db" -ForegroundColor White
Write-Host "  - Username: review_user" -ForegroundColor White
Write-Host "  - Password: review_password_change_me" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
