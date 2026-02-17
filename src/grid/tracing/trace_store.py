"""Trace store for persisting action traces."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .action_trace import ActionTrace, TraceOrigin


class TraceStore:
    """Store for persisting and querying action traces."""

    def __init__(self, storage_path: Path | None = None):
        """Initialize trace store.

        Args:
            storage_path: Path to store traces (default: ./grid/logs/traces)
        """
        if storage_path is None:
            storage_path = Path("grid/logs/traces")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory index for fast lookups
        self._trace_index: dict[str, str] = {}  # trace_id -> file_path
        self._load_index()

    def _load_index(self) -> None:
        """Load trace index from disk."""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    self._trace_index = json.load(f)
            except Exception:
                self._trace_index = {}

    def _save_index(self) -> None:
        """Save trace index to disk."""
        index_file = self.storage_path / "index.json"
        try:
            with open(index_file, "w") as f:
                json.dump(self._trace_index, f, indent=2)
        except Exception:
            pass  # Best effort

    def _get_trace_file(self, trace_id: str) -> Path:
        """Get file path for a trace ID."""
        # Organize by date
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        date_dir = self.storage_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        return date_dir / f"{trace_id}.json"

    def save_trace(self, trace: ActionTrace) -> None:
        """Save a trace to storage.

        Args:
            trace: Action trace to save
        """
        trace_file = self._get_trace_file(trace.trace_id)
        try:
            with open(trace_file, "w") as f:
                json.dump(trace.model_dump(mode="json"), f, indent=2, default=str)

            # Update index
            self._trace_index[trace.trace_id] = str(trace_file)
            self._save_index()
        except Exception as e:
            # Log error but don't fail
            print(f"Failed to save trace {trace.trace_id}: {e}")

    def get_trace(self, trace_id: str) -> ActionTrace | None:
        """Get a trace by ID.

        Args:
            trace_id: Trace identifier

        Returns:
            Action trace or None if not found
        """
        trace_file = self._trace_index.get(trace_id)
        if not trace_file:
            return None

        try:
            with open(trace_file) as f:
                data = json.load(f)
                return ActionTrace(**data)
        except Exception:
            return None

    def query_traces(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        origin: TraceOrigin | None = None,
        action_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[ActionTrace]:
        """Query traces by various criteria.

        Args:
            user_id: Filter by user ID
            org_id: Filter by organization ID
            origin: Filter by origin type
            action_type: Filter by action type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results

        Returns:
            List of matching traces
        """
        results = []
        count = 0

        # Search through index
        for _trace_id, trace_file in self._trace_index.items():
            if count >= limit:
                break

            try:
                with open(trace_file) as f:
                    data = json.load(f)
                    trace = ActionTrace(**data)

                    # Apply filters
                    if user_id and trace.context.user_id != user_id:
                        continue
                    if org_id and trace.context.org_id != org_id:
                        continue
                    if origin and trace.context.origin != origin:
                        continue
                    if action_type and trace.action_type != action_type:
                        continue
                    if start_time and trace.context.timestamp < start_time:
                        continue
                    if end_time and trace.context.timestamp > end_time:
                        continue

                    results.append(trace)
                    count += 1
            except Exception:
                continue

        return results

    def get_trace_chain(self, trace_id: str) -> list[ActionTrace]:
        """Get full trace chain from root to leaf.

        Args:
            trace_id: Trace ID to start from

        Returns:
            List of traces from root to leaf
        """
        chain = []
        current_id = trace_id

        while current_id:
            trace = self.get_trace(current_id)
            if not trace:
                break

            chain.insert(0, trace)
            if trace.context.parent_trace_id:
                current_id = trace.context.parent_trace_id
            else:
                break

        return chain

    def cleanup_old_traces(self, days: int = 30) -> int:
        """Clean up traces older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of traces cleaned up
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        cleaned = 0

        for trace_id, trace_file in list(self._trace_index.items()):
            try:
                trace = self.get_trace(trace_id)
                if trace and trace.context.timestamp < cutoff:
                    Path(trace_file).unlink(missing_ok=True)
                    del self._trace_index[trace_id]
                    cleaned += 1
            except Exception:
                continue

        self._save_index()
        return cleaned
