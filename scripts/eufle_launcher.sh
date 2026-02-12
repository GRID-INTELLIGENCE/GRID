#!/bin/bash
# EUFLE Launcher Script
# This script ensures the environment is properly set before running EUFLE

# Mount E: drive if not already mounted
if [ ! -d /mnt/e/EUFLE ]; then
    echo "Mounting E: drive..."
    sudo mount -t drvfs E: /mnt/e
fi

# Set environment variables
export PYTHONPATH=/mnt/e/EUFLE:$PYTHONPATH
export EUFLE_HOME=/mnt/e/EUFLE
export LLAMACPP_PATH=/home/irfan/eufle_work/llama.cpp/build/bin

# Change to EUFLE directory
cd /mnt/e/EUFLE

# Run EUFLE with all arguments passed to this script
python3 eufle.py "$@"
