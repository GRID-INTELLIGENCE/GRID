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

$explicit = "C:\Users\irfan\AppData\Local\Programs\Python\Python313\python.exe"
$candidates = @()

if ($env:PYTHON_EXE) {
    $candidates += $env:PYTHON_EXE
}

$candidates += $explicit
$candidates += @(
    "E:\grid\.venv\Scripts\python.exe",
    "E:\Coinbase\.venv\Scripts\python.exe",
    "E:\wellness_studio\.venv\Scripts\python.exe",
    "E:\.venv\Scripts\python.exe"
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

throw "Python interpreter not found. Set PYTHON_EXE or install at $explicit."
