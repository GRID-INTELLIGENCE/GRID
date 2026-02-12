"""Tests for agentic system."""


from coinbase.agentic_system import AgenticSystem


def test_execute_case_success():
    """Test successful case execution."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    result = system.execute_case(case_id="test-123", task="test_task", agent_role="Executor")

    assert result["success"] is True
    assert result["result"] == {"result": "success"}
    assert result["case_id"] == "test-123"
    assert result["execution_time_seconds"] > 0


def test_execute_case_failure():
    """Test case execution with handler error."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        raise ValueError("Handler error")

    system.register_handler("test_task", mock_handler)

    result = system.execute_case(case_id="test-456", task="test_task", agent_role="Executor")

    assert result["success"] is False
    assert result["error"] is not None
    assert "Handler error" in result["error"]


def test_event_publishing():
    """Test that events are published on execution."""
    system = AgenticSystem()
    events_received = []

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    # Subscribe to events
    system.event_bus.subscribe("case_executed", lambda e: events_received.append(("executed", e)))
    system.event_bus.subscribe("case_completed", lambda e: events_received.append(("completed", e)))

    system.execute_case(case_id="test-events", task="test_task", agent_role="Executor")

    assert len(events_received) == 2
    assert events_received[0][0] == "executed"
    assert events_received[1][0] == "completed"


def test_skill_generation():
    """Test that skills are generated for successful cases."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    system.execute_case(case_id="test-skill", task="test_task", agent_role="Executor")

    # Check that skill was generated
    stats = system.executor.learning_coordinator.get_skill_stats("test-skill")
    assert stats is not None
    assert stats.success_count == 1


def test_performance_stats():
    """Test getting performance statistics."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    system.execute_case(case_id="test-stats", task="test_task", agent_role="Executor")

    stats = system.get_performance_stats()
    assert stats["total_executions"] == 1
    assert stats["success_rate"] == 1.0


def test_learning_summary():
    """Test getting learning summary."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    system.execute_case(case_id="test-summary", task="test_task", agent_role="Executor")

    summary = system.get_learning_summary()
    assert summary["total_skills"] == 1
    assert summary["total_executions"] == 1


def test_multiple_executions():
    """Test multiple case executions."""
    system = AgenticSystem()

    def mock_handler(case_id, reference, agent_role):
        return {"result": "success"}

    system.register_handler("test_task", mock_handler)

    for i in range(5):
        system.execute_case(case_id=f"test-multi-{i}", task="test_task", agent_role="Executor")

    stats = system.get_performance_stats()
    assert stats["total_executions"] == 5

    summary = system.get_learning_summary()
    assert summary["total_executions"] == 5
