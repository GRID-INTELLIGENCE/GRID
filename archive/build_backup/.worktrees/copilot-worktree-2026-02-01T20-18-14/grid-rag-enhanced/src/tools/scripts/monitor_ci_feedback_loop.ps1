# GRID CI/CD Pipeline Monitoring & Feedback Loop (PowerShell)
# ============================================================
# Monitors GitHub Actions workflows from CLI and iteratively fixes issues
# until all CI/CD jobs pass (fully green pipeline).
#

param(
    [string]$WorkflowName = "GRID CI/CD Pipeline",
    [int]$MaxIterations = 10,
    [switch]$WatchOnly
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[GRID] CI/CD Pipeline Feedback Loop" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Workflow: $WorkflowName"
Write-Host "Max iterations: $MaxIterations"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

function Get-LatestWorkflowRun {
    param([string]$Workflow)

    Write-Host "[INFO] Fetching latest workflow run for: $Workflow" -ForegroundColor Yellow

    $runs = gh run list --workflow $Workflow --limit 1 --json databaseId,name,status,conclusion,url,headSha,headBranch 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to fetch workflow runs" -ForegroundColor Red
        return $null
    }

    $runData = $runs | ConvertFrom-Json | Select-Object -First 1
    if (-not $runData) {
        Write-Host "[WARN] No workflow runs found" -ForegroundColor Yellow
        return $null
    }

    $runId = $runData.databaseId
    $jobsJson = gh run view $runId --json jobs 2>&1
    $jobsData = $jobsJson | ConvertFrom-Json

    return @{
        Id = $runId
        Name = $runData.name
        Status = $runData.status
        Conclusion = $runData.conclusion
        Url = $runData.url
        Branch = $runData.headBranch
        Sha = $runData.headSha
        Jobs = $jobsData.jobs
    }
}

function Test-WorkflowComplete {
    param($Run)

    return $Run.Status -in @("completed", "failure", "cancelled")
}

function Test-WorkflowSuccessful {
    param($Run)

    if (-not (Test-WorkflowComplete $Run)) {
        return $false
    }

    $criticalJobs = @("lint", "test", "build")
    foreach ($job in $Run.Jobs) {
        $jobLower = $job.name.ToLower()
        foreach ($critical in $criticalJobs) {
            if ($jobLower -like "*$critical*") {
                if ($job.conclusion -ne "success") {
                    return $false
                }
            }
        }
    }

    return $Run.Conclusion -eq "success"
}

function Get-FailedJobs {
    param($Run)

    return $Run.Jobs | Where-Object { $_.conclusion -eq "failure" }
}

function Test-LocalLint {
    Write-Host "[INFO] Running local lint check (ruff)..." -ForegroundColor Yellow
    uv run ruff check . 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Lint check passed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[FAIL] Lint check failed" -ForegroundColor Red
        return $false
    }
}

function Fix-LintIssues {
    Write-Host "[INFO] Attempting to auto-fix lint issues..." -ForegroundColor Yellow
    uv run ruff check . --fix 2>&1 | Out-Null
    return $LASTEXITCODE -eq 0
}

function Test-LocalFormat {
    Write-Host "[INFO] Running local format check (black)..." -ForegroundColor Yellow
    uv run black --check grid/ application/ tools/ tests/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Format check passed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[FAIL] Format check failed" -ForegroundColor Red
        return $false
    }
}

function Fix-FormatIssues {
    Write-Host "[INFO] Attempting to auto-fix format issues..." -ForegroundColor Yellow
    uv run black grid/ application/ tools/ tests/ 2>&1 | Out-Null
    return $LASTEXITCODE -eq 0
}

function Test-LocalTests {
    Write-Host "[INFO] Running local unit tests..." -ForegroundColor Yellow
    uv run pytest tests/unit/ -v -q --tb=short 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Unit tests passed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[FAIL] Unit tests failed" -ForegroundColor Red
        return $false
    }
}

function Commit-AndPushFixes {
    param([string]$Message)

    Write-Host "[INFO] Committing fixes: $Message" -ForegroundColor Yellow

    $status = git status --porcelain
    if (-not $status) {
        Write-Host "[INFO] No changes to commit" -ForegroundColor Yellow
        return $false
    }

    git add -A 2>&1 | Out-Null
    git commit -m $Message 2>&1 | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to commit" -ForegroundColor Red
        return $false
    }

    git push 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to push" -ForegroundColor Red
        return $false
    }

    Write-Host "[OK] Changes committed and pushed" -ForegroundColor Green
    return $true
}

# Main feedback loop
for ($iteration = 1; $iteration -le $MaxIterations; $iteration++) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Iteration $iteration/$MaxIterations" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $run = Get-LatestWorkflowRun -Workflow $WorkflowName
    if (-not $run) {
        Write-Host "[ERROR] Could not fetch workflow run" -ForegroundColor Red
        exit 1
    }

    Write-Host "[INFO] Workflow Run: $($run.Id)" -ForegroundColor Cyan
    Write-Host "[INFO] Status: $($run.Status)" -ForegroundColor Cyan
    Write-Host "[INFO] Conclusion: $($run.Conclusion)" -ForegroundColor Cyan
    Write-Host "[INFO] URL: $($run.Url)" -ForegroundColor Cyan
    Write-Host "[INFO] Branch: $($run.Branch)" -ForegroundColor Cyan
    Write-Host "[INFO] SHA: $($run.Sha.Substring(0, 8))" -ForegroundColor Cyan

    if (-not (Test-WorkflowComplete $run)) {
        Write-Host "[INFO] Workflow is still running, waiting for completion..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        $run = Get-LatestWorkflowRun -Workflow $WorkflowName
        if (-not $run) {
            continue
        }
    }

    if (Test-WorkflowSuccessful $run) {
        Write-Host ""
        Write-Host "[SUCCESS] All CI/CD jobs passed! Pipeline is green." -ForegroundColor Green
        exit 0
    }

    $failedJobs = Get-FailedJobs -Run $run
    if (-not $failedJobs) {
        if ($run.Status -eq "completed" -and $run.Conclusion -eq "success") {
            Write-Host ""
            Write-Host "[SUCCESS] Workflow completed successfully!" -ForegroundColor Green
            exit 0
        }
        Write-Host "[INFO] No failed jobs, but workflow not successful" -ForegroundColor Yellow
        continue
    }

    Write-Host ""
    Write-Host "[INFO] Found $($failedJobs.Count) failed job(s):" -ForegroundColor Yellow
    foreach ($job in $failedJobs) {
        Write-Host "  - $($job.name): $($job.conclusion) ($($job.url))" -ForegroundColor Red
    }

    if ($WatchOnly) {
        Write-Host "[INFO] Watch-only mode: not attempting fixes" -ForegroundColor Yellow
        continue
    }

    $fixesApplied = $false
    foreach ($job in $failedJobs) {
        Write-Host ""
        Write-Host "[INFO] Attempting to fix: $($job.name)" -ForegroundColor Yellow

        $jobLower = $job.name.ToLower()
        if ($jobLower -like "*lint*") {
            if (-not (Test-LocalLint)) {
                $fixesApplied = Fix-LintIssues
            }
        } elseif ($jobLower -like "*format*" -or $jobLower -like "*black*") {
            if (-not (Test-LocalFormat)) {
                $fixesApplied = Fix-FormatIssues
            }
        } elseif ($jobLower -like "*test*") {
            $fixesApplied = Test-LocalTests
        }
    }

    if ($fixesApplied) {
        $commitMsg = "ci: auto-fix CI/CD pipeline issues (iteration $iteration)"
        if (Commit-AndPushFixes -Message $commitMsg) {
            Write-Host ""
            Write-Host "[INFO] Fixes pushed, waiting for next workflow run..." -ForegroundColor Yellow
            Start-Sleep -Seconds 15
        }
    } else {
        Write-Host ""
        Write-Host "[WARN] Could not auto-fix issues. Manual intervention required." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Failed jobs:" -ForegroundColor Red
        foreach ($job in $failedJobs) {
            Write-Host "  - $($job.name): $($job.url)" -ForegroundColor Red
        }
        exit 1
    }
}

Write-Host ""
Write-Host "[ERROR] Max iterations ($MaxIterations) reached. Pipeline not green." -ForegroundColor Red
exit 1
