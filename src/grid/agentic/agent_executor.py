"""Agent execution engine for executing agent tasks."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import aiofiles

from .adaptive_timeout import AdaptiveTimeoutManager
from .error_classifier import ErrorClassifier
from .learning_coordinator import OnlineLearningCoordinator
from .recovery_engine import RecoveryEngine
from .runtime_behavior_tracer import ExecutionBehavior, ExecutionOutcome, RuntimeBehaviorTracer
from .skill_retriever import SkillRetriever

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes agent tasks using role templates and task prompts."""

    def __init__(self, knowledge_base_path: Path, skill_store_path: Path | None = None):
        """Initialize agent executor.

        Args:
            knowledge_base_path: Path to knowledge base (agent prompts)
            skill_store_path: Optional path to Antigravity skill store
        """
        self.knowledge_base_path = knowledge_base_path
        self.role_templates_path = knowledge_base_path / "role_templates.md"
        self.task_prompts_path = knowledge_base_path / "task_prompts.md"
        self.agent_prompts_json = knowledge_base_path / "agent_prompts.json"

        # Skill store integration
        self.skill_store_path = skill_store_path or Path(
            os.getenv("GRID_SKILL_STORE_PATH", str(Path.home() / ".grid" / "knowledge"))
        )
        self.skill_retriever = SkillRetriever(self.skill_store_path)

        # Behavior Intelligence (Phase 1)
        self.tracer = RuntimeBehaviorTracer()
        self.timeout_manager = AdaptiveTimeoutManager()
        self.recovery_engine = RecoveryEngine()
        self.learning_coordinator = OnlineLearningCoordinator()

    async def execute_task(
        self,
        case_id: str,
        reference_file_path: str,
        agent_role: str | None = None,
        task: str | None = None,
    ) -> dict[str, Any]:
        """Execute an agent task for a case.

        Args:
            case_id: Case identifier
            reference_file_path: Path to reference file
            agent_role: Specific agent role to use (optional)
            task: Specific task to execute (optional)

        Returns:
            Execution result dictionary
        """
        # Load reference file
        reference = await self._load_reference_file(reference_file_path)
        if not reference:
            raise ValueError(f"Reference file not found: {reference_file_path}")

        # Determine agent role
        if not agent_role:
            recommended_roles = reference.get("recommended_roles", [])
            agent_role = recommended_roles[0] if recommended_roles else "Analyst"

        # Determine task
        if not task:
            recommended_tasks = reference.get("recommended_tasks", [])
            task = recommended_tasks[0] if recommended_tasks else "/inventory"

        logger.info(f"Executing task {task} with role {agent_role} for case {case_id}")

        # Start Behavior Trace
        trace = self.tracer.start_trace(case_id=case_id, agent_role=agent_role, task_type=task)

        # Retrieve relevant skills to enhance context
        category = reference.get("metadata", {}).get("category")
        keywords = reference.get("structured_data", {}).get("keywords", [])

        relevant_skills = self.skill_retriever.find_relevant_skills(category=category, keywords=keywords, limit=3)

        trace.skills_retrieved = len(relevant_skills)
        if relevant_skills:
            logger.info(f"Found {len(relevant_skills)} relevant skills to enhance execution.")
            # Record skills in metadata
            trace.metadata["retrieved_skill_ids"] = [s.get("id") for s in relevant_skills]

        # Determine adaptive timeout
        timeout_ms = self.timeout_manager.get_timeout_for_task(task, agent_role)
        trace.metadata["timeout_applied_ms"] = timeout_ms

        # Execute based on task type with recovery logic (bounded by adaptive timeout)
        try:
            async with asyncio.timeout(timeout_ms / 1000):
                result = await self.recovery_engine.execute_with_recovery(
                    self._execute_task_by_type,
                    case_id=case_id,
                    reference=reference,
                    agent_role=agent_role,
                    task=task,
                    trace=trace,
                )

            # Record success
            self.tracer.end_trace(trace.trace_id, ExecutionOutcome.SUCCESS)
            self.timeout_manager.record_execution_time(task, agent_role, trace.duration_ms, True)

            # Finalize learning
            await self.learning_coordinator.record_execution_outcome(case_id, trace)

            return result
        except TimeoutError:
            self.tracer.end_trace(trace.trace_id, ExecutionOutcome.FAILURE)
            self.timeout_manager.record_execution_time(task, agent_role, trace.duration_ms, False)
            trace.error_category = "timeout"
            trace.metadata["error_message"] = f"Task timed out after {timeout_ms}ms"
            logger.error(f"Task execution timed out ({timeout_ms}ms) for {task} as {agent_role}")
            raise
        except Exception as e:
            # Record failure with classification
            error_context = ErrorClassifier.classify(e)
            trace.error_category = error_context.category.value
            trace.metadata["error_severity"] = error_context.severity.value
            trace.metadata["error_message"] = error_context.message

            self.tracer.end_trace(trace.trace_id, ExecutionOutcome.FAILURE)
            self.timeout_manager.record_execution_time(task, agent_role, trace.duration_ms, False)
            logger.error(f"Task execution failed ({error_context.category.value}): {e}")
            raise

    async def _load_reference_file(self, reference_file_path: str) -> dict[str, Any] | None:
        """Load reference file for case execution with path validation."""
        try:
            # Security fix: Validate path is within knowledge base
            base_path = Path(self.knowledge_base_path)
            path = (base_path / reference_file_path).resolve()

            # Security check: ensure the resolved path is still within knowledge base
            if not path.is_relative_to(base_path):
                logger.error(f"Access denied: path outside knowledge base: {reference_file_path}")
                return None

            if not await asyncio.to_thread(path.exists):
                logger.warning(f"Reference file not found: {reference_file_path}")
                return None

            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading reference file {reference_file_path}: {e}")
            return None

    async def _execute_task_by_type(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
        task: str,
        trace: ExecutionBehavior | None = None,
    ) -> dict[str, Any]:
        """Execute task based on task type.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role
            task: Task to execute
            trace: Active behavior trace

        Returns:
            Execution result
        """
        # Map task to execution method
        task_handlers = {
            "/inventory": self._execute_inventory,
            "/gapanalysis": self._execute_gap_analysis,
            "/plan": self._execute_plan,
            "/execute": self._execute_code_generation,
            "/validate": self._execute_validation,
            "/safety review": self._execute_safety_review,
        }

        handler = task_handlers.get(task)
        if not handler:
            logger.warning(f"Unknown task type: {task}. Using default handler.")
            handler = self._execute_default

        # Record route decision
        if trace:
            trace.add_decision(
                decision_type="route",
                rationale=f"Routing {task} to {handler.__name__}",
                confidence=1.0,  # Static mapping is high confidence
            )

        return await handler(case_id, reference, agent_role)

    async def _execute_inventory(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute inventory task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing inventory for case {case_id}")
        # In a real implementation, this would call the inventory script
        # For now, return a placeholder result
        return {
            "task": "/inventory",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "inventory_completed": True,
                "note": "Inventory execution would be implemented here",
            },
        }

    async def _execute_gap_analysis(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute gap analysis task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing gap analysis for case {case_id}")
        return {
            "task": "/gapanalysis",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "gaps_identified": [],
                "note": "Gap analysis execution would be implemented here",
            },
        }

    async def _execute_plan(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute planning task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing plan for case {case_id}")
        return {
            "task": "/plan",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "backlog_created": True,
                "note": "Planning execution would be implemented here",
            },
        }

    async def _execute_code_generation(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute code generation task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing code generation for case {case_id}")
        return {
            "task": "/execute",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "artifacts_generated": [],
                "note": "Code generation execution would be implemented here",
            },
        }

    async def _execute_validation(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute validation task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing validation for case {case_id}")
        return {
            "task": "/validate",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "validation_passed": True,
                "note": "Validation execution would be implemented here",
            },
        }

    async def _execute_safety_review(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Execute safety review task.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing safety review for case {case_id}")
        return {
            "task": "/safety review",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "safety_review_passed": True,
                "note": "Safety review execution would be implemented here",
            },
        }

    async def _execute_default(
        self,
        case_id: str,
        reference: dict[str, Any],
        agent_role: str,
    ) -> dict[str, Any]:
        """Default task execution handler.

        Args:
            case_id: Case identifier
            reference: Reference file content
            agent_role: Agent role

        Returns:
            Execution result
        """
        logger.info(f"Executing default task for case {case_id}")
        return {
            "task": "default",
            "status": "completed",
            "result": {
                "case_id": case_id,
                "note": "Default task execution",
            },
        }
