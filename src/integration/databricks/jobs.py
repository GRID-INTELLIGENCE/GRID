"""Databricks Jobs management."""

from __future__ import annotations

import logging
from typing import Any

from databricks.sdk.service.jobs import (
    JobSettings,
    NotebookTask,
    Task,
)

logger = logging.getLogger(__name__)


class DatabricksJobsManager:
    """Manage Databricks jobs."""

    def __init__(self, client):
        """Initialize jobs manager.

        Args:
            client: DatabricksClient instance
        """
        self.client = client

    def create_notebook_job(
        self,
        job_name: str,
        notebook_path: str,
        cluster_id: str | None = None,
        base_parameters: dict[str, Any] | None = None,
    ) -> str:
        """Create a job that runs a notebook.

        Args:
            job_name: Name for the job
            notebook_path: Path to notebook in workspace (e.g., /Repos/user/repo/notebook.ipynb)
            cluster_id: Cluster ID to run on (optional, can use new_cluster)
            base_parameters: Parameters to pass to notebook

        Returns:
            Job ID
        """
        task = Task(
            task_key="notebook_task",
            description=f"Run notebook: {notebook_path}",
            notebook_task=NotebookTask(
                notebook_path=notebook_path,
                base_parameters=base_parameters or {},
            ),
        )

        if cluster_id:
            task.existing_cluster_id = cluster_id

        settings = JobSettings(
            name=job_name,
            tasks=[task],
        )

        job = self.client.workspace.jobs.create(settings=settings)
        logger.info(f"Created job '{job_name}' with ID: {job.job_id}")
        return job.job_id

    def run_job(
        self,
        job_id: str,
        jar_params: list[str] | None = None,
        notebook_params: dict[str, Any] | None = None,
    ) -> int:
        """Run a job and return the run ID.

        Args:
            job_id: Job ID to run
            jar_params: Parameters for JAR jobs
            notebook_params: Parameters for notebook jobs

        Returns:
            Run ID
        """
        run = self.client.workspace.jobs.run_now(
            job_id=job_id,
            jar_params=jar_params,
            notebook_params=notebook_params,
        )
        logger.info(f"Started job {job_id}, run ID: {run.run_id}")
        return run.run_id

    def get_run_status(self, run_id: int) -> dict[str, Any]:
        """Get the status of a job run.

        Args:
            run_id: Run ID

        Returns:
            Run status information
        """
        run = self.client.workspace.jobs.get_run(run_id=run_id)
        return {
            "run_id": run.run_id,
            "job_id": run.job_id,
            "state": run.life_cycle_state,
            "result_state": run.state.result_state,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "setup_duration": run.setup_duration,
            "execution_duration": run.execution_duration,
            "cleanup_duration": run.cleanup_duration,
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all jobs in the workspace.

        Returns:
            List of job information
        """
        jobs = [
                {
                    "job_id": job.job_id,
                    "settings": job.settings.name,
                    "created_time": job.created_time,
                }
            for job in self.client.workspace.jobs.list()
        ]
        return jobs

    def delete_job(self, job_id: str) -> bool:
        """Delete a job.

        Args:
            job_id: Job ID to delete

        Returns:
            True if successful
        """
        try:
            self.client.workspace.jobs.delete(job_id=job_id)
            logger.info(f"Deleted job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
