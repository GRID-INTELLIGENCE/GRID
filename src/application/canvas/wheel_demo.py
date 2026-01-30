"""Demo script showing the environment wheel visualization."""

import asyncio
import time
from pathlib import Path

from application.canvas import Canvas
from application.canvas.wheel import WheelZone


async def demo_wheel():
    """Demonstrate the environment wheel visualization."""
    print("=" * 60)
    print("Environment Wheel Demo - GRID Agent Movement Visualization")
    print("=" * 60)
    print()

    # Initialize canvas
    canvas = Canvas(workspace_root=Path.cwd())

    # Add some sample agents to the wheel
    canvas.wheel.add_agent(
        agent_id="agent_1",
        agent_name="Agent Router",
        zone=WheelZone.CORE,
        metadata={"type": "routing"},
    )

    canvas.wheel.add_agent(
        agent_id="agent_2",
        agent_name="Navigation Agent",
        zone=WheelZone.COGNITIVE,
        metadata={"type": "navigation"},
    )

    canvas.wheel.add_agent(
        agent_id="agent_3",
        agent_name="Canvas Agent",
        zone=WheelZone.CANVAS,
        metadata={"type": "canvas"},
    )

    print("Initial wheel state:")
    print(canvas.get_wheel_visualization(format="text"))
    print()

    # Simulate some routing to create movement
    print("Simulating routing operations...")
    print()

    queries = [
        "find agent routing system",
        "search cognitive layer",
        "locate API endpoints",
        "find integration state",
    ]

    for i, query in enumerate(queries):
        print(f"Routing: {query}")
        result = await canvas.route(query, max_results=3, enable_motivation=False)
        print(f"  Found {len(result.routes)} routes")
        print(f"  Top route: {result.routes[0].path if result.routes else 'None'}")
        print()

        # Show wheel state after each routing
        if (i + 1) % 2 == 0:
            print("Current wheel state:")
            print(canvas.get_wheel_visualization(format="text"))
            print()

        # Small delay for animation
        time.sleep(0.5)

    # Show final visualization
    print("=" * 60)
    print("Final Environment Wheel State")
    print("=" * 60)
    print(canvas.get_wheel_visualization(format="text"))
    print()

    # Show JSON visualization
    print("JSON Visualization (sample):")
    viz_json = canvas.get_wheel_visualization(format="json")
    print(f"  Rotation: {viz_json['rotation_angle_degrees']:.1f}°")
    print(f"  Total Agents: {viz_json['total_agents']}")
    print(f"  Active Zones: {len([z for z in viz_json['zones'].values() if z['agent_count'] > 0])}")
    print()


if __name__ == "__main__":
    asyncio.run(demo_wheel())
