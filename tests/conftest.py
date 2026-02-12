import sys
import os
from pathlib import Path

# Remove work/GRID/src from path to avoid conflicts
work_grid_src_path = Path(__file__).parent.parent / "work" / "GRID" / "src"
if str(work_grid_src_path) in sys.path:
    sys.path.remove(str(work_grid_src_path))

# Add src directory to Python path for all tests
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add work/GRID/src directory to Python path for all tests (but with lower priority)
if work_grid_src_path.exists() and str(work_grid_src_path) not in sys.path:
    sys.path.append(str(work_grid_src_path))

# Ensure grid.security can be found from main src
main_security_path = Path(__file__).parent.parent / "src" / "grid" / "security"
if main_security_path.exists() and str(main_security_path.parent) not in sys.path:
    sys.path.insert(0, str(main_security_path.parent))
