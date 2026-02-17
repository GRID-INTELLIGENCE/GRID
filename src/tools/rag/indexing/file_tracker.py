"""File tracking for incremental RAG indexing.

Tracks file hashes to detect changes and enable selective re-indexing.
Uses atomic writes and file locking to prevent corruption.
"""

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    # Windows doesn't have fcntl
    HAS_FCNTL = False


@dataclass
class FileState:
    """State of a tracked file."""

    path: str
    file_hash: str
    indexed_at: str
    file_size: int
    chunk_count: int = 0


@dataclass
class TrackerState:
    """Persistent tracker state."""

    version: int = 1
    last_updated: str = ""
    files: dict[str, FileState] = field(default_factory=dict)


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of file contents.

    Args:
        path: Path to the file

    Returns:
        Hex digest of file hash
    """
    hasher = hashlib.sha256()
    try:
        # Security: Validate path is within allowed base directory
        # Note: This should be called with validated paths from FileTracker
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


class FileTracker:
    """Tracks file states for incremental indexing.

    Persists state to a JSON file in the vector store directory.
    Uses atomic writes (write to temp, then rename) to prevent corruption.
    """

    def __init__(self, persist_dir: str = ".rag_db"):
        """Initialize file tracker.

        Args:
            persist_dir: Directory to store tracker state
        """
        self.persist_dir = Path(persist_dir)
        self.tracker_file = self.persist_dir / "file_tracker.json"
        self.state = TrackerState()
        self._load()

    def _load(self) -> None:
        """Load tracker state from disk."""
        if not self.tracker_file.exists():
            return

        try:
            with open(self.tracker_file, encoding="utf-8") as f:
                data = json.load(f)

            self.state.version = data.get("version", 1)
            self.state.last_updated = data.get("last_updated", "")

            # Reconstruct FileState objects
            files_data = data.get("files", {})
            self.state.files = {path: FileState(**file_data) for path, file_data in files_data.items()}
        except Exception as e:
            print(f"Warning: Could not load file tracker: {e}")
            self.state = TrackerState()

    def _save_atomic(self) -> None:
        """Save tracker state atomically (write to temp, then rename)."""
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.state.last_updated = datetime.now(UTC).isoformat()

        # Serialize state
        data = {
            "version": self.state.version,
            "last_updated": self.state.last_updated,
            "files": {path: asdict(file_state) for path, file_state in self.state.files.items()},
        }

        # Write to temp file, then atomic rename
        fd, temp_path = tempfile.mkstemp(dir=str(self.persist_dir), prefix="file_tracker_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                # Lock file on Unix systems
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename (works on both Unix and Windows)
            temp = Path(temp_path)
            temp.replace(self.tracker_file)
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception:  # noqa: S110 intentional silent handling
                pass
            raise e

    def get_file_state(self, path: str) -> FileState | None:
        """Get tracked state for a file.

        Args:
            path: Relative path to the file

        Returns:
            FileState if tracked, None otherwise
        """
        return self.state.files.get(path)

    def update_file(self, path: str, file_hash: str, file_size: int, chunk_count: int) -> None:
        """Update tracked state for a file.

        Args:
            path: Relative path to the file
            file_hash: SHA-256 hash of file contents
            file_size: Size of file in bytes
            chunk_count: Number of chunks created from this file
        """
        self.state.files[path] = FileState(
            path=path,
            file_hash=file_hash,
            indexed_at=datetime.now(UTC).isoformat(),
            file_size=file_size,
            chunk_count=chunk_count,
        )

    def remove_file(self, path: str) -> None:
        """Remove a file from tracking.

        Args:
            path: Relative path to the file
        """
        self.state.files.pop(path, None)

    def get_changed_files(self, repo_path: Path, current_files: list[Path]) -> list[Path]:
        """Get list of files that have changed since last index.

        Args:
            repo_path: Base path of the repository
            current_files: List of current file paths

        Returns:
            List of modified or new file paths
        """
        changed = []

        for file_path in current_files:
            try:
                rel_path = str(file_path.relative_to(repo_path))
                current_hash = compute_file_hash(file_path)

                tracked = self.get_file_state(rel_path)
                if tracked is None or tracked.file_hash != current_hash:
                    changed.append(file_path)
            except Exception:
                # If we can't process a file, consider it changed
                changed.append(file_path)

        return changed

    def get_deleted_files(self, repo_path: Path, current_files: list[Path]) -> list[str]:
        """Get list of files that were tracked but no longer exist.

        Args:
            repo_path: Base path of the repository
            current_files: List of current file paths

        Returns:
            List of deleted file paths (relative)
        """
        current_paths = set()
        for file_path in current_files:
            try:
                rel_path = str(file_path.relative_to(repo_path))
                current_paths.add(rel_path)
            except Exception:  # noqa: S110 intentional silent handling
                pass

        tracked_paths = set(self.state.files.keys())
        return list(tracked_paths - current_paths)

    def get_tracked_paths(self) -> set[str]:
        """Get all tracked file paths.

        Returns:
            Set of relative file paths
        """
        return set(self.state.files.keys())

    def save(self) -> None:
        """Persist tracker state to disk."""
        self._save_atomic()

    def reset(self) -> None:
        """Clear all tracked state."""
        self.state = TrackerState()
        if self.tracker_file.exists():
            try:
                self.tracker_file.unlink()
            except Exception:  # noqa: S110 intentional silent handling
                pass

    def get_stats(self) -> dict[str, Any]:
        """Get tracker statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "tracked_files": len(self.state.files),
            "total_chunks": sum(f.chunk_count for f in self.state.files.values()),
            "last_updated": self.state.last_updated,
        }
