"""
PYTHONPATH Cleanup Script
=========================
Removes non-existent paths from PYTHONPATH environment variable.
"""

import os
import sys


def clean_python_path():
    """Remove non-existent paths from PYTHONPATH."""
    current_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
    valid_paths = [p for p in current_paths if p and os.path.exists(p)]

    # Update environment variable
    os.environ['PYTHONPATH'] = os.pathsep.join(valid_paths)

    print(f"PYTHONPATH Cleanup Results:")
    print(f"  Original paths: {len(current_paths)}")
    print(f"  Valid paths: {len(valid_paths)}")
    print(f"  Removed: {len(current_paths) - len(valid_paths)}")

    if valid_paths:
        print(f"\nValid paths:")
        for path in valid_paths:
            print(f"  - {path}")

    return valid_paths


if __name__ == "__main__":
    clean_python_path()
