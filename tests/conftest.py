import sys
import os
from pathlib import Path

# Add root directory to path to allow imports from tests.utils
_root_dir = Path(__file__).parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

# Import centralized path manager
try:
    from tests.utils.path_manager import PathManager
    # Setup paths atomically to prevent race conditions
    PathManager.setup_test_paths(__file__)
except ImportError:
    # Fallback if path_manager not available
    pass
