"""Tests for event bus system."""


from coinbase.events import (
    CaseCompletedEvent,
    CaseExecutedEvent,
    EventBus,
)


def test_publish_case_executed_event():
    """Test publishing case executed event."""
    bus = EventBus()
    results = []

    def handler(event):
        results.append(event)

    bus.subscribe("case_executed", handler)

    event = CaseExecutedEvent(case_id="test-123", agent_role="Executor", task="test_task")

    bus.publish({"type": "case_executed", **event.__dict__})

    assert len(results) == 1
    assert results[0]["case_id"] == "test-123"


def test_publish_case_completed_event():
    """Test publishing case completed event."""
    bus = EventBus()
    results = []

    def handler(event):
        results.append(event)

    bus.subscribe("case_completed", handler)

    event = CaseCompletedEvent(
        case_id="test-456", outcome="success", solution="Test solution", execution_time_seconds=1.5
    )

    bus.publish({"type": "case_completed", **event.__dict__})

    assert len(results) == 1
    assert results[0]["outcome"] == "success"


def test_multiple_subscribers():
    """Test multiple subscribers to same event."""
    bus = EventBus()
    results_1 = []
    results_2 = []

    def handler_1(event):
        results_1.append(event)

    def handler_2(event):
        results_2.append(event)

    bus.subscribe("case_executed", handler_1)
    bus.subscribe("case_executed", handler_2)

    event = CaseExecutedEvent(case_id="test-789", agent_role="Executor", task="test_task")

    bus.publish({"type": "case_executed", **event.__dict__})

    assert len(results_1) == 1
    assert len(results_2) == 1


def test_unsubscribe():
    """Test unsubscribing from events."""
    bus = EventBus()
    results = []

    def handler(event):
        results.append(event)

    bus.subscribe("case_executed", handler)

    event = CaseExecutedEvent(case_id="test-abc", agent_role="Executor", task="test_task")

    bus.publish({"type": "case_executed", **event.__dict__})
    assert len(results) == 1

    bus.unsubscribe("case_executed", handler)

    bus.publish({"type": "case_executed", **event.__dict__})
    assert len(results) == 1  # No new result


def test_event_handler_error():
    """Test that handler errors don't stop other handlers."""
    bus = EventBus()
    results = []

    def failing_handler(event):
        raise Exception("Handler error")

    def working_handler(event):
        results.append(event)

    bus.subscribe("case_executed", failing_handler)
    bus.subscribe("case_executed", working_handler)

    event = CaseExecutedEvent(case_id="test-error", agent_role="Executor", task="test_task")

    bus.publish({"type": "case_executed", **event.__dict__})

    # Working handler should still execute
    assert len(results) == 1
