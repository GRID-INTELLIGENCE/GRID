# Windsurf IDE Audit Verification Script
# Run this PowerShell script to verify Windsurf configuration compliance
# Usage: .\windsurf-audit-verify.ps1

param(
    [switch]$FixIssues,
    [switch]$Verbose
)

Write-Host "🔍 Windsurf IDE Configuration Audit" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Define expected core settings
$coreSettings = @{
    "files.autoSave" = "onFocusChange"
    "files.trimTrailingWhitespace" = $true
    "files.insertFinalNewline" = $true
    "files.eol" = "\n"
    "editor.formatOnSave" = $true
    "editor.formatOnSaveMode" = "file"
    "editor.minimap.enabled" = $false
    "editor.bracketPairColorization.enabled" = $true
    "editor.stickyScroll.enabled" = $true
    "chat.agent.maxRequests" = 35
    "git.enableSmartCommit" = $true
    "git.autofetch" = $false
}

# Expected Python settings
$pythonSettings = @{
    "editor.defaultFormatter" = "charliermarsh.ruff"
    "editor.tabSize" = 4
}

# Expected cache exclusions
$expectedExclusions = @(
    "**/.venv",
    "**/__pycache__",
    "**/.pytest_cache",
    "**/.mypy_cache",
    "**/.ruff_cache",
    "**/*.pyc",
    "**/.DS_Store"
)

function Test-Settings {
    param(
        [string]$IdeName,
        [string]$SettingsPath
    )

    Write-Host "📋 Checking $IdeName settings..." -ForegroundColor Yellow

    if (!(Test-Path $SettingsPath)) {
        Write-Host "❌ Settings file not found: $SettingsPath" -ForegroundColor Red
        return $false
    }

    try {
        $settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Host "❌ Invalid JSON in settings file" -ForegroundColor Red
        return $false
    }

    $allGood = $true

    # Check core settings
    Write-Host "  Core Settings:" -ForegroundColor Gray
    foreach ($setting in $coreSettings.Keys) {
        $expected = $coreSettings[$setting]
        $actual = $settings.$setting

        if ($actual -eq $expected) {
            Write-Host "    ✅ $setting" -ForegroundColor Green
        }
        else {
            Write-Host "    ❌ $setting (Expected: $expected, Got: $actual)" -ForegroundColor Red
            $allGood = $false

            if ($FixIssues) {
                $settings.$setting = $expected
                Write-Host "      🔧 Fixed automatically" -ForegroundColor Blue
            }
        }
    }

    # Check Python settings
    Write-Host "  Python Settings:" -ForegroundColor Gray
    if ($settings.'[python]') {
        foreach ($setting in $pythonSettings.Keys) {
            $expected = $pythonSettings[$setting]
            $actual = $settings.'[python]'.$setting

            if ($actual -eq $expected) {
                Write-Host "    ✅ [python].$setting" -ForegroundColor Green
            }
            else {
                Write-Host "    ❌ [python].$setting (Expected: $expected, Got: $actual)" -ForegroundColor Red
                $allGood = $false

                if ($FixIssues) {
                    $settings.'[python]'.$setting = $expected
                    Write-Host "      🔧 Fixed automatically" -ForegroundColor Blue
                }
            }
        }
    }
    else {
        Write-Host "    ❌ [python] section missing" -ForegroundColor Red
        $allGood = $false
    }

    # Check cache exclusions
    Write-Host "  Cache Exclusions:" -ForegroundColor Gray
    $exclusions = $settings.'files.exclude'
    if ($exclusions) {
        $missingExclusions = @()
        foreach ($pattern in $expectedExclusions) {
            if ($exclusions.$pattern -ne $true) {
                $missingExclusions += $pattern
            }
        }

        if ($missingExclusions.Count -eq 0) {
            Write-Host "    ✅ All 7 cache patterns present" -ForegroundColor Green
        }
        else {
            Write-Host "    ❌ Missing patterns: $($missingExclusions -join ', ')" -ForegroundColor Red
            $allGood = $false

            if ($FixIssues) {
                foreach ($pattern in $missingExclusions) {
                    $exclusions.$pattern = $true
                }
                Write-Host "      🔧 Added missing patterns" -ForegroundColor Blue
            }
        }
    }
    else {
        Write-Host "    ❌ files.exclude section missing" -ForegroundColor Red
        $allGood = $false
    }

    # Check terminal settings (Windsurf/Cursor specific)
    if ($IdeName -in @("Windsurf", "Cursor")) {
        Write-Host "  Terminal Settings:" -ForegroundColor Gray

        $scrollback = $settings.'terminal.integrated.scrollback'
        if ($scrollback -eq 10000) {
            Write-Host "    ✅ terminal.integrated.scrollback = 10000" -ForegroundColor Green
        }
        else {
            Write-Host "    ❌ terminal.integrated.scrollback (Expected: 10000, Got: $scrollback)" -ForegroundColor Red
            $allGood = $false

            if ($FixIssues) {
                $settings.'terminal.integrated.scrollback' = 10000
                Write-Host "      🔧 Fixed scrollback" -ForegroundColor Blue
            }
        }

        $smoothScrolling = $settings.'terminal.integrated.smoothScrolling'
        if ($smoothScrolling -eq $true) {
            Write-Host "    ✅ terminal.integrated.smoothScrolling = true" -ForegroundColor Green
        }
        else {
            Write-Host "    ❌ terminal.integrated.smoothScrolling (Expected: true, Got: $smoothScrolling)" -ForegroundColor Red
            $allGood = $false

            if ($FixIssues) {
                $settings.'terminal.integrated.smoothScrolling' = $true
                Write-Host "      🔧 Enabled smooth scrolling" -ForegroundColor Blue
            }
        }
    }

    # Save changes if fixing
    if ($FixIssues -and !$allGood) {
        try {
            $settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsPath -Encoding UTF8
            Write-Host "💾 Changes saved to $SettingsPath" -ForegroundColor Blue
        }
        catch {
            Write-Host "❌ Failed to save changes" -ForegroundColor Red
        }
    }

    Write-Host ""
    return $allGood
}

# Test each IDE
$results = @{}

$results["VS Code"] = Test-Settings -IdeName "VS Code" -SettingsPath "$env:USERPROFILE\AppData\Roaming\Code\User\settings.json"
$results["Cursor"] = Test-Settings -IdeName "Cursor" -SettingsPath "$env:USERPROFILE\AppData\Roaming\Cursor\User\settings.json"
$results["Windsurf"] = Test-Settings -IdeName "Windsurf" -SettingsPath "$env:USERPROFILE\AppData\Roaming\Windsurf\User\settings.json"

# Summary
Write-Host "📊 Audit Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

$passed = 0
$total = $results.Count

foreach ($ide in $results.Keys) {
    if ($results[$ide]) {
        Write-Host "✅ $ide : COMPLIANT" -ForegroundColor Green
        $passed++
    }
    else {
        Write-Host "❌ $ide : NON-COMPLIANT" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Overall Result: $passed/$total IDEs compliant" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

if ($passed -eq $total) {
    Write-Host "🎉 All IDEs are fully compliant with THE GRID standards!" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Some issues found. Run with -FixIssues to auto-correct." -ForegroundColor Yellow
}

if ($Verbose) {
    Write-Host ""
    Write-Host "🔗 Related Files:" -ForegroundColor Gray
    Write-Host "  - Audit Report: E:\grid\docs\guides\WINDSURF_AUDIT_REPORT.md"
    Write-Host "  - Verification Prompt: E:\grid\docs\guides\WINDSURF_AGENT_VERIFICATION_PROMPT.md"
    Write-Host "  - Cross-Drive Config: E:\grid\docs\guides\CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md"
}
