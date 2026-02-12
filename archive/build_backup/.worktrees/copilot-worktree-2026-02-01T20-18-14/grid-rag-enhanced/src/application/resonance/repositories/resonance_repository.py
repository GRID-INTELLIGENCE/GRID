"""
Resonance Repository (Mothership-aligned).

Repository for persisting ActivityResonance metadata, feedback, and events.
Follows Mothership patterns using StateStore (in-memory) with future DB migration path.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from ..activity_resonance import ResonanceFeedback
from ..repositories import BaseRepository, StateStore, get_state_store

logger = logging.getLogger(__name__)


class ResonanceRepository(BaseRepository[dict[str, Any]]):
    """Repository for Resonance persistence (Mothership-aligned)."""

    def __init__(self, store: StateStore | None = None):
        """Initialize repository with optional StateStore."""
        self._store = store or get_state_store()
        # Initialize resonance-specific collections if they don't exist
        if not hasattr(self._store, "resonance_activities"):
            self._store.resonance_activities = {}
        if not hasattr(self._store, "resonance_feedback"):
            self._store.resonance_feedback = {}
        if not hasattr(self._store, "resonance_events"):
            self._store.resonance_events = {}

    async def save_activity_metadata(
        self,
        activity_id: str,
        activity_type: str,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Save activity metadata."""
        async with self._store.transaction():
            self._store.resonance_activities[activity_id] = {
                "activity_id": activity_id,
                "activity_type": activity_type,
                "query": query,
                "context": context or {},
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "completed_at": None,
            }

    async def save_feedback(self, activity_id: str, feedback: ResonanceFeedback) -> None:
        """Save resonance feedback."""
        async with self._store.transaction():
            # Serialize feedback components
            feedback_data = {
                "activity_id": activity_id,
                "state": feedback.state.value if hasattr(feedback.state, "value") else str(feedback.state),
                "urgency": feedback.urgency,
                "message": feedback.message,
                "timestamp": datetime.now(UTC),
                "context": None,
                "paths": None,
                "envelope": None,
            }

            if feedback.context:
                feedback_data["context"] = {
                    "content": feedback.context.content,
                    "source": feedback.context.source,
                    "metrics": {
                        "sparsity": feedback.context.metrics.sparsity,
                        "attention_tension": feedback.context.metrics.attention_tension,
                        "decision_pressure": feedback.context.metrics.decision_pressure,
                        "clarity": feedback.context.metrics.clarity,
                        "confidence": feedback.context.metrics.confidence,
                    },
                    "timestamp": feedback.context.timestamp,
                    "relevance_score": feedback.context.relevance_score,
                }

            if feedback.paths:
                feedback_data["paths"] = {
                    "goal": feedback.paths.goal,
                    "glimpse_summary": feedback.paths.glimpse_summary,
                    "total_options": feedback.paths.total_options,
                    "options": [
                        {
                            "id": opt.id,
                            "name": opt.name,
                            "description": opt.description,
                            "complexity": (
                                opt.complexity.value if hasattr(opt.complexity, "value") else str(opt.complexity)
                            ),
                            "steps": opt.steps,
                            "input_scenario": opt.input_scenario,
                            "output_scenario": opt.output_scenario,
                            "estimated_time": opt.estimated_time,
                            "confidence": opt.confidence,
                            "recommendation_score": opt.recommendation_score,
                        }
                        for opt in feedback.paths.options
                    ],
                    "recommended": (
                        {
                            "id": feedback.paths.recommended.id,
                            "name": feedback.paths.recommended.name,
                            "description": feedback.paths.recommended.description,
                            "complexity": (
                                feedback.paths.recommended.complexity.value
                                if hasattr(feedback.paths.recommended.complexity, "value")
                                else str(feedback.paths.recommended.complexity)
                            ),
                            "steps": feedback.paths.recommended.steps,
                            "input_scenario": feedback.paths.recommended.input_scenario,
                            "output_scenario": feedback.paths.recommended.output_scenario,
                            "estimated_time": feedback.paths.recommended.estimated_time,
                            "confidence": feedback.paths.recommended.confidence,
                            "recommendation_score": feedback.paths.recommended.recommendation_score,
                        }
                        if feedback.paths.recommended
                        else None
                    ),
                }

            if feedback.envelope:
                feedback_data["envelope"] = {
                    "phase": (
                        feedback.envelope.phase.value
                        if hasattr(feedback.envelope.phase, "value")
                        else str(feedback.envelope.phase)
                    ),
                    "amplitude": feedback.envelope.amplitude,
                    "velocity": feedback.envelope.velocity,
                    "time_in_phase": feedback.envelope.time_in_phase,
                    "total_time": feedback.envelope.total_time,
                    "peak_amplitude": feedback.envelope.peak_amplitude,
                }

            self._store.resonance_feedback[activity_id] = feedback_data

    async def mark_activity_completed(self, activity_id: str) -> None:
        """Mark an activity as completed."""
        async with self._store.transaction():
            if activity_id in self._store.resonance_activities:
                self._store.resonance_activities[activity_id]["completed_at"] = datetime.now(UTC)
                self._store.resonance_activities[activity_id]["updated_at"] = datetime.now(UTC)

    async def delete_activity(self, activity_id: str) -> None:
        """Delete an activity and all related data."""
        async with self._store.transaction():
            self._store.resonance_activities.pop(activity_id, None)
            self._store.resonance_feedback.pop(activity_id, None)
            self._store.resonance_events.pop(activity_id, None)

    async def list_activities(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List activities, optionally filtered by user."""
        activities = list(self._store.resonance_activities.values())
        if user_id:
            # Filter by user_id if present in context
            activities = [a for a in activities if a.get("context", {}).get("user_id") == user_id]
        return activities

    async def get_activity(self, activity_id: str) -> dict[str, Any] | None:
        """Get activity metadata."""
        return self._store.resonance_activities.get(activity_id)

    async def get_feedback(self, activity_id: str) -> dict[str, Any] | None:
        """Get feedback for an activity."""
        return self._store.resonance_feedback.get(activity_id)

    async def get_latest_feedback(self, activity_id: str) -> dict[str, Any] | None:
        """Get the latest feedback for an activity."""
        return self._store.resonance_feedback.get(activity_id)  # In-memory store only keeps latest

    async def get(self, id: str) -> dict[str, Any] | None:
        """Get activity by ID."""
        return await self.get_activity(id)

    async def add(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Add new activity."""
        activity_id = entity.get("activity_id") or str(uuid.uuid4())
        await self.save_activity_metadata(
            activity_id,
            entity.get("activity_type", "general"),
            entity.get("query", ""),
            entity.get("context"),
        )
        return await self.get_activity(activity_id) or entity

    async def update(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Update existing activity."""
        return await self.add(entity)

    async def delete(self, id: str) -> None:
        """Delete activity by ID."""
        await self.delete_activity(id)

    async def count_activities(self) -> int:
        """Count total activities."""
        return len(self._store.resonance_activities)

    async def count_completed_activities(self) -> int:
        """Count completed activities."""
        return sum(1 for a in self._store.resonance_activities.values() if a.get("completed_at"))
