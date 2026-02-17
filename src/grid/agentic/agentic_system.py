"""Core agentic system orchestrator."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Protocol, cast

import aiofiles

from cognitive import CognitiveEngine, InteractionEvent, get_cognitive_engine
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import CognitiveState
from cognitive.scaffolding_engine import get_scaffolding_engine
from grid.exceptions import SkillStoreError
from grid.xai.explainer import explainer
from safety.guardian.engine import RuleAction, get_guardian_engine
from safety.guardian.engine import Severity as GuardianSeverity

from .agent_executor import AgentExecutor
from .event_bus import EventBus, get_event_bus
from .events import CaseCompletedEvent, CaseExecutedEvent
from .memo_generator import MemoGenerator
from .skill_retriever import SkillRetriever

logger = logging.getLogger(__name__)


class _Adaptation(Protocol):
    adaptation_type: str


class _CaseLike(Protocol):
    case_id: str
    category: str
    solution: str
    outcome: str


class AgenticSystem:
    """Main orchestrator for agentic system with cognitive awareness."""

    def __init__(
        self,
        knowledge_base_path: Path,
        event_bus: EventBus | None = None,
        repository: Any | None = None,
        cognitive_engine: CognitiveEngine | None = None,
        enable_cognitive: bool = True,
    ):
        """Initialize agentic system.

        Args:
            knowledge_base_path: Path to knowledge base (agent prompts)
            event_bus: Optional event bus instance
            repository: Optional repository for case operations
            cognitive_engine: Optional cognitive engine instance
            enable_cognitive: Whether to enable cognitive features
        """
        self.knowledge_base_path = knowledge_base_path
        self.event_bus = event_bus or get_event_bus()
        self.repository = repository
        self.agent_executor = AgentExecutor(knowledge_base_path)

        # Use environment variable for skill store path or default to home directory
        self.skill_store_path = Path(os.getenv("GRID_SKILL_STORE_PATH", str(Path.home() / ".grid" / "knowledge")))
        self.skill_retriever = SkillRetriever(self.skill_store_path)
        self.memo_generator = MemoGenerator()

        # Cognitive components
        self.enable_cognitive = enable_cognitive
        self.cognitive_engine = cognitive_engine or (get_cognitive_engine() if enable_cognitive else None)
        self.scaffolding_engine = get_scaffolding_engine() if enable_cognitive else None

        # Store cognitive context per case
        self._cognitive_context: dict[str, dict[str, Any]] = {}

    async def execute_case(
        self,
        case_id: str,
        reference_file_path: str,
        agent_role: str | None = None,
        task: str | None = None,
        user_id: str = "default",
    ) -> dict[str, Any]:
        """Execute a case using the agent executor with cognitive awareness.

        Args:
            case_id: Case identifier
            reference_file_path: Path to reference file
            agent_role: Specific agent role to use (optional)
            task: Specific task to execute (optional)
            user_id: User identifier for cognitive tracking

        Returns:
            Execution result dictionary
        """
        import time

        start_time = time.time()

        # Track cognitive state before execution
        cognitive_state: CognitiveState | None = None
        cognitive_adaptations: list[str] = []

        if self.enable_cognitive and self.cognitive_engine:
            try:
                # Create interaction event for case start
                interaction = InteractionEvent(
                    user_id=user_id,
                    action="case_start",
                    case_id=case_id,
                    metadata={"agent_role": agent_role, "task": task},
                )
                cognitive_state = await self.cognitive_engine.track_interaction(interaction)

                # Get adaptations based on cognitive state
                _, adaptations_raw = await self.cognitive_engine.adapt_response(
                    query=task or "/execute",
                    context={"case_id": case_id},
                    user_id=user_id,
                )
                adaptations = cast("list[_Adaptation]", adaptations_raw)
                cognitive_adaptations = [a.adaptation_type for a in adaptations]

                logger.debug(
                    f"Cognitive state for {case_id}: load={cognitive_state.estimated_load:.2f}, "
                    f"mode={cognitive_state.processing_mode.value}, "
                    f"adaptations={cognitive_adaptations}"
                )

                # Apply scaffolding if cognitive load is high
                if cognitive_state.estimated_load > 7.0 and self.scaffolding_engine:
                    # Scaffolding would be applied to reference file content
                    pass  # Implementation depends on reference file format

            except Exception as e:
                logger.warning(f"Cognitive tracking failed for {case_id}: {e}")

        # Store cognitive context
        self._cognitive_context[case_id] = {
            "user_id": user_id,
            "cognitive_state": cognitive_state,
            "adaptations": cognitive_adaptations,
        }

        # Emit case.executed event with cognitive context
        executed_event = CaseExecutedEvent(
            case_id=case_id,
            agent_role=agent_role or "Executor",
            task=task or "/execute",
        )
        event_dict: dict[str, Any] = executed_event.to_dict()
        if cognitive_state:
            event_dict["cognitive_context"] = {
                "load": cognitive_state.estimated_load,
                "mode": cognitive_state.processing_mode.value,
                "adaptations": cognitive_adaptations,
            }
        await self.event_bus.publish(event_dict)

        # Execute task
        try:
            result: dict[str, Any] = await self.agent_executor.execute_task(
                case_id=case_id,
                reference_file_path=reference_file_path,
                agent_role=agent_role,
                task=task,
            )

            execution_time = time.time() - start_time

            # Determine outcome
            outcome = "success"
            if result.get("status") != "completed":
                outcome = "partial"

            # Track cognitive state after execution
            if self.enable_cognitive and self.cognitive_engine and user_id:
                try:
                    outcome_interaction = InteractionEvent(
                        user_id=user_id,
                        action="case_complete",
                        case_id=case_id,
                        metadata={
                            "agent_role": agent_role,
                            "task": task,
                            "duration": execution_time,
                            "outcome": outcome,
                        },
                    )
                    await self.cognitive_engine.track_interaction(outcome_interaction)
                except Exception as e:
                    logger.warning(f"Post-execution cognitive tracking failed: {e}")

            # Emit case.completed event with cognitive context
            completed_event = CaseCompletedEvent(
                case_id=case_id,
                outcome=outcome,
                solution=str(result.get("result", {})),
                agent_experience={
                    "execution_time_seconds": execution_time,
                    "agent_role": agent_role or "Executor",
                    "task": task or "/execute",
                },
                execution_time_seconds=execution_time,
            )
            completed_event_dict: dict[str, Any] = completed_event.to_dict()
            if cognitive_state:
                completed_event_dict["cognitive_context"] = {
                    "load": cognitive_state.estimated_load,
                    "mode": cognitive_state.processing_mode.value,
                    "adaptations": cognitive_adaptations,
                }
            await self.event_bus.publish(completed_event_dict)

            logger.info(f"Case {case_id} executed successfully in {execution_time:.2f}s")

            return {
                **result,
                "execution_time_seconds": execution_time,
                "outcome": outcome,
                "cognitive_state": cognitive_state.model_dump(mode="json") if cognitive_state else None,
                "cognitive_adaptations": cognitive_adaptations,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing case {case_id}: {e}")

            # Track error in cognitive state
            if self.enable_cognitive and self.cognitive_engine and user_id:
                try:
                    error_interaction = InteractionEvent(
                        user_id=user_id,
                        action="error",
                        case_id=case_id,
                        metadata={
                            "error": str(e),
                            "agent_role": agent_role,
                            "duration": execution_time,
                            "outcome": "failure",
                        },
                    )
                    await self.cognitive_engine.track_interaction(error_interaction)
                except Exception as ce:
                    logger.warning(f"Error cognitive tracking failed: {ce}")

            # Emit failure event
            failed_event = CaseCompletedEvent(
                case_id=case_id,
                outcome="failure",
                solution=f"Execution failed: {str(e)}",
                agent_experience={
                    "execution_time_seconds": execution_time,
                    "error": str(e),
                },
                execution_time_seconds=execution_time,
            )
            await self.event_bus.publish(failed_event.to_dict())

            raise

    async def get_recommendations(
        self,
        case_id: str,
        reference_file_path: str,
    ) -> list[dict[str, Any]]:
        """Get recommendations for a case based on similar past cases.

        Args:
            case_id: Case identifier
            reference_file_path: Path to reference file

        Returns:
            List of recommendation dictionaries
        """
        # 1. Look in local Antigravity Skill Store first
        recommendations: list[dict[str, Any]] = []

        # Load reference to get category and keywords
        import json

        try:
            async with aiofiles.open(reference_file_path) as f:
                content = await f.read()
                reference = cast("dict[str, Any]", json.loads(content))
        except FileNotFoundError as e:
            logger.error(f"Reference file not found: {reference_file_path}", exc_info=True)
            raise SkillStoreError(f"Reference file not found: {reference_file_path}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in reference file: {reference_file_path}", exc_info=True)
            raise SkillStoreError(f"Invalid JSON in reference file: {reference_file_path}") from e
        except Exception as e:
            logger.warning(f"Could not load reference file: {reference_file_path}: {e}")
            return []

        category = reference.get("metadata", {}).get("category")
        keywords = reference.get("structured_data", {}).get("keywords", [])

        # Find historical skills
        historical_skills: list[dict[str, Any]] = self.skill_retriever.find_relevant_skills(
            category=category, keywords=keywords, limit=5
        )

        recommendations.extend(
            {
                "case_id": skill["id"],
                "category": skill["metadata"].get("category", "Uncategorized"),
                "solution": skill["metadata"].get("summary", "Historical skill found"),
                "outcome": "success",
                "source": "antigravity_skill_store",
            }
            for skill in historical_skills
        )

        # 2. Then look in repository if available
        if self.repository:
            similar_cases = cast(
                "list[_CaseLike]",
                await self.repository.find_similar_cases(
                    category=category,
                    keywords=keywords,
                    limit=5,
                ),
            )
            recommendations.extend(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "solution": case.solution,
                    "outcome": case.outcome,
                    "source": "repository",
                }
                for case in similar_cases
            )

        return recommendations

    # Minimum confidence floor for Lawyer convergence
    LAWYER_CONFIDENCE_FLOOR = 0.6

    async def iterative_execute(
        self, case_id: str, reference_file_path: str, max_iterations: int = 3
    ) -> dict[str, Any]:
        """Perform iterative execution for the Lawyer phase."""
        logger.info(f"Starting iterative execution for case {case_id}")

        guardian = get_guardian_engine()
        results: list[dict[str, Any]] = []
        iteration_audits: list[dict[str, Any]] = []
        guardian_blocked = False

        for i in range(max_iterations):
            logger.info(f"Lawyer iteration {i + 1}/{max_iterations}")
            result = await self.execute_case(
                case_id=case_id, reference_file_path=reference_file_path, agent_role="Lawyer", task=f"/iterate/{i + 1}"
            )
            results.append(result)

            # --- Guardian safety gate: evaluate iteration output ---
            result_text = (
                json.dumps(result.get("result", {}))
                if isinstance(result.get("result"), dict)
                else str(result.get("result", ""))
            )
            matches, latency_ms = guardian.evaluate(result_text, use_cache=True)

            blocking_matches = [
                m
                for m in matches
                if m.action in (RuleAction.BLOCK, RuleAction.CANARY)
                or (
                    m.action == RuleAction.ESCALATE and m.severity in (GuardianSeverity.HIGH, GuardianSeverity.CRITICAL)
                )
            ]
            warning_matches = [m for m in matches if m.action in (RuleAction.WARN, RuleAction.LOG)]

            audit_entry: dict[str, Any] = {
                "iteration": i + 1,
                "outcome": result.get("outcome"),
                "guardian_latency_ms": round(latency_ms, 2),
                "guardian_matches": len(matches),
                "guardian_blocked": len(blocking_matches) > 0,
                "guardian_warnings": len(warning_matches),
                "matched_rules": [m.to_dict() for m in matches],
                "result_snapshot": result.get("result"),
            }
            iteration_audits.append(audit_entry)

            if blocking_matches:
                logger.warning(
                    f"Guardian blocked Lawyer iteration {i + 1} for case {case_id}: "
                    f"{[m.rule_name for m in blocking_matches]}"
                )
                guardian_blocked = True
                break

            # Convergence: require both success outcome AND confidence above floor
            execution_confidence = (
                result.get("cognitive_state", {}).get("estimated_load", 5.0) if result.get("cognitive_state") else 5.0
            )
            # Normalize: lower cognitive load = higher confidence (load 0-10 → confidence 1.0-0.0)
            iteration_confidence = max(0.0, 1.0 - (execution_confidence / 10.0))

            if result.get("outcome") == "success" and iteration_confidence >= self.LAWYER_CONFIDENCE_FLOOR:
                logger.info(f"Lawyer converged at iteration {i + 1} (confidence={iteration_confidence:.2f})")
                break
            elif result.get("outcome") == "success":
                logger.info(
                    f"Lawyer iteration {i + 1} succeeded but confidence {iteration_confidence:.2f} "
                    f"below floor {self.LAWYER_CONFIDENCE_FLOOR}, continuing"
                )

        # --- Synthesize final result with real Guardian data ---
        total_guardian_matches = sum(a["guardian_matches"] for a in iteration_audits)
        total_warnings = sum(a["guardian_warnings"] for a in iteration_audits)
        safety_passed = not guardian_blocked

        final_outcome = "blocked" if guardian_blocked else results[-1].get("outcome", "unknown")

        summary_report: dict[str, Any] = {
            "case_id": case_id,
            "iterations": len(results),
            "final_outcome": final_outcome,
            "summary": "Consolidated lawyer report after iterative analysis.",
            "audit_trail": iteration_audits,
            "guardian_summary": {
                "safety_passed": safety_passed,
                "total_matches": total_guardian_matches,
                "total_warnings": total_warnings,
                "blocked_at_iteration": next((a["iteration"] for a in iteration_audits if a["guardian_blocked"]), None),
            },
        }

        # Synthesize XAI explanation with real Guardian evaluation data
        xai_trace: dict[str, Any] = explainer.synthesize_explanation(
            decision_id=f"DEC-{case_id}-MAIN",
            context={
                "safety_check": "PASSED" if safety_passed else "BLOCKED",
                "guardian_matches": total_guardian_matches,
                "guardian_warnings": total_warnings,
                "iterations_completed": len(results),
                "evidence": cast("list[Any]", iteration_audits)[:2],
            },
            rationale=(
                f"Lawyer completed {len(results)} iteration(s). "
                f"Guardian evaluated each output: {total_guardian_matches} rule match(es), "
                f"{total_warnings} warning(s). "
                f"Final safety status: {'PASSED' if safety_passed else 'BLOCKED'}."
            ),
        )

        # Generate final memo with XAI
        memo_path = self.memo_generator.generate_memo(
            case_id=case_id,
            lawyer_report=summary_report,
            decisions=[{"feature": "monitoring", "value": safety_passed, "protocol": "GRID-ENFORCE"}],
            xai_explanations=[xai_trace],
        )
        self.memo_generator.create_markdown_memo(memo_path)

        return {"summary_report": summary_report, "memo_path": memo_path, "status": "completed"}

    def get_cognitive_state(self, case_id: str) -> dict[str, Any] | None:
        """Get the cognitive state for a specific case.

        Args:
            case_id: Case identifier

        Returns:
            Cognitive context dictionary or None
        """
        return self._cognitive_context.get(case_id)

    async def get_user_cognitive_state(self, user_id: str) -> dict[str, Any] | None:
        """Get the current cognitive state for a user.

        Args:
            user_id: User identifier

        Returns:
            Cognitive state dictionary or None
        """
        if self.cognitive_engine:
            state = await self.cognitive_engine.get_cognitive_state(user_id)
            result: dict[str, Any] = state.model_dump(mode="json")
            return result
        return None

    def clear_cognitive_context(self, case_id: str | None = None) -> None:
        """Clear cached cognitive context.

        Args:
            case_id: Optional case ID to clear specific case's context.
                     If None, clears all cached contexts.
        """
        if case_id is None:
            self._cognitive_context.clear()
        elif case_id in self._cognitive_context:
            del self._cognitive_context[case_id]
