"""Tests for agent executor."""


from coinbase.agent_executor import AgentExecutor


def test_execute_task_success():
    """Test successful task execution."""
    import time

    executor = AgentExecutor()

    def mock_handler(case_id, reference, agent_role):
        time.sleep(0.001)  # Small delay to ensure duration > 0
        return {"result": "success"}

    executor.register_handler("test_task", mock_handler)

    result = executor.execute_task(case_id="test-123", task="test_task", agent_role="Executor")

    assert result.success is True
    assert result.result == {"result": "success"}
    assert result.duration_ms >= 0


def test_execute_task_failure():
    """Test task execution with handler error."""
    executor = AgentExecutor()

    def mock_handler(case_id, reference, agent_role):
        raise ValueError("Handler error")

    executor.register_handler("test_task", mock_handler)

    result = executor.execute_task(case_id="test-456", task="test_task", agent_role="Executor")

    assert result.success is False
    assert result.error is not None
    assert "Handler error" in result.error


def test_execute_task_no_handler():
    """Test task execution with no registered handler."""
    executor = AgentExecutor()

    result = executor.execute_task(
        case_id="test-789", task="nonexistent_task", agent_role="Executor"
    )

    assert result.success is False
    assert "No handler registered" in result.error


def test_execute_task_with_recovery():
    """Test task execution with automatic retry."""
    executor = AgentExecutor()
    attempt_count = 0

    def mock_handler(case_id, reference, agent_role):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise TimeoutError("Timed out")
        return {"result": "success after retry"}

    executor.register_handler("test_task", mock_handler)

    result = executor.execute_task(case_id="test-retry", task="test_task", agent_role="Executor")

    assert result.success is True
    assert result.result == {"result": "success after retry"}
    assert attempt_count == 2


def test_learning_coordinator_updated():
    """Test that learning coordinator is updated on execution."""
    executor = AgentExecutor()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    executor.register_handler("test_task", mock_handler)

    executor.execute_task(case_id="test-learning", task="test_task", agent_role="Executor")

    stats = executor.learning_coordinator.get_skill_stats("test-learning")

    assert stats is not None
    assert stats.usage_count == 1
    assert stats.success_count == 1


def test_tracer_updated():
    """Test that tracer is updated on execution."""
    executor = AgentExecutor()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    executor.register_handler("test_task", mock_handler)

    executor.execute_task(case_id="test-tracer", task="test_task", agent_role="Executor")

    stats = executor.tracer.get_performance_stats()

    assert stats["total_executions"] == 1
    assert stats["success_rate"] == 1.0
