#!/usr/bin/env python3
"""Case Filing System

Handles iterative logging, labeling, categorization, and structure creation
from raw input. Uses advanced but simple iterative logging technique.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CaseCategory(Enum):
    """Case categories."""

    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUG_FIX = "bug_fix"
    FEATURE_REQUEST = "feature_request"
    REFACTORING = "refactoring"
    INTEGRATION = "integration"
    RARE = "rare"  # New/rare cases that don't fit existing categories


@dataclass
class CaseStructure:
    """Structured case data."""

    # Basic metadata
    timestamp: str
    labels: list[str] = field(default_factory=list)
    category: CaseCategory = CaseCategory.RARE
    priority: str = "medium"  # low, medium, high, critical

    # Content analysis
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)

    # User context
    user_examples: list[str] = field(default_factory=list)
    user_scenarios: list[str] = field(default_factory=list)
    user_phenomena: list[str] = field(default_factory=list)

    # Classification confidence
    confidence: float = 0.0  # 0.0-1.0

    # Iterative logging data
    logging_iterations: list[dict[str, Any]] = field(default_factory=list)


class CaseFilingSystem:
    """Case filing system with iterative logging."""

    def __init__(self) -> None:
        """Initialize case filing system."""
        # Category keywords mapping
        self.category_keywords: dict[CaseCategory, set[str]] = {
            CaseCategory.CODE_ANALYSIS: {
                "code",
                "analyze",
                "review",
                "inspect",
                "examine",
                "debug",
                "function",
                "class",
                "module",
                "implementation",
            },
            CaseCategory.ARCHITECTURE: {
                "architecture",
                "design",
                "structure",
                "system",
                "component",
                "module",
                "interface",
                "contract",
                "schema",
            },
            CaseCategory.TESTING: {
                "test",
                "testing",
                "unit",
                "integration",
                "coverage",
                "pytest",
                "assert",
                "validation",
            },
            CaseCategory.DOCUMENTATION: {
                "documentation",
                "doc",
                "readme",
                "guide",
                "tutorial",
                "api",
                "reference",
                "manual",
            },
            CaseCategory.DEPLOYMENT: {
                "deploy",
                "deployment",
                "ci",
                "cd",
                "pipeline",
                "release",
                "production",
                "staging",
                "environment",
            },
            CaseCategory.SECURITY: {
                "security",
                "vulnerability",
                "attack",
                "threat",
                "secure",
                "encryption",
                "authentication",
                "authorization",
            },
            CaseCategory.PERFORMANCE: {
                "performance",
                "speed",
                "latency",
                "throughput",
                "optimize",
                "efficient",
                "slow",
                "bottleneck",
            },
            CaseCategory.BUG_FIX: {
                "bug",
                "error",
                "fix",
                "issue",
                "problem",
                "broken",
                "crash",
                "exception",
                "failure",
            },
            CaseCategory.FEATURE_REQUEST: {
                "feature",
                "add",
                "implement",
                "new",
                "enhancement",
                "request",
                "suggestion",
                "improvement",
            },
            CaseCategory.REFACTORING: {
                "refactor",
                "restructure",
                "reorganize",
                "cleanup",
                "improve",
                "optimize",
                "simplify",
            },
            CaseCategory.INTEGRATION: {
                "integrate",
                "integration",
                "connect",
                "api",
                "service",
                "external",
                "third-party",
                "interface",
                "eufle",
                "resonance",
            },
        }

        # Priority keywords
        self.priority_keywords = {
            "critical": {"critical", "urgent", "emergency", "blocking", "broken"},
            "high": {"important", "high", "priority", "asap", "soon"},
            "medium": {"medium", "normal", "standard"},
            "low": {"low", "nice-to-have", "optional", "later"},
        }

    def log_and_categorize(
        self,
        raw_input: str,
        user_context: dict[str, Any] | None = None,
        examples: list[str] | None = None,
        scenarios: list[str] | None = None,
    ) -> CaseStructure:
        """Log and categorize input using iterative logging technique.

        Args:
            raw_input: Raw user input
            user_context: Optional user context
            examples: Optional user examples
            scenarios: Optional user scenarios

        Returns:
            CaseStructure with categorized and structured data
        """
        timestamp = datetime.now().isoformat()

        # Initialize structure
        structure = CaseStructure(timestamp=timestamp)

        # Iterative logging: multiple passes to refine structure
        logging_iterations = []

        # Iteration 1: Basic extraction
        iteration_1 = self._iteration_basic_extraction(raw_input)
        logging_iterations.append(iteration_1)
        structure.keywords.extend(iteration_1.get("keywords", []))
        structure.entities.extend(iteration_1.get("entities", []))

        # Iteration 2: Category detection
        iteration_2 = self._iteration_category_detection(raw_input, structure)
        logging_iterations.append(iteration_2)
        structure.category = iteration_2.get("category", CaseCategory.RARE)
        structure.confidence = iteration_2.get("confidence", 0.0)

        # Iteration 3: Priority detection
        iteration_3 = self._iteration_priority_detection(raw_input)
        logging_iterations.append(iteration_3)
        structure.priority = iteration_3.get("priority", "medium")

        # Iteration 4: Label generation
        iteration_4 = self._iteration_label_generation(raw_input, structure)
        logging_iterations.append(iteration_4)
        structure.labels.extend(iteration_4.get("labels", []))

        # Iteration 5: Relationship detection
        iteration_5 = self._iteration_relationship_detection(raw_input, structure)
        logging_iterations.append(iteration_5)
        structure.relationships.extend(iteration_5.get("relationships", []))

        # Add user context
        if examples:
            structure.user_examples = examples
        if scenarios:
            structure.user_scenarios = scenarios
        if user_context:
            structure.user_phenomena = user_context.get("phenomena", [])

        structure.logging_iterations = logging_iterations

        return structure

    def _iteration_basic_extraction(self, text: str) -> dict[str, Any]:
        """Iteration 1: Extract basic keywords and entities."""
        text_lower = text.lower()

        # Extract keywords (common technical terms)
        keywords = []
        technical_terms = {
            "python",
            "javascript",
            "typescript",
            "java",
            "rust",
            "go",
            "api",
            "rest",
            "graphql",
            "database",
            "sql",
            "nosql",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "test",
            "unit",
            "integration",
            "ci",
            "cd",
            "deploy",
        }

        for term in technical_terms:
            if term in text_lower:
                keywords.append(term)

        # Extract entities (capitalized words, likely proper nouns)
        words = re.findall(r"\b[A-Z][a-z]+\b", text)
        entities = list(set(words))[:10]  # Limit to top 10

        return {"iteration": 1, "keywords": keywords, "entities": entities}

    def _iteration_category_detection(self, text: str, structure: CaseStructure) -> dict[str, Any]:
        """Iteration 2: Detect category based on keywords."""
        text_lower = text.lower()

        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score / len(keywords)

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
        else:
            best_category = CaseCategory.RARE
            confidence = 0.0

        return {
            "iteration": 2,
            "category": best_category,
            "confidence": min(confidence, 1.0),
            "category_scores": {k.name: v for k, v in category_scores.items()},
        }

    def _iteration_priority_detection(self, text: str) -> dict[str, Any]:
        """Iteration 3: Detect priority level."""
        text_lower = text.lower()

        for priority, keywords in self.priority_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return {"iteration": 3, "priority": priority}

        return {"iteration": 3, "priority": "medium"}

    def _iteration_label_generation(self, text: str, structure: CaseStructure) -> dict[str, Any]:
        """Iteration 4: Generate labels."""
        labels = []

        # Add category label
        labels.append(f"category:{structure.category.value}")

        # Add priority label
        labels.append(f"priority:{structure.priority}")

        # Add keyword-based labels
        for keyword in structure.keywords[:5]:  # Top 5 keywords
            labels.append(f"keyword:{keyword}")

        return {"iteration": 4, "labels": labels}

    def _iteration_relationship_detection(self, text: str, structure: CaseStructure) -> dict[str, Any]:
        """Iteration 5: Detect relationships between entities."""
        relationships = []

        # Simple relationship detection based on common patterns
        relationship_patterns = [
            (r"(\w+)\s+(uses|depends on|requires|needs)\s+(\w+)", "depends_on"),
            (r"(\w+)\s+(calls|invokes|executes)\s+(\w+)", "calls"),
            (r"(\w+)\s+(extends|inherits from)\s+(\w+)", "extends"),
            (r"(\w+)\s+(implements)\s+(\w+)", "implements"),
        ]

        for pattern, rel_type in relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                relationships.append({"source": match.group(1), "target": match.group(3), "type": rel_type})

        return {
            "iteration": 5,
            "relationships": relationships[:10],  # Limit to top 10
        }

    def is_rare_case(self, structure: CaseStructure) -> bool:
        """Check if case is rare (doesn't fit existing categories)."""
        return structure.category == CaseCategory.RARE or structure.confidence < 0.3


if __name__ == "__main__":
    # Example usage
    filing_system = CaseFilingSystem()

    test_input = "I need to add a new API endpoint for user authentication with JWT tokens"

    result = filing_system.log_and_categorize(
        raw_input=test_input,
        examples=["Similar auth endpoint in another service"],
        scenarios=["User logs in, receives JWT, uses it for subsequent requests"],
    )

    print(f"Category: {result.category.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Priority: {result.priority}")
    print(f"Labels: {result.labels}")
    print(f"Is Rare: {filing_system.is_rare_case(result)}")
