# GRID Pulsar Launcher (Compatible with 2026-01-07 Structure)
Write-Host "[ PULSAR ] Starting GRID Pulsar Infrastructure..." -ForegroundColor Cyan

# Ensure we are in the project root
$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot | Split-Path -Parent } else { Get-Location }
if (-not $ProjectRoot) { $ProjectRoot = "e:\grid" }
Set-Location $ProjectRoot

# 1. Start Mothership Backend
Write-Host "[ BACKEND ] Initializing Mothership Cockpit (Port 8080)..." -ForegroundColor Blue

$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = "uv run python"
}

# Start backend in a new background process
# Check if backend module exists before starting
$BackendPath = Join-Path $ProjectRoot "application\mothership\main.py"
if (Test-Path $BackendPath) {
    $backendCmd = "uv run uvicorn application.mothership.main:app --reload --port 8080"
    Write-Host "[ BACKEND ] Starting: $backendCmd" -ForegroundColor Blue
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -NoNewWindow
} else {
    Write-Host "[ ERROR ] Backend not found at $BackendPath" -ForegroundColor Red
    Write-Host "[ INFO ] API will not be available. Continuing..." -ForegroundColor Yellow
}

# 2. Wait for backend
Write-Host "[ STATUS ] Waiting for Mothership sync..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 3. Handle Frontend (If present)
$UIManifestPath = Join-Path $ProjectRoot "ui\manifest.json"
$PackageJsonPath = Join-Path $ProjectRoot "ui\package.json"
if (Test-Path $PackageJsonPath) {
    Write-Host "[ FRONTEND ] Launching Pulsar Dashboard..." -ForegroundColor Blue
    Set-Location (Join-Path $ProjectRoot "ui")
    Start-Process npm -ArgumentList "run dev" -NoNewWindow
} else {
    Write-Host "[ INFO ] UI package.json not detected at $PackageJsonPath" -ForegroundColor Yellow
    Write-Host "[ INFO ] API operational at http://localhost:8080/docs (if backend started)" -ForegroundColor Yellow
}

Write-Host "[ SUCCESS ] System Operational!" -ForegroundColor Green
Write-Host "Mothership Cockpit: http://localhost:8080/docs" -ForegroundColor Yellow
