"""Event handlers for case lifecycle events."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseEventHandler:
    """Base class for event handlers."""

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle an event.

        Args:
            event: Event dictionary
        """
        raise NotImplementedError


class CaseCreatedHandler(BaseEventHandler):
    """Handler for case.created events."""

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cases
        """
        self.repository = repository

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle case.created event.

        Args:
            event: Event dictionary
        """
        case_id = event.get("case_id")
        logger.info(f"Handling case.created event for {case_id}")

        if self.repository:
            try:
                await self.repository.create_case(
                    case_id=case_id,
                    raw_input=event.get("raw_input", ""),
                    user_id=event.get("user_id"),
                    status="created",
                )
                logger.debug(f"Case {case_id} stored in repository")
            except Exception as e:
                logger.error(f"Error storing case {case_id}: {e}")


class CaseCategorizedHandler(BaseEventHandler):
    """Handler for case.categorized events."""

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cases
        """
        self.repository = repository

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle case.categorized event.

        Args:
            event: Event dictionary
        """
        case_id = event.get("case_id")
        logger.info(f"Handling case.categorized event for {case_id}")

        if self.repository:
            try:
                await self.repository.update_case_status(
                    case_id=case_id,
                    status="categorized",
                    category=event.get("category"),
                    priority=event.get("priority"),
                    confidence=event.get("confidence"),
                    structured_data=event.get("structured_data", {}),
                )
                logger.debug(f"Case {case_id} status updated to categorized")
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {e}")


class CaseReferenceGeneratedHandler(BaseEventHandler):
    """Handler for case.reference_generated events."""

    def __init__(self, repository: Any | None = None, agent_system: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cases
            agent_system: Optional agent system to notify
        """
        self.repository = repository
        self.agent_system = agent_system

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle case.reference_generated event.

        Args:
            event: Event dictionary
        """
        case_id = event.get("case_id")
        logger.info(f"Handling case.reference_generated event for {case_id}")

        if self.repository:
            try:
                await self.repository.update_case_status(
                    case_id=case_id,
                    status="reference_generated",
                    reference_file_path=event.get("reference_file_path"),
                )
                logger.debug(f"Case {case_id} reference file stored")
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {e}")

        # Notify agent system that case is ready
        if self.agent_system:
            try:
                logger.debug(f"Notifying agent system about case {case_id}")
                # Agent system can check for ready cases periodically
            except Exception as e:
                logger.error(f"Error notifying agent system: {e}")


class CaseExecutedHandler(BaseEventHandler):
    """Handler for case.executed events."""

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cases
        """
        self.repository = repository

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle case.executed event.

        Args:
            event: Event dictionary
        """
        case_id = event.get("case_id")
        logger.info(f"Handling case.executed event for {case_id}")

        if self.repository:
            try:
                await self.repository.update_case_status(
                    case_id=case_id,
                    status="executed",
                    agent_role=event.get("agent_role"),
                    task=event.get("task"),
                )
                logger.debug(f"Case {case_id} execution started")
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {e}")


class CaseCompletedHandler(BaseEventHandler):
    """Handler for case.completed events."""

    def __init__(
        self,
        repository: Any | None = None,
        learning_system: Any | None = None,
    ):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cases
            learning_system: Optional continuous learning system
        """
        self.repository = repository
        self.learning_system = learning_system

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle case.completed event.

        Args:
            event: Event dictionary
        """
        case_id = event.get("case_id")
        logger.info(f"Handling case.completed event for {case_id}")

        if self.repository:
            try:
                await self.repository.update_case_status(
                    case_id=case_id,
                    status="completed",
                    outcome=event.get("outcome"),
                    solution=event.get("solution", ""),
                    agent_experience=event.get("agent_experience", {}),
                )
                logger.debug(f"Case {case_id} marked as completed")
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {e}")

        # Update learning system
        if self.learning_system:
            try:
                # Get case data from repository
                case = await self.repository.get_case(case_id)
                if case:
                    await self.learning_system.record_case_completion(
                        case_id=case_id,
                        structure=case.get("structured_data", {}),
                        solution=event.get("solution", ""),
                        outcome=event.get("outcome", ""),
                        agent_experience=event.get("agent_experience", {}),
                    )
                    logger.debug(f"Case {case_id} recorded in learning system")
            except Exception as e:
                logger.error(f"Error updating learning system: {e}")


class EventHandlerRegistry:
    """Registry for event handlers."""

    def __init__(self):
        """Initialize registry."""
        self.handlers: dict[str, list[BaseEventHandler]] = {}

    def register(self, event_type: str, handler: BaseEventHandler) -> None:
        """Register a handler for an event type.

        Args:
            event_type: Event type (e.g., "case.created")
            handler: Handler instance
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    async def handle_event(self, event: dict[str, Any]) -> None:
        """Handle an event by calling registered handlers.

        Args:
            event: Event dictionary
        """
        event_type = event.get("event_type", "unknown")
        handlers = self.handlers.get(event_type, [])

        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}")


# ========== Cognitive Event Handlers ==========


class CognitiveLoadExceededHandler(BaseEventHandler):
    """Handler for cognitive.load.exceeded events.

    Triggered when cognitive load exceeds threshold, indicating the user
    needs additional support or simplification.
    """

    def __init__(self, load_threshold: float = 7.0, repository: Any | None = None):
        """Initialize handler.

        Args:
            load_threshold: Cognitive load threshold (default 7.0)
            repository: Optional repository for storing cognitive events
        """
        self.load_threshold = load_threshold
        self.repository = repository

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle cognitive.load.exceeded event.

        Args:
            event: Event dictionary with cognitive context
        """
        user_id = event.get("user_id", "unknown")
        case_id = event.get("case_id")
        cognitive_context = event.get("cognitive_context", {})
        load = cognitive_context.get("load", 0.0)

        logger.info(f"Cognitive load exceeded for {user_id}: {load:.2f} (threshold: {self.load_threshold})")

        # Store cognitive event if repository available
        if self.repository:
            try:
                await self.repository.record_cognitive_event(
                    event_type="load_exceeded",
                    user_id=user_id,
                    case_id=case_id,
                    load=load,
                    timestamp=event.get("timestamp"),
                )
            except Exception as e:
                logger.error(f"Error recording cognitive event: {e}")


class ProcessingModeSwitchHandler(BaseEventHandler):
    """Handler for cognitive.mode.switch events.

    Triggered when user switches between System 1 (fast) and
    System 2 (slow) processing modes.
    """

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cognitive events
        """
        self.repository = repository
        self._user_modes: dict[str, str] = {}

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle cognitive.mode.switch event.

        Args:
            event: Event dictionary with cognitive context
        """
        user_id = event.get("user_id", "unknown")
        case_id = event.get("case_id")
        cognitive_context = event.get("cognitive_context", {})
        new_mode = cognitive_context.get("mode", "unknown")

        # Get previous mode
        previous_mode = self._user_modes.get(user_id)

        if previous_mode != new_mode:
            logger.info(f"Processing mode switch for {user_id}: {previous_mode} -> {new_mode}")
            self._user_modes[user_id] = new_mode

            # Record mode switch if repository available
            if self.repository:
                try:
                    await self.repository.record_cognitive_event(
                        event_type="mode_switch",
                        user_id=user_id,
                        case_id=case_id,
                        previous_mode=previous_mode,
                        new_mode=new_mode,
                        timestamp=event.get("timestamp"),
                    )
                except Exception as e:
                    logger.error(f"Error recording mode switch: {e}")


class MentalModelMismatchHandler(BaseEventHandler):
    """Handler for cognitive.mental_model.mismatch events.

    Triggered when user expectations diverge from system behavior,
    indicating potential confusion or need for clarification.
    """

    def __init__(self, alignment_threshold: float = 0.5, repository: Any | None = None):
        """Initialize handler.

        Args:
            alignment_threshold: Mental model alignment threshold (default 0.5)
            repository: Optional repository for storing cognitive events
        """
        self.alignment_threshold = alignment_threshold
        self.repository = repository
        self._mismatch_counts: dict[str, int] = {}

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle cognitive.mental_model.mismatch event.

        Args:
            event: Event dictionary with cognitive context
        """
        user_id = event.get("user_id", "unknown")
        case_id = event.get("case_id")
        cognitive_context = event.get("cognitive_context", {})
        alignment = cognitive_context.get("alignment", 1.0)
        mismatches = cognitive_context.get("mismatches", [])

        if alignment < self.alignment_threshold:
            self._mismatch_counts[user_id] = self._mismatch_counts.get(user_id, 0) + 1

            logger.warning(
                f"Mental model mismatch for {user_id}: alignment={alignment:.2f}, "
                f"mismatches={mismatches} (count: {self._mismatch_counts[user_id]})"
            )

            # Record mismatch if repository available
            if self.repository:
                try:
                    await self.repository.record_cognitive_event(
                        event_type="mental_model_mismatch",
                        user_id=user_id,
                        case_id=case_id,
                        alignment=alignment,
                        mismatches=mismatches,
                        mismatch_count=self._mismatch_counts[user_id],
                        timestamp=event.get("timestamp"),
                    )
                except Exception as e:
                    logger.error(f"Error recording mental model mismatch: {e}")

            # Suggest improvements for user if frequent mismatches
            if self._mismatch_counts[user_id] >= 3:
                logger.info(f"Suggesting UX improvements for {user_id} due to frequent mental model mismatches")


class FlowStateDetectedHandler(BaseEventHandler):
    """Handler for cognitive.flow.detected events.

    Triggered when user enters a flow state - optimal experience
    with balanced cognitive load and high engagement.
    """

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cognitive events
        """
        self.repository = repository
        self._flow_start_times: dict[str, float] = {}

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle cognitive.flow.detected event.

        Args:
            event: Event dictionary with flow context
        """
        user_id = event.get("user_id", "unknown")
        case_id = event.get("case_id")
        flow_context = event.get("flow_context", {})
        flow_confidence = flow_context.get("confidence", 0.0)

        if flow_confidence > 0.7:  # High confidence flow detection
            logger.info(f"Flow state detected for {user_id}: confidence={flow_confidence:.2f}")

            # Track flow duration
            import time

            current_time = time.time()
            if user_id not in self._flow_start_times:
                self._flow_start_times[user_id] = current_time
            else:
                flow_duration = current_time - self._flow_start_times[user_id]
                logger.debug(f"Flow duration for {user_id}: {flow_duration:.1f}s")

            # Record flow event if repository available
            if self.repository:
                try:
                    await self.repository.record_cognitive_event(
                        event_type="flow_detected",
                        user_id=user_id,
                        case_id=case_id,
                        confidence=flow_confidence,
                        timestamp=event.get("timestamp"),
                    )
                except Exception as e:
                    logger.error(f"Error recording flow event: {e}")
        else:
            # Flow ended
            if user_id in self._flow_start_times:
                import time

                flow_duration = time.time() - self._flow_start_times[user_id]
                logger.info(f"Flow state ended for {user_id}: duration={flow_duration:.1f}s")
                del self._flow_start_times[user_id]


class PatternDetectedHandler(BaseEventHandler):
    """Handler for cognitive.pattern.detected events.

    Triggered when one of the 9 cognition patterns is detected.
    """

    def __init__(self, repository: Any | None = None):
        """Initialize handler.

        Args:
            repository: Optional repository for storing cognitive events
        """
        self.repository = repository
        self._pattern_counts: dict[str, dict[str, int]] = {}

    async def handle(self, event: dict[str, Any]) -> None:
        """Handle cognitive.pattern.detected event.

        Args:
            event: Event dictionary with pattern information
        """
        user_id = event.get("user_id", "unknown")
        case_id = event.get("case_id")
        pattern_data = event.get("pattern_data", {})
        pattern_name = pattern_data.get("pattern_name", "unknown")
        detected = pattern_data.get("detected", False)
        confidence = pattern_data.get("confidence", 0.0)

        if detected and confidence > 0.5:
            # Update pattern counts
            if user_id not in self._pattern_counts:
                self._pattern_counts[user_id] = {}
            self._pattern_counts[user_id][pattern_name] = self._pattern_counts[user_id].get(pattern_name, 0) + 1

            logger.info(
                f"Pattern detected for {user_id}: {pattern_name} "
                f"(confidence={confidence:.2f}, count={self._pattern_counts[user_id][pattern_name]})"
            )

            # Record pattern event if repository available
            if self.repository:
                try:
                    await self.repository.record_cognitive_event(
                        event_type="pattern_detected",
                        user_id=user_id,
                        case_id=case_id,
                        pattern_name=pattern_name,
                        confidence=confidence,
                        pattern_count=self._pattern_counts[user_id][pattern_name],
                        timestamp=event.get("timestamp"),
                    )
                except Exception as e:
                    logger.error(f"Error recording pattern event: {e}")
