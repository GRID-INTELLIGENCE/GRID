"""
Event snapshotting for performance optimization in event sourcing.

Provides periodic state snapshots to enable fast recovery without replaying
all events. Implements audio engineering-inspired lossless capture with
configurable snapshot intervals and retention policies.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EventSnapshot:
    """Snapshot of aggregate state at a specific point in time."""

    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    snapshot_version: int
    state_data: dict[str, Any]
    created_at: datetime
    last_event_id: str | None = None
    event_count: int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SnapshotManager:
    """
    Manages event snapshots for performance optimization.

    Features:
    - Configurable snapshot intervals based on event count or time
    - Automatic cleanup of old snapshots
    - Fast recovery from latest snapshot
    - Integration with existing EventBus
    """

    def __init__(
        self,
        storage_dir: Path = Path("./data/snapshots"),
        snapshot_interval_events: int = 100,
        snapshot_interval_hours: int = 24,
        retention_days: int = 30,
        enable_compression: bool = True,
    ):
        """
        Initialize snapshot manager.

        Args:
            storage_dir: Directory to store snapshots
            snapshot_interval_events: Create snapshot every N events
            snapshot_interval_hours: Create snapshot every N hours
            retention_days: Keep snapshots for N days
            enable_compression: Compress snapshot files
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.snapshot_interval_events = snapshot_interval_events
        self.snapshot_interval_hours = snapshot_interval_hours
        self.retention_days = retention_days
        self.enable_compression = enable_compression

        # Track last snapshot times per aggregate
        self._last_snapshot: dict[str, datetime] = {}
        self._event_counts: dict[str, int] = {}

        logger.info(f"SnapshotManager initialized with storage at {storage_dir}")

    def should_snapshot(self, aggregate_id: str, event_id: str, event_timestamp: datetime) -> bool:
        """
        Determine if a snapshot should be created for this event.

        Args:
            aggregate_id: ID of the aggregate
            event_id: ID of the current event
            event_timestamp: Timestamp of the current event

        Returns:
            True if snapshot should be created
        """
        now = datetime.now()

        # Initialize tracking for new aggregates
        if aggregate_id not in self._last_snapshot:
            self._last_snapshot[aggregate_id] = datetime.min
            self._event_counts[aggregate_id] = 0

        # Check event count threshold
        self._event_counts[aggregate_id] += 1
        if self._event_counts[aggregate_id] >= self.snapshot_interval_events:
            return True

        # Check time threshold
        time_since_last = now - self._last_snapshot[aggregate_id]
        if time_since_last >= timedelta(hours=self.snapshot_interval_hours):
            return True

        return False

    def create_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        current_state: dict[str, Any],
        last_event_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventSnapshot:
        """
        Create a snapshot of the current aggregate state.

        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of the aggregate
            current_state: Current state data
            last_event_id: ID of the last processed event
            metadata: Additional metadata

        Returns:
            Created EventSnapshot
        """
        snapshot_id = f"{aggregate_type}_{aggregate_id}_{int(time.time())}"
        snapshot_version = self._get_next_version(aggregate_id)

        snapshot = EventSnapshot(
            snapshot_id=snapshot_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot_version=snapshot_version,
            state_data=current_state,
            created_at=datetime.now(),
            last_event_id=last_event_id,
            event_count=self._event_counts.get(aggregate_id, 0),
            metadata=metadata or {},
        )

        # Save snapshot
        self._save_snapshot(snapshot)

        # Update tracking
        self._last_snapshot[aggregate_id] = snapshot.created_at
        self._event_counts[aggregate_id] = 0

        logger.info(f"Created snapshot {snapshot_id} for {aggregate_type}:{aggregate_id}")
        return snapshot

    def _get_next_version(self, aggregate_id: str) -> int:
        """Get the next version number for an aggregate."""
        aggregate_dir = self.storage_dir / aggregate_id
        if not aggregate_dir.exists():
            return 1

        existing_versions = [
            int(f.stem.split('_v')[-1])
            for f in aggregate_dir.glob("*.json")
            if f.stem.endswith("_v")
        ]

        return max(existing_versions, default=0) + 1

    def _save_snapshot(self, snapshot: EventSnapshot) -> None:
        """Save snapshot to disk."""
        aggregate_dir = self.storage_dir / snapshot.aggregate_id
        aggregate_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{snapshot.snapshot_id}_v{snapshot.snapshot_version}.json"
        filepath = aggregate_dir / filename

        # Convert datetime to ISO string for JSON serialization
        snapshot_data = asdict(snapshot)
        snapshot_data["created_at"] = snapshot.created_at.isoformat()

        with open(filepath, "w") as f:
            json.dump(snapshot_data, f, indent=2)

    def get_latest_snapshot(self, aggregate_id: str) -> EventSnapshot | None:
        """
        Get the latest snapshot for an aggregate.

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Latest EventSnapshot or None if not found
        """
        aggregate_dir = self.storage_dir / aggregate_id
        if not aggregate_dir.exists():
            return None

        # Find the most recent snapshot file
        snapshot_files = list(aggregate_dir.glob("*.json"))
        if not snapshot_files:
            return None

        latest_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file) as f:
                data = json.load(f)

            # Convert ISO string back to datetime
            data["created_at"] = datetime.fromisoformat(data["created_at"])

            return EventSnapshot(**data)
        except Exception as e:
            logger.error(f"Failed to load snapshot {latest_file}: {e}")
            return None

    def recover_from_snapshot(self, aggregate_id: str) -> dict[str, Any] | None:
        """
        Recover aggregate state from latest snapshot.

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Recovered state data or None if no snapshot found
        """
        snapshot = self.get_latest_snapshot(aggregate_id)
        if not snapshot:
            return None

        logger.info(f"Recovered {aggregate_id} from snapshot {snapshot.snapshot_id}")
        return snapshot.state_data

    def cleanup_old_snapshots(self) -> int:
        """
        Remove snapshots older than retention period.

        Returns:
            Number of snapshots removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        for aggregate_dir in self.storage_dir.iterdir():
            if not aggregate_dir.is_dir():
                continue

            for snapshot_file in aggregate_dir.glob("*.json"):
                try:
                    file_mtime = datetime.fromtimestamp(snapshot_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        snapshot_file.unlink()
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete old snapshot {snapshot_file}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old snapshots")

        return removed_count

    def get_snapshot_stats(self) -> dict[str, Any]:
        """
        Get statistics about snapshots.

        Returns:
            Dictionary with snapshot statistics
        """
        total_snapshots = 0
        aggregate_counts = {}

        for aggregate_dir in self.storage_dir.iterdir():
            if not aggregate_dir.is_dir():
                continue

            count = len(list(aggregate_dir.glob("*.json")))
            total_snapshots += count
            aggregate_counts[aggregate_dir.name] = count

        return {
            "total_snapshots": total_snapshots,
            "aggregate_counts": aggregate_counts,
            "storage_dir": str(self.storage_dir),
            "retention_days": self.retention_days,
        }


# Global snapshot manager instance
_global_snapshot_manager: SnapshotManager | None = None


def get_snapshot_manager() -> SnapshotManager:
    """Get or create global snapshot manager instance."""
    global _global_snapshot_manager
    if _global_snapshot_manager is None:
        _global_snapshot_manager = SnapshotManager()
    return _global_snapshot_manager


def set_snapshot_manager(manager: SnapshotManager) -> None:
    """Set global snapshot manager instance."""
    global _global_snapshot_manager
    _global_snapshot_manager = manager
