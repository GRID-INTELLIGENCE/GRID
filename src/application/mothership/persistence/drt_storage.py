"""
DRT (Don't Repeat Themselves) Persistence Layer.

Provides persistent storage for behavioral history and attack vectors
using JSON files. Data survives application restarts.
"""

from __future__ import annotations

import aiofiles
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StoredBehavioralSignature:
    """Serializable version of BehavioralSignature."""

    path_pattern: str
    method: str
    headers: tuple  # JSON converts tuple to list
    body_pattern: str | None
    query_pattern: str | None
    timestamp: str
    request_count: int

    @classmethod
    def from_dict(cls, data: dict) -> StoredBehavioralSignature:
        """Create from dictionary."""
        return cls(
            path_pattern=data["path_pattern"],
            method=data["method"],
            headers=tuple(data["headers"]) if data.get("headers") else (),
            body_pattern=data.get("body_pattern"),
            query_pattern=data.get("query_pattern"),
            timestamp=data["timestamp"],
            request_count=data["request_count"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path_pattern": self.path_pattern,
            "method": self.method,
            "headers": list(self.headers),
            "body_pattern": self.body_pattern,
            "query_pattern": self.query_pattern,
            "timestamp": self.timestamp,
            "request_count": self.request_count,
        }


@dataclass
class StoredAttackVector:
    """Serializable version of attack vector."""

    path_pattern: str
    method: str
    headers: tuple
    body_pattern: str | None
    query_pattern: str | None
    timestamp: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> StoredAttackVector:
        """Create from dictionary."""
        return cls(
            path_pattern=data["path_pattern"],
            method=data["method"],
            headers=tuple(data["headers"]) if data.get("headers") else (),
            body_pattern=data.get("body_pattern"),
            query_pattern=data.get("query_pattern"),
            timestamp=data["timestamp"],
            description=data.get("description", ""),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path_pattern": self.path_pattern,
            "method": self.method,
            "headers": list(self.headers),
            "body_pattern": self.body_pattern,
            "query_pattern": self.query_pattern,
            "timestamp": self.timestamp,
            "description": self.description,
        }


class DRTStorage:
    """
    Persistent storage for DRT data.

    Stores behavioral history and attack vectors in JSON files.
    """

    def __init__(
        self, storage_dir: str | None = None, max_history_entries: int = 10000, save_interval_seconds: int = 60
    ):
        """
        Initialize DRT storage.

        Args:
            storage_dir: Directory to store JSON files. Defaults to ~/.grid/drt
            max_history_entries: Maximum number of behavioral history entries to store
            save_interval_seconds: Interval between automatic saves
        """
        if storage_dir is None:
            home = Path.home()
            storage_dir = home / ".grid" / "drt"
        else:
            storage_dir = Path(storage_dir)

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.behavioral_history_file = self.storage_dir / "behavioral_history.json"
        self.attack_vectors_file = self.storage_dir / "attack_vectors.json"

        self.max_history_entries = max_history_entries
        self.save_interval_seconds = save_interval_seconds

        # In-memory storage
        self._behavioral_history: list[dict] = []
        self._attack_vectors: list[dict] = []

        # Lock for thread-safe access
        self._lock = asyncio.Lock()

        # Background save task
        self._save_task: asyncio.Task | None = None

        # Load existing data
        self._load_all()

    async def start(self) -> None:
        """Start background save task."""
        if self._save_task is None or self._save_task.done():
            self._save_task = asyncio.create_task(self._background_save())
            logger.info("DRT storage background save task started")

    async def stop(self) -> None:
        """Stop background save task and save all data."""
        if self._save_task and not self._save_task.done():
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

        # Final save
        await self.save_all()
        logger.info("DRT storage stopped and data saved")

    def _load_all(self) -> None:
        """Load all data from disk."""
        self._load_behavioral_history()
        self._load_attack_vectors()
        logger.info(
            f"DRT storage loaded: {len(self._behavioral_history)} history entries, "
            f"{len(self._attack_vectors)} attack vectors"
        )

    def _load_behavioral_history(self) -> None:
        """Load behavioral history from disk (synchronous for __init__)."""
        if self.behavioral_history_file.exists():
            try:
                with open(self.behavioral_history_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._behavioral_history = data[-self.max_history_entries :]
            except Exception as e:
                logger.warning(f"Failed to load behavioral history: {e}")
                self._behavioral_history = []

    def _load_attack_vectors(self) -> None:
        """Load attack vectors from disk (synchronous for __init__)."""
        if self.attack_vectors_file.exists():
            try:
                with open(self.attack_vectors_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._attack_vectors = data
            except Exception as e:
                logger.warning(f"Failed to load attack vectors: {e}")
                self._attack_vectors = []

    async def save_all(self) -> None:
        """Save all data to disk."""
        async with self._lock:
            await self._save_behavioral_history()
            await self._save_attack_vectors()

    async def _save_behavioral_history(self) -> None:
        """Save behavioral history to disk asynchronously."""
        try:
            # Limit history before saving
            history_to_save = self._behavioral_history[-self.max_history_entries :]

            async with aiofiles.open(self.behavioral_history_file, mode="w") as f:
                await f.write(json.dumps(history_to_save, indent=2))

            logger.debug(f"Saved {len(history_to_save)} behavioral history entries")
        except Exception as e:
            logger.error(f"Failed to save behavioral history: {e}")

    async def _save_attack_vectors(self) -> None:
        """Save attack vectors to disk asynchronously."""
        try:
            async with aiofiles.open(self.attack_vectors_file, mode="w") as f:
                await f.write(json.dumps(self._attack_vectors, indent=2))

            logger.debug(f"Saved {len(self._attack_vectors)} attack vectors")
        except Exception as e:
            logger.error(f"Failed to save attack vectors: {e}")

    async def _background_save(self) -> None:
        """Background task that periodically saves data."""
        while True:
            try:
                await asyncio.sleep(self.save_interval_seconds)
                await self.save_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background save: {e}")

    # Pub

    # Public API

    async def add_behavioral_entry(self, entry: dict) -> None:
        """
        Add a behavioral history entry.

        Args:
            entry: Dictionary with behavioral data
        """
        async with self._lock:
            self._behavioral_history.append(entry)

            # Trim if exceeding max
            if len(self._behavioral_history) > self.max_history_entries:
                self._behavioral_history = self._behavioral_history[-self.max_history_entries :]

    async def get_behavioral_history(self, limit: int = 1000, since: datetime | None = None) -> list[dict]:
        """
        Get behavioral history entries.

        Args:
            limit: Maximum number of entries to return
            since: Only return entries after this datetime

        Returns:
            List of behavioral history entries
        """
        async with self._lock:
            entries = self._behavioral_history.copy()

        if since:
            since_str = since.isoformat()
            entries = [e for e in entries if e.get("timestamp", "") >= since_str]

        return entries[-limit:]

    async def add_attack_vector(self, vector: dict) -> None:
        """
        Add an attack vector.

        Args:
            vector: Dictionary with attack vector data
        """
        async with self._lock:
            self._attack_vectors.append(vector)
            await self._save_attack_vectors()

    async def remove_attack_vector(self, path_pattern: str, method: str) -> bool:
        """
        Remove an attack vector.

        Args:
            path_pattern: Path pattern to remove
            method: HTTP method

        Returns:
            True if vector was removed, False if not found
        """
        async with self._lock:
            original_count = len(self._attack_vectors)
            self._attack_vectors = [
                v
                for v in self._attack_vectors
                if not (v.get("path_pattern") == path_pattern and v.get("method") == method)
            ]
            removed = len(self._attack_vectors) < original_count

            if removed:
                await self._save_attack_vectors()

            return removed

    async def get_attack_vectors(self) -> list[dict]:
        """
        Get all attack vectors.

        Returns:
            List of attack vectors
        """
        async with self._lock:
            return self._attack_vectors.copy()

    async def clear_behavioral_history(self) -> None:
        """Clear all behavioral history."""
        async with self._lock:
            self._behavioral_history = []
            await self._save_behavioral_history()
        logger.info("DRT behavioral history cleared")

    async def clear_attack_vectors(self) -> None:
        """Clear all attack vectors."""
        async with self._lock:
            self._attack_vectors = []
            await self._save_attack_vectors()
        logger.info("DRT attack vectors cleared")

    async def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        async with self._lock:
            return {
                "behavioral_history_count": len(self._behavioral_history),
                "attack_vectors_count": len(self._attack_vectors),
                "storage_dir": str(self.storage_dir),
                "max_history_entries": self.max_history_entries,
                "save_interval_seconds": self.save_interval_seconds,
                "files": {
                    "behavioral_history": str(self.behavioral_history_file),
                    "attack_vectors": str(self.attack_vectors_file),
                },
            }


# Singleton instance
_drt_storage: DRTStorage | None = None


def get_drt_storage() -> DRTStorage:
    """Get the singleton DRT storage instance."""
    global _drt_storage
    if _drt_storage is None:
        _drt_storage = DRTStorage()
    return _drt_storage


async def init_drt_storage() -> DRTStorage:
    """Initialize and start DRT storage."""
    storage = get_drt_storage()
    await storage.start()
    return storage


async def shutdown_drt_storage() -> None:
    """Shutdown DRT storage."""
    global _drt_storage
    if _drt_storage:
        await _drt_storage.stop()
        _drt_storage = None
