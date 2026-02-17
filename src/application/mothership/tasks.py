"""Celery background tasks for Mothership application.

Note: Celery tasks run in worker processes, so blocking calls like time.sleep()
are acceptable here (unlike in async FastAPI context).
"""

import logging
import time
from typing import Any

from celery import Celery  # type: ignore[import-untyped]

from application.mothership.config import get_settings

logger = logging.getLogger(__name__)

# Initialize Celery
settings = get_settings()
app = Celery("mothership_tasks", broker=settings.database.redis_url, backend=settings.database.redis_url)


@app.task(name="agentic.execute_case")
def execute_case_task(case_id: str, agent_role: str, task: str) -> dict[str, Any]:
    """Background task to execute an agentic case.

    Args:
        case_id: Unique identifier for the case
        agent_role: Role of the agent executing the case
        task: Task description to execute

    Returns:
        Dictionary with case_id and status
    """
    logger.info(f"Starting execution for case {case_id} as {agent_role}")

    # In a real implementation, we would import AgenticSystem here
    # and call its execute method.
    # For now, we simulate heavy processing.
    time.sleep(10)

    logger.info(f"Completed execution for case {case_id}")
    return {"case_id": case_id, "status": "completed"}


@app.task(name="pipeline.harvest")
def harvest_task(run_id: str) -> dict[str, Any]:
    """Background task for repository harvesting.

    Args:
        run_id: Unique identifier for the harvest run

    Returns:
        Dictionary with run_id and harvested status
    """
    logger.info(f"Starting harvest for run {run_id}")
    # Integration with harvest logic
    time.sleep(30)
    logger.info(f"Harvest completed for run {run_id}")
    return {"run_id": run_id, "harvested": True}
