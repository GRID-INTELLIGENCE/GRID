"""
Path Visualizer - Right Side (light_of_the_seven/).

Creates concise and vivid articulation of paths, displays them fast,
and gives glimpses of input/output scenarios when coding presents
recommendation triage (3-4 different paths/ways/options/choices).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PathComplexity(str, Enum):
    """Complexity level of a path."""

    SIMPLE = "simple"  # Straightforward, minimal steps
    MODERATE = "moderate"  # Some complexity, manageable
    COMPLEX = "complex"  # Multiple steps, dependencies
    VERY_COMPLEX = "very_complex"  # Many steps, high cognitive load


@dataclass
class PathOption:
    """A single path option with input/output scenarios."""

    id: str
    name: str
    description: str
    complexity: PathComplexity
    steps: list[str]
    input_scenario: str
    output_scenario: str
    estimated_time: float  # seconds
    confidence: float  # 0.0 to 1.0
    recommendation_score: float = 0.5  # 0.0 to 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PathTriage:
    """Triage result with multiple path options."""

    goal: str
    options: list[PathOption]
    recommended: PathOption | None = None
    glimpse_summary: str = ""
    total_options: int = 0


class PathVisualizer:
    """
    Path visualization and triage system from light_of_the_seven/.

    Provides alternate views of straight-line point A to B paths,
    quickly overviewing in glimpses for seamless flow and optimizing
    synchronous feedbacks mid-activity.
    """

    def __init__(self, light_path: Path | None = None):
        """
        Initialize path visualizer.

        Args:
            light_path: Path to light_of_the_seven directory
        """
        if light_path is None:
            # Default to workspace light_of_the_seven directory
            light_path = Path(__file__).parent.parent.parent / "light_of_the_seven"
        self.light_path = Path(light_path)
        self._path_cache: dict[str, PathTriage] = {}

    def triage_paths(self, goal: str, context: dict[str, Any] | None = None, max_options: int = 4) -> PathTriage:
        """
        Generate path triage with multiple options (3-4 paths).

        Args:
            goal: The goal or task
            context: Optional context for path generation
            max_options: Maximum number of options to generate

        Returns:
            Path triage with options and recommendations
        """
        # Check cache
        cache_key = f"{goal}:{max_options}"
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        # Generate path options
        options = self._generate_path_options(goal, context, max_options)

        # Score and rank options
        for option in options:
            option.recommendation_score = self._score_option(option, goal, context)

        # Sort by recommendation score
        options.sort(key=lambda o: o.recommendation_score, reverse=True)

        # Select recommended
        recommended = options[0] if options else None

        # Generate glimpse summary
        glimpse_summary = self._generate_glimpse_summary(options, goal)

        triage = PathTriage(
            goal=goal,
            options=options,
            recommended=recommended,
            glimpse_summary=glimpse_summary,
            total_options=len(options),
        )

        # Cache result
        self._path_cache[cache_key] = triage
        return triage

    def _generate_path_options(
        self, goal: str, context: dict[str, Any] | None, max_options: int
    ) -> list[PathOption]:
        """Generate multiple path options for a goal."""
        options = []

        goal_lower = goal.lower()

        # Path 1: Direct/Simple approach
        if "create" in goal_lower or "add" in goal_lower:
            options.append(
                PathOption(
                    id="direct",
                    name="Direct Creation",
                    description="Create directly with minimal setup",
                    complexity=PathComplexity.SIMPLE,
                    steps=[
                        "Define structure",
                        "Implement core logic",
                        "Add basic validation",
                    ],
                    input_scenario="Minimal input, clear requirements",
                    output_scenario="Working implementation, basic functionality",
                    estimated_time=5.0,
                    confidence=0.8,
                )
            )

        # Path 2: Incremental/Iterative approach
        options.append(
            PathOption(
                id="incremental",
                name="Incremental Build",
                description="Build incrementally with testing at each step",
                complexity=PathComplexity.MODERATE,
                steps=[
                    "Create skeleton structure",
                    "Add core functionality",
                    "Write tests",
                    "Iterate and refine",
                ],
                input_scenario="Evolving requirements, need for validation",
                output_scenario="Tested, validated implementation",
                estimated_time=10.0,
                confidence=0.9,
            )
        )

        # Path 3: Pattern-based approach
        if "service" in goal_lower or "api" in goal_lower:
            options.append(
                PathOption(
                    id="pattern",
                    name="Pattern-Based",
                    description="Follow established patterns from codebase",
                    complexity=PathComplexity.MODERATE,
                    steps=[
                        "Identify similar patterns",
                        "Adapt pattern to goal",
                        "Integrate with existing system",
                    ],
                    input_scenario="Existing patterns available, integration needed",
                    output_scenario="Consistent, integrated implementation",
                    estimated_time=8.0,
                    confidence=0.85,
                )
            )

        # Path 4: Comprehensive approach
        options.append(
            PathOption(
                id="comprehensive",
                name="Comprehensive Solution",
                description="Full-featured implementation with all considerations",
                complexity=PathComplexity.COMPLEX,
                steps=[
                    "Design architecture",
                    "Implement core features",
                    "Add error handling",
                    "Write comprehensive tests",
                    "Add documentation",
                ],
                input_scenario="Complex requirements, production-ready needed",
                output_scenario="Production-ready, fully tested solution",
                estimated_time=20.0,
                confidence=0.95,
            )
        )

        # Limit to max_options
        return options[:max_options]

    def _score_option(self, option: PathOption, goal: str, context: dict[str, Any] | None) -> float:
        """Score an option for recommendation."""
        score = 0.5  # Base score

        # Prefer simpler options for quick tasks
        if option.complexity == PathComplexity.SIMPLE:
            score += 0.2
        elif option.complexity == PathComplexity.COMPLEX:
            score -= 0.1

        # Higher confidence = higher score
        score += option.confidence * 0.2

        # Shorter time = higher score (for quick decisions)
        if option.estimated_time < 10.0:
            score += 0.1

        # Context-aware scoring
        if context:
            if context.get("urgency", False):
                # Prefer faster options when urgent
                if option.estimated_time < 10.0:
                    score += 0.2
            if context.get("production", False):
                # Prefer comprehensive when production
                if option.complexity == PathComplexity.COMPLEX:
                    score += 0.2

        return min(1.0, max(0.0, score))

    def _generate_glimpse_summary(self, options: list[PathOption], goal: str) -> str:
        """Generate a quick glimpse summary of all paths."""
        if not options:
            return "No paths available"

        # Create a concise summary
        summary_parts = [f"Goal: {goal}"]
        summary_parts.append(f"Paths: {len(options)} options")

        for i, option in enumerate(options[:3], 1):  # Show top 3
            summary_parts.append(
                f"{i}. {option.name} ({option.complexity.value}) - "
                f"{option.estimated_time:.1f}s, confidence: {option.confidence:.0%}"
            )

        return " | ".join(summary_parts)

    def visualize_path(self, option: PathOption) -> str:
        """
        Create vivid visualization of a single path.

        Args:
            option: Path option to visualize

        Returns:
            Visualized path string
        """
        lines = [
            f"📊 Path: {option.name}",
            f"   Complexity: {option.complexity.value}",
            f"   Time: {option.estimated_time:.1f}s",
            f"   Confidence: {option.confidence:.0%}",
            "",
            "📥 Input:",
            f"   {option.input_scenario}",
            "",
            "🔄 Steps:",
        ]

        for i, step in enumerate(option.steps, 1):
            lines.append(f"   {i}. {step}")

        lines.extend(
            [
                "",
                "📤 Output:",
                f"   {option.output_scenario}",
            ]
        )

        return "\n".join(lines)

    def clear_cache(self) -> None:
        """Clear path cache."""
        self._path_cache.clear()
