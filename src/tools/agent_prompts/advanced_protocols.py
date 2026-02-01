#!/usr/bin/env python3
"""Advanced Protocols Handler

Handles rare cases with web search, memory integration, and query generation.
For cases that cache missed, this step is crucial for refinement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .case_filing import CaseStructure  # type: ignore[import-not-found]
except ImportError:
    # For standalone execution
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from case_filing import CaseStructure  # type: ignore[import-not-found]


class AdvancedProtocolHandler:
    """Handles advanced protocols for rare cases."""

    def __init__(self, memory_path: Path | None = None, enable_web_search: bool = True):
        """Initialize advanced protocols handler.

        Args:
            memory_path: Path to memory/knowledgebase storage
            enable_web_search: Enable web search for refinement
        """
        self.memory_path = memory_path or Path(".case_memory")
        self.enable_web_search = enable_web_search

        # Ensure memory directory exists
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Load existing memory
        self.memory = self._load_memory()

    def handle_rare_case(
        self, case_id: str, structured_data: CaseStructure, raw_input: str, reference_file_path: str
    ) -> dict[str, Any]:
        """Handle rare case with advanced protocols.

        Args:
            case_id: Case identifier
            structured_data: Structured case data
            raw_input: Original raw input
            reference_file_path: Path to reference file

        Returns:
            Processing metadata with refinements
        """
        metadata = {
            "protocol": "advanced",
            "web_search_performed": False,
            "memory_searches": [],
            "generated_queries": [],
            "nuances": [],
            "insights": [],
        }

        # Step 1: Search memory/knowledgebase
        memory_results = self._search_memory(structured_data, raw_input)
        metadata["memory_searches"] = memory_results

        # Step 2: Web search (if enabled)
        if self.enable_web_search:
            web_results = self._web_search(structured_data, raw_input)
            metadata["web_search_performed"] = True
            metadata["web_search_results"] = web_results

        # Step 3: Generate nuances and insights
        nuances, insights = self._generate_nuances_and_insights(structured_data, raw_input, memory_results)
        metadata["nuances"] = nuances
        metadata["insights"] = insights

        # Step 4: Generate MCQ-style queries for contextualization
        queries = self._generate_contextualization_queries(structured_data, raw_input, nuances, insights)
        metadata["generated_queries"] = queries

        # Step 5: Update reference file with advanced protocol data
        self._update_reference_file(reference_file_path, metadata)

        # Step 6: Store in memory for future cases
        self._store_in_memory(case_id, structured_data, metadata)

        return metadata

    def _load_memory(self) -> dict[str, Any]:
        """Load existing memory/knowledgebase."""
        memory_file = self.memory_path / "memory.json"
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    return json.load(f)
            except Exception:
                pass

        return {"cases": [], "patterns": {}, "solutions": {}, "keywords": {}}

    def _search_memory(self, structure: CaseStructure, raw_input: str) -> list[dict[str, Any]]:
        """Search memory/knowledgebase for similar cases."""
        results = []

        # Search by keywords
        for case in self.memory.get("cases", []):
            similarity_score = self._calculate_similarity(structure.keywords, case.get("keywords", []))

            if similarity_score > 0.3:  # Threshold
                results.append(
                    {
                        "case_id": case.get("case_id"),
                        "similarity": similarity_score,
                        "category": case.get("category"),
                        "solution": case.get("solution_summary"),
                        "type": "keyword_match",
                    }
                )

        # Search by category
        category_matches = [
            case for case in self.memory.get("cases", []) if case.get("category") == structure.category.value
        ]

        for case in category_matches[:5]:  # Top 5
            results.append(
                {
                    "case_id": case.get("case_id"),
                    "similarity": 0.5,  # Category match
                    "category": case.get("category"),
                    "solution": case.get("solution_summary"),
                    "type": "category_match",
                }
            )

        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:10]

    def _calculate_similarity(self, keywords1: list[str], keywords2: list[str]) -> float:
        """Calculate similarity between keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _web_search(self, structure: CaseStructure, raw_input: str) -> dict[str, Any]:
        """Perform web search for case refinement.

        Note: This is a placeholder. In production, integrate with actual
        web search API (e.g., Google Search API, Bing API, or local RAG).
        """
        # Generate search queries from keywords and category
        search_queries = []

        # Query 1: Category + main keywords
        main_keywords = " ".join(structure.keywords[:3])
        search_queries.append(f"{structure.category.value} {main_keywords}")

        # Query 2: Problem statement
        if len(raw_input) < 100:
            search_queries.append(raw_input)

        # Placeholder for actual web search results
        # In production, this would call a web search API
        return {
            "queries": search_queries,
            "results": [
                {
                    "title": f"Example result for {structure.category.value}",
                    "snippet": "Relevant information about the case category",
                    "url": "https://example.com",
                }
            ],
            "note": "Web search integration required - use local RAG or external API",
        }

    def _generate_nuances_and_insights(
        self, structure: CaseStructure, raw_input: str, memory_results: list[dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """Generate nuances and insights from case analysis."""
        nuances = []
        insights = []

        # Nuance: Category confidence
        if structure.confidence < 0.5:
            nuances.append(
                f"Low category confidence ({structure.confidence:.2f}) - "
                "case may require manual review or additional context"
            )

        # Nuance: Rare case indicators
        if structure.category.value == "rare":
            nuances.append(
                "Case doesn't fit standard categories - may require " "custom solution or new category definition"
            )

        # Insight: Similar cases found
        if memory_results:
            insights.append(f"Found {len(memory_results)} similar cases in memory - " "review solutions for patterns")

        # Insight: Keyword patterns
        if len(structure.keywords) > 5:
            insights.append(f"Rich keyword set ({len(structure.keywords)} keywords) - " "case has multiple dimensions")

        # Insight: User context available
        if structure.user_examples or structure.user_scenarios:
            insights.append("User provided examples/scenarios - use for contextualization")

        return nuances, insights

    def _generate_contextualization_queries(
        self, structure: CaseStructure, raw_input: str, nuances: list[str], insights: list[str]
    ) -> list[dict[str, str]]:
        """Generate MCQ-style queries for contextualization.

        Similar to custom mode where agent asks questions to contextualize.
        """
        queries = []

        # Query 1: Category confirmation
        if structure.confidence < 0.7:
            queries.append(
                {
                    "question": f"Is this case primarily about {structure.category.value}?",
                    "type": "multiple_choice",
                    "options": [
                        f"Yes, it's about {structure.category.value}",
                        "No, it's about something else",
                        "Partially, but also involves other aspects",
                    ],
                    "purpose": "Confirm category classification",
                }
            )

        # Query 2: Priority confirmation
        queries.append(
            {
                "question": "What is the priority level for this case?",
                "type": "multiple_choice",
                "options": ["Critical", "High", "Medium", "Low"],
                "purpose": "Confirm priority level",
            }
        )

        # Query 3: Scope clarification
        queries.append(
            {
                "question": "What is the scope of this case?",
                "type": "multiple_choice",
                "options": [
                    "Single module/component",
                    "Multiple modules/components",
                    "System-wide change",
                    "Architectural change",
                ],
                "purpose": "Clarify scope",
            }
        )

        # Query 4: User examples relevance
        if structure.user_examples:
            queries.append(
                {
                    "question": "Are the provided examples relevant to the solution?",
                    "type": "multiple_choice",
                    "options": [
                        "Yes, very relevant",
                        "Somewhat relevant",
                        "Not directly relevant",
                        "Need more examples",
                    ],
                    "purpose": "Assess example relevance",
                }
            )

        return queries

    def _update_reference_file(self, reference_file_path: str, metadata: dict[str, Any]):
        """Update reference file with advanced protocol data."""
        reference_path = Path(reference_file_path)
        if not reference_path.exists():
            return

        with open(reference_path) as f:
            reference = json.load(f)

        reference["advanced_protocols"] = metadata
        reference["requires_contextualization"] = len(metadata["generated_queries"]) > 0

        with open(reference_path, "w") as f:
            json.dump(reference, f, indent=2)

    def _store_in_memory(self, case_id: str, structure: CaseStructure, metadata: dict[str, Any]):
        """Store case in memory for future reference."""
        case_entry = {
            "case_id": case_id,
            "timestamp": structure.timestamp,
            "category": structure.category.value,
            "keywords": structure.keywords,
            "priority": structure.priority,
            "confidence": structure.confidence,
            "solution_summary": None,  # Will be filled after case resolution
            "metadata": metadata,
        }

        self.memory["cases"].append(case_entry)

        # Update keyword index
        for keyword in structure.keywords:
            if keyword not in self.memory["keywords"]:
                self.memory["keywords"][keyword] = []
            self.memory["keywords"][keyword].append(case_id)

        # Save memory
        memory_file = self.memory_path / "memory.json"
        with open(memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)


if __name__ == "__main__":
    from .case_filing import CaseFilingSystem

    # Example usage
    filing_system = CaseFilingSystem()
    handler = AdvancedProtocolHandler()

    test_input = "I have a very unusual integration requirement that doesn't fit standard patterns"
    structure = filing_system.log_and_categorize(raw_input=test_input)

    metadata = handler.handle_rare_case(
        case_id="TEST-002",
        structured_data=structure,
        raw_input=test_input,
        reference_file_path=".case_references/TEST-002_reference.json",
    )

    print("Generated Queries:")
    for query in metadata["generated_queries"]:
        print(f"  Q: {query['question']}")
        print(f"     Options: {', '.join(query['options'])}")
