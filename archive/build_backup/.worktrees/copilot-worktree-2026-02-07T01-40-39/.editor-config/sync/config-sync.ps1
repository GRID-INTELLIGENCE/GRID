# config-sync.ps1 - Bidirectional sync VS Code & Windsurf settings
# Usage: .\config-sync.ps1 -Action pull|push|merge|compare
# 
# Actions:
#   pull  - Copy settings from C:\Users\irfan\AppData to E:\.editor-config (backup + sync)
#   push  - Deploy settings from E:\.editor-config to C:\Users\irfan\AppData (with backup)
#   merge - Intelligently merge MCP configs from both sources
#   compare - Show differences between sources

param(
    [ValidateSet("pull", "push", "merge", "compare", "status")]
    [string]$Action = "status",
    
    [switch]$NoBackup,
    [switch]$Force
)

# Configuration
$CodeUserPath = "$env:USERPROFILE\AppData\Roaming\Code\User"
$WindsurfUserPath = "$env:USERPROFILE\AppData\Roaming\Windsurf\User"
$ConfigRepoPath = "E:\.editor-config"
$BackupSuffix = "_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Colors for output
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

function Write-Status {
    param([string]$Message, [System.ConsoleColor]$Color = $Cyan)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $Yellow
}

# Validate paths
function Test-Paths {
    $paths = @(
        $CodeUserPath,
        $WindsurfUserPath,
        "$ConfigRepoPath"
    )
    
    foreach ($path in $paths) {
        if (-not (Test-Path $path)) {
            Write-Error-Custom "Path not found: $path"
            return $false
        }
    }
    return $true
}

# Backup file with timestamp
function Backup-File {
    param(
        [string]$FilePath,
        [string]$Description = ""
    )
    
    if ($NoBackup) {
        Write-Warning-Custom "Skipping backup (NoBackup flag set)"
        return
    }
    
    if (Test-Path $FilePath) {
        $BackupPath = "$FilePath$BackupSuffix"
        Copy-Item $FilePath $BackupPath -Force
        Write-Status "Backed up: $Description → $BackupPath" $Yellow
    }
}

# Pull action: Copy from C: to E:
function Invoke-Pull {
    Write-Status "=== PULL ACTION: C: → E: ===" $Cyan
    
    if (-not (Test-Paths)) { return }
    
    # Windsurf settings
    Write-Status "Pulling Windsurf settings..."
    Backup-File "$ConfigRepoPath\windsurf\settings.json" "Existing Windsurf config"
    Copy-Item "$WindsurfUserPath\settings.json" "$ConfigRepoPath\windsurf\settings.json" -Force
    Write-Success "Windsurf settings.json pulled"
    
    # VS Code settings
    Write-Status "Pulling VS Code settings..."
    Backup-File "$ConfigRepoPath\vscode\settings.json" "Existing VS Code config"
    Copy-Item "$CodeUserPath\settings.json" "$ConfigRepoPath\vscode\settings.json" -Force
    Write-Success "VS Code settings.json pulled"
    
    # MCP configs (if they exist)
    if (Test-Path "$CodeUserPath\mcp.json") {
        Copy-Item "$CodeUserPath\mcp.json" "$ConfigRepoPath\vscode\mcp.json" -Force
        Write-Success "VS Code mcp.json pulled"
    }
    
    Write-Status "Pull completed at $(Get-Date)" $Green
}

# Push action: Deploy from E: to C:
function Invoke-Push {
    Write-Status "=== PUSH ACTION: E: → C: ===" $Cyan
    
    if (-not (Test-Paths)) { return }
    
    if (-not $Force) {
        Write-Warning-Custom "This will overwrite settings on C:. Use -Force to confirm."
        return
    }
    
    # Backup existing
    Write-Status "Creating backups on C:..."
    Backup-File "$WindsurfUserPath\settings.json" "Current Windsurf settings"
    Backup-File "$CodeUserPath\settings.json" "Current VS Code settings"
    
    # Deploy Windsurf
    Write-Status "Deploying Windsurf settings..."
    if (Test-Path "$ConfigRepoPath\windsurf\settings.json") {
        Copy-Item "$ConfigRepoPath\windsurf\settings.json" "$WindsurfUserPath\settings.json" -Force
        Write-Success "Windsurf settings deployed"
    } else {
        Write-Error-Custom "Windsurf settings not found in repo"
    }
    
    # Deploy VS Code
    Write-Status "Deploying VS Code settings..."
    if (Test-Path "$ConfigRepoPath\vscode\settings.json") {
        Copy-Item "$ConfigRepoPath\vscode\settings.json" "$CodeUserPath\settings.json" -Force
        Write-Success "VS Code settings deployed"
    } else {
        Write-Error-Custom "VS Code settings not found in repo"
    }
    
    # Deploy MCP configs
    if (Test-Path "$ConfigRepoPath\vscode\mcp.json") {
        Copy-Item "$ConfigRepoPath\vscode\mcp.json" "$CodeUserPath\mcp.json" -Force
        Write-Success "VS Code MCP config deployed"
    }
    
    Write-Status "Push completed at $(Get-Date)" $Green
}

# Compare action: Show differences
function Invoke-Compare {
    Write-Status "=== COMPARE ACTION ===" $Cyan
    
    if (-not (Test-Paths)) { return }
    
    Write-Status "Comparing Windsurf settings..."
    $WindsurfRepo = "$ConfigRepoPath\windsurf\settings.json"
    if (Test-Path $WindsurfRepo) {
        Compare-Object -ReferenceObject (Get-Content "$WindsurfUserPath\settings.json") `
                      -DifferenceObject (Get-Content $WindsurfRepo) | 
            Format-Table -AutoSize
    }
    
    Write-Status "Comparing VS Code settings..."
    $VSCodeRepo = "$ConfigRepoPath\vscode\settings.json"
    if (Test-Path $VSCodeRepo) {
        Compare-Object -ReferenceObject (Get-Content "$CodeUserPath\settings.json") `
                      -DifferenceObject (Get-Content $VSCodeRepo) | 
            Format-Table -AutoSize
    }
}

# Merge action: Intelligently merge MCP configs
function Invoke-Merge {
    Write-Status "=== MERGE ACTION ===" $Cyan
    
    Write-Status "Merging MCP server configurations..."
    
    # Load shared MCP config
    $SharedMCP = "$ConfigRepoPath\shared\mcp-servers.json"
    if (-not (Test-Path $SharedMCP)) {
        Write-Error-Custom "Shared MCP config not found: $SharedMCP"
        return
    }
    
    $SharedConfig = Get-Content $SharedMCP | ConvertFrom-Json
    
    # Create VS Code MCP from shared config
    $VSCodeMCP = @{
        "mcpServers" = $SharedConfig.mcpServers
    } | ConvertTo-Json -Depth 10
    
    Set-Content -Path "$ConfigRepoPath\vscode\mcp.json" -Value $VSCodeMCP -Force
    Write-Success "Generated VS Code MCP config"
    
    # Create Windsurf MCP from shared config
    $WindsurfMCP = @{
        "mcpServers" = $SharedConfig.mcpServers
    } | ConvertTo-Json -Depth 10
    
    Set-Content -Path "$ConfigRepoPath\windsurf\mcp.json" -Value $WindsurfMCP -Force
    Write-Success "Generated Windsurf MCP config"
    
    Write-Status "Merge completed at $(Get-Date)" $Green
}

# Status action: Show current state
function Invoke-Status {
    Write-Status "=== STATUS CHECK ===" $Cyan
    
    Write-Status "Checking paths:"
    
    $paths = @{
        "Windsurf settings (C:)" = "$WindsurfUserPath\settings.json"
        "VS Code settings (C:)" = "$CodeUserPath\settings.json"
        "Config repo (E:)" = "$ConfigRepoPath"
        "Shared MCP config" = "$ConfigRepoPath\shared\mcp-servers.json"
        "Ollama config" = "$ConfigRepoPath\shared\ollama-config.json"
        "Sync script" = "$ConfigRepoPath\sync\config-sync.ps1"
    }
    
    foreach ($name in $paths.Keys) {
        $path = $paths[$name]
        $exists = Test-Path $path
        $status = if ($exists) { "✓" } else { "✗" }
        Write-Host "$status $name"
        Write-Host "   → $path"
    }
    
    # Check Ollama
    Write-Status "Checking Ollama..."
    try {
        $OllamaUrl = "http://localhost:11434/api/tags"
        $Response = Invoke-WebRequest -Uri $OllamaUrl -ErrorAction Stop -TimeoutSec 2
        $Models = ($Response.Content | ConvertFrom-Json).models
        Write-Success "Ollama is running. Available models:"
        $Models | ForEach-Object { Write-Host "  - $($_.name)" }
    } catch {
        Write-Error-Custom "Ollama not accessible at localhost:11434"
    }
}

# Main execution
switch ($Action) {
    "pull" { Invoke-Pull }
    "push" { Invoke-Push }
    "merge" { Invoke-Merge }
    "compare" { Invoke-Compare }
    "status" { Invoke-Status }
    default { 
        Write-Error-Custom "Unknown action: $Action"
        Write-Host "Usage: .\config-sync.ps1 -Action pull|push|merge|compare|status"
    }
}

Write-Host ""
Write-Status "Script completed" $Green
