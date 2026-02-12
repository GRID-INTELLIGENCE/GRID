#!/bin/bash
# OpenCode CLI Wrapper for WSL2
# Provides unified interface for OpenCode commands

OPENCODE_DIR="/mnt/c/Users/irfan/opencode"
OPENCODE_BIN="${OPENCODE_DIR}/packages/opencode/bin/opencode"
BUN_BIN="${HOME}/.bun/bin/bun"

# Check if bun exists
if [ ! -f "$BUN_BIN" ]; then
    echo "Bun not found. Please install bun first."
    exit 1
fi

# Check if OpenCode exists
if [ ! -f "$OPENCODE_BIN" ]; then
    echo "OpenCode CLI not found at $OPENCODE_BIN"
    exit 1
fi

# Change to opencode directory to run properly
cd "$OPENCODE_DIR"

# Use bun to run OpenCode with all arguments
"$BUN_BIN" run "$OPENCODE_BIN" "$@"
