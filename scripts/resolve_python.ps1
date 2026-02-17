#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Resolve a safe Python interpreter path.

.DESCRIPTION
    Prefers explicit per-user Python 3.13 install, then known venvs,
    and avoids the Windows py.exe launcher.
#>

param(
    [switch]$AllowSystem = $true
)

# Resolve project root (parent of scripts/)
$projectRoot = Split-Path -Parent $PSScriptRoot
$candidates = @()

if ($env:PYTHON_EXE) {
    $candidates += $env:PYTHON_EXE
}

# Prefer the project's UV-managed venv
$candidates += @(
    "$projectRoot\.venv\Scripts\python.exe"
)

foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
        Write-Output $candidate
        return
    }
}

if ($AllowSystem) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -and ($cmd.Source -notmatch "\\\\py\\.exe$")) {
        Write-Output $cmd.Source
        return
    }
}

throw "Python interpreter not found. Run 'uv sync' to create .venv, or set PYTHON_EXE."
