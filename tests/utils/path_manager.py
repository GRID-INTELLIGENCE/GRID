"""
Centralized path management for GRID test suite
Provides atomic path operations to prevent race conditions
"""

import sys
import threading
from pathlib import Path


class PathManager:
    """Atomic path management for test environments"""

    _configured_paths: set[str] = set()
    _lock = threading.Lock()

    @classmethod
    def setup_test_paths(cls, test_file_path: str) -> None:
        """Atomic path setup for tests - prevents race conditions"""
        if not test_file_path or not isinstance(test_file_path, str):
            raise ValueError("test_file_path must be a non-empty string")

        try:
            test_file = Path(test_file_path)
            if not test_file.exists():
                raise FileNotFoundError(f"Test file does not exist: {test_file_path}")
        except (OSError, ValueError) as e:
            # Preserve original exception type
            if isinstance(e, FileNotFoundError):
                raise
            raise ValueError(f"Invalid test_file_path: {test_file_path}") from e

        with cls._lock:
            paths_to_add: list[tuple[int, str]] = []
            paths_to_remove: list[str] = []

            # Calculate paths
            src_path = test_file.parent.parent / "src"
            work_grid_src_path = test_file.parent.parent / "work" / "GRID" / "src"

            # Prepare removals
            work_grid_str = str(work_grid_src_path)
            if work_grid_str in sys.path:
                paths_to_remove.append(work_grid_str)

            # Prepare additions with proper priority
            src_str = str(src_path)
            if src_str not in sys.path and src_str not in cls._configured_paths:
                paths_to_add.append((0, src_str))  # Priority 0: insert at beginning
                cls._configured_paths.add(src_str)

            if (
                work_grid_src_path.exists()
                and work_grid_str not in sys.path
                and work_grid_str not in cls._configured_paths
            ):
                paths_to_add.append((1, work_grid_str))  # Priority 1: insert after src
                cls._configured_paths.add(work_grid_str)

            # Apply changes atomically
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)
                    cls._configured_paths.discard(path)

            # Insert paths in correct order (by priority, then reverse for insertion)
            for priority, path in sorted(paths_to_add, key=lambda x: x[0], reverse=True):
                if path not in sys.path:
                    if priority == 0:
                        sys.path.insert(0, path)  # Insert at beginning
                    else:
                        sys.path.append(path)  # Append for priority 1+

    @classmethod
    def reset_paths(cls) -> None:
        """Reset configured paths cache"""
        with cls._lock:
            cls._configured_paths.clear()

    @classmethod
    def get_configured_paths(cls) -> set[str]:
        """Get currently configured paths"""
        with cls._lock:
            return cls._configured_paths.copy()
