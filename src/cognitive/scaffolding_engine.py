"""Scaffolding Engine for dynamic content adaptation.

The Scaffolding Engine provides dynamic content simplification and support
based on cognitive load, user expertise, and context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.chunking import InformationChunker
from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.scaffolding import (
    ScaffoldingLevel,
    ScaffoldingManager,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    UserCognitiveProfile,
)

logger = logging.getLogger(__name__)


class ScaffoldingStrategy(StrEnum):
    """Types of scaffolding strategies."""

    # Content-based strategies
    CHUNKING = "chunking"  # Break content into chunks
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"  # Show gradually
    SIMPLIFICATION = "simplification"  # Simplify language/complexity

    # Support-based strategies
    HINTS = "hints"  # Add hints to guide user
    EXAMPLES = "examples"  # Add illustrative examples
    EXPLANATIONS = "explanations"  # Add explanatory text
    WORKED_EXAMPLES = "worked_examples"  # Show step-by-step solutions

    # Structure-based strategies
    STEP_BY_STEP = "step_by_step"  # Show steps explicitly
    CHECKLIST = "checklist"  # Provide checklist
    TEMPLATE = "template"  # Provide fill-in template

    # Visual strategies
    DIAGRAMS = "diagrams"  # Add visual representations
    HIGHLIGHTING = "highlighting"  # Highlight key information


@dataclass
class ScaffoldingAction:
    """Represents a single scaffolding action."""

    strategy: ScaffoldingStrategy
    description: str
    position: str = "prepend"  # prepend, append, replace, insert
    content: str | None = None
    priority: int = 0  # Higher priority actions applied first


@dataclass
class ScaffoldingResult:
    """Result of applying scaffolding."""

    original_content: Any
    scaffolded_content: Any
    actions_applied: list[ScaffoldingAction]
    cognitive_reduction: float  # Estimated cognitive load reduction (0-1)


class ScaffoldingEngine:
    """Dynamic scaffolding engine for content adaptation.

    The Scaffolding Engine analyzes content and user characteristics to
    determine and apply appropriate scaffolding strategies.
    """

    def __init__(self):
        """Initialize the scaffolding engine."""
        self.scaffolding_manager = ScaffoldingManager()
        self.chunker = InformationChunker()

        # Strategy priorities (higher = applied first)
        self.strategy_priorities = {
            ScaffoldingStrategy.HINTS: 100,
            ScaffoldingStrategy.STEP_BY_STEP: 90,
            ScaffoldingStrategy.CHUNKING: 80,
            ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE: 70,
            ScaffoldingStrategy.EXAMPLES: 60,
            ScaffoldingStrategy.EXPLANATIONS: 50,
            ScaffoldingStrategy.WORKED_EXAMPLES: 40,
            ScaffoldingStrategy.SIMPLIFICATION: 30,
            ScaffoldingStrategy.CHECKLIST: 20,
            ScaffoldingStrategy.TEMPLATE: 10,
        }

        logger.info("ScaffoldingEngine initialized")

    def determine_strategies(
        self,
        cognitive_load: float,
        profile: UserCognitiveProfile | None = None,
        content_type: str = "text",
    ) -> list[ScaffoldingStrategy]:
        """Determine appropriate scaffolding strategies based on context.

        Args:
            cognitive_load: Current cognitive load (0-10)
            profile: Optional user profile
            content_type: Type of content (text, code, list, etc.)

        Returns:
            List of strategies to apply, ordered by priority
        """
        strategies: list[ScaffoldingStrategy] = []

        # Critical load - maximum scaffolding
        if cognitive_load > 8.0:
            strategies.extend(
                [
                    ScaffoldingStrategy.HINTS,
                    ScaffoldingStrategy.STEP_BY_STEP,
                    ScaffoldingStrategy.CHUNKING,
                    ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE,
                ]
            )

        # High load - moderate scaffolding
        elif cognitive_load > 6.0:
            strategies.extend(
                [
                    ScaffoldingStrategy.EXAMPLES,
                    ScaffoldingStrategy.EXPLANATIONS,
                    ScaffoldingStrategy.CHUNKING,
                ]
            )

        # Medium load - minimal scaffolding
        elif cognitive_load > 4.0:
            strategies.append(ScaffoldingStrategy.EXAMPLES)

        # Novice users get extra scaffolding regardless of load
        if profile and profile.expertise_level.value in ["novice", "beginner"]:
            strategies.extend(
                [
                    ScaffoldingStrategy.WORKED_EXAMPLES,
                    ScaffoldingStrategy.EXPLANATIONS,
                ]
            )

        # Code content gets specific strategies
        if content_type == "code":
            strategies.append(ScaffoldingStrategy.COMMENTS)
            if profile and profile.learning_style.value == "code_examples":
                strategies.append(ScaffoldingStrategy.WORKED_EXAMPLES)

        # Sort by priority
        strategies.sort(key=lambda s: self.strategy_priorities.get(s, 0), reverse=True)

        return strategies

    def apply_scaffolding(
        self,
        content: Any,
        strategies: list[ScaffoldingStrategy],
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingResult:
        """Apply scaffolding strategies to content.

        Args:
            content: Original content to scaffold
            strategies: List of strategies to apply
            profile: Optional user profile

        Returns:
            ScaffoldingResult with scaffolded content and actions applied
        """
        actions_applied: list[ScaffoldingAction] = []
        scaffolded = content

        # Calculate estimated load reduction
        load_reduction = self._estimate_load_reduction(strategies)

        # Apply each strategy
        for strategy in strategies:
            action = self._apply_strategy(scaffolded, strategy, profile)
            if action:
                actions_applied.append(action)
                scaffolded = self._update_content(scaffolded, action)

        return ScaffoldingResult(
            original_content=content,
            scaffolded_content=scaffolded,
            actions_applied=actions_applied,
            cognitive_reduction=load_reduction,
        )

    def scaffold_text(
        self,
        text: str,
        cognitive_load: float,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingResult:
        """Apply scaffolding to text content.

        Args:
            text: Text content to scaffold
            cognitive_load: Current cognitive load
            profile: Optional user profile

        Returns:
            ScaffoldingResult with scaffolded text
        """
        strategies = self.determine_strategies(cognitive_load, profile, "text")
        return self.apply_scaffolding(text, strategies, profile)

    def scaffold_code(
        self,
        code: str,
        cognitive_load: float,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingResult:
        """Apply scaffolding to code content.

        Args:
            code: Code content to scaffold
            cognitive_load: Current cognitive load
            profile: Optional user profile

        Returns:
            ScaffoldingResult with scaffolded code
        """
        strategies = self.determine_strategies(cognitive_load, profile, "code")
        return self.apply_scaffolding(code, strategies, profile)

    def scaffold_list(
        self,
        items: list[Any],
        cognitive_load: float,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingResult:
        """Apply scaffolding to list content.

        Args:
            items: List of items to scaffold
            cognitive_load: Current cognitive load
            profile: Optional user profile

        Returns:
            ScaffoldingResult with scaffolded list
        """
        strategies = self.determine_strategies(cognitive_load, profile, "list")
        return self.apply_scaffolding(items, strategies, profile)

    def _apply_strategy(
        self,
        content: Any,
        strategy: ScaffoldingStrategy,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction | None:
        """Apply a single scaffolding strategy.

        Args:
            content: Content to apply strategy to
            strategy: Strategy to apply
            profile: Optional user profile

        Returns:
            ScaffoldingAction if strategy was applied, None otherwise
        """
        if strategy == ScaffoldingStrategy.CHUNKING:
            return self._chunk_content(content, profile)
        elif strategy == ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE:
            return self._progressive_disclosure(content, profile)
        elif strategy == ScaffoldingStrategy.HINTS:
            return self._add_hint(content, profile)
        elif strategy == ScaffoldingStrategy.EXAMPLES:
            return self._add_example(content, profile)
        elif strategy == ScaffoldingStrategy.EXPLANATIONS:
            return self._add_explanation(content, profile)
        elif strategy == ScaffoldingStrategy.STEP_BY_STEP:
            return self._add_step_by_step(content, profile)
        elif strategy == ScaffoldingStrategy.SIMPLIFICATION:
            return self._simplify(content, profile)
        else:
            # Strategy not implemented or not applicable
            return None

    def _chunk_content(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Chunk content into manageable pieces."""
        if isinstance(content, str):
            # Chunk text by paragraphs
            paragraphs = content.split("\n\n")
            chunks = self.chunker.chunk(paragraphs, profile)
            return ScaffoldingAction(
                strategy=ScaffoldingStrategy.CHUNKING,
                description="Content chunked into manageable sections",
                position="replace",
                content=f"\n\n[Content chunked into {len(chunks)} sections]\n\n",
            )

        elif isinstance(content, list):
            chunks = self.chunker.chunk(content, profile)
            return ScaffoldingAction(
                strategy=ScaffoldingStrategy.CHUNKING,
                description=f"List chunked into {len(chunks)} groups",
                position="replace",
                content=chunks,
            )

        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.CHUNKING,
            description="Chunking applied",
            position="append",
            content="",
        )

    def _progressive_disclosure(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Apply progressive disclosure - show initial items first."""
        if isinstance(content, list):
            result = self.scaffolding_manager.progressive_disclosure(content, profile)
            showing = len(result["initial"])
            return ScaffoldingAction(
                strategy=ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE,
                description=f"Showing {showing} of {result['total_count']} items",
                position="replace",
                content=result["initial"],
            )

        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE,
            description="Progressive disclosure applied",
            position="append",
            content="",
        )

    def _add_hint(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Add a helpful hint."""
        hints = [
            "💡 Hint: Start by identifying the main goal.",
            "💡 Hint: Break down complex problems into smaller steps.",
            "💡 Hint: Consider what you already know about this topic.",
            "💡 Hint: Look for patterns or similar problems you've solved.",
        ]

        hint_text = hints[hash(str(content)) % len(hints)]

        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.HINTS,
            description="Added helpful hint",
            position="prepend",
            content=hint_text + "\n\n",
        )

    def _add_example(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Add an illustrative example."""
        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.EXAMPLES,
            description="Added illustrative example",
            position="append",
            content="\n\n📝 Example: This is a similar case to illustrate the concept.",
        )

    def _add_explanation(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Add an explanatory section."""
        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.EXPLANATIONS,
            description="Added explanatory section",
            position="prepend",
            content="📖 Explanation: Here's what you need to understand before proceeding.\n\n",
        )

    def _add_step_by_step(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Add step-by-step breakdown."""
        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.STEP_BY_STEP,
            description="Added step-by-step breakdown",
            position="prepend",
            content="📋 Step-by-Step:\n\n",
        )

    def _simplify(
        self,
        content: Any,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingAction:
        """Simplify content complexity."""
        return ScaffoldingAction(
            strategy=ScaffoldingStrategy.SIMPLIFICATION,
            description="Simplified content complexity",
            position="prepend",
            content="⚡ Simplified View: Key information presented directly.\n\n",
        )

    def _update_content(self, content: Any, action: ScaffoldingAction) -> Any:
        """Update content based on scaffolding action.

        Args:
            content: Original content
            action: Action to apply

        Returns:
            Updated content
        """
        if action.content is None:
            return content

        if isinstance(content, str):
            if action.position == "prepend":
                return action.content + content
            elif action.position == "append":
                return content + action.content
            elif action.position == "replace":
                return action.content
            elif action.position == "insert":
                # Insert at middle
                mid = len(content) // 2
                return content[:mid] + action.content + content[mid:]

        elif isinstance(content, list):
            if action.position == "prepend":
                if isinstance(action.content, list):
                    return action.content + content
                return [action.content] + content
            elif action.position == "append":
                if isinstance(action.content, list):
                    return content + action.content
                return content + [action.content]
            elif action.position == "replace":
                return action.content if isinstance(action.content, list) else [action.content]

        return content

    def _estimate_load_reduction(self, strategies: list[ScaffoldingStrategy]) -> float:
        """Estimate cognitive load reduction from strategies.

        Args:
            strategies: Strategies being applied

        Returns:
            Estimated reduction (0-1)
        """
        # Strategy effectiveness weights
        effectiveness = {
            ScaffoldingStrategy.HINTS: 0.3,
            ScaffoldingStrategy.STEP_BY_STEP: 0.4,
            ScaffoldingStrategy.CHUNKING: 0.35,
            ScaffoldingStrategy.PROGRESSIVE_DISCLOSURE: 0.25,
            ScaffoldingStrategy.EXAMPLES: 0.3,
            ScaffoldingStrategy.EXPLANATIONS: 0.25,
            ScaffoldingStrategy.WORKED_EXAMPLES: 0.5,
            ScaffoldingStrategy.SIMPLIFICATION: 0.4,
            ScaffoldingStrategy.CHECKLIST: 0.2,
            ScaffoldingStrategy.TEMPLATE: 0.3,
        }

        # Cumulative reduction with diminishing returns
        reduction = 0.0
        for strategy in strategies:
            reduction += effectiveness.get(strategy, 0.1) * (1 - reduction)

        return min(0.8, reduction)  # Cap at 80% reduction

    def get_scaffolding_level(
        self,
        profile: UserCognitiveProfile | None = None,
    ) -> ScaffoldingLevel:
        """Get current scaffolding level.

        Args:
            profile: Optional user profile

        Returns:
            Current scaffolding level
        """
        return self.scaffolding_manager.get_scaffolding_level(profile)

    def should_apply_scaffolding(
        self,
        cognitive_load: float,
        profile: UserCognitiveProfile | None = None,
    ) -> bool:
        """Determine if scaffolding should be applied.

        Args:
            cognitive_load: Current cognitive load
            profile: Optional user profile

        Returns:
            True if scaffolding should be applied
        """
        # Apply if load is high
        if cognitive_load > 6.0:
            return True

        # Apply if user is novice
        if profile and profile.expertise_level.value in ["novice", "beginner"]:
            return True

        return False


# Global instance for convenience
_scaffolding_engine: ScaffoldingEngine | None = None


def get_scaffolding_engine() -> ScaffoldingEngine:
    """Get the global scaffolding engine instance.

    Returns:
        Scaffolding engine singleton
    """
    global _scaffolding_engine
    if _scaffolding_engine is None:
        _scaffolding_engine = ScaffoldingEngine()
    return _scaffolding_engine


# Add missing strategy to enum
ScaffoldingStrategy.COMMENTS = "comments"  # type: ignore
