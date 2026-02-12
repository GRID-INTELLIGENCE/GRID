# Setup terminal profile for GRID
Write-Host "========================================"
Write-Host " GRID Terminal Setup"
Write-Host "========================================"

# Check if .venv exists
Write-Host "[1/3] Checking Virtual Environment..."
if (-not (Test-Path ".venv")) {
    Write-Host "Error: Virtual environment '.venv' not found."
    exit 1
}

# Activate venv
Write-Host "[2/3] Activating virtual environment..."
.venv\Scripts\Activate.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment."
    exit 1
}

# Install packages
Write-Host "[3/3] Installing/upgrading packages..."
pip install --upgrade chromadb httpx numpy ollama

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully."
} else {
    Write-Host "Error: Failed to install packages."
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host " Terminal Ready!"
Write-Host "========================================"
Write-Host "To start querying, run: python -m tools.rag.cli query 'your question'"
