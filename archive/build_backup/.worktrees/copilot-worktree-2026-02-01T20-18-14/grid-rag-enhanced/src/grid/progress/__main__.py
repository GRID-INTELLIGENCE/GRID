"""
Integration: Make motivator available as grid.progress module.

This ensures you can use it in your code or CLI anywhere:

    from grid.progress import quick_check
    quick_check()

    python -m grid.progress  # Runs quick check automatically
"""

import sys
from pathlib import Path

# Make sure src is importable
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import all the motivational functions
from .quick import quick_check

# When run as module: python -m grid.progress
if __name__ == "__main__":
    quick_check()
