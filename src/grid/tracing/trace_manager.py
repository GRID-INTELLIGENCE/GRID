"""Trace manager for coordinating action tracing across the system."""

import inspect
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional

from .action_trace import ActionTrace, TraceContext, TraceOrigin
from .trace_store import TraceStore

logger = logging.getLogger(__name__)


class TraceManager:
    """Manages action traces throughout the system."""

    def __init__(self, store: Optional["TraceStore"] = None):
        """Initialize trace manager.

        Args:
            store: Optional trace store for persistence
        """
        self.store = store
        self._active_traces: dict[str, ActionTrace] = {}
        self._context_stack: list[TraceContext] = []

    def create_trace(
        self,
        action_type: str,
        action_name: str,
        origin: TraceOrigin = TraceOrigin.INTERNAL_PIPELINE,
        user_id: str | None = None,
        org_id: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        operation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: set[str] | None = None,
        skip_frames: int = 0,
    ) -> ActionTrace:
        """Create a new action trace.

        Args:
            action_type: Type of action
            action_name: Human-readable action name
            origin: Origin type
            user_id: User identifier
            org_id: Organization identifier
            session_id: Session identifier
            request_id: Request identifier
            operation_id: Operation identifier
            metadata: Additional metadata
            tags: Tags for categorization
            skip_frames: Number of stack frames to skip (for internal calls)

        Returns:
            Created action trace
        """
        # Get source location
        frame = inspect.currentframe()
        for _ in range(skip_frames + 1):
            if frame:
                frame = frame.f_back

        source_module = "unknown"
        source_function = "unknown"
        source_file = None
        source_line = None

        if frame:
            source_module = frame.f_globals.get("__name__", "unknown")
            source_function = frame.f_code.co_name
            source_file = frame.f_code.co_filename
            source_line = frame.f_lineno

        # Get parent context
        parent_context = self._context_stack[-1] if self._context_stack else None
        root_trace_id = parent_context.root_trace_id if parent_context else None

        # Create context
        context = TraceContext(
            origin=origin,
            source_module=source_module,
            source_function=source_function,
            source_file=source_file,
            source_line=source_line,
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            request_id=request_id,
            operation_id=operation_id,
            parent_trace_id=parent_context.trace_id if parent_context else None,
            root_trace_id=root_trace_id or None,
            metadata=metadata or {},
            tags=tags or set(),
        )

        # Create trace
        trace = ActionTrace(
            trace_id=context.trace_id,
            action_type=action_type,
            action_name=action_name,
            context=context,
            parent_traces=[parent_context.trace_id] if parent_context else [],
        )

        # Store active trace
        self._active_traces[trace.trace_id] = trace
        self._context_stack.append(context)

        return trace

    @contextmanager
    def trace_action(
        self,
        action_type: str,
        action_name: str,
        origin: TraceOrigin = TraceOrigin.INTERNAL_PIPELINE,
        user_id: str | None = None,
        org_id: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        operation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: set[str] | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> Iterator[ActionTrace]:
        """
        Context manager for tracing an action.

        FIXED: Only pushes to context stack after successful trace creation,
        preventing stack corruption if create_trace raises an exception.
        """
        # Create trace first - may raise exception
        try:
            trace = self.create_trace(
                action_type=action_type,
                action_name=action_name,
                origin=origin,
                user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                request_id=request_id,
                operation_id=operation_id,
                metadata=metadata,
                tags=tags,
                skip_frames=1,
            )
        except Exception:
            # Don't modify stack if creation failed
            raise

        # Only set input data and push to stack after successful creation
        if input_data:
            trace.input_data = input_data

        # FIXED: Push to stack only after successful creation
        self._context_stack.append(trace.context)

        try:
            yield trace
            trace.complete(success=True)
        except Exception as e:
            import traceback

            trace.complete(success=False, error=f"{str(e)}\n{traceback.format_exc()}")
            raise
        finally:
            # FIXED: Pop only the exact context we pushed (verified by trace_id)
            if self._context_stack and self._context_stack[-1].trace_id == trace.trace_id:
                self._context_stack.pop()
            elif trace.trace_id in self._context_stack:
                # Context is in stack but not at top - log error but still remove
                idx = next((i for i, ctx in enumerate(self._context_stack) if ctx.trace_id == trace.trace_id), None)
                if idx is not None:
                    self._context_stack.pop(idx)
                    logger.error(f"Trace stack out of order: removed {trace.trace_id} from middle of stack")
            else:
                logger.error(f"Trace {trace.trace_id} not found in context stack during cleanup")

            # Remove from active traces
            if trace.trace_id in self._active_traces:
                del self._active_traces[trace.trace_id]

            # Store trace
            if self.store:
                self.store.save_trace(trace)

    def get_active_trace(self, trace_id: str | None = None) -> ActionTrace | None:
        """Get active trace by ID or current trace.

        Args:
            trace_id: Optional trace ID, defaults to current trace

        Returns:
            Action trace or None
        """
        if trace_id:
            return self._active_traces.get(trace_id)

        if self._context_stack:
            current_context = self._context_stack[-1]
            return self._active_traces.get(current_context.trace_id)

        return None

    def get_trace_chain(self, trace_id: str) -> list[ActionTrace]:
        """Get full trace chain from root to leaf.

        Args:
            trace_id: Trace ID to start from

        Returns:
            List of traces from root to leaf
        """
        chain = []
        current_id = trace_id

        while current_id:
            trace = self.store.get_trace(current_id) if self.store else self._active_traces.get(current_id)
            if not trace:
                break

            chain.insert(0, trace)
            if trace.context.parent_trace_id:
                current_id = trace.context.parent_trace_id
            else:
                break

        return chain


# Global trace manager instance
_global_trace_manager: TraceManager | None = None


def get_trace_manager() -> TraceManager:
    """Get global trace manager instance."""
    global _global_trace_manager
    if _global_trace_manager is None:
        _global_trace_manager = TraceManager()
    return _global_trace_manager


def set_trace_manager(manager: TraceManager) -> None:
    """Set global trace manager instance."""
    global _global_trace_manager
    _global_trace_manager = manager
