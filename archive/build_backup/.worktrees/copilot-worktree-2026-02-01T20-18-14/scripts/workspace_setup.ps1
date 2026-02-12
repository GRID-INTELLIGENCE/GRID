# Workspace Setup Script
# Verifies workspace initialization and validates dependencies

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Workspace Setup Verification" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

$errors = @()
$warnings = @()

# Check Python environment
Write-Host "`n[1/5] Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
    } else {
        $errors += "Python not found"
        Write-Host "  ✗ Python not found" -ForegroundColor Red
    }
} catch {
    $errors += "Python check failed: $_"
    Write-Host "  ✗ Python check failed: $_" -ForegroundColor Red
}

# Check Node.js/npm versions
Write-Host "`n[2/5] Checking Node.js/npm versions..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
        Write-Host "  ✓ npm: $npmVersion" -ForegroundColor Green
    } else {
        $warnings += "Node.js/npm not found"
        Write-Host "  ⚠ Node.js/npm not found" -ForegroundColor Yellow
    }
} catch {
    $warnings += "Node.js check failed: $_"
    Write-Host "  ⚠ Node.js check failed: $_" -ForegroundColor Yellow
}

# Validate EUFLE setup
Write-Host "`n[3/5] Validating EUFLE setup..." -ForegroundColor Yellow
try {
    $euflePath = "E:\EUFLE"
    if (Test-Path $euflePath) {
        Write-Host "  ✓ EUFLE directory exists" -ForegroundColor Green
        
        # Check for key files
        $requiredFiles = @(
            "$euflePath\eufle.py",
            "$euflePath\studio"
        )
        foreach ($file in $requiredFiles) {
            if (Test-Path $file) {
                Write-Host "  ✓ Found: $(Split-Path $file -Leaf)" -ForegroundColor Green
            } else {
                $warnings += "Missing: $file"
                Write-Host "  ⚠ Missing: $(Split-Path $file -Leaf)" -ForegroundColor Yellow
            }
        }
    } else {
        $warnings += "EUFLE directory not found"
        Write-Host "  ⚠ EUFLE directory not found" -ForegroundColor Yellow
    }
} catch {
    $warnings += "EUFLE validation failed: $_"
    Write-Host "  ⚠ EUFLE validation failed: $_" -ForegroundColor Yellow
}

# Check workspace utilities
Write-Host "`n[4/5] Checking workspace utilities..." -ForegroundColor Yellow
try {
    $utilsPath = "E:\workspace_utils"
    if (Test-Path $utilsPath) {
        Write-Host "  ✓ workspace_utils package found" -ForegroundColor Green
        
        # Test import
        python -c "import sys; sys.path.insert(0, 'E:\\'); from workspace_utils import RepositoryAnalyzer; print('  ✓ Import successful')" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $warnings += "workspace_utils import failed"
            Write-Host "  ⚠ workspace_utils import failed" -ForegroundColor Yellow
        }
    } else {
        $warnings += "workspace_utils package not found"
        Write-Host "  ⚠ workspace_utils package not found" -ForegroundColor Yellow
    }
} catch {
    $warnings += "Workspace utilities check failed: $_"
    Write-Host "  ⚠ Workspace utilities check failed: $_" -ForegroundColor Yellow
}

# Run utility script tests (if available)
Write-Host "`n[5/5] Running utility script tests..." -ForegroundColor Yellow
try {
    # This would run actual tests when test suite is implemented
    Write-Host "  ⚠ Test suite not yet implemented" -ForegroundColor Yellow
} catch {
    $warnings += "Test execution failed: $_"
    Write-Host "  ⚠ Test execution failed: $_" -ForegroundColor Yellow
}

# Summary
Write-Host "`n===========================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "`n✓ All checks passed! Workspace is ready." -ForegroundColor Green
    exit 0
} elseif ($errors.Count -eq 0) {
    Write-Host "`n⚠ Some warnings found (see above), but workspace is functional." -ForegroundColor Yellow
    Write-Host "Warnings: $($warnings.Count)" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "`n✗ Errors found:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    if ($warnings.Count -gt 0) {
        Write-Host "`nWarnings: $($warnings.Count)" -ForegroundColor Yellow
    }
    exit 1
}