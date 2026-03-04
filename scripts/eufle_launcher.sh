#!/bin/bash
# EUFLE Launcher Script (user-space; no sudo inside script)

set -e

if [ ! -d /mnt/e ]; then
    echo "E: not mounted. Run once (WSL): sudo mount -t drvfs E: /mnt/e"
    exit 1
fi
if [ ! -d /mnt/e/EUFLE ]; then
    echo "EUFLE directory not found at /mnt/e/EUFLE. Ensure E: is mounted and the EUFLE project exists at E:\\EUFLE."
    exit 1
fi

export PYTHONPATH=/mnt/e/EUFLE:$PYTHONPATH
export EUFLE_HOME=/mnt/e/EUFLE
export LLAMACPP_PATH="${LLAMACPP_PATH:-/home/irfan/eufle_work/llama.cpp/build/bin}"

cd /mnt/e/EUFLE
exec python3 eufle.py "$@"
