# Safety Deployment Launcher for Windows PowerShell
# This script sets up the environment and starts all services

Write-Host "🚀 Safety Enforcement Pipeline Deployment Launcher" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$projectRoot\pyproject.toml")) {
    Write-Host "❌ Error: Cannot find project root. Run from the safety/ directory or set GRID_ROOT." -ForegroundColor Red
    exit 1
}

# Set environment variables
Write-Host "Setting up environment..." -ForegroundColor Yellow
$env:PYTHONPATH = "$projectRoot\src;$PSScriptRoot"
$env:DATABASE_URL = Read-Host "Enter DATABASE_URL (or press Enter for SQLite test mode)"
if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    $env:DATABASE_URL = "sqlite+aiosqlite:///./safety_test.db"
    Write-Host "Using SQLite test database: $env:DATABASE_URL" -ForegroundColor Cyan
}

$env:REDIS_URL = Read-Host "Enter REDIS_URL (or press Enter for localhost:6379)"
if ([string]::IsNullOrWhiteSpace($env:REDIS_URL)) {
    $env:REDIS_URL = "redis://localhost:6379"
}

$env:SAFETY_JWT_SECRET = "dev-secret-key-change-in-production"
$env:SAFETY_API_KEYS = "test-key-1:verified,test-key-2:user"
$env:MODEL_API_URL = "http://localhost:8080/v1/completions"
$env:SAFETY_ENV = "development"
$env:SAFETY_LOG_LEVEL = "INFO"

Write-Host ""
Write-Host "Environment configured:" -ForegroundColor Green
Write-Host "  PYTHONPATH: $env:PYTHONPATH"
Write-Host "  DATABASE_URL: $env:DATABASE_URL"
Write-Host "  REDIS_URL: $env:REDIS_URL"
Write-Host ""

# Check Redis
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisTest.TcpTestSucceeded) {
        Write-Host "✅ Redis is running on localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis not found on localhost:6379" -ForegroundColor Yellow
        Write-Host "   Please start Redis first:" -ForegroundColor Yellow
        Write-Host "   - Docker: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Cyan
        Write-Host "   - Or download Redis for Windows from https://github.com/microsoftarchive/redis/releases" -ForegroundColor Cyan
        Write-Host ""
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne 'y') {
            exit 1
        }
    }
} catch {
    Write-Host "⚠️  Could not check Redis status" -ForegroundColor Yellow
}

Write-Host ""

# Menu
Write-Host "What would you like to do?" -ForegroundColor Green
Write-Host "1. Run database migration"
Write-Host "2. Start Mothership API (with safety)"
Write-Host "3. Start Safety Worker"
Write-Host "4. Start Safety API (standalone)"
Write-Host "5. Run tests"
Write-Host "6. Exit"
Write-Host ""

$choice = Read-Host "Enter choice (1-6)"

switch ($choice) {
    '1' {
        Write-Host "Running database migration..." -ForegroundColor Yellow
        python safety/scripts/migrate.py
    }
    '2' {
        Write-Host "Starting Mothership API..." -ForegroundColor Yellow
        Write-Host "Access at: http://localhost:8080" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host ""
        Set-Location $projectRoot
        uv run uvicorn application.mothership.main:app --host 0.0.0.0 --port 8080
    }
    '3' {
        Write-Host "Starting Safety Worker..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host ""
        Set-Location $projectRoot
        uv run python -m safety.workers.consumer
    }
    '4' {
        Write-Host "Starting Safety API (standalone)..." -ForegroundColor Yellow
        Write-Host "Access at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host ""
        Set-Location $projectRoot
        uv run python -c "
import sys
sys.path.insert(0, 'src')
from safety.api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
    }
    '5' {
        Write-Host "Running tests..." -ForegroundColor Yellow
        python -m pytest safety/tests/ -v
    }
    '6' {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}
