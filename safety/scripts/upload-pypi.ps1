# Publish grid-safety to PyPI. Run from repo root: .\safety\scripts\upload-pypi.ps1
# Requires: PYPI_API_TOKEN set in your environment (User variables).

$ErrorActionPreference = "Stop"
if (-not $env:PYPI_API_TOKEN) {
    Write-Error "PYPI_API_TOKEN is not set. Set it in User environment variables."
    exit 1
}

$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $env:PYPI_API_TOKEN

Push-Location $PSScriptRoot\..
try {
    if (-not (Test-Path dist)) {
        Write-Host "Building..."
        python -m build --wheel --sdist
    }
    Write-Host "Uploading to PyPI..."
    python -m twine upload --skip-existing dist/*
} finally {
    Pop-Location
}
