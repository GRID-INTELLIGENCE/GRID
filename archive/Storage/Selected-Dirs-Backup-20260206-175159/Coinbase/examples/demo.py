"""Demo of GRID agentic system usage."""

import asyncio
from pathlib import Path

from coinbase import (
    AgenticSystem,
    CognitiveEngine,
    EventBus,
    InteractionEvent,
    SystemConfig,
    VersionMetrics,
    VersionScorer,
)


async def demo_basic_execution():
    """Demo basic case execution with behavior tracking."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Case Execution")
    print("=" * 60)

    # Create agentic system
    system = AgenticSystem()

    # Register a task handler
    async def data_processing_handler(case_id, reference, agent_role):
        print(f"  [Handler] Processing case {case_id}")
        await asyncio.sleep(0.1)  # Simulate work
        return {"processed": True, "data": f"Result for {case_id}"}

    system.register_handler("data_processing", data_processing_handler)

    # Execute a case
    result = await system.execute_case(
        case_id="case-001", task="data_processing", agent_role="DataProcessor"
    )

    print(f"  Result: {result['success']}")
    print(f"  Duration: {result['duration_ms']}ms")

    # Get performance stats
    stats = system.get_performance_stats()
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")


async def demo_error_recovery():
    """Demo error recovery with automatic retry."""
    print("\n" + "=" * 60)
    print("DEMO 2: Error Recovery with Retry")
    print("=" * 60)

    system = AgenticSystem()
    attempt_count = 0

    async def flaky_handler(case_id, reference, agent_role):
        nonlocal attempt_count
        attempt_count += 1
        print(f"  [Handler] Attempt {attempt_count}")

        if attempt_count < 2:
            raise TimeoutError("Simulated timeout")

        return {"recovered": True}

    system.register_handler("flaky_task", flaky_handler)

    result = await system.execute_case(
        case_id="case-002", task="flaky_task", agent_role="RetryAgent"
    )

    print(f"  Final result: {result['success']}")
    print(f"  Total attempts: {attempt_count}")


async def demo_skill_generation():
    """Demo automatic skill generation from successful cases."""
    print("\n" + "=" * 60)
    print("DEMO 3: Skill Generation")
    print("=" * 60)

    # Create system with custom skill store path
    skill_store = Path.home() / ".grid" / "knowledge"
    config = SystemConfig(skill_store_path=str(skill_store))
    system = AgenticSystem(config)

    async def analysis_handler(case_id, reference, agent_role):
        return {"analysis": f"Analysis for {case_id}"}

    system.register_handler("analysis", analysis_handler)

    # Execute multiple cases
    for i in range(3):
        await system.execute_case(case_id=f"analysis-{i}", task="analysis", agent_role="Analyst")

    # Get learning summary
    summary = system.get_learning_summary()
    print(f"  Total skills: {summary['total_skills']}")
    print(f"  Total executions: {summary['total_executions']}")
    print(f"  Overall success rate: {summary['overall_success_rate']:.2%}")

    # Get ranked skills
    ranked = system.executor.learning_coordinator.get_ranked_skills()
    print(f"  Top skills: {[skill_id for skill_id, _ in ranked]}")


async def demo_version_scoring():
    """Demo version scoring and tier assignment."""
    print("\n" + "=" * 60)
    print("DEMO 4: Version Scoring & Tier Assignment")
    print("=" * 60)

    scorer = VersionScorer()

    # Simulate high-performing metrics (gold tier)
    metrics_gold = VersionMetrics(
        coherence_accumulation=0.95,
        evolution_count=85,
        pattern_emergence_rate=0.9,
        operation_success_rate=0.95,
        avg_confidence=0.92,
        skill_retrieval_score=0.88,
        resource_efficiency=0.85,
        error_recovery_rate=0.9,
    )

    score, version = scorer.calculate_version_score(metrics_gold)
    print(f"  Gold tier: score={score:.2f}, version={version}")

    # Simulate medium performance (silver tier)
    metrics_silver = VersionMetrics(
        coherence_accumulation=0.75,
        evolution_count=60,
        pattern_emergence_rate=0.7,
        operation_success_rate=0.75,
        avg_confidence=0.72,
        skill_retrieval_score=0.7,
        resource_efficiency=0.7,
        error_recovery_rate=0.7,
    )

    score, version = scorer.calculate_version_score(metrics_silver)
    print(f"  Silver tier: score={score:.2f}, version={version}")

    # Record checkpoints and validate momentum
    scorer.record_version_checkpoint(batch=1, score=0.75, version="3.0")
    scorer.record_version_checkpoint(batch=2, score=0.82, version="3.0")
    scorer.record_version_checkpoint(batch=3, score=0.88, version="3.5")

    print(f"  Momentum valid: {scorer.validate_momentum()}")
    print(f"  Latest version: {scorer.get_latest_version()}")


async def demo_cognitive_tracking():
    """Demo cognitive state tracking."""
    print("\n" + "=" * 60)
    print("DEMO 5: Cognitive State Tracking")
    print("=" * 60)

    engine = CognitiveEngine()

    # Track interactions
    events = [
        InteractionEvent(user_id="user-001", action="task started"),
        InteractionEvent(user_id="user-001", action="error occurred"),
        InteractionEvent(user_id="user-001", action="task completed successfully"),
    ]

    for event in events:
        state = await engine.track_interaction(event)
        print(f"  Action: {event.action}")
        print(f"  Load: {state.load.value}")
        print(f"  Processing mode: {state.processing_mode}")
        print(f"  Confidence: {state.confidence:.2f}")
        print()

    # Check if scaffolding needed
    should_scaffold = engine.should_apply_scaffolding("user-001")
    print(f"  Should apply scaffolding: {should_scaffold}")


async def demo_event_bus():
    """Demo event bus for decoupled communication."""
    print("\n" + "=" * 60)
    print("DEMO 6: Event Bus Communication")
    print("=" * 60)

    bus = EventBus()
    received = []

    # Subscribe to events
    def handler(event):
        received.append(event)
        print(f"  Received: {event.get('type')} - {event.get('case_id')}")

    bus.subscribe("case_executed", handler)
    bus.subscribe("case_completed", handler)

    # Publish events
    bus.publish(
        {"type": "case_executed", "case_id": "case-001", "agent_role": "Executor", "task": "test"}
    )

    bus.publish({"type": "case_completed", "case_id": "case-001", "outcome": "success"})

    print(f"  Total events received: {len(received)}")


async def demo_full_workflow():
    """Demo complete workflow with all components."""
    print("\n" + "=" * 60)
    print("DEMO 7: Complete Workflow")
    print("=" * 60)

    # Create system
    system = AgenticSystem()

    # Register handlers
    async def task_a_handler(case_id, reference, agent_role):
        return {"task": "A", "status": "complete"}

    async def task_b_handler(case_id, reference, agent_role):
        return {"task": "B", "status": "complete"}

    system.register_handler("task_a", task_a_handler)
    system.register_handler("task_b", task_b_handler)

    # Execute multiple cases
    print("  Executing cases...")
    for i in range(5):
        task = "task_a" if i % 2 == 0 else "task_b"
        await system.execute_case(case_id=f"case-{i:03d}", task=task, agent_role="Worker")

    # Show results
    print("\n  Performance Stats:")
    stats = system.get_performance_stats()
    print(f"    Total executions: {stats['total_executions']}")
    print(f"    Success rate: {stats['success_rate']:.2%}")
    print(f"    P50 latency: {stats['p50_latency_ms']}ms")
    print(f"    P95 latency: {stats['p95_latency_ms']}ms")

    print("\n  Learning Summary:")
    summary = system.get_learning_summary()
    print(f"    Total skills: {summary['total_skills']}")
    print(f"    Overall success rate: {summary['overall_success_rate']:.2%}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("GRID Agentic System - Complete Demo")
    print("=" * 60)

    await demo_basic_execution()
    await demo_error_recovery()
    await demo_skill_generation()
    await demo_version_scoring()
    await demo_cognitive_tracking()
    await demo_event_bus()
    await demo_full_workflow()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
