import sys
import os
from pathlib import Path

# Ensure the correct src is in Python path (not work/GRID/src)
src_path = Path(__file__).parent.parent.parent / "src"
work_grid_src_path = Path(__file__).parent.parent.parent / "work" / "GRID" / "src"

# Remove work/GRID/src from path if it exists
if str(work_grid_src_path) in sys.path:
    sys.path.remove(str(work_grid_src_path))

# Add our src to the beginning
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
