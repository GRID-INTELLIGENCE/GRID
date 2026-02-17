"""Databricks-backed continuous learning system.

Integrates continuous learning with Databricks database for persistent storage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from application.mothership.repositories.agentic import AgenticRepository

try:
    from .case_filing import CaseStructure  # type: ignore[import-not-found]
    from .continuous_learning import ContinuousLearningSystem  # type: ignore[import-not-found]
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from case_filing import CaseStructure  # type: ignore[import-not-found]
    from continuous_learning import ContinuousLearningSystem  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class DatabricksLearningSystem(ContinuousLearningSystem):
    """Continuous learning system backed by Databricks."""

    def __init__(
        self,
        repository: AgenticRepository,
        memory_path: Path | None = None,
        max_memory_size_mb: int = 100,
        enable_auto_cleanup: bool = True,
    ):
        """Initialize Databricks-backed learning system.

        Args:
            repository: Agentic repository for Databricks operations
            memory_path: Optional local memory path (for fallback)
            max_memory_size_mb: Maximum memory size in MB (for local fallback)
            enable_auto_cleanup: Enable automatic cleanup
        """
        # Initialize base class with local memory as fallback
        super().__init__(
            memory_path=memory_path or Path(".case_memory"),
            max_memory_size_mb=max_memory_size_mb,
            enable_auto_cleanup=enable_auto_cleanup,
        )
        self.repository = repository

    async def record_case_completion(
        self,
        case_id: str,
        structure: dict[str, Any],
        solution: str,
        outcome: str,
        agent_experience: dict[str, Any],
    ) -> None:
        """Record completed case in Databricks.

        Args:
            case_id: Case identifier
            structure: Case structure (can be CaseStructure dict or dict)
            solution: Solution applied
            outcome: Outcome (success, partial, failure)
            agent_experience: Agent experience data
        """
        # Convert structure to CaseStructure if needed
        if isinstance(structure, dict):
            # Extract category from structure
            category = structure.get("category")
            if isinstance(category, str):
                # Try to convert to CaseCategory enum
                try:
                    from .case_filing import CaseCategory

                    category_enum = CaseCategory(category)
                except (ValueError, KeyError):
                    category_enum = None
            else:
                category_enum = None
        else:
            category_enum = structure.category if hasattr(structure, "category") else None

        # Update case in Databricks
        try:
            await self.repository.update_case_status(
                case_id=case_id,
                status="completed",
                outcome=outcome,
                solution=solution,
                agent_experience=agent_experience,
            )
            logger.info(f"Recorded case completion for {case_id} in Databricks")
        except Exception as e:
            logger.error(f"Error recording case completion in Databricks: {e}")
            # Fallback to local storage
            await super().record_case_completion(
                case_id=case_id,
                structure=(
                    structure
                    if isinstance(structure, CaseStructure)
                    else CaseStructure(
                        timestamp="",
                        category=category_enum or CaseCategory.RARE,
                    )
                ),
                solution=solution,
                outcome=outcome,
                agent_experience=agent_experience,
            )

    async def get_agent_experience(self) -> dict[str, Any]:
        """Get aggregated agent experience from Databricks.

        Returns:
            Experience metrics dictionary
        """
        try:
            # Get experience from Databricks
            db_experience = await self.repository.get_agent_experience()

            # Get local experience as fallback
            local_experience = super().get_agent_experience()

            # Merge results (prefer Databricks)
            merged = {
                "total_cases": db_experience.get("total_cases", 0),
                "success_rate": db_experience.get("success_rate", 0.0),
                "category_distribution": db_experience.get("category_distribution", {}),
                "experience_by_category": db_experience.get("experience_by_category", {}),
                "common_patterns": local_experience.get("common_patterns", []),
                "learning_insights": self._generate_learning_insights_from_db(db_experience),
            }

            return merged

        except Exception as e:
            logger.error(f"Error getting experience from Databricks: {e}")
            # Fallback to local
            return super().get_agent_experience()

    async def get_recommendations(
        self,
        structure: CaseStructure,
    ) -> list[dict[str, Any]]:
        """Get recommendations from Databricks.

        Args:
            structure: Case structure

        Returns:
            List of recommendation dictionaries
        """
        try:
            # Find similar cases in Databricks
            similar_cases = await self.repository.find_similar_cases(
                category=structure.category.value,
                keywords=structure.keywords,
                limit=5,
            )

            recommendations = []
            for case in similar_cases:
                recommendations.append(
                    {
                        "case_id": case.case_id,
                        "similarity": 0.5,  # Would calculate actual similarity
                        "recommended_solution": case.solution,
                        "expected_outcome": case.outcome,
                        "lessons_learned": case.agent_experience.get("lessons", []) if case.agent_experience else [],
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations from Databricks: {e}")
            # Fallback to local
            return super().get_recommendations(structure)

    def _generate_learning_insights_from_db(self, db_experience: dict[str, Any]) -> list[str]:
        """Generate learning insights from Databricks experience data.

        Args:
            db_experience: Experience data from Databricks

        Returns:
            List of insight strings
        """
        insights = []

        total = db_experience.get("total_cases", 0)
        if total > 0:
            insights.append(f"Processed {total} cases total")

        success_rate = db_experience.get("success_rate", 0.0)
        if success_rate > 0.8:
            insights.append(f"High success rate ({success_rate:.1%}) - system performing well")
        elif success_rate < 0.5:
            insights.append(f"Low success rate ({success_rate:.1%}) - may need review")

        # Category insights
        category_dist = db_experience.get("category_distribution", {})
        if category_dist:
            most_common = max(category_dist.items(), key=lambda x: x[1])
            insights.append(f"Most common category: {most_common[0]} ({most_common[1]} cases)")

        return insights
