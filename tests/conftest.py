import sys
import os
from pathlib import Path

# Import centralized path manager
from tests.utils.path_manager import PathManager

# Setup paths atomically to prevent race conditions
PathManager.setup_test_paths(__file__)
