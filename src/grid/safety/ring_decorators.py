"""
Ring Decorators - OS-Inspired Privilege Ring System.

This module implements privilege ring decorators inspired by OS kernel
protection rings. The decorators enforce access control and validation
at different privilege levels.

Ring Hierarchy:
    Ring 3: User Input (CLI, API) - Least privileged
    Ring 2: Validation (type checks, bounds)
    Ring 1: Engine Core (state mutation)
    Ring 0: Persistence & Guardians (Aegis) - Most privileged
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from enum import IntEnum
from typing import Any, TypeVar, cast

from grid.tracing.action_trace import TraceOrigin
from grid.tracing.trace_manager import get_trace_manager

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class PrivilegeRing(IntEnum):
    """
    Privilege rings from most to least privileged.

    Lower numbers = higher privilege (OS convention).
    """

    RING_0 = 0  # Guardians, persistence
    RING_1 = 1  # Engine core, state mutation
    RING_2 = 2  # Validation
    RING_3 = 3  # User input


# Track current execution ring (thread-local would be better for production)
_current_ring: PrivilegeRing = PrivilegeRing.RING_3


def get_current_ring() -> PrivilegeRing:
    """Get the current execution privilege ring."""
    return _current_ring


def _set_ring(ring: PrivilegeRing) -> None:
    """Set the current execution privilege ring."""
    global _current_ring
    _current_ring = ring


def ring0_protect[F: Callable[..., Any]](func: F) -> F:
    """
    Ring 0: Guardian and Persistence operations.

    Most privileged level. Used for:
    - Aegis guardian operations
    - Persistence layer access
    - Kill switch execution
    - Emergency operations

    Example:
        @ring0_protect
        def execute_kill_switch(switch_type: KillSwitchType) -> None:
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        previous_ring = get_current_ring()
        _set_ring(PrivilegeRing.RING_0)
        try:
            manager = get_trace_manager()
            with manager.trace_action(
                action_type="ring0_operation",
                action_name=f"[RING-0] {func.__name__}",
                origin=TraceOrigin.SYSTEM_INIT,
            ) as trace:
                trace.safety_score = 1.0  # Guardian operations are trusted
                result = func(*args, **kwargs)
                return result
        finally:
            _set_ring(previous_ring)

    return cast(F, wrapper)


def ring1_mutate(
    requires_ring0: bool = False,
    safety_critical: bool = True,
) -> Callable[[F], F]:
    """
    Ring 1: Engine Core state mutation operations.

    Used for:
    - Game state mutations
    - Entity modifications
    - Resource allocation

    Args:
        requires_ring0: If True, can only be called from Ring 0.
        safety_critical: If True, extra validation is applied.

    Example:
        @ring1_mutate(safety_critical=True)
        def update_entity_position(entity_id: str, position: Vector3) -> None:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current = get_current_ring()

            if requires_ring0 and current > PrivilegeRing.RING_0:
                raise PermissionError(
                    f"Function {func.__name__} requires Ring 0 privilege, " f"but current ring is {current.name}"
                )

            previous_ring = current
            _set_ring(PrivilegeRing.RING_1)
            try:
                manager = get_trace_manager()
                with manager.trace_action(
                    action_type="ring1_mutation",
                    action_name=f"[RING-1] {func.__name__}",
                    origin=TraceOrigin.COGNITIVE_DECISION,
                ) as trace:
                    if safety_critical:
                        trace.safety_score = 0.8  # Mutations need monitoring
                    result = func(*args, **kwargs)
                    return result
            finally:
                _set_ring(previous_ring)

        return cast(F, wrapper)

    return decorator


def ring2_validate(
    min_privilege: PrivilegeRing = PrivilegeRing.RING_3,
) -> Callable[[F], F]:
    """
    Ring 2: Validation operations.

    Used for:
    - Type checking
    - Bounds validation
    - Input sanitization
    - Schema validation

    Args:
        min_privilege: Minimum ring required to call this function.

    Example:
        @ring2_validate()
        def validate_command(command: str) -> bool:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current = get_current_ring()

            if current > min_privilege:
                logger.warning(
                    f"Function {func.__name__} called from Ring {current.value}, "
                    f"expected Ring {min_privilege.value} or lower"
                )

            previous_ring = current
            _set_ring(PrivilegeRing.RING_2)
            try:
                manager = get_trace_manager()
                with manager.trace_action(
                    action_type="ring2_validation",
                    action_name=f"[RING-2] {func.__name__}",
                    origin=TraceOrigin.SAFETY_ANALYSIS,
                ) as trace:
                    trace.safety_score = 0.9  # Validation is trusted
                    result = func(*args, **kwargs)
                    return result
            finally:
                _set_ring(previous_ring)

        return cast(F, wrapper)

    return decorator


def ring3_input(
    trace_origin: TraceOrigin = TraceOrigin.USER_INPUT,
) -> Callable[[F], F]:
    """
    Ring 3: User Input operations.

    Least privileged level. Used for:
    - CLI input handlers
    - API endpoint handlers
    - External webhook receivers

    Args:
        trace_origin: The origin type for tracing.

    Example:
        @ring3_input(trace_origin=TraceOrigin.API_REQUEST)
        def handle_api_request(request: Request) -> Response:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            previous_ring = get_current_ring()
            _set_ring(PrivilegeRing.RING_3)
            try:
                manager = get_trace_manager()
                with manager.trace_action(
                    action_type="ring3_input",
                    action_name=f"[RING-3] {func.__name__}",
                    origin=trace_origin,
                ) as trace:
                    trace.safety_score = 0.5  # Input needs verification
                    result = func(*args, **kwargs)
                    return result
            finally:
                _set_ring(previous_ring)

        return cast(F, wrapper)

    return decorator


def require_ring(min_ring: PrivilegeRing) -> Callable[[F], F]:
    """
    Generic decorator to require a minimum privilege ring.

    Args:
        min_ring: The minimum ring required to execute the function.

    Example:
        @require_ring(PrivilegeRing.RING_1)
        def protected_operation() -> None:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current = get_current_ring()
            if current > min_ring:
                raise PermissionError(
                    f"Function {func.__name__} requires Ring {min_ring.value} or lower, "
                    f"but current ring is {current.name} (Ring {current.value})"
                )
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
