"""Sensory store for persisting sensory inputs."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .sensory_input import SensoryInput, SensoryType


class SensoryStore:
    """Store for persisting and querying sensory inputs."""

    def __init__(self, storage_path: Path | None = None):
        """Initialize sensory store.

        Args:
            storage_path: Path to store sensory inputs (default: ./grid/data/senses)
        """
        if storage_path is None:
            storage_path = Path("grid/data/senses")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_input(self, input_data: SensoryInput) -> None:
        """Save a sensory input.

        Args:
            input_data: Sensory input to save
        """
        # Organize by date and type
        date_str = input_data.timestamp.strftime("%Y-%m-%d")
        date_dir = self.storage_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        type_dir = date_dir / input_data.sensory_type.value
        type_dir.mkdir(parents=True, exist_ok=True)

        input_file = type_dir / f"{input_data.input_id}.json"
        try:
            with open(input_file, "w") as f:
                json.dump(input_data.model_dump(mode="json"), f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save sensory input {input_data.input_id}: {e}")

    def query_inputs(
        self,
        sensory_type: SensoryType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[SensoryInput]:
        """Query sensory inputs by criteria.

        Args:
            sensory_type: Filter by sensory type
            start_time: Filter by start time
            end_time: Filter by end time
            source: Filter by source
            limit: Maximum number of results

        Returns:
            List of matching sensory inputs
        """
        results = []
        count = 0

        # Search through date directories
        for date_dir in sorted(self.storage_path.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            if start_time and date_dir.name < start_time.strftime("%Y-%m-%d"):
                continue
            if end_time and date_dir.name > end_time.strftime("%Y-%m-%d"):
                continue

            # Search type directories
            for type_dir in date_dir.iterdir():
                if not type_dir.is_dir():
                    continue

                if sensory_type and type_dir.name != sensory_type.value:
                    continue

                # Load inputs
                for input_file in type_dir.glob("*.json"):
                    if count >= limit:
                        break

                    try:
                        with open(input_file) as f:
                            data = json.load(f)
                            input_data = SensoryInput(**data)

                            # Apply filters
                            if source and input_data.source != source:
                                continue
                            if start_time and input_data.timestamp < start_time:
                                continue
                            if end_time and input_data.timestamp > end_time:
                                continue

                            results.append(input_data)
                            count += 1
                    except Exception:  # noqa: S112 intentional skip on error
                        continue

                if count >= limit:
                    break

            if count >= limit:
                break

        return results

    def cleanup_old_inputs(self, days: int = 30) -> int:
        """Clean up inputs older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of inputs cleaned up
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        cleaned = 0

        for date_dir in self.storage_path.iterdir():
            if not date_dir.is_dir():
                continue

            if date_dir.name < cutoff_str:
                # Remove entire date directory
                import shutil

                shutil.rmtree(date_dir, ignore_errors=True)
                cleaned += 1

        return cleaned
