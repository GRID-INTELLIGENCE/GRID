#!/usr/bin/env python3
"""Continuous Learning System

Enables knowledge enrichment, experience tracking, and self-evolving training.
Manages memory constraints naturally and provides systematic operational method.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .case_filing import CaseCategory, CaseStructure  # type: ignore[import-not-found]
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from case_filing import CaseStructure  # type: ignore[import-not-found]


class ContinuousLearningSystem:
    """Manages continuous learning and knowledge enrichment."""

    def __init__(self, memory_path: Path, max_memory_size_mb: int = 100, enable_auto_cleanup: bool = True):
        """Initialize continuous learning system.

        Args:
            memory_path: Path to memory storage
            max_memory_size_mb: Maximum memory size in MB
            enable_auto_cleanup: Enable automatic cleanup of old entries
        """
        self.memory_path = memory_path
        self.max_memory_size_mb = max_memory_size_mb
        self.enable_auto_cleanup = enable_auto_cleanup

        # Ensure memory directory exists
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Load existing knowledge
        self.knowledge_base = self._load_knowledge_base()
        self.experience_tracker = self._load_experience_tracker()

    async def record_case_completion(
        self, case_id: str, structure: CaseStructure, solution: str, outcome: str, agent_experience: dict[str, Any]
    ):
        """Record completed case for learning.

        Args:
            case_id: Case identifier
            structure: Case structure
            solution: Solution applied
            outcome: Outcome (success, partial, failure)
            agent_experience: Agent experience data
        """
        # Record in knowledge base
        case_entry = {
            "case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "category": structure.category.value,
            "keywords": structure.keywords,
            "priority": structure.priority,
            "solution": solution,
            "outcome": outcome,
            "agent_experience": agent_experience,
            "user_feedback": None,  # Can be added later
        }

        self.knowledge_base["cases"].append(case_entry)

        # Update experience tracker
        self._update_experience_tracker(structure, outcome, agent_experience)

        # Update patterns
        self._update_patterns(structure, solution, outcome)

        # Check memory constraints
        if self.enable_auto_cleanup:
            self._check_memory_constraints()

        # Save knowledge base
        self._save_knowledge_base()
        self._save_experience_tracker()

    def enrich_knowledge_base(self, case_id: str, additional_data: dict[str, Any]):
        """Enrich knowledge base with additional data from case."""
        # Find case in knowledge base
        case = next((c for c in self.knowledge_base["cases"] if c["case_id"] == case_id), None)

        if case:
            case.update(additional_data)
            case["last_updated"] = datetime.now().isoformat()
            self._save_knowledge_base()

    def get_agent_experience(self) -> dict[str, Any]:
        """Get aggregated agent experience data."""
        return {
            "total_cases": len(self.knowledge_base["cases"]),
            "category_distribution": self._get_category_distribution(),
            "success_rate": self._calculate_success_rate(),
            "experience_by_category": self._get_experience_by_category(),
            "common_patterns": self._get_common_patterns(),
            "learning_insights": self._generate_learning_insights(),
        }

    def get_recommendations(self, structure: CaseStructure) -> list[dict[str, Any]]:
        """Get recommendations based on similar past cases."""
        recommendations = []

        # Find similar cases
        similar_cases = self._find_similar_cases(structure)

        recommendations.extend(
            {
                "case_id": case["case_id"],
                "similarity": case["similarity"],
                "recommended_solution": case.get("solution"),
                "expected_outcome": case.get("outcome"),
                "lessons_learned": case.get("agent_experience", {}).get("lessons", []),
            }
            for case in similar_cases[:5]
        )

        return recommendations

    def _load_knowledge_base(self) -> dict[str, Any]:
        """Load knowledge base from storage."""
        kb_file = self.memory_path / "knowledge_base.json"
        if kb_file.exists():
            try:
                with open(kb_file) as f:
                    return json.load(f)
            except Exception:  # noqa: S110 intentional silent handling
                pass

        return {"cases": [], "patterns": {}, "solutions": {}, "last_updated": datetime.now().isoformat()}

    def _load_experience_tracker(self) -> dict[str, Any]:
        """Load experience tracker from storage."""
        tracker_file = self.memory_path / "experience_tracker.json"
        if tracker_file.exists():
            try:
                with open(tracker_file) as f:
                    return json.load(f)
            except Exception:  # noqa: S110 intentional silent handling
                pass

        return {
            "total_cases": 0,
            "by_category": defaultdict(int),
            "by_outcome": defaultdict(int),
            "by_priority": defaultdict(int),
            "success_rate": 0.0,
            "last_updated": datetime.now().isoformat(),
        }

    def _update_experience_tracker(self, structure: CaseStructure, outcome: str, agent_experience: dict[str, Any]):
        """Update experience tracker with new case."""
        self.experience_tracker["total_cases"] += 1
        self.experience_tracker["by_category"][structure.category.value] += 1
        self.experience_tracker["by_outcome"][outcome] += 1
        self.experience_tracker["by_priority"][structure.priority] += 1

        # Update success rate
        total = self.experience_tracker["total_cases"]
        successes = self.experience_tracker["by_outcome"].get("success", 0)
        self.experience_tracker["success_rate"] = successes / total if total > 0 else 0.0
        self.experience_tracker["last_updated"] = datetime.now().isoformat()

    def _update_patterns(self, structure: CaseStructure, solution: str, outcome: str):
        """Update pattern recognition."""
        category = structure.category.value

        if category not in self.knowledge_base["patterns"]:
            self.knowledge_base["patterns"][category] = {
                "solutions": defaultdict(int),
                "outcomes": defaultdict(int),
                "keywords": defaultdict(int),
            }

        # Track solution patterns
        self.knowledge_base["patterns"][category]["solutions"][solution] += 1

        # Track outcome patterns
        self.knowledge_base["patterns"][category]["outcomes"][outcome] += 1

        # Track keyword patterns
        for keyword in structure.keywords:
            self.knowledge_base["patterns"][category]["keywords"][keyword] += 1

    def _check_memory_constraints(self):
        """Check and enforce memory constraints."""
        # Calculate current memory size (approximate)
        kb_file = self.memory_path / "knowledge_base.json"
        if kb_file.exists():
            size_mb = kb_file.stat().st_size / (1024 * 1024)

            if size_mb > self.max_memory_size_mb:
                # Remove oldest cases (keep most recent)
                cases = self.knowledge_base["cases"]
                cases.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

                # Keep top 80% of cases
                keep_count = int(len(cases) * 0.8)
                self.knowledge_base["cases"] = cases[:keep_count]

                # Update last updated
                self.knowledge_base["last_updated"] = datetime.now().isoformat()

    def _save_knowledge_base(self):
        """Save knowledge base to storage."""
        kb_file = self.memory_path / "knowledge_base.json"
        with open(kb_file, "w") as f:
            json.dump(self.knowledge_base, f, indent=2)

    def _save_experience_tracker(self):
        """Save experience tracker to storage."""
        tracker_file = self.memory_path / "experience_tracker.json"
        with open(tracker_file, "w") as f:
            json.dump(dict(self.experience_tracker), f, indent=2)

    def _get_category_distribution(self) -> dict[str, int]:
        """Get distribution of cases by category."""
        return dict(self.experience_tracker["by_category"])

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        return self.experience_tracker.get("success_rate", 0.0)

    def _get_experience_by_category(self) -> dict[str, dict[str, Any]]:
        """Get experience breakdown by category."""
        experience_by_category = {}

        for category in self.experience_tracker["by_category"]:
            category_cases = [c for c in self.knowledge_base["cases"] if c.get("category") == category]

            if category_cases:
                successes = sum(1 for c in category_cases if c.get("outcome") == "success")
                experience_by_category[category] = {
                    "total": len(category_cases),
                    "successes": successes,
                    "success_rate": successes / len(category_cases) if category_cases else 0.0,
                }

        return experience_by_category

    def _get_common_patterns(self) -> list[dict[str, Any]]:
        """Get common patterns from knowledge base."""
        patterns = []

        for category, pattern_data in self.knowledge_base["patterns"].items():
            # Most common solution
            solutions = pattern_data.get("solutions", {})
            if solutions:
                most_common_solution = max(solutions.items(), key=lambda x: x[1])
                patterns.append(
                    {
                        "category": category,
                        "pattern_type": "solution",
                        "pattern": most_common_solution[0],
                        "frequency": most_common_solution[1],
                    }
                )

        return sorted(patterns, key=lambda x: x["frequency"], reverse=True)[:10]

    def _generate_learning_insights(self) -> list[str]:
        """Generate learning insights from experience."""
        insights = []

        total = self.experience_tracker["total_cases"]
        if total > 0:
            insights.append(f"Processed {total} cases total")

        success_rate = self.experience_tracker.get("success_rate", 0.0)
        if success_rate > 0.8:
            insights.append(f"High success rate ({success_rate:.1%}) - system performing well")
        elif success_rate < 0.5:
            insights.append(f"Low success rate ({success_rate:.1%}) - may need review")

        # Category insights
        category_dist = self._get_category_distribution()
        if category_dist:
            most_common = max(category_dist.items(), key=lambda x: x[1])
            insights.append(f"Most common category: {most_common[0]} ({most_common[1]} cases)")

        return insights

    def _find_similar_cases(self, structure: CaseStructure) -> list[dict[str, Any]]:
        """Find similar cases in knowledge base."""
        similar = []

        for case in self.knowledge_base["cases"]:
            # Calculate similarity
            similarity = self._calculate_case_similarity(structure, case)

            if similarity > 0.3:  # Threshold
                case_copy = case.copy()
                case_copy["similarity"] = similarity
                similar.append(case_copy)

        return sorted(similar, key=lambda x: x["similarity"], reverse=True)

    def _calculate_case_similarity(self, structure: CaseStructure, case: dict[str, Any]) -> float:
        """Calculate similarity between case structure and stored case."""
        # Category match
        category_match = 1.0 if case.get("category") == structure.category.value else 0.0

        # Keyword overlap
        case_keywords = set(case.get("keywords", []))
        structure_keywords = set(structure.keywords)

        if structure_keywords:
            keyword_overlap = len(case_keywords & structure_keywords) / len(structure_keywords)
        else:
            keyword_overlap = 0.0

        # Combined similarity
        similarity = (category_match * 0.4) + (keyword_overlap * 0.6)

        return similarity


if __name__ == "__main__":
    import asyncio

    from .case_filing import CaseFilingSystem

    async def _main() -> None:
        filing_system = CaseFilingSystem()
        learning_system = ContinuousLearningSystem(memory_path=Path(".case_memory"))

        test_input = "Add authentication endpoint"
        structure = filing_system.log_and_categorize(raw_input=test_input)

        await learning_system.record_case_completion(
            case_id="TEST-003",
            structure=structure,
            solution="Implemented JWT authentication endpoint",
            outcome="success",
            agent_experience={"lessons": ["Use secure token storage", "Implement rate limiting"], "time_taken": "2 hours"},
        )

        experience = learning_system.get_agent_experience()
        print("Agent Experience:")
        print(json.dumps(experience, indent=2))

    asyncio.run(_main())
