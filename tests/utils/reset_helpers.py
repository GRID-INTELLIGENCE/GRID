"""
tests/utils/reset_helpers.py
────────────────────────────
Centralised reset helpers for global singletons.

These helpers ensure test isolation by resetting module-level singletons
that can leak state across tests. Use them in fixtures that touch
resilience, middleware, metrics, or accountability components.

Usage in conftest.py or per-test fixtures:

    from tests.utils.reset_helpers import reset_all_singletons

    @pytest.fixture(autouse=True)
    def isolation():
        reset_all_singletons()
        yield
        reset_all_singletons()

Individual helpers can also be called directly when only specific
singletons need to be reset:

    from tests.utils.reset_helpers import reset_circuit_manager

    @pytest.fixture
    def clean_circuit():
        reset_circuit_manager()
        yield
"""

from __future__ import annotations


def reset_circuit_manager() -> None:
    """Clear the global CircuitBreakerManager singleton.

    This resets the circuit breaker state between tests that exercise
    resilience patterns or the mothership middleware stack.
    """
    try:
        import importlib

        _module = importlib.import_module("application.mothership.resilience.circuit_breaker")
        _do_reset = getattr(_module, "_reset_circuit_manager", None)
        if callable(_do_reset):
            _do_reset()
    except ImportError:
        # Module not available — nothing to do
        pass


def reset_metrics_collector() -> None:
    """Clear the global MetricsCollector singleton.

    This ensures metrics accumulated in one test don't affect another.
    """
    try:
        import importlib

        _module = importlib.import_module("application.mothership.metrics.collector")
        if hasattr(_module, "_global_collector"):
            _module._global_collector = None  # type: ignore[attr-defined]
    except ImportError:
        pass


def reset_accountability_calculator() -> None:
    """Clear the global AccountabilityCalculator singleton.

    This ensures accountability scores and state don't leak between tests.
    """
    try:
        import importlib

        _module = importlib.import_module("application.mothership.accountability.calculator")
        if hasattr(_module, "_global_calculator"):
            _module._global_calculator = None  # type: ignore[attr-defined]
    except ImportError:
        pass


def reset_rate_limiter_state() -> None:
    """Clear the global rate limiter state if present.

    Some rate limiter implementations hold in-memory state that should
    be cleared between tests to avoid false positives.
    """
    try:
        import importlib

        _module = importlib.import_module("application.mothership.middleware.rate_limiter")
        if hasattr(_module, "_global_rate_limiter"):
            _module._global_rate_limiter = None  # type: ignore[attr-defined]
    except ImportError:
        pass


def reset_mastermind_session() -> None:
    """Reset the global MastermindSession singleton to defaults.

    The module-level ``session`` in ``grid.mcp.mastermind_server`` carries
    mutable state (project_root, indexed_files, query_count, last_analysis)
    that can leak across tests.
    """
    try:
        import importlib

        _module = importlib.import_module("grid.mcp.mastermind_server")
        _session = getattr(_module, "session", None)
        if _session is not None:
            _session.last_analysis = None
            _session.indexed_files = []
            _session.query_count = 0
            # project_root is reset to module default (grid_root) on next reload;
            # clearing the mutable fields is sufficient for isolation.
    except ImportError:
        pass


def reset_parasite_profiler() -> None:
    """Reset the lazy-initialised ParasiteProfiler singleton.

    ``grid.security.parasite_guard._profiler`` is created on first call to
    ``get_profiler()`` and never cleared, causing stale state to leak
    between tests that exercise the pruner metrics path.
    """
    try:
        import importlib

        _module = importlib.import_module("grid.security.parasite_guard")
        if hasattr(_module, "_profiler"):
            _module._profiler = None  # type: ignore[attr-defined]
    except ImportError:
        pass


def reset_all_singletons() -> None:
    """Reset all known global singletons.

    Call this before/after tests that touch resilience, middleware,
    metrics, or accountability components to ensure clean isolation.

    This is a convenience wrapper that calls all individual reset helpers.
    """
    reset_circuit_manager()
    reset_metrics_collector()
    reset_accountability_calculator()
    reset_rate_limiter_state()
    reset_mastermind_session()
    reset_parasite_profiler()


__all__ = [
    "reset_circuit_manager",
    "reset_metrics_collector",
    "reset_accountability_calculator",
    "reset_rate_limiter_state",
    "reset_mastermind_session",
    "reset_parasite_profiler",
    "reset_all_singletons",
]
