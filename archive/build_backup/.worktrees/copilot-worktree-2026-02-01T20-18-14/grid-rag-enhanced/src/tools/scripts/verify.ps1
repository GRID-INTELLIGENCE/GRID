# GRID Local Verification Script (PowerShell)
# Mirrors CI pipeline checks for local development

$ErrorActionPreference = "Stop"

Write-Host "GRID Local Verification" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "Using virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green
} elseif (Test-Path ".venv") {
    Write-Host "Activating .venv..." -ForegroundColor Yellow
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: No virtual environment detected. Using system Python." -ForegroundColor Yellow
}

# Check Python version
$pythonVersion = python --version
Write-Host "Python: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:PYTHONPATH = "."
$env:BLOCKER_DISABLED = "1"
$env:GRID_ENVIRONMENT = "testing"

# Step 1: Lint with Ruff
Write-Host "[1/4] Linting with Ruff..." -ForegroundColor Yellow
ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Ruff linting failed" -ForegroundColor Red
    exit 1
}
Write-Host "PASSED: Ruff linting" -ForegroundColor Green
Write-Host ""

# Step 2: Check formatting with Black
Write-Host "[2/4] Checking code formatting (Black)..." -ForegroundColor Yellow
black --check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Black formatting check failed" -ForegroundColor Red
    Write-Host "Run 'black .' to fix formatting" -ForegroundColor Yellow
    exit 1
}
Write-Host "PASSED: Black formatting check" -ForegroundColor Green
Write-Host ""

# Step 3: Type checking with Pyright
Write-Host "[3/4] Type checking with Pyright..." -ForegroundColor Yellow
pyright .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Pyright type checking failed" -ForegroundColor Red
    exit 1
}
Write-Host "PASSED: Pyright type checking" -ForegroundColor Green
Write-Host ""

# Step 4: Run tests
Write-Host "[4/4] Running tests..." -ForegroundColor Yellow
pytest tests/ --ignore=tests/unit/test_pattern_engine_dbscan.py -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Tests failed" -ForegroundColor Red
    exit 1
}
Write-Host "PASSED: All tests" -ForegroundColor Green
Write-Host ""

Write-Host "========================" -ForegroundColor Cyan
Write-Host "All checks passed!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Cyan
