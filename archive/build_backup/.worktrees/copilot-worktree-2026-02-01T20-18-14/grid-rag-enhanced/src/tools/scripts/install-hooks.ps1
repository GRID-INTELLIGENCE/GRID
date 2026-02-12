# GRID Hook Installation Script (PowerShell)
# ===========================================
# Installs git hooks aligned with CI/CD pipeline and deployment map.
# Windows PowerShell version.
#

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HooksSrcDir = Join-Path $ScriptDir "hooks"
$HooksDestDir = ".git\hooks"

Write-Host "[GRID] Installing Git Hooks" -ForegroundColor Cyan
Write-Host "============================================================"

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Create hooks directory if it doesn't exist
if (-not (Test-Path $HooksDestDir)) {
    New-Item -ItemType Directory -Path $HooksDestDir -Force | Out-Null
}

# Install pre-push hook
$PrePushSrc = Join-Path $HooksSrcDir "pre-push-evolved"
$PrePushDest = Join-Path $HooksDestDir "pre-push"

if (Test-Path $PrePushSrc) {
    Copy-Item -Path $PrePushSrc -Destination $PrePushDest -Force
    Write-Host "[OK] Installed pre-push hook" -ForegroundColor Green
} else {
    Write-Host "[WARN] pre-push-evolved not found in $HooksSrcDir" -ForegroundColor Yellow
}

# Install commit-msg hook
$CommitMsgSrc = Join-Path $HooksSrcDir "commit-msg"
$CommitMsgDest = Join-Path $HooksDestDir "commit-msg"

if (Test-Path $CommitMsgSrc) {
    Copy-Item -Path $CommitMsgSrc -Destination $CommitMsgDest -Force
    Write-Host "[OK] Installed commit-msg hook" -ForegroundColor Green
} else {
    Write-Host "[WARN] commit-msg not found in $HooksSrcDir" -ForegroundColor Yellow
}

# Install pre-commit hook (optional, if using pre-commit framework)
if (Test-Path ".pre-commit-config.yaml") {
    if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
        Write-Host "Installing pre-commit framework hooks..." -ForegroundColor Cyan
        pre-commit install
        Write-Host "[OK] Installed pre-commit framework hooks" -ForegroundColor Green
    } else {
        Write-Host "[INFO] pre-commit framework detected but 'pre-commit' command not found" -ForegroundColor Yellow
        Write-Host "      Install with: pip install pre-commit" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "[OK] Git hooks installed successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Hooks are now aligned with CI/CD pipeline (.github/workflows/main.yaml)"
Write-Host "See docs/DEPLOYMENT_MAP.md for details on the deployment architecture."
Write-Host ""
Write-Host "To bypass hooks (not recommended):"
Write-Host "  - Pre-push: git push --no-verify"
Write-Host "  - Commit-msg: `$env:SKIP_COMMIT_MSG_VALIDATION=1; git commit"
