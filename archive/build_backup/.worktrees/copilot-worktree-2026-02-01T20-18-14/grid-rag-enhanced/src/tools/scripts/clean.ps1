# Cache cleanup script for GRID
Write-Host "Starting cache cleanup..."

# Remove __pycache__ directories
Get-ChildItem -Path . -Directory -Recurse | Where-Object { $_.Name -eq '__pycache__' } | ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item $_.FullName -Recurse -Force
}

# Remove .pyc files
Get-ChildItem -Path . -File -Recurse -Filter "*.pyc" | ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item $_.FullName -Force
}

# Remove cache directories
$cacheDirs = @('.ruff_cache', '.pytest_cache', '.mypy_cache', '.cache')
foreach ($dir in $cacheDirs) {
    if (Test-Path $dir) {
        Write-Host "Removing $dir"
        Remove-Item $dir -Recurse -Force
    }
}

Write-Host "Cache cleanup complete."
