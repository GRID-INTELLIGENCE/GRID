"""Learning engine that adapts to user corrections and preferences."""

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from .schemas import Correction, LearnedPreference
from .user_context_manager import UserContextManager

logger = logging.getLogger(__name__)


class LearningEngine:
    """Learns from user interactions and adapts preferences."""

    def __init__(
        self,
        context_manager: UserContextManager,
    ) -> None:
        """Initialize learning engine.

        Args:
            context_manager: User context manager instance
        """
        self.context_manager = context_manager
        self.storage = context_manager.storage

    def record_correction(
        self,
        context: str,
        correction_type: str,
        original: Any,
        corrected: Any,
        reason: str | None = None,
    ) -> bool:
        """Record a user correction for learning.

        Args:
            context: What was being done when correction occurred
            correction_type: Type of correction (e.g., "code_style", "tool_usage")
            original: Original value/action
            corrected: Corrected value/action
            reason: Optional reason for correction

        Returns:
            True if correction was recorded successfully
        """
        correction = Correction(
            context=context,
            correction_type=correction_type,
            original=original,
            corrected=corrected,
            reason=reason,
        )

        success = self.storage.save_correction(correction)
        if success:
            # Immediately process correction for learning
            self._process_correction(correction)

        return success

    def _process_correction(self, correction: Correction) -> None:
        """Process a correction to update learned preferences."""
        corrections = self.storage.load_corrections()

        # Group corrections by type
        by_type: dict[str, list[Correction]] = {}
        for c in corrections:
            if c.correction_type not in by_type:
                by_type[c.correction_type] = []
            by_type[c.correction_type].append(c)

        # Update learned preferences based on corrections
        learned_prefs = self.storage.load_learned_preferences()

        for correction_type, type_corrections in by_type.items():
            if len(type_corrections) < 2:
                continue  # Need multiple corrections to learn

            # Analyze pattern in corrections
            corrected_values = [c.corrected for c in type_corrections]

            value_counts = Counter(corrected_values)

            # Most common corrected value becomes preference
            most_common = value_counts.most_common(1)[0]
            preferred_value = most_common[0]
            confidence = min(most_common[1] / len(type_corrections), 1.0)

            # Update or create learned preference
            if correction_type in learned_prefs:
                pref = learned_prefs[correction_type]
                # Increase confidence with more corrections
                pref.confidence = min(pref.confidence + 0.1, 1.0)
                pref.usage_count += 1
            else:
                learned_prefs[correction_type] = LearnedPreference(
                    preference_type=correction_type,
                    value=preferred_value,
                    confidence=confidence,
                    source="correction",
                )

        self.storage.save_learned_preferences(learned_prefs)

    def learn_from_patterns(self) -> dict[str, LearnedPreference]:
        """Learn preferences from user patterns."""
        if self.context_manager.profile is None:
            return {}

        learned_prefs = self.storage.load_learned_preferences()

        # Learn from tool usage patterns
        tool_patterns = self.context_manager.profile.tool_usage_patterns
        for tool_name, pattern in tool_patterns.items():
            if pattern.usage_count >= 5 and pattern.success_rate > 0.8:
                pref_key = f"preferred_tool_{tool_name}"
                if pref_key not in learned_prefs:
                    learned_prefs[pref_key] = LearnedPreference(
                        preference_type=pref_key,
                        value=True,
                        confidence=min(pattern.success_rate, 0.9),
                        source="pattern",
                    )

        # Learn from file access patterns
        file_patterns = self.context_manager.profile.file_access_patterns
        frequent_files = [(path, pattern) for path, pattern in file_patterns.items() if pattern.access_count >= 10]

        if frequent_files:
            # Learn preferred file types
            file_types = Counter(p.file_type for _, p in frequent_files if p.file_type)
            if file_types:
                most_common_type = file_types.most_common(1)[0][0]
                pref_key = "preferred_file_type"
                if pref_key not in learned_prefs:
                    learned_prefs[pref_key] = LearnedPreference(
                        preference_type=pref_key,
                        value=most_common_type,
                        confidence=0.7,
                        source="pattern",
                    )

        # Learn from work patterns
        work_patterns = self.context_manager.profile.work_patterns
        if len(work_patterns) >= 20:
            # Learn preferred work hours

            hours = Counter(p.timestamp.hour for p in work_patterns)
            if hours:
                most_common_hour = hours.most_common(1)[0][0]
                pref_key = "preferred_work_hour"
                if pref_key not in learned_prefs:
                    learned_prefs[pref_key] = LearnedPreference(
                        preference_type=pref_key,
                        value=most_common_hour,
                        confidence=0.6,
                        source="pattern",
                    )

        self.storage.save_learned_preferences(learned_prefs)
        return learned_prefs

    def get_learned_preferences(self) -> dict[str, LearnedPreference]:
        """Get all learned preferences."""
        return self.storage.load_learned_preferences()

    def apply_learned_preferences(self) -> None:
        """Apply learned preferences to user profile."""
        learned_prefs = self.get_learned_preferences()

        if self.context_manager.profile is None:
            return

        for pref_type, preference in learned_prefs.items():
            if preference.confidence < 0.5:
                continue  # Skip low-confidence preferences

            # Apply to user preferences based on type
            if pref_type.startswith("preferred_tool_"):
                tool_name = pref_type.replace("preferred_tool_", "")
                if tool_name not in self.context_manager.profile.preferences.preferred_tools:
                    self.context_manager.profile.preferences.preferred_tools.append(tool_name)

            elif pref_type == "preferred_file_type":
                # Store in metadata
                self.context_manager.profile.metadata["preferred_file_type"] = preference.value

            elif pref_type == "preferred_work_hour":
                # Update work hours if not explicitly set
                if self.context_manager.profile.preferences.work_hours_start is None:
                    self.context_manager.profile.preferences.work_hours_start = preference.value
                    self.context_manager.profile.preferences.work_hours_end = preference.value + 8

        self.context_manager.save_profile()

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learning progress."""
        corrections = self.storage.load_corrections()
        learned_prefs = self.get_learned_preferences()

        # Group corrections by type
        correction_types: dict[str, int] = {}
        for correction in corrections:
            if correction.correction_type not in correction_types:
                correction_types[correction.correction_type] = 0
            correction_types[correction.correction_type] += 1

        # Calculate learning metrics
        high_confidence_prefs = [p for p in learned_prefs.values() if p.confidence >= 0.7]

        return {
            "total_corrections": len(corrections),
            "correction_types": correction_types,
            "learned_preferences": len(learned_prefs),
            "high_confidence_preferences": len(high_confidence_prefs),
            "recent_corrections": len([c for c in corrections if (datetime.now() - c.timestamp).days <= 7]),
        }
