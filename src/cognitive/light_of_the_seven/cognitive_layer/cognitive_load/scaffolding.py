"""Scaffolding manager for progressive disclosure based on expertise."""

from enum import StrEnum
from typing import Any

from ..schemas.user_cognitive_profile import ExpertiseLevel, UserCognitiveProfile


class ScaffoldingLevel(StrEnum):
    """Levels of scaffolding support."""

    FULL = "full"  # Maximum support
    MODERATE = "moderate"  # Some support
    MINIMAL = "minimal"  # Minimal support
    NONE = "none"  # No support


class ScaffoldingManager:
    """Manages scaffolding for progressive disclosure.

    Provides support based on user expertise level and gradually removes it.
    """

    def __init__(self):
        """Initialize the scaffolding manager."""
        self.scaffolding_levels = {
            ExpertiseLevel.NOVICE: ScaffoldingLevel.FULL,
            ExpertiseLevel.BEGINNER: ScaffoldingLevel.MODERATE,
            ExpertiseLevel.INTERMEDIATE: ScaffoldingLevel.MINIMAL,
            ExpertiseLevel.ADVANCED: ScaffoldingLevel.MINIMAL,
            ExpertiseLevel.EXPERT: ScaffoldingLevel.NONE,
        }

    def get_scaffolding_level(self, user_profile: UserCognitiveProfile | None = None) -> ScaffoldingLevel:
        """Get appropriate scaffolding level for user.

        Args:
            user_profile: Optional user cognitive profile

        Returns:
            Scaffolding level
        """
        if user_profile:
            return self.scaffolding_levels.get(user_profile.expertise_level, ScaffoldingLevel.MODERATE)

        return ScaffoldingLevel.MODERATE

    def apply_scaffolding(
        self, content: dict[str, Any], user_profile: UserCognitiveProfile | None = None
    ) -> dict[str, Any]:
        """Apply scaffolding to content based on user expertise.

        Args:
            content: Content to scaffold
            user_profile: Optional user cognitive profile

        Returns:
            Scaffolded content
        """
        level = self.get_scaffolding_level(user_profile)
        scaffolded = content.copy()

        if level == ScaffoldingLevel.FULL:
            # Full scaffolding: add examples, explanations, hints
            scaffolded["examples"] = content.get("examples", [])
            scaffolded["explanations"] = content.get("explanations", [])
            scaffolded["hints"] = content.get("hints", [])
            scaffolded["step_by_step"] = True

        elif level == ScaffoldingLevel.MODERATE:
            # Moderate scaffolding: add examples and some explanations
            scaffolded["examples"] = content.get("examples", [])
            scaffolded["explanations"] = content.get("explanations", [])
            scaffolded["step_by_step"] = False

        elif level == ScaffoldingLevel.MINIMAL:
            # Minimal scaffolding: just examples
            scaffolded["examples"] = content.get("examples", [])
            scaffolded["step_by_step"] = False

        else:  # NONE
            # No scaffolding: just core content
            scaffolded["step_by_step"] = False

        return scaffolded

    def progressive_disclosure(
        self,
        information: list[dict[str, Any]],
        user_profile: UserCognitiveProfile | None = None,
        initial_count: int | None = None,
    ) -> dict[str, Any]:
        """Apply progressive disclosure to information.

        Args:
            information: List of information items
            user_profile: Optional user cognitive profile
            initial_count: Optional initial number of items to show

        Returns:
            Dictionary with initial and remaining information
        """
        # Determine initial count based on expertise
        if initial_count is None:
            if user_profile:
                if user_profile.expertise_level == ExpertiseLevel.NOVICE:
                    initial_count = 2
                elif user_profile.expertise_level == ExpertiseLevel.BEGINNER:
                    initial_count = 3
                elif user_profile.expertise_level == ExpertiseLevel.INTERMEDIATE:
                    initial_count = 5
                else:
                    initial_count = 7  # Advanced/Expert
            else:
                initial_count = 3

        # Split information
        initial = information[:initial_count]
        remaining = information[initial_count:]

        return {
            "initial": initial,
            "remaining": remaining,
            "total_count": len(information),
            "showing_count": len(initial),
            "has_more": len(remaining) > 0,
        }

    def fade_scaffolding(self, current_level: ScaffoldingLevel, performance: dict[str, Any]) -> ScaffoldingLevel:
        """Fade scaffolding based on user performance.

        Args:
            current_level: Current scaffolding level
            performance: User performance metrics

        Returns:
            New scaffolding level (potentially reduced)
        """
        # Check performance indicators
        success_rate = performance.get("success_rate", 0.0)
        error_rate = performance.get("error_rate", 1.0)
        confidence = performance.get("confidence", 0.0)

        # Fade if performance is good
        if current_level == ScaffoldingLevel.FULL:
            if success_rate > 0.8 and error_rate < 0.2:
                return ScaffoldingLevel.MODERATE

        elif current_level == ScaffoldingLevel.MODERATE:
            if success_rate > 0.9 and error_rate < 0.1 and confidence > 0.7:
                return ScaffoldingLevel.MINIMAL

        elif current_level == ScaffoldingLevel.MINIMAL:
            if success_rate > 0.95 and error_rate < 0.05 and confidence > 0.8:
                return ScaffoldingLevel.NONE

        # Don't fade if performance is poor
        if success_rate < 0.6 or error_rate > 0.4:
            # Increase scaffolding if possible
            if current_level == ScaffoldingLevel.MINIMAL:
                return ScaffoldingLevel.MODERATE
            elif current_level == ScaffoldingLevel.NONE:
                return ScaffoldingLevel.MINIMAL

        return current_level

    def create_worked_example(
        self, problem: dict[str, Any], solution: dict[str, Any], user_profile: UserCognitiveProfile | None = None
    ) -> dict[str, Any]:
        """Create a worked example for scaffolding.

        Args:
            problem: Problem description
            solution: Solution with steps
            user_profile: Optional user cognitive profile

        Returns:
            Worked example structure
        """
        level = self.get_scaffolding_level(user_profile)

        example = {
            "problem": problem,
            "solution": solution,
            "show_steps": level in [ScaffoldingLevel.FULL, ScaffoldingLevel.MODERATE],
            "show_explanations": level == ScaffoldingLevel.FULL,
            "interactive": level == ScaffoldingLevel.FULL,
        }

        return example

    def create_completion_example(
        self, template: dict[str, Any], user_profile: UserCognitiveProfile | None = None
    ) -> dict[str, Any]:
        """Create a completion example (partially filled template).

        Args:
            template: Template with some parts filled
            user_profile: Optional user cognitive profile

        Returns:
            Completion example structure
        """
        level = self.get_scaffolding_level(user_profile)

        example = {
            "template": template,
            "completion_level": 0.6 if level == ScaffoldingLevel.FULL else 0.4,
            "hints": level == ScaffoldingLevel.FULL,
        }

        return example
