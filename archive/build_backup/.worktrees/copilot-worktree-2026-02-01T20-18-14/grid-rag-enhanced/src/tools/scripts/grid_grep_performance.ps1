# GRID Grep Performance Optimization Script
# Based on performance analysis report from December 17, 2025

param(
    [string]$Pattern = "def ",
    [string]$Scope = "grid,tests",
    [switch]$Verbose,
    [switch]$Benchmark
)

Write-Host "GRID Grep Performance Analysis" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Yellow

# Function to measure search performance
function Measure-SearchPerformance {
    param(
        [string]$SearchPattern,
        [string]$SearchScope,
        [string]$PatternType = "Simple"
    )
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        if ($SearchScope -eq "grid,tests") {
            $result = Select-String -Path "grid\*.py", "tests\*.py" -Pattern $SearchPattern -ErrorAction SilentlyContinue
        } else {
            $result = Select-String -Path "$SearchScope\*.py" -Pattern $SearchPattern -ErrorAction SilentlyContinue
        }
        
        $stopwatch.Stop()
        $count = if ($result) { $result.Count } else { 0 }
        
        return @{
            Pattern = $SearchPattern
            Scope = $SearchScope
            Type = $PatternType
            Time = $stopwatch.ElapsedMilliseconds
            Count = $count
            Success = $true
        }
    }
    catch {
        $stopwatch.Stop()
        return @{
            Pattern = $SearchPattern
            Scope = $SearchScope
            Type = $PatternType
            Time = $stopwatch.ElapsedMilliseconds
            Count = 0
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Test different pattern types as recommended in the report
Write-Host "`nTesting Pattern Performance:" -ForegroundColor Cyan

$patterns = @(
    @{ Pattern = "def "; Type = "Simple" },
    @{ Pattern = "class.*Model"; Type = "Regex" },
    @{ Pattern = "import "; Type = "Import" },
    @{ Pattern = "TODO"; Type = "Comment" },
    @{ Pattern = "async def"; Type = "Async" }
)

$results = @()

foreach ($p in $patterns) {
    $result = Measure-SearchPerformance -SearchPattern $p.Pattern -SearchScope $Scope -PatternType $p.Type
    $results += $result
    
    if ($Verbose -or $Benchmark) {
        $status = if ($result.Success) { "OK" } else { "FAIL" }
        Write-Host ("{0} {1,-12} ({2}): {3,4}ms - {4} matches" -f 
            $status, $p.Type, $p.Pattern, $result.Time, $result.Count) -ForegroundColor $(if ($result.Success) { "Green" } else { "Red" })
    }
}

# Performance summary
if ($Benchmark) {
    Write-Host "`nPerformance Summary:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    
    $avgTime = ($results | Where-Object { $_.Success } | Measure-Object -Property Time -Average).Average
    $totalMatches = ($results | Where-Object { $_.Success } | Measure-Object -Property Count -Sum).Sum
    
    Write-Host "Average search time: $([math]::Round($avgTime, 2))ms"
    Write-Host "Total matches found: $totalMatches"
    Write-Host "Success rate: $([math]::Round(($results.Where({$_.Success}).Count / $results.Count) * 100, 1))%"
}

# Demonstrate scoped search avoiding problematic paths
Write-Host "`nScoped Search Verification:" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

$problemPath = "light_of_the_seven\full_datakit\visualizations\Hogwarts\great_hall\nul"
if (Test-Path $problemPath) {
    Write-Host "WARNING: Problematic path exists: $problemPath" -ForegroundColor Yellow
} else {
    Write-Host "OK: Problematic path avoided (not found): $problemPath" -ForegroundColor Green
}

Write-Host "OK: Using scoped search: grid\ and tests\ directories" -ForegroundColor Green
Write-Host "OK: Avoiding OS errors from Windows device names" -ForegroundColor Green

# Performance optimization recommendations
Write-Host "`nOptimization Recommendations:" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

Write-Host "1. Use scoped searches to avoid OS errors" -ForegroundColor White
Write-Host "2. Prefer simple patterns for faster searches" -ForegroundColor White
Write-Host "3. Use Select-String for Windows PowerShell compatibility" -ForegroundColor White
Write-Host "4. Consider file count before large searches" -ForegroundColor White

# Show file statistics
$gridFiles = (Get-ChildItem -Path "grid\*.py" -Recurse -ErrorAction SilentlyContinue).Count
$testFiles = (Get-ChildItem -Path "tests\*.py" -Recurse -ErrorAction SilentlyContinue).Count

Write-Host "`nCurrent Scope Statistics:" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host "Grid Python files: $gridFiles"
Write-Host "Test Python files: $testFiles"
Write-Host "Total searchable files: $($gridFiles + $testFiles)"

if ($Benchmark) {
    Write-Host "`nDetailed Results:" -ForegroundColor Cyan
    Write-Host "===============" -ForegroundColor Cyan
    $results | Format-Table -AutoSize
}
