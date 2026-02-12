#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# Path to the actual implementation
EUFLE_ROOT = Path(r"E:\EUFLE")
ACTUAL_CLI = EUFLE_ROOT / "eufle.py"

def main():
    if not ACTUAL_CLI.exists():
        print(f"Error: EUFLE implementation not found at {ACTUAL_CLI}")
        sys.exit(1)

    # Run the actual CLI with all arguments
    cmd = [sys.executable, str(ACTUAL_CLI)] + sys.argv[1:]

    # Ensure the environment variables are set for this subprocess
    env = os.environ.copy()
    if not env.get("EUFLE_DEFAULT_PROVIDER"):
        env["EUFLE_DEFAULT_PROVIDER"] = "ollama"
    if not env.get("EUFLE_MODEL"):
        env["EUFLE_MODEL"] = "mistral-nemo:latest"

    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    main()
