"""
Centralized path management for GRID test suite
Provides atomic path operations to prevent race conditions
"""

import sys
from pathlib import Path
from typing import Set, Tuple, List
import threading


class PathManager:
    """Atomic path management for test environments"""
    
    _configured_paths: Set[str] = set()
    _lock = threading.Lock()
    
    @classmethod
    def setup_test_paths(cls, test_file_path: str) -> None:
        """Atomic path setup for tests - prevents race conditions"""
        with cls._lock:
            paths_to_add: List[Tuple[int, str]] = []
            paths_to_remove: List[str] = []
            
            # Calculate paths
            test_file = Path(test_file_path)
            src_path = test_file.parent.parent / "src"
            work_grid_src_path = test_file.parent.parent / "work" / "GRID" / "src"
            
            # Prepare removals
            work_grid_str = str(work_grid_src_path)
            if work_grid_str in sys.path:
                paths_to_remove.append(work_grid_str)
            
            # Prepare additions with proper priority
            src_str = str(src_path)
            if src_str not in sys.path and src_str not in cls._configured_paths:
                paths_to_add.append((0, src_str))
                cls._configured_paths.add(src_str)
            
            if work_grid_src_path.exists() and work_grid_str not in sys.path and work_grid_str not in cls._configured_paths:
                paths_to_add.append((len(sys.path), work_grid_str))
                cls._configured_paths.add(work_grid_str)
            
            # Apply changes atomically
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)
                    cls._configured_paths.discard(path)
            
            # Sort by position (reverse order for insertion)
            for position, path in sorted(paths_to_add, key=lambda x: x[0], reverse=True):
                if path not in sys.path:
                    sys.path.insert(position, path)
    
    @classmethod
    def reset_paths(cls) -> None:
        """Reset configured paths cache"""
        with cls._lock:
            cls._configured_paths.clear()
    
    @classmethod
    def get_configured_paths(cls) -> Set[str]:
        """Get currently configured paths"""
        with cls._lock:
            return cls._configured_paths.copy()
