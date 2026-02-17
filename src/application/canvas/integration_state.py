"""Integration State Manager - Manages integration state consistency with integration.json."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

from .schemas import IntegrationStateUpdate

logger = logging.getLogger(__name__)


class IntegrationStateManager:
    """Manages integration state consistency with integration.json."""

    def __init__(self, integration_json_path: Path):
        """Initialize integration state manager.

        Args:
            integration_json_path: Path to integration.json file
        """
        self.integration_json_path = Path(integration_json_path)
        self._state: dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load integration state from JSON."""
        if self.integration_json_path.exists():
            try:
                with open(self.integration_json_path, encoding="utf-8") as f:
                    self._state = json.load(f)
                logger.info(f"Loaded integration state from {self.integration_json_path}")
            except Exception as e:
                logger.error(f"Failed to load integration state: {e}")
                self._state = {}
        else:
            logger.warning(f"Integration state file not found: {self.integration_json_path}")
            self._state = {
                "generated_at": datetime.now().isoformat(),
                "total_integrations": 0,
                "open_mismatches": 0,
                "resolution_queue_size": 0,
                "integrations_by_status": {
                    "active": 0,
                    "inactive": 0,
                    "degraded": 0,
                    "error": 0,
                },
                "success_rate": 100,
                "top_mismatch_types": [],
            }

    async def _save_state(self) -> None:
        """Save integration state to JSON asynchronously."""
        try:
            # Ensure directory exists
            await asyncio.to_thread(self.integration_json_path.parent.mkdir, parents=True, exist_ok=True)

            # Write atomically
            temp_path = self.integration_json_path.with_suffix(".tmp")
            async with aiofiles.open(temp_path, mode="w", encoding="utf-8") as f:
                await f.write(json.dumps(self._state, indent=2))
            temp_path.replace(self.integration_json_path)

            logger.debug(f"Saved integration state to {self.integration_json_path}")
        except Exception as e:
            logger.error(f"Failed to save integration state: {e}")

    async def update_state(
        self,
        updates: dict[str, Any],
        route_path: Path | None = None,
    ) -> IntegrationStateUpdate:
        """Update integration state while maintaining consistency.

        Args:
            updates: Dictionary of updates to apply
            route_path: Optional route path for tracking

        Returns:
            IntegrationStateUpdate with previous and new state
        """
        previous_state = self._state.copy()

        # Update state
        self._state.update(updates)

        # Track route if provided
        if route_path:
            if "routing_history" not in self._state:
                self._state["routing_history"] = []
            self._state["routing_history"].append(
                {
                    "path": str(route_path),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "updates": updates,
                }
            )

            # Keep only last 100 entries
            if len(self._state["routing_history"]) > 100:
                self._state["routing_history"] = self._state["routing_history"][-100:]

        # Save state
        await self._save_state()

        return IntegrationStateUpdate(
            success=True,
            previous_state=previous_state,
            new_state=self._state.copy(),
            route_path=str(route_path) if route_path else None,
        )

    def check_integration_alignment(self, route_path: Path | None) -> float:
        """Check how well a route aligns with integration state.

        Args:
            route_path: Route path to check

        Returns:
            Alignment score (0.0 to 1.0)
        """
        if not route_path:
            return 0.5  # Neutral if no path

        alignment = 1.0

        # Check if route is in active integrations
        integrations_by_status = self._state.get("integrations_by_status", {})
        active_integrations = integrations_by_status.get("active", 0)

        if active_integrations > 0:
            # Higher alignment if route has been used in routing history
            routing_history = self._state.get("routing_history", [])
            route_str = str(route_path)
            route_usage = sum(1 for entry in routing_history if route_str in entry.get("path", ""))

            if route_usage > 0:
                alignment = 0.9
            else:
                alignment = 0.7
        else:
            alignment = 0.5

        # Penalize if mismatches exist
        open_mismatches = self._state.get("open_mismatches", 0)
        if open_mismatches > 0:
            alignment *= 0.8

        # Check success rate
        success_rate = self._state.get("success_rate", 100)
        if success_rate < 80:
            alignment *= 0.9

        return alignment

    def get_state(self) -> dict[str, Any]:
        """Get current integration state.

        Returns:
            Current state dictionary
        """
        return self._state.copy()
