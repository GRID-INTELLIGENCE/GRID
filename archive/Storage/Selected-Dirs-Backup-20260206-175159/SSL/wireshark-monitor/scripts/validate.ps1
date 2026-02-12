$errors = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    'E:\SSL\wireshark-monitor\scripts\route_wsl_traffic.ps1',
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -eq 0) {
    Write-Host 'PARSE OK - no syntax errors found'
} else {
    Write-Host "PARSE ERRORS: $($errors.Count)"
    foreach ($e in $errors) {
        Write-Host "  Line $($e.Extent.StartLineNumber): $($e.Message)"
    }
}
