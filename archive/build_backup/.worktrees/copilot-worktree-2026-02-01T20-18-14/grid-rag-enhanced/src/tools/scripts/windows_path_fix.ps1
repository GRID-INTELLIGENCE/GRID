# scripts/windows_path_fix.ps1
# Enable Long Paths in Windows Registry
Write-Host "Checking Long Paths configuration..."

try {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"
    $name = "LongPathsEnabled"
    $current = Get-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue

    if ($null -eq $current) {
        Write-Host "LongPathsEnabled not found. Creating..."
        New-ItemProperty -Path $path -Name $name -Value 1 -PropertyType DWord -Force
        Write-Host "Long Paths ENABLED."
    }
    elseif ($current.LongPathsEnabled -ne 1) {
        Write-Host "LongPathsEnabled is disabled (0). Enabling..."
        Set-ItemProperty -Path $path -Name $name -Value 1 -Type DWord
        Write-Host "Long Paths ENABLED."
    }
    else {
        Write-Host "Long Paths are already enabled."
    }
}
catch {
    Write-Error "Failed to modify registry. extensive permissions may be required. Run as Administrator."
    Write-Error $_
}
