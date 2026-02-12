"""
Collaborative/Workspace Support for Privacy Shield.

Manages privacy configurations for team workspaces and shared environments.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from safety.privacy.cache.result_cache import get_detection_cache
from safety.privacy.core.engine import PrivacyAction, PrivacyEngine, PrivacyResult
from safety.privacy.core.presets import PrivacyPreset, get_preset_config
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import PRIVACY_COLLABORATIVE_CONTEXT_TOTAL

# Module-level default so type checker treats it as PrivacyPreset, not Literal['collaborative']
_DEFAULT_COLLABORATIVE_PRESET: PrivacyPreset = PrivacyPreset.COLLABORATIVE

logger = get_logger("privacy.collaborative")


@dataclass
class WorkspaceConfig:
    """Configuration for a collaborative workspace."""

    workspace_id: str
    name: str
    preset: PrivacyPreset = _DEFAULT_COLLABORATIVE_PRESET
    allowed_users: list[str] = field(default_factory=list)
    admin_users: list[str] = field(default_factory=list)
    audit_enabled: bool = True
    created_at: float = field(default_factory=time.time)
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserChoice:
    """User's choice for a PII detection."""

    detection_id: str
    choice: str  # mask, allow, block
    timestamp: float = field(default_factory=time.time)


class CollaborativeManager:
    """
    Manages privacy configurations for collaborative workspaces.

    Features:
    - Per-workspace privacy settings
    - User preference management
    - Audit logging for compliance
    - Bulk operations for teams
    """

    def __init__(self):
        self._workspaces: dict[str, WorkspaceConfig] = {}
        self._engines: dict[str, PrivacyEngine] = {}
        self._user_choices: dict[str, list[UserChoice]] = {}  # detection_id -> choices
        self._lock = asyncio.Lock()

    async def create_workspace(
        self,
        workspace_id: str,
        name: str,
        preset: PrivacyPreset = _DEFAULT_COLLABORATIVE_PRESET,
        allowed_users: list[str] | None = None,
        admin_users: list[str] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> WorkspaceConfig:
        """Create a new collaborative workspace."""
        async with self._lock:
            if workspace_id in self._workspaces:
                raise ValueError(f"Workspace {workspace_id} already exists")

            config = WorkspaceConfig(
                workspace_id=workspace_id,
                name=name,
                preset=preset,
                allowed_users=allowed_users or [],
                admin_users=admin_users or [],
                settings=settings or {},
            )

            self._workspaces[workspace_id] = config

            # Create engine for this workspace
            from safety.privacy.core.engine import create_privacy_engine

            self._engines[workspace_id] = create_privacy_engine(
                preset=preset,
                collaborative=True,
                context_id=workspace_id,
            )

            PRIVACY_COLLABORATIVE_CONTEXT_TOTAL.labels(operation="created").inc()
            logger.info("workspace_created", workspace_id=workspace_id, name=name)

            return config

    async def get_workspace(self, workspace_id: str) -> WorkspaceConfig | None:
        """Get workspace configuration."""
        return self._workspaces.get(workspace_id)

    async def update_workspace(
        self,
        workspace_id: str,
        **updates,
    ) -> WorkspaceConfig | None:
        """Update workspace configuration."""
        async with self._lock:
            if workspace_id not in self._workspaces:
                return None

            config = self._workspaces[workspace_id]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # Invalidate cache if preset changed
            if "preset" in updates:
                await get_detection_cache(collaborative=True).invalidate(workspace_id)
                # Recreate engine
                from safety.privacy.core.engine import create_privacy_engine

                self._engines[workspace_id] = create_privacy_engine(
                    preset=updates["preset"],
                    collaborative=True,
                    context_id=workspace_id,
                )

            logger.info("workspace_updated", workspace_id=workspace_id)
            return config

    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace and its cache."""
        async with self._lock:
            if workspace_id not in self._workspaces:
                return False

            del self._workspaces[workspace_id]
            if workspace_id in self._engines:
                del self._engines[workspace_id]

            # Invalidate cache
            await get_detection_cache(collaborative=True).invalidate(workspace_id)

            PRIVACY_COLLABORATIVE_CONTEXT_TOTAL.labels(operation="invalidated").inc()
            logger.info("workspace_deleted", workspace_id=workspace_id)

            return True

    async def get_engine(self, workspace_id: str) -> PrivacyEngine | None:
        """Get privacy engine for a workspace."""
        return self._engines.get(workspace_id)

    async def process_for_workspace(
        self,
        workspace_id: str,
        text: str,
        user_choice: str | None = None,
    ) -> PrivacyResult | None:
        """Process text through workspace's privacy engine."""
        engine = await self.get_engine(workspace_id)
        if engine is None:
            return None

        return await engine.process(
            text,
            user_choice=user_choice,
            context_id=workspace_id,
        )

    async def record_user_choice(
        self,
        detection_id: str,
        choice: str,
    ) -> None:
        """Record user's choice for a detection (for learning)."""
        async with self._lock:
            if detection_id not in self._user_choices:
                self._user_choices[detection_id] = []
            self._user_choices[detection_id].append(UserChoice(detection_id=detection_id, choice=choice))

    async def get_user_choice_stats(self) -> dict[str, int]:
        """Get statistics on user choices."""
        stats = {"mask": 0, "allow": 0, "block": 0}
        for choices in self._user_choices.values():
            for choice in choices:
                if choice.choice in stats:
                    stats[choice.choice] += 1
        return stats

    async def list_workspaces(self) -> list[WorkspaceConfig]:
        """List all workspaces."""
        return list(self._workspaces.values())

    async def add_user_to_workspace(
        self,
        workspace_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Add a user to a workspace."""
        async with self._lock:
            if workspace_id not in self._workspaces:
                return False

            config = self._workspaces[workspace_id]
            if user_id not in config.allowed_users:
                config.allowed_users.append(user_id)

            if is_admin and user_id not in config.admin_users:
                config.admin_users.append(user_id)

            return True

    async def remove_user_from_workspace(
        self,
        workspace_id: str,
        user_id: str,
    ) -> bool:
        """Remove a user from a workspace."""
        async with self._lock:
            if workspace_id not in self._workspaces:
                return False

            config = self._workspaces[workspace_id]
            if user_id in config.allowed_users:
                config.allowed_users.remove(user_id)
            if user_id in config.admin_users:
                config.admin_users.remove(user_id)

            return True


# Global instance
_collaborative_manager: CollaborativeManager | None = None


def get_collaborative_manager() -> CollaborativeManager:
    """Get the global collaborative manager instance."""
    global _collaborative_manager
    if _collaborative_manager is None:
        _collaborative_manager = CollaborativeManager()
    return _collaborative_manager


# Convenience async function
async def create_workspace(
    workspace_id: str,
    name: str,
    preset: PrivacyPreset = _DEFAULT_COLLABORATIVE_PRESET,
    **kwargs,
) -> WorkspaceConfig:
    """Create a new workspace."""
    manager = get_collaborative_manager()
    return await manager.create_workspace(workspace_id, name, preset, **kwargs)


async def get_workspace(workspace_id: str) -> WorkspaceConfig | None:
    """Get a workspace by ID."""
    manager = get_collaborative_manager()
    return await manager.get_workspace(workspace_id)


async def process_for_workspace(
    workspace_id: str,
    text: str,
    user_choice: str | None = None,
) -> PrivacyResult | None:
    """Process text for a workspace."""
    manager = get_collaborative_manager()
    return await manager.process_for_workspace(workspace_id, text, user_choice)
