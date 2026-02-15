# OpenCode CLI Wrapper for Windows PowerShell
# Uses WSL2 for OpenCode execution

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Check if WSL is available
$wslAvailable = Get-Command wsl -ErrorAction SilentlyContinue

if (-not $wslAvailable) {
    Write-Host "WSL is not available. OpenCode CLI requires WSL2." -ForegroundColor Red
    Write-Host "Please install WSL2: wsl --install" -ForegroundColor Yellow
    exit 1
}

# Convert PowerShell arguments to WSL format
$wslArgs = @()
foreach ($arg in $Args) {
    # Convert Windows paths to WSL paths if needed
    if ($arg -match '^[A-Z]:\\') {
        $wslPath = $arg -replace '^([A-Z]):\\', '/mnt/$1/' -replace '\\', '/'
        $wslArgs += $wslPath
    } else {
        $wslArgs += $arg
    }
}

# Get script directory for wrapper script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wrapperScript = Join-Path $scriptDir "opencode_wrapper.sh"

# Convert Windows path to WSL path
$wslScriptPath = $wrapperScript -replace '^([A-Z]):\\', '/mnt/$1/' -replace '\\', '/'

# Execute via WSL
wsl bash $wslScriptPath $wslArgs

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}