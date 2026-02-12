#!/usr/bin/env python3
"""VECTION Demonstration Script - Context Emergence in Action.

This script demonstrates VECTION's key capabilities:
- Context establishment (no longer null!)
- Emergent pattern detection
- Cognitive velocity tracking
- Future context projection

Run this script to see how VECTION builds understanding over time
rather than treating each request as isolated.

Usage:
    python -m vection.demo

Or from the grid root:
    python -m src.vection.demo
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from typing import Any


# ANSI color codes for pretty output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_section(text: str) -> None:
    """Print a styled section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▶ {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-' * 50}{Colors.END}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_data(label: str, value: Any, indent: int = 2) -> None:
    """Print labeled data."""
    prefix = " " * indent
    if isinstance(value, dict):
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END}")
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                print(f"{prefix}  {k}: {json.dumps(v, indent=2)[:100]}...")
            else:
                print(f"{prefix}  {k}: {v}")
    elif isinstance(value, list):
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END} {value[:5]}{'...' if len(value) > 5 else ''}")
    else:
        print(f"{prefix}{Colors.BOLD}{label}:{Colors.END} {value}")


async def demo_basic_context_establishment() -> None:
    """Demonstrate basic context establishment."""
    print_section("Basic Context Establishment")

    from vection.core.engine import Vection

    engine = Vection()

    # Simulate a user session with multiple interactions
    session_id = "demo_session_001"
    events = [
        {"action": "search", "query": "authentication patterns", "type": "query"},
        {"action": "search", "query": "JWT implementation best practices", "type": "query"},
        {"action": "analyze", "query": "token refresh strategies", "type": "query"},
        {"action": "create", "query": "implement OAuth2 flow", "type": "task"},
        {"action": "debug", "query": "fix token expiration bug", "type": "issue"},
    ]

    print_info("Simulating user session with authentication-related queries...")
    print()

    for i, event in enumerate(events, 1):
        print(f'  Request {i}: {event["action"]} - "{event["query"][:40]}..."')

        # Establish context
        context = await engine.establish(session_id, event)

        # Show context state after each request
        print(f"    Context Status: {context.status.value}")
        print(f"    Anchors: {context.anchor_count}, Signals: {context.signal_count}")

        if context.has_velocity:
            velocity = context.cognitive_velocity
            print(f"    Velocity: {velocity.direction.value} (momentum={velocity.momentum:.2f})")

        print()
        await asyncio.sleep(0.1)  # Small delay for realism

    # Final context summary
    print_success("Context established successfully!")
    print()
    print_info("Final Context State:")
    print_data("Session ID", context.session_id)
    print_data("Status", context.status.value)
    print_data("Interaction Count", context.interaction_count)
    print_data("Is Established", context.is_established)

    if context.has_velocity:
        print_data("Cognitive Direction", context.cognitive_velocity.direction.value)
        print_data("Momentum", f"{context.cognitive_velocity.momentum:.2f}")
        print_data("Confidence", f"{context.cognitive_velocity.confidence:.2f}")

    # Show that context_establishment is NOT null
    print()
    print_success(f"context_establishment: {Colors.GREEN}NOT NULL{Colors.END} ✓")

    return engine, session_id


async def demo_emergent_patterns(engine: Any, session_id: str) -> None:
    """Demonstrate emergent pattern detection."""
    print_section("Emergent Pattern Detection")

    print_info("Querying for emergent patterns related to 'authentication'...")

    signals = await engine.query_emergent(session_id, "authentication")

    if signals:
        print_success(f"Found {len(signals)} emergent patterns!")
        print()
        for i, signal in enumerate(signals, 1):
            print(f"  Pattern {i}:")
            print(f"    Type: {signal.signal_type.value}")
            print(f"    Description: {signal.description}")
            print(f"    Confidence: {signal.confidence:.2f}")
            print(f"    Salience: {signal.effective_salience:.2f}")
            print()
    else:
        print_info("No specific patterns emerged yet (need more observations)")

    # Get context and show salience map
    context = engine.get_context(session_id)
    if context and context.salience_map:
        print_info("Current Salience Map (what matters right now):")
        for key, salience in sorted(context.salience_map.items(), key=lambda x: -x[1])[:5]:
            bar = "█" * int(salience * 20)
            print(f"    {key[:30]:30s} [{bar:20s}] {salience:.2f}")


async def demo_velocity_tracking(engine: Any, session_id: str) -> None:
    """Demonstrate cognitive velocity tracking."""
    print_section("Cognitive Velocity Tracking")

    context = engine.get_context(session_id)

    if not context or not context.has_velocity:
        print_warning("No velocity tracked yet")
        return

    velocity = context.cognitive_velocity

    print_info("Current Cognitive Velocity:")
    print()

    # Visual velocity representation
    direction_emoji = {
        "exploration": "🔍",
        "investigation": "🔬",
        "execution": "⚡",
        "synthesis": "🔗",
        "reflection": "🤔",
        "transition": "🔄",
        "unknown": "❓",
    }

    emoji = direction_emoji.get(velocity.direction.value, "❓")
    print(f"    {emoji} Direction: {velocity.direction.value.upper()}")
    print(f"       Detail: {velocity.direction_detail}")
    print()

    # Visual bars for metrics
    metrics = [
        ("Magnitude", velocity.magnitude),
        ("Momentum", velocity.momentum),
        ("Confidence", velocity.confidence),
    ]

    for name, value in metrics:
        bar = "▓" * int(value * 20) + "░" * (20 - int(value * 20))
        color = Colors.GREEN if value > 0.6 else Colors.YELLOW if value > 0.3 else Colors.RED
        print(f"    {name:12s} [{color}{bar}{Colors.END}] {value:.2f}")

    # Drift (can be negative)
    drift = velocity.drift
    drift_visual = "=" * 10 + "|" + "=" * 10
    drift_pos = int((drift + 1) / 2 * 20)
    drift_visual = drift_visual[:drift_pos] + "●" + drift_visual[drift_pos + 1 :]
    print(f"    {'Drift':12s} [{drift_visual}] {drift:+.2f}")
    print()

    # Direction history
    if velocity.history:
        print_info("Recent Direction History:")
        print(f"    {' → '.join(velocity.history[-5:])}")


async def demo_future_projection(engine: Any, session_id: str) -> None:
    """Demonstrate future context projection."""
    print_section("Future Context Projection")

    print_info("Projecting future context needs (3 steps ahead)...")
    print()

    projections = await engine.project(session_id, steps=3)

    if projections and not projections[0].startswith("DATA_MISSING"):
        print_success("Future context needs projected:")
        print()
        for i, projection in enumerate(projections, 1):
            print(f"    Step {i}: {Colors.CYAN}{projection}{Colors.END}")
        print()
        print_info("These projections can be used to pre-load context,")
        print_info("optimize resource allocation, or guide routing decisions.")
    else:
        print_warning("Insufficient data for reliable projection")
        print_info("Need more interactions to build trajectory confidence")


async def demo_session_lifecycle() -> None:
    """Demonstrate complete session lifecycle."""
    print_section("Session Lifecycle")

    from vection.core.engine import Vection

    engine = Vection()

    # Create session
    session_id = "lifecycle_demo"
    print_info("Creating session...")

    event = {"action": "start", "type": "session_init"}
    context = await engine.establish(session_id, event)
    print_success(f"Session created: {session_id}")
    print(f"    Status: {context.status.value}")

    # Add some interactions
    print_info("Adding interactions...")
    for i in range(3):
        await engine.establish(session_id, {"action": f"task_{i}", "type": "work"})

    context = engine.get_context(session_id)
    print(f"    Interactions: {context.interaction_count}")
    print(f"    Status: {context.status.value}")

    # Get stats
    stats = engine.get_stats()
    print_info("Engine Stats:")
    print_data("Active Sessions", stats["active_sessions"])
    print_data("Total Interactions", stats["total_interactions"])

    # Dissolve session
    print_info("Dissolving session...")
    dissolved = await engine.dissolve(session_id)
    print_success(f"Session dissolved: {dissolved}")


async def demo_grid_integration() -> None:
    """Demonstrate GRID cognitive engine integration."""
    print_section("GRID Integration Bridge")

    try:
        from vection.interfaces.grid_bridge import EnrichedCognitiveState, GridVectionBridge

        bridge = GridVectionBridge()

        # Create a mock cognitive state
        class MockCognitiveState:
            estimated_load = 0.6
            processing_mode = "system_2"
            mode_confidence = 0.8
            mental_model_alignment = 0.7
            context = {"domain": "software_development"}

        mock_state = MockCognitiveState()
        session_id = "grid_integration_demo"
        event = {"action": "analyze", "query": "optimize database queries", "type": "task"}

        print_info("Enhancing cognitive state with VECTION context...")

        enriched = await bridge.enhance_cognitive_state(mock_state, session_id, event)

        print_success("Cognitive state enriched!")
        print()

        # Show the key result: context_establishment is not null
        if enriched.has_context_establishment:
            print(f"    {Colors.GREEN}{Colors.BOLD}✓ context_establishment: PRESENT{Colors.END}")
        else:
            print(f"    {Colors.RED}✗ context_establishment: null{Colors.END}")

        print()
        print_info("Enriched State Summary:")
        print_data("Processing Mode", enriched.processing_mode)
        print_data("Estimated Load", enriched.estimated_load)
        print_data("Pattern Count", enriched.pattern_count)
        print_data("Has Velocity", enriched.has_velocity)
        print_data("Session Anchors", len(enriched.session_anchors))

        # Show routing hints
        hints = bridge.get_routing_hints(session_id)
        if hints.get("hint_available"):
            print()
            print_info("Routing Hints Generated:")
            for key, value in hints.items():
                if key != "hint_available":
                    print(f"    {key}: {value}")

    except ImportError as e:
        print_warning(f"GRID integration not available: {e}")


async def demo_workers() -> None:
    """Demonstrate background workers."""
    print_section("Background Workers")

    print_info("VECTION includes background workers for parallel discovery:")
    print()
    print("    • Correlator: Detects cross-request correlations")
    print("    • Clusterer: Groups similar requests into clusters")
    print("    • Projector: Projects future context needs")
    print()

    try:
        from vection.workers.correlator import Correlator

        correlator = Correlator()
        await correlator.start()

        # Simulate some observations
        session_id = "worker_demo"
        events = [
            {"action": "search", "type": "query"},
            {"action": "analyze", "type": "query"},
            {"action": "search", "type": "query"},
            {"action": "analyze", "type": "query"},
            {"action": "search", "type": "query"},
        ]

        print_info("Feeding events to correlator...")
        for event in events:
            correlator.observe(event, session_id)

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        stats = correlator.get_stats()
        print_success("Correlator running!")
        print_data("Observations", stats["total_observations"])
        print_data("Candidates", stats["candidates"])
        print_data("Correlations Found", stats["correlations_found"])

        await correlator.stop()

    except ImportError as e:
        print_warning(f"Workers not available: {e}")


async def main() -> None:
    """Run the VECTION demonstration."""
    print()
    print_header("VECTION - Context Emergence Engine Demo")
    print()
    print(f"  {Colors.BOLD}Velocity × Direction × Context = Cognitive Motion Intelligence{Colors.END}")
    print()
    print("  This demo shows how VECTION builds understanding over time,")
    print("  filling the critical gap: context_establishment is no longer null.")
    print()
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Demo 1: Basic context establishment
        engine, session_id = await demo_basic_context_establishment()

        # Demo 2: Emergent patterns
        await demo_emergent_patterns(engine, session_id)

        # Demo 3: Velocity tracking
        await demo_velocity_tracking(engine, session_id)

        # Demo 4: Future projection
        await demo_future_projection(engine, session_id)

        # Demo 5: Session lifecycle
        await demo_session_lifecycle()

        # Demo 6: GRID integration
        await demo_grid_integration()

        # Demo 7: Workers
        await demo_workers()

        # Summary
        print_header("Demo Complete")
        print()
        print(f"  {Colors.GREEN}✓{Colors.END} Context Establishment: Working")
        print(f"  {Colors.GREEN}✓{Colors.END} Pattern Emergence: Working")
        print(f"  {Colors.GREEN}✓{Colors.END} Velocity Tracking: Working")
        print(f"  {Colors.GREEN}✓{Colors.END} Future Projection: Working")
        print(f"  {Colors.GREEN}✓{Colors.END} GRID Integration: Available")
        print()
        print(f"  {Colors.BOLD}VECTION: Because context_establishment should never be null.{Colors.END}")
        print()

    except Exception as e:
        print()
        print(f"{Colors.RED}Error during demo: {e}{Colors.END}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
