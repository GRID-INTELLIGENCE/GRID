"""Tests for runtime behavior tracer."""


from coinbase.tracer import (
    DecisionType,
    ExecutionOutcome,
    RuntimeBehaviorTracer,
)


def test_start_trace():
    """Test starting a new execution trace."""
    tracer = RuntimeBehaviorTracer()
    trace = tracer.start_trace(case_id="test-123", agent_role="Executor", task_type="test_task")

    assert trace.case_id == "test-123"
    assert trace.agent_role == "Executor"
    assert trace.task_type == "test_task"
    assert trace.start_time is not None
    assert trace.end_time is None
    assert trace.outcome is None


def test_end_trace():
    """Test ending a trace with outcome."""
    import asyncio

    tracer = RuntimeBehaviorTracer()
    trace = tracer.start_trace(case_id="test-456")

    # Add small delay to ensure duration > 0
    asyncio.run(asyncio.sleep(0.001))

    ended = tracer.end_trace(trace.trace_id, ExecutionOutcome.SUCCESS)

    assert ended is not None
    assert ended.outcome == ExecutionOutcome.SUCCESS
    assert ended.end_time is not None
    assert ended.duration_ms > 0


def test_add_decision():
    """Test adding decision points to trace."""
    tracer = RuntimeBehaviorTracer()
    trace = tracer.start_trace(case_id="test-789")

    trace.add_decision(
        decision_type=DecisionType.ROUTE,
        rationale="Routing to handler",
        confidence=0.9,
        alternatives=["handler_a", "handler_b"],
    )

    assert len(trace.decisions) == 1
    assert trace.decisions[0].decision_type == DecisionType.ROUTE
    assert trace.decisions[0].rationale == "Routing to handler"
    assert trace.decisions[0].confidence == 0.9
    assert "handler_a" in trace.decisions[0].alternatives


def test_performance_stats():
    """Test performance statistics calculation."""
    import asyncio

    tracer = RuntimeBehaviorTracer()

    # Create some traces with delays
    for i in range(5):
        trace = tracer.start_trace(case_id=f"test-{i}")
        asyncio.run(asyncio.sleep(0.001))  # Small delay
        tracer.end_trace(
            trace.trace_id, ExecutionOutcome.SUCCESS if i < 4 else ExecutionOutcome.FAILURE
        )

    stats = tracer.get_performance_stats()

    assert stats["total_executions"] == 5
    assert stats["success_rate"] == 0.8
    assert stats["p50_latency_ms"] >= 0
    assert stats["p95_latency_ms"] >= 0


def test_get_trace():
    """Test retrieving a trace by ID."""
    tracer = RuntimeBehaviorTracer()
    trace = tracer.start_trace(case_id="test-retrieve")

    retrieved = tracer.get_trace(trace.trace_id)

    assert retrieved is not None
    assert retrieved.case_id == "test-retrieve"


def test_history_limit():
    """Test that history is limited to max_history."""
    tracer = RuntimeBehaviorTracer(max_history=3)

    # Create more traces than limit
    for i in range(5):
        trace = tracer.start_trace(case_id=f"test-{i}")
        tracer.end_trace(trace.trace_id, ExecutionOutcome.SUCCESS)

    # Should only keep last 3
    assert len(tracer.history) == 3
