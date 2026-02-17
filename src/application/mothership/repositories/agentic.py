"""Repository for agentic system Databricks operations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.mothership.db.models_agentic import AgenticCase

logger = logging.getLogger(__name__)


class AgenticRepository:
    """Repository for agentic case operations in Databricks."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_case(
        self,
        case_id: str,
        raw_input: str,
        user_id: str | None = None,
        status: str = "created",
    ) -> AgenticCase:
        """Create a new case.

        Args:
            case_id: Unique case identifier
            raw_input: Raw user input
            user_id: User identifier
            status: Initial status

        Returns:
            Created AgenticCase instance
        """
        case = AgenticCase(
            case_id=case_id,
            raw_input=raw_input,
            user_id=user_id,
            status=status,
            created_at=datetime.now(UTC),
        )
        self.session.add(case)
        await self.session.commit()
        await self.session.refresh(case)
        logger.debug(f"Created case {case_id}")
        return case

    async def get_case(self, case_id: str) -> AgenticCase | None:
        """Get case by ID.

        Args:
            case_id: Case identifier

        Returns:
            AgenticCase instance or None
        """
        result = await self.session.execute(select(AgenticCase).where(AgenticCase.case_id == case_id))
        return result.scalar_one_or_none()

    async def update_case_status(
        self,
        case_id: str,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        confidence: float | None = None,
        structured_data: dict[str, Any] | None = None,
        reference_file_path: str | None = None,
        agent_role: str | None = None,
        task: str | None = None,
        outcome: str | None = None,
        solution: str | None = None,
        agent_experience: dict[str, Any] | None = None,
    ) -> AgenticCase | None:
        """Update case status and fields.

        Args:
            case_id: Case identifier
            status: New status
            category: Category
            priority: Priority
            confidence: Confidence score
            structured_data: Structured data dictionary
            reference_file_path: Reference file path
            agent_role: Agent role
            task: Task executed
            outcome: Outcome
            solution: Solution
            agent_experience: Agent experience data

        Returns:
            Updated AgenticCase instance or None
        """
        case = await self.get_case(case_id)
        if not case:
            logger.warning(f"Case {case_id} not found")
            return None

        if status:
            case.status = status
        if category:
            case.category = category
        if priority:
            case.priority = priority
        if confidence is not None:
            case.confidence = confidence
        if structured_data:
            case.structured_data = structured_data
        if reference_file_path:
            case.reference_file_path = reference_file_path
        if agent_role:
            case.agent_role = agent_role
        if task:
            case.task = task
        if outcome:
            case.outcome = outcome
        if solution:
            case.solution = solution
        if agent_experience:
            case.agent_experience = agent_experience

        case.updated_at = datetime.now(UTC)

        if status == "completed":
            case.completed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(case)
        logger.debug(f"Updated case {case_id} status to {status}")
        return case

    async def find_similar_cases(
        self,
        category: str | None = None,
        keywords: list[str] | None = None,
        limit: int = 10,
    ) -> list[AgenticCase]:
        """Find similar cases for recommendations.

        Args:
            category: Filter by category
            keywords: Filter by keywords
            limit: Maximum number of results

        Returns:
            List of similar cases
        """
        query = select(AgenticCase).where(AgenticCase.status == "completed")

        if category:
            query = query.where(AgenticCase.category == category)

        # Filter by keywords if provided (simple contains check)
        if keywords:
            # This is a simplified implementation
            # In production, you might want to use full-text search or vector similarity
            conditions = []
            for keyword in keywords:
                conditions.append(AgenticCase.raw_input.contains(keyword))
            if conditions:
                query = query.where(and_(*conditions))

        query = query.order_by(AgenticCase.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_agent_experience(self) -> dict[str, Any]:
        """Get aggregated agent experience metrics.

        Returns:
            Dictionary with experience metrics
        """
        # Total cases
        total_result = await self.session.execute(select(func.count(AgenticCase.case_id)))
        total_cases = total_result.scalar() or 0

        # Success rate
        success_result = await self.session.execute(
            select(func.count(AgenticCase.case_id)).where(AgenticCase.outcome == "success")
        )
        success_count = success_result.scalar() or 0
        success_rate = success_count / total_cases if total_cases > 0 else 0.0

        # Category distribution
        category_result = await self.session.execute(
            select(AgenticCase.category, func.count(AgenticCase.case_id))
            .where(AgenticCase.category.isnot(None))
            .group_by(AgenticCase.category)
        )
        category_distribution = {row[0]: row[1] for row in category_result.all()}

        # Experience by category
        experience_by_category = {}
        for category in category_distribution.keys():
            cat_total_result = await self.session.execute(
                select(func.count(AgenticCase.case_id)).where(AgenticCase.category == category)
            )
            cat_total = cat_total_result.scalar() or 0

            cat_success_result = await self.session.execute(
                select(func.count(AgenticCase.case_id)).where(
                    and_(AgenticCase.category == category, AgenticCase.outcome == "success")
                )
            )
            cat_success = cat_success_result.scalar() or 0
            cat_success_rate = cat_success / cat_total if cat_total > 0 else 0.0

            experience_by_category[category] = {
                "total": cat_total,
                "successes": cat_success,
                "success_rate": cat_success_rate,
            }

        return {
            "total_cases": total_cases,
            "success_rate": success_rate,
            "category_distribution": category_distribution,
            "experience_by_category": experience_by_category,
        }

    async def get_category_distribution(self) -> dict[str, int]:
        """Get distribution of cases by category.

        Returns:
            Dictionary mapping category to count
        """
        result = await self.session.execute(
            select(AgenticCase.category, func.count(AgenticCase.case_id))
            .where(AgenticCase.category.isnot(None))
            .group_by(AgenticCase.category)
        )
        return {row[0]: row[1] for row in result.all()}

    async def list_cases(
        self,
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgenticCase]:
        """List cases with optional filters.

        Args:
            status: Filter by status
            category: Filter by category
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of cases
        """
        query = select(AgenticCase)

        if status:
            query = query.where(AgenticCase.status == status)
        if category:
            query = query.where(AgenticCase.category == category)

        query = query.order_by(AgenticCase.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())
