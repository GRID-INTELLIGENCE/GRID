#!/bin/bash

# ============================================================================
# Network Security System - Installation Script
# ============================================================================
# This script installs and configures the network security system
# for comprehensive network access control and monitoring.
#
# Usage:
#   bash security/install.sh
#   bash security/install.sh --quick    # Skip confirmation prompts
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECURITY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SECURITY_DIR")"
QUICK_MODE=false

# Parse arguments
if [[ "$1" == "--quick" ]]; then
    QUICK_MODE=true
fi

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

confirm() {
    if [[ "$QUICK_MODE" == "true" ]]; then
        return 0
    fi

    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Installation Steps
# ============================================================================

print_header "🔒 NETWORK SECURITY SYSTEM INSTALLATION"
echo
echo "This script will install and configure comprehensive network security"
echo "monitoring for your codebase. By default, ALL network access will be"
echo "DENIED until explicitly whitelisted."
echo
echo "Installation directory: $SECURITY_DIR"
echo "Project root: $ROOT_DIR"
echo

if ! confirm "Continue with installation?"; then
    echo "Installation cancelled."
    exit 0
fi

echo

# ----------------------------------------------------------------------------
# Step 1: Check Python version
# ----------------------------------------------------------------------------

print_info "Step 1/8: Checking Python version..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"
echo

# ----------------------------------------------------------------------------
# Step 2: Create logs directory
# ----------------------------------------------------------------------------

print_info "Step 2/8: Creating logs directory..."

LOGS_DIR="$SECURITY_DIR/logs"
mkdir -p "$LOGS_DIR"
print_success "Logs directory created: $LOGS_DIR"
echo

# ----------------------------------------------------------------------------
# Step 3: Install Python dependencies
# ----------------------------------------------------------------------------

print_info "Step 3/8: Installing Python dependencies..."

if [[ -f "$SECURITY_DIR/requirements.txt" ]]; then
    echo "   Installing from requirements.txt..."
    python3 -m pip install -r "$SECURITY_DIR/requirements.txt" --quiet
    print_success "Dependencies installed"
else
    print_warning "requirements.txt not found, installing manually..."
    python3 -m pip install pyyaml rich --quiet
    print_success "Core dependencies installed"
fi
echo

# ----------------------------------------------------------------------------
# Step 4: Verify configuration file
# ----------------------------------------------------------------------------

print_info "Step 4/8: Verifying configuration file..."

CONFIG_FILE="$SECURITY_DIR/network_access_control.yaml"
if [[ -f "$CONFIG_FILE" ]]; then
    print_success "Configuration file found: network_access_control.yaml"
else
    print_error "Configuration file not found!"
    print_info "Expected location: $CONFIG_FILE"
    exit 1
fi
echo

# ----------------------------------------------------------------------------
# Step 5: Test security module
# ----------------------------------------------------------------------------

print_info "Step 5/8: Testing security module..."

cd "$ROOT_DIR"
python3 -c "
import sys
sys.path.insert(0, '$ROOT_DIR')
try:
    import security
    print('✅ Security module loaded successfully')
except Exception as e:
    print(f'❌ Failed to load security module: {e}')
    sys.exit(1)
" || exit 1

echo

# ----------------------------------------------------------------------------
# Step 6: Scan codebase for network usage
# ----------------------------------------------------------------------------

print_info "Step 6/8: Scanning codebase for network usage..."
echo "   This may take a few minutes for large projects..."
echo

if [[ -f "$SECURITY_DIR/integrate_security.py" ]]; then
    python3 "$SECURITY_DIR/integrate_security.py" --scan --root "$ROOT_DIR" || {
        print_warning "Scan encountered some issues but continuing..."
    }
    echo
else
    print_warning "Integration scanner not found, skipping scan"
    echo
fi

# ----------------------------------------------------------------------------
# Step 7: Create backup of configuration
# ----------------------------------------------------------------------------

print_info "Step 7/8: Creating configuration backup..."

BACKUP_FILE="$SECURITY_DIR/network_access_control.yaml.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
print_success "Backup created: $(basename $BACKUP_FILE)"
echo

# ----------------------------------------------------------------------------
# Step 8: Initialize security system
# ----------------------------------------------------------------------------

print_info "Step 8/8: Initializing security system..."

# Test that the system works
python3 -c "
import sys
sys.path.insert(0, '$ROOT_DIR')
import os
os.environ['DISABLE_NETWORK_SECURITY'] = 'false'
import security
status = security.get_status()
print(f\"Status: {status['status']}\")
print(f\"Mode: {status['mode']}\")
print(f\"Default Policy: {status['default_policy']}\")
" || {
    print_error "Failed to initialize security system"
    exit 1
}

print_success "Security system initialized"
echo

# ============================================================================
# Post-Installation
# ============================================================================

print_header "✅ INSTALLATION COMPLETE"
echo
echo "Network security system has been installed and configured."
echo
echo -e "${GREEN}📋 Next Steps:${NC}"
echo
echo "1. Review the configuration:"
echo "   cat security/network_access_control.yaml"
echo
echo "2. Start monitoring (in a separate terminal):"
echo "   python security/monitor_network.py dashboard"
echo
echo "3. Run your application and observe blocked requests:"
echo "   python your_main_application.py"
echo
echo "4. Check what was blocked:"
echo "   python security/monitor_network.py blocked"
echo
echo "5. Whitelist trusted domains:"
echo "   python security/monitor_network.py add api.example.com"
echo
echo "6. Enable network access (after whitelisting):"
echo "   python security/monitor_network.py enable"
echo
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "   - ALL network access is DENIED by default"
echo "   - Review blocked requests carefully before whitelisting"
echo "   - Monitor for data leaks: python security/monitor_network.py leaks"
echo "   - Read documentation: security/README.md"
echo
echo -e "${BLUE}📁 Files and Directories:${NC}"
echo "   Config:  $CONFIG_FILE"
echo "   Logs:    $LOGS_DIR"
echo "   Monitor: python security/monitor_network.py dashboard"
echo
echo -e "${GREEN}🔒 Security Status:${NC}"
python3 -c "
import sys
sys.path.insert(0, '$ROOT_DIR')
import security
security.print_status()
" 2>/dev/null || echo "   Run: python -c 'import security; security.print_status()'"
echo
echo -e "${BLUE}============================================================================${NC}"
echo

# ============================================================================
# Create quick start scripts
# ============================================================================

# Create monitor script
cat > "$SECURITY_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# Quick monitor script
cd "$(dirname "$0")/.."
python security/monitor_network.py dashboard
EOF
chmod +x "$SECURITY_DIR/monitor.sh"

# Create enable network script
cat > "$SECURITY_DIR/enable_network.sh" << 'EOF'
#!/bin/bash
# Enable network access
cd "$(dirname "$0")/.."
python security/monitor_network.py enable
EOF
chmod +x "$SECURITY_DIR/enable_network.sh"

# Create disable network script
cat > "$SECURITY_DIR/disable_network.sh" << 'EOF'
#!/bin/bash
# Disable network access
cd "$(dirname "$0")/.."
python security/monitor_network.py disable
EOF
chmod +x "$SECURITY_DIR/disable_network.sh"

print_success "Quick start scripts created:"
echo "   - security/monitor.sh (launch dashboard)"
echo "   - security/enable_network.sh"
echo "   - security/disable_network.sh"
echo

print_header "🎉 Installation successful!"
echo

exit 0
