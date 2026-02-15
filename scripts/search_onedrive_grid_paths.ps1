# OneDrive GRID path reference search
# Run from user or elevated shell. Finds configs/docs that reference E:\grid, PROJECT_GRID, or grid-rag-enhanced.
# Deliverable: list of files and whether they are correct once E:\grid junction exists.

$ErrorActionPreference = 'Continue'
$extensions = '\.(json|env|template|md|code-workspace|yml|yaml)$'
$pattern = 'E:\\\\grid|E:/grid|PROJECT_GRID|grid-rag-enhanced|E:\\\\_projects'

$locations = @(
    "$env:UserProfile\OneDrive",
    "$env:UserProfile\OneDrive - *"
)

$results = @()
foreach ($root in $locations) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -match $extensions } |
        ForEach-Object {
            $matches = Select-String -Path $_.FullName -Pattern $pattern -ErrorAction SilentlyContinue
            if ($matches) {
                foreach ($m in $matches) {
                    $results += [PSCustomObject]@{
                        Path       = $_.FullName
                        LineNumber = $m.LineNumber
                        Line       = $m.Line.Trim()
                    }
                }
            }
        }
}

# Output deliverable
Write-Output "=== OneDrive GRID path reference search ==="
Write-Output "Searched: $($locations -join ', ')"
Write-Output "Matches: $($results.Count)"
Write-Output ""
if ($results.Count -eq 0) {
    Write-Output "No matching files found. Paths are either not in OneDrive or already correct (E:\grid junction resolves)."
} else {
    $results | Format-Table -AutoSize -Wrap
    Write-Output ""
    Write-Output "Action: Once E:\grid junction exists, PROJECT_GRID=E:\grid and path E:/grid in workspaces resolve automatically. No edit needed unless path was wrong."
}
