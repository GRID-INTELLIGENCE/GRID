#!/bin/bash
# Quick Health Check Script for WSL2
# Provides fast workspace validation

echo "=========================================="
echo "Workspace Health Check"
echo "=========================================="

ERRORS=0
WARNINGS=0

# Check disk space
echo ""
echo "[1/4] Checking disk space..."
df -h / | tail -1 | awk '{print "  Disk usage: " $5 " (" $3 "/" $2 ")"}'
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 90 ]; then
    echo "  ✗ Disk usage is above 90%" 
    ((ERRORS++))
elif [ "$USAGE" -gt 80 ]; then
    echo "  ⚠ Disk usage is above 80%"
    ((WARNINGS++))
else
    echo "  ✓ Disk space OK"
fi

# Verify services (if any)
echo ""
echo "[2/4] Checking services..."
# Add service checks here if needed
echo "  ✓ Service checks passed (none configured)"

# Test OpenCode connectivity (if installed)
echo ""
echo "[3/4] Testing OpenCode connectivity..."
if command -v opencode &> /dev/null; then
    OPENCODE_VERSION=$(opencode --version 2>&1)
    if [ $? -eq 0 ]; then
        echo "  ✓ OpenCode CLI available: $OPENCODE_VERSION"
    else
        echo "  ⚠ OpenCode CLI found but not responding"
        ((WARNINGS++))
    fi
else
    echo "  ⚠ OpenCode CLI not installed (optional)"
    ((WARNINGS++))
fi

# Validate workspace paths
echo ""
echo "[4/4] Validating workspace paths..."
WORKSPACE_ROOT="/mnt/e"
REQUIRED_PATHS=(
    "$WORKSPACE_ROOT/workspace_utils"
    "$WORKSPACE_ROOT/EUFLE"
    "$WORKSPACE_ROOT/.vscode"
)

for path in "${REQUIRED_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "  ✓ Found: $(basename $path)"
    else
        echo "  ⚠ Missing: $(basename $path)"
        ((WARNINGS++))
    fi
done

# Summary
echo ""
echo "=========================================="
echo "Health Check Summary"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✓ All checks passed! Workspace is healthy."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠ $WARNINGS warning(s) found, but workspace is functional."
    exit 0
else
    echo "✗ $ERRORS error(s) and $WARNINGS warning(s) found."
    exit 1
fi