# AI Agent Development Environment Setup
# Usage: .\scripts\agent_setup.ps1

Write-Host "Setting up GRID Agent Development Environment..." -ForegroundColor Cyan

# GRID Framework setup
Write-Host "`n[1/3] Setting up GRID Framework..." -ForegroundColor Yellow
Set-Location "E:\grid"
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test

# Security validation
Write-Host "`n[2/3] Running Security Validation..." -ForegroundColor Yellow
python -m pytest tests/security/test_path_traversal.py -v

# EUFLE ML Stack (optional)
if ($env:EUFLE_SETUP -eq "1") {
    Write-Host "`n[3/3] Setting up EUFLE ML Stack..." -ForegroundColor Yellow
    Set-Location "E:\grid\EUFLE"
    uv sync --group dev --group training
} else {
    Write-Host "`n[3/3] Skipping EUFLE ML Stack (set EUFLE_SETUP=1 to enable)" -ForegroundColor Gray
}

Write-Host "`nAgent environment ready!" -ForegroundColor Green
