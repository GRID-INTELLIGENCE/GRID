#!/bin/bash
# EUFLE launcher

set -e

if [ ! -d /mnt/e/EUFLE ]; then
  sudo mount -t drvfs E: /mnt/e
fi

export PYTHONPATH=/mnt/e/EUFLE:$PYTHONPATH
export EUFLE_HOME=/mnt/e/EUFLE
export LLAMACPP_PATH=/home/irfan/eufle_work/llama.cpp/build/bin

cd /mnt/e/EUFLE
python3 eufle.py "$@"
