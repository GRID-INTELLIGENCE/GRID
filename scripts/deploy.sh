#!/bin/bash
# Deployment Script for Enhanced RAG Server

set -e

echo "=========================================="
echo "Enhanced RAG Server Deployment"
echo "=========================================="

# Configuration
PYTHON_VERSION="3.13"
DEPLOY_DIR="/opt/grid-rag-enhanced"
BACKUP_DIR="/opt/grid-rag-enhanced-backups"
LOG_DIR="/var/log/grid-rag-enhanced"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root or with sudo"
    exit 1
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$DEPLOY_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    print_status "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Backup existing deployment
if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
    print_status "Backing up existing deployment..."
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR/$BACKUP_NAME"
    print_status "Backup created: $BACKUP_NAME"
fi

# Copy deployment files
print_status "Copying deployment files..."
cp -r src/ "$DEPLOY_DIR/"
cp -r tests/ "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp pyproject.toml "$DEPLOY_DIR/"
cp -r mcp-setup/ "$DEPLOY_DIR/"
cp -r workspace/ "$DEPLOY_DIR/"

# Create virtual environment
print_status "Creating virtual environment..."
cd "$DEPLOY_DIR"
uv venv --python $PYTHON_VERSION

# Install dependencies
print_status "Installing dependencies..."
source .venv/bin/activate
uv sync --group dev --group test

# Verify installation
print_status "Verifying installation..."
python -c "from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer"
python -c "from tools.rag.conversational_rag import create_conversational_rag_engine"
python -c "from src.application.mothership.rag_handlers import register_rag_handlers; register_rag_handlers()"

# Create systemd service files
print_status "Creating systemd services..."

# Enhanced RAG Server
cat > /etc/systemd/system/grid-rag-enhanced.service << EOF
[Unit]
Description=GRID Enhanced RAG MCP Server
After=network.target

[Service]
Type=simple
User=grid
Group=grid
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/.venv/bin"
ExecStart=$DEPLOY_DIR/.venv/bin/python -m grid.mcp.enhanced_rag_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Memory MCP Server
cat > /etc/systemd/system/memory-mcp.service << EOF
[Unit]
Description=Memory MCP Server
After=network.target

[Service]
Type=simple
User=grid
Group=grid
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/.venv/bin"
ExecStart=$DEPLOY_DIR/.venv/bin/python workspace/mcp/servers/memory/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Agentic MCP Server
cat > /etc/systemd/system/grid-agentic.service << EOF
[Unit]
Description=GRID Agentic MCP Server
After=network.target

[Service]
Type=simple
User=grid
Group=grid
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/.venv/bin"
ExecStart=$DEPLOY_DIR/.venv/bin/python workspace/mcp/servers/agentic/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
print_status "Enabling services..."
systemctl daemon-reload
systemctl enable grid-rag-enhanced.service
systemctl enable memory-mcp.service
systemctl enable grid-agentic.service

# Start services
print_status "Starting services..."
systemctl start grid-rag-enhanced.service
systemctl start memory-mcp.service
systemctl start grid-agentic.service

# Wait for services to start
sleep 5

# Check service status
print_status "Checking service status..."
systemctl status grid-rag-enhanced.service --no-pager
systemctl status memory-mcp.service --no-pager
systemctl status grid-agentic.service --no-pager

# Create log rotation config
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/grid-rag-enhanced << EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 grid grid
}
EOF

# Print summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - grid-rag-enhanced (port 8002)"
echo "  - memory-mcp (port 8003)"
echo "  - grid-agentic (port 8004)"
echo ""
echo "Management commands:"
echo "  systemctl status grid-rag-enhanced"
echo "  systemctl restart grid-rag-enhanced"
echo "  systemctl stop grid-rag-enhanced"
echo "  journalctl -u grid-rag-enhanced -f"
echo ""
echo "Logs: $LOG_DIR"
echo "Deployment: $DEPLOY_DIR"
echo "Backups: $BACKUP_DIR"
echo ""
echo "To rollback:"
echo "  systemctl stop grid-rag-enhanced memory-mcp grid-agentic"
echo "  rm -rf $DEPLOY_DIR/*"
echo "  cp -r $BACKUP_DIR/<backup-name>/* $DEPLOY_DIR/"
echo "  systemctl start grid-rag-enhanced memory-mcp grid-agentic"
echo ""

print_status "Deployment successful!"
