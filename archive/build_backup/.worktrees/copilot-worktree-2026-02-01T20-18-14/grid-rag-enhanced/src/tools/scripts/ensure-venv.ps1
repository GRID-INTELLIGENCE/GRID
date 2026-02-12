#!/usr/bin/env pwsh
# GRID Venv Wrapper - Ensures all commands run inside the project virtual environment
# Usage: .\scripts\ensure-venv.ps1 <command> [args...]

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$CommandArgs = @()
)

$VenvPath = ".\.venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $VenvPath. Run 'uv venv --python 3.13 --clear' first."
    exit 1
}

# Check if UV is available and use it for known tools
$KnownTools = @("python", "pip", "pytest", "ruff", "black", "mypy", "hatch")
if ($Command -in $KnownTools -and (Get-Command uv -ErrorAction SilentlyContinue)) {
    & uv run $Command @CommandArgs
} else {
    # Fallback to direct venv execution for 3rd-party tools
    $Env:VIRTUAL_ENV = (Resolve-Path $VenvPath).Path
    $Env:PATH = "$($Env:VIRTUAL_ENV)\Scripts;$($Env:PATH)"
    & $Command @CommandArgs
}
