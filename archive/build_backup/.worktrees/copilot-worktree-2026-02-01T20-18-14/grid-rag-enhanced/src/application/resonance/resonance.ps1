# Activity Resonance Tool - PowerShell Wrapper
# Provides seamless integration with PowerShell terminal

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Query,

    [Parameter(Mandatory=$false)]
    [ValidateSet("general", "code", "config")]
    [string]$Type = "general",

    [Parameter(Mandatory=$false)]
    [switch]$Json,

    [Parameter(Mandatory=$false)]
    [switch]$NoContext,

    [Parameter(Mandatory=$false)]
    [switch]$NoPaths,

    [Parameter(Mandatory=$false)]
    [string]$Context
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# Build command arguments
$Args = @(
    "-m", "application.resonance.cli",
    $Query,
    "--type", $Type
)

if ($Json) {
    $Args += "--json"
}

if ($NoContext) {
    $Args += "--no-context"
}

if ($NoPaths) {
    $Args += "--no-paths"
}

if ($Context) {
    $Args += "--context", $Context
}

# Execute Python command
try {
    python $Args
    exit $LASTEXITCODE
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

