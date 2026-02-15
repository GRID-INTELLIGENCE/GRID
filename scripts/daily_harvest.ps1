# Daily Harvest Routine - Robust Windows Solution
# Runs repository analysis and artifact generation with error handling

$LogFile = "E:\logs\daily_harvest.log"
if (!(Test-Path "E:\logs")) { New-Item -ItemType Directory -Path "E:\logs" }

function Log-Message($Message) {
    $Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Stamp - $Message" | Out-File -FilePath $LogFile -Append
    Write-Host "$Stamp - $Message"
}

try {
    Log-Message "Starting daily harvest routine..."

    # Check if backend is available
    $MaxRetries = 5
    $RetryCount = 0
    $BackendReady = $false

    while (-not $BackendReady -and $RetryCount -lt $MaxRetries) {
        try {
            $Health = Invoke-RestMethod -Uri 'http://localhost:8000/api/harness/health' -Method GET -ErrorAction Stop
            $BackendReady = $true
            Log-Message "Backend is healthy."
        } catch {
            $RetryCount++
            Log-Message "Backend not reachable. Retrying ($RetryCount/$MaxRetries)..."
            Start-Sleep -Seconds 10
        }
    }

    if (-not $BackendReady) {
        Log-Message "ERROR: Backend failed to respond after $MaxRetries retries. Aborting."
        exit 1
    }

    # 1. Create new run
    Log-Message "Creating new run..."
    $runBody = @{
        display_name = "Daily Harvest - $(Get-Date -Format 'yyyy-MM-dd')"
        tags = @("daily", "automated")
    } | ConvertTo-Json

    $runResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/harness/runs' -Method POST -ContentType 'application/json' -Body $runBody -ErrorAction Stop
    $runId = $runResponse.run_id
    Log-Message "Run created with ID: $runId"

    # 2. Execute harvest
    Log-Message "Executing harvest for run $runId..."
    Invoke-RestMethod -Uri "http://localhost:8000/api/harness/harvest?run_id=$runId&refresh=true" -Method POST -ErrorAction Stop

    # 3. Generate packs
    Log-Message "Generating packs for run $runId..."
    Invoke-RestMethod -Uri "http://localhost:8000/api/harness/runs/$runId/packs/generate" -Method POST -ErrorAction Stop

    Log-Message "Daily harvest completed successfully! Run ID: $runId"
    Log-Message "Artifacts available at: http://localhost:8000/api/harness/runs/$runId/packs"

} catch {
    Log-Message "FATAL ERROR in daily harvest: $_"
    exit 1
}
