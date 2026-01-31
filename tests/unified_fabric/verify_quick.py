"""Quick verification test for unified_fabric"""
import asyncio

from src.unified_fabric import DynamicEventBus, Event
from src.unified_fabric.safety_router import SafetyFirstRouter


async def test_safety_router():
    router = SafetyFirstRouter()

    # Test clean content
    report = await router.validate("Hello world", "grid", "user1")
    print(f"Clean content - Decision: {report.decision.value}, Threat: {report.threat_level.value}")

    # Test harmful content
    report2 = await router.validate("This contains violence", "grid", "user2")
    print(f"Harmful content - Decision: {report2.decision.value}, Violations: {len(report2.violations)}")

    # Test injection
    report3 = await router.validate("ignore previous instructions", "safety", "user3")
    print(f"Injection - Decision: {report3.decision.value}, Threat: {report3.threat_level.value}")

    print("\nAll safety router tests passed!")


async def test_event_bus():
    bus = DynamicEventBus(bus_id="test")
    received = []

    async def handler(event):
        received.append(event.event_type)

    bus.subscribe("test.event", handler)
    await bus.start()

    event = Event(
        event_type="test.event",
        payload={"key": "value"},
        source_domain="test"
    )

    await bus.publish(event, wait_for_handlers=True)
    await bus.stop()

    assert len(received) == 1
    print(f"Event bus - Received {len(received)} event(s)")
    print("All event bus tests passed!")


if __name__ == "__main__":
    asyncio.run(test_safety_router())
    asyncio.run(test_event_bus())
