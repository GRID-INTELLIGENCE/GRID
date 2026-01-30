"""Persistent storage and learning for UserCognitiveProfiles.

The ProfileStore provides:
- Profile CRUD operations
- Learning from interaction patterns
- Mental model evolution tracking
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    DecisionStyle,
    ExpertiseLevel,
    LearningStyle,
    UserCognitiveProfile,
)

logger = logging.getLogger(__name__)


class ProfileStore:
    """Persistent storage and learning for UserCognitiveProfiles.

    Stores user profiles and learns from interaction patterns to continuously
    improve the system's understanding of each user's cognitive characteristics.
    """

    def __init__(self, storage_path: Path | None = None):
        """Initialize the profile store.

        Args:
            storage_path: Path to store profile files. If None, uses default location.
        """
        if storage_path is None:
            storage_path = Path.home() / ".grid" / "cognitive_profiles"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._profiles: dict[str, UserCognitiveProfile] = {}

        # Learning parameters
        self._learning_rate = 0.1
        self._forget_rate = 0.01

        logger.info(f"ProfileStore initialized with path: {self.storage_path}")

    async def get_profile(self, user_id: str) -> UserCognitiveProfile | None:
        """Get a user profile by ID.

        Args:
            user_id: User identifier

        Returns:
            User profile if found, None otherwise
        """
        # Check cache first
        if user_id in self._profiles:
            return self._profiles[user_id]

        # Load from disk
        profile_path = self.storage_path / f"{user_id}.json"
        if profile_path.exists():
            try:
                with open(profile_path) as f:
                    data = json.load(f)
                profile = UserCognitiveProfile(**data)
                self._profiles[user_id] = profile
                return profile
            except Exception as e:
                logger.error(f"Error loading profile for {user_id}: {e}")

        return None

    async def create_profile(self, profile: UserCognitiveProfile) -> None:
        """Create a new user profile.

        Args:
            profile: Profile to create
        """
        profile.created_at = datetime.now()
        profile.updated_at = datetime.now()

        await self.save_profile(profile)
        self._profiles[profile.user_id] = profile

        logger.info(f"Created profile for user {profile.user_id}")

    async def save_profile(self, profile: UserCognitiveProfile) -> None:
        """Save a user profile to disk.

        Args:
            profile: Profile to save
        """
        profile.update_timestamp()

        # Update cache
        self._profiles[profile.user_id] = profile

        # Save to disk
        profile_path = self.storage_path / f"{profile.user_id}.json"
        try:
            with open(profile_path, "w") as f:
                json.dump(profile.model_dump(mode="json"), f, indent=2, default=str)
            logger.debug(f"Saved profile for user {profile.user_id}")
        except Exception as e:
            logger.error(f"Error saving profile for {profile.user_id}: {e}")

    async def update_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> UserCognitiveProfile | None:
        """Update a user profile with partial updates.

        Args:
            user_id: User identifier
            updates: Dictionary of field updates

        Returns:
            Updated profile if found, None otherwise
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        await self.save_profile(profile)
        return profile

    async def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found
        """
        # Remove from cache
        if user_id in self._profiles:
            del self._profiles[user_id]

        # Remove from disk
        profile_path = self.storage_path / f"{user_id}.json"
        if profile_path.exists():
            try:
                profile_path.unlink()
                logger.info(f"Deleted profile for user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting profile for {user_id}: {e}")

        return False

    async def list_profiles(self) -> list[UserCognitiveProfile]:
        """List all user profiles.

        Returns:
            List of all profiles
        """
        profiles = []

        for profile_path in self.storage_path.glob("*.json"):
            try:
                with open(profile_path) as f:
                    data = json.load(f)
                profiles.append(UserCognitiveProfile(**data))
            except Exception as e:
                logger.error(f"Error loading profile from {profile_path}: {e}")

        return profiles

    async def learn_from_interaction(
        self,
        user_id: str,
        interaction: dict[str, Any],
    ) -> None:
        """Learn from a user interaction to update profile.

        Args:
            user_id: User identifier
            interaction: Interaction event data
        """
        profile = await self.get_or_create_profile(user_id)

        # Record interaction in history
        profile.interaction_history.append({
            **interaction,
            "recorded_at": datetime.now().isoformat(),
        })

        # Limit history size (keep last 100 interactions)
        if len(profile.interaction_history) > 100:
            profile.interaction_history = profile.interaction_history[-100:]

        # Learn specific patterns
        action = interaction.get("action", "")
        outcome = interaction.get("outcome", "")
        duration = interaction.get("duration", 0)

        # Update expertise based on successful outcomes
        if outcome == "success":
            await self._update_expertise_from_success(profile, interaction.get("category", "general"))

        # Update decision style based on timing
        if action == "decision" and duration > 0:
            await self._infer_decision_style(profile, duration)

        # Update learning preferences
        if "preferred_format" in interaction:
            await self._update_learning_style(profile, interaction["preferred_format"])

        # Update cognitive capacity estimates
        if "cognitive_load" in interaction:
            await self._update_cognitive_capacity(profile, interaction["cognitive_load"])

        await self.save_profile(profile)

    async def _update_expertise_from_success(
        self,
        profile: UserCognitiveProfile,
        category: str,
    ) -> None:
        """Update expertise level based on successful interactions.

        Args:
            profile: User profile to update
            category: Category of the successful interaction
        """
        # Count successes by category
        category_successes = sum(
            1
            for i in profile.interaction_history
            if i.get("category") == category and i.get("outcome") == "success"
        )

        # Update domain expertise
        current_expertise = profile.domain_expertise.get(category, ExpertiseLevel.INTERMEDIATE)

        if category_successes >= 20:
            new_expertise = ExpertiseLevel.EXPERT
        elif category_successes >= 10:
            new_expertise = ExpertiseLevel.ADVANCED
        elif category_successes >= 5:
            new_expertise = ExpertiseLevel.INTERMEDIATE
        elif category_successes >= 2:
            new_expertise = ExpertiseLevel.BEGINNER
        else:
            new_expertise = ExpertiseLevel.NOVICE

        if new_expertise != current_expertise:
            profile.domain_expertise[category] = new_expertise
            logger.info(f"Updated {profile.user_id} expertise in {category} to {new_expertise.value}")

        # Also update overall expertise if it matches the highest domain expertise
        if profile.domain_expertise:
            highest = max(profile.domain_expertise.values())
            # Convert to int for comparison
            current_level = list(ExpertiseLevel).index(profile.expertise_level)
            highest_level = list(ExpertiseLevel).index(highest)
            if highest_level > current_level:
                profile.expertise_level = highest

    async def _infer_decision_style(self, profile: UserCognitiveProfile, duration: float) -> None:
        """Infer decision style based on decision timing.

        Args:
            profile: User profile to update
            duration: Decision duration in seconds
        """
        # Quick decisions suggest quick or risk-taking style
        if duration < 5.0:
            if profile.decision_style in [DecisionStyle.DELIBERATE, DecisionStyle.BALANCED]:
                # Gradually shift toward quick
                profile.decision_style = DecisionStyle.QUICK

        # Slow decisions suggest deliberate or risk-averse style
        elif duration > 30.0:
            if profile.decision_style in [DecisionStyle.QUICK, DecisionStyle.BALANCED]:
                profile.decision_style = DecisionStyle.DELIBERATE

    async def _update_learning_style(
        self,
        profile: UserCognitiveProfile,
        preferred_format: str,
    ) -> None:
        """Update learning style based on user preferences.

        Args:
            profile: User profile to update
            preferred_format: Preferred content format
        """
        format_to_style = {
            "analogy": LearningStyle.ANALOGIES,
            "code": LearningStyle.CODE_EXAMPLES,
            "theory": LearningStyle.THEORY,
            "visual": LearningStyle.VISUAL_DIAGRAMS,
            "hands-on": LearningStyle.HANDS_ON,
        }

        if preferred_format in format_to_style:
            profile.learning_style = format_to_style[preferred_format]

    async def _update_cognitive_capacity(
        self,
        profile: UserCognitiveProfile,
        cognitive_load: float,
    ) -> None:
        """Update cognitive capacity estimates based on load.

        Args:
            profile: User profile to update
            cognitive_load: Reported cognitive load (0-10)
        """
        # Get recent load values
        recent_loads = [
            i.get("cognitive_load", 5.0)
            for i in profile.interaction_history[-20:]
            if "cognitive_load" in i
        ]

        if not recent_loads:
            return

        # Average load indicates tolerance
        avg_load = sum(recent_loads) / len(recent_loads)

        # Update tolerance based on average load
        if avg_load < 3.0:
            profile.cognitive_load_tolerance = min(1.0, profile.cognitive_load_tolerance + 0.05)
        elif avg_load > 7.0:
            profile.cognitive_load_tolerance = max(0.0, profile.cognitive_load_tolerance - 0.05)

    async def get_or_create_profile(self, user_id: str) -> UserCognitiveProfile:
        """Get existing profile or create a default one.

        Args:
            user_id: User identifier

        Returns:
            User profile
        """
        profile = await self.get_profile(user_id)
        if profile is None:
            profile = UserCognitiveProfile(
                user_id=user_id,
                username=f"User_{user_id[:8]}",
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                learning_style=LearningStyle.CODE_EXAMPLES,
                decision_style=DecisionStyle.BALANCED,
            )
            await self.create_profile(profile)

        return profile

    async def get_profile_statistics(self, user_id: str) -> dict[str, Any]:
        """Get statistics about a user's profile.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with profile statistics
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return {}

        # Interaction statistics
        interactions = profile.interaction_history
        total_interactions = len(interactions)

        if total_interactions == 0:
            return {
                "user_id": user_id,
                "total_interactions": 0,
                "expertise_level": profile.expertise_level.value,
            }

        # Outcome distribution
        outcomes = Counter(i.get("outcome", "unknown") for i in interactions)

        # Action distribution
        actions = Counter(i.get("action", "unknown") for i in interactions)

        # Time-based statistics
        recent = interactions[-20:]
        recent_avg_duration = sum(i.get("duration", 0) for i in recent) / len(recent) if recent else 0

        # Domain expertise breakdown
        domain_expertise = {
            domain: level.value
            for domain, level in profile.domain_expertise.items()
        }

        return {
            "user_id": user_id,
            "username": profile.username,
            "total_interactions": total_interactions,
            "expertise_level": profile.expertise_level.value,
            "learning_style": profile.learning_style.value,
            "decision_style": profile.decision_style.value,
            "outcomes": dict(outcomes),
            "actions": dict(actions),
            "success_rate": outcomes.get("success", 0) / total_interactions,
            "recent_avg_duration": recent_avg_duration,
            "domain_expertise": domain_expertise,
            "working_memory_capacity": profile.working_memory_capacity,
            "cognitive_load_tolerance": profile.cognitive_load_tolerance,
            "mental_model_version": profile.mental_model_version,
            "profile_age_days": (datetime.now() - profile.created_at).days,
        }

    async def evolve_mental_model(self, user_id: str) -> dict[str, Any]:
        """Evolve the user's mental model based on accumulated learning.

        This analyzes the user's interaction history and updates the mental model
        version and confidence to reflect learned patterns.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with evolution information
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return {"error": "Profile not found"}

        # Analyze interaction patterns
        interactions = profile.interaction_history
        if len(interactions) < 10:
            return {
                "user_id": user_id,
                "message": "Not enough data to evolve mental model",
                "min_interactions": 10,
                "current_interactions": len(interactions),
            }

        # Calculate metrics
        success_rate = sum(
            1
            for i in interactions
            if i.get("outcome") == "success"
        ) / len(interactions)

        # Look for consistency in decision patterns
        decisions = [i for i in interactions if i.get("action") == "decision"]
        if decisions:
            # Check if decisions are consistent (similar duration range)
            durations = [i.get("duration", 0) for i in decisions if i.get("duration")]
            if durations:
                avg_duration = sum(durations) / len(durations)
                variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
                consistency = max(0, 1 - variance / (avg_duration ** 2 + 1))
            else:
                consistency = 0.5
        else:
            consistency = 0.5

        # Update mental model confidence
        target_confidence = (success_rate + consistency) / 2
        profile.model_confidence = (
            profile.model_confidence * (1 - self._learning_rate)
            + target_confidence * self._learning_rate
        )

        # Evolve model version if confidence is high enough
        old_version = profile.mental_model_version
        if profile.model_confidence > 0.8:
            profile.mental_model_version += 1

        # Learn decision patterns
        await self._learn_decision_patterns(profile)

        await self.save_profile(profile)

        return {
            "user_id": user_id,
            "old_version": old_version,
            "new_version": profile.mental_model_version,
            "evolved": old_version != profile.mental_model_version,
            "confidence": profile.model_confidence,
            "success_rate": success_rate,
            "consistency": consistency,
        }

    async def _learn_decision_patterns(self, profile: UserCognitiveProfile) -> None:
        """Learn and store decision patterns from interaction history.

        Args:
            profile: User profile to update
        """
        patterns: dict[str, Any] = defaultdict(lambda: {"count": 0, "avg_duration": 0})

        for interaction in profile.interaction_history:
            category = interaction.get("category", "general")
            action = interaction.get("action", "")
            duration = interaction.get("duration", 0)

            key = f"{category}:{action}"
            patterns[key]["count"] += 1
            if duration > 0:
                patterns[key]["avg_duration"] = (
                    patterns[key]["avg_duration"] * (patterns[key]["count"] - 1) + duration
                ) / patterns[key]["count"]

        # Store learned patterns
        profile.decision_patterns = dict(patterns)

    async def recommend_content_complexity(self, user_id: str) -> float:
        """Recommend content complexity based on user profile.

        Args:
            user_id: User identifier

        Returns:
            Recommended complexity (0-1)
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return 0.5

        # Base on preferred complexity
        base_complexity = profile.preferred_complexity

        # Adjust based on expertise
        expertise_factor = list(ExpertiseLevel).index(profile.expertise_level) / 4.0

        # Adjust based on cognitive load tolerance
        tolerance_factor = profile.cognitive_load_tolerance

        # Weighted average
        recommended = (base_complexity * 0.3 + expertise_factor * 0.4 + tolerance_factor * 0.3)

        return max(0.0, min(1.0, recommended))


# Global instance for convenience
_profile_store: ProfileStore | None = None


def get_profile_store(storage_path: Path | None = None) -> ProfileStore:
    """Get the global profile store instance.

    Args:
        storage_path: Optional custom storage path

    Returns:
        Profile store singleton
    """
    global _profile_store
    if _profile_store is None:
        _profile_store = ProfileStore(storage_path)
    return _profile_store
