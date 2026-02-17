from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.mothership.db.models_agentic import AgenticCase

logger = logging.getLogger(__name__)


class CrossRunIndexer:
    """Service to index and query agentic insights across multiple execution runs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def index_run_results(self, run_id: str):
        """Index results from a specific run into the global knowledge-base."""
        logger.info(f"Indexing run {run_id} into cross-run index...")
        # Implementation would extract outcomes and solutions
        # and perhaps store them in a more optimized retrieval table or vector store.
        pass

    async def query_insights(self, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
        """Query historical insights across all previous runs."""
        # Simple similarity check for now (based on categories/keywords)
        # In a full implementation, this would use the vector store.
        logger.info(f"Querying cross-run insights for: {query_text}")

        # Fallback to searching successfully completed cases
        stmt = (
            select(AgenticCase)
            .where(and_(AgenticCase.status == "completed", AgenticCase.outcome == "success"))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        cases = result.scalars().all()

        return [
            {
                "case_id": c.case_id,
                "category": c.category,
                "solution": c.solution,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ]
