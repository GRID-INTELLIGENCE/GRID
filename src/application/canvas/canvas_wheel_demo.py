"""
Canvas Integration Example #2 - Complete demonstration of Canvas routing
with Environment Wheel visualization showing agent movement tracking.
"""

import asyncio
import time
from pathlib import Path

from application.canvas import Canvas


async def main():
    """Main demo showing Canvas routing integrated with wheel visualization."""

    print("\n" + "=" * 80)
    print(" " * 15 + "CANVAS INTEGRATION #2 - ROUTING & WHEEL VISUALIZATION")
    print("=" * 80)
    print()
    print("This demonstrates how Canvas routing operations automatically")
    print("create and track agents on the Environment Wheel.")
    print()

    # Initialize Canvas
    print("Step 1: Initializing Canvas with Environment Wheel")
    print("-" * 80)
    canvas = Canvas(workspace_root=Path.cwd())
    print("[OK] Canvas initialized")
    print(f"[OK] Wheel ready with {len(canvas.wheel.state.agents)} agents")
    print()

    # Show initial wheel
    print("Initial Wheel State:")
    print("-" * 80)
    initial = canvas.get_wheel_visualization(format="text")
    print(initial)
    print()

    # Perform routing operations
    print("Step 2: Performing Canvas Routing Operations")
    print("-" * 80)
    print()

    routing_tasks = [
        "find agent routing system in grid agentic",
        "search cognitive navigation agents",
        "locate API endpoints application",
        "find integration state canvas",
        "search tools utilities",
    ]

    for i, query in enumerate(routing_tasks, 1):
        print(f"Routing Operation {i}: {query}")

        # Perform routing
        result = await canvas.route(query, max_results=2, enable_motivation=False)

        # Show results
        if result.routes:
            route_path = str(result.routes[0].path)
            print(f"  => Found route: {route_path}")
            print(f"  => Relevance: {result.relevance_scores[0].final_score:.2f}")
        else:
            print("  => No routes found")

        # Update wheel
        canvas.spin_wheel(delta_time=0.2)
        print(f"  => Wheel agents: {len(canvas.wheel.state.agents)}")
        print()

        # Show wheel every 2 operations
        if i % 2 == 0:
            print("  Current Wheel State:")
            wheel_viz = canvas.get_wheel_visualization(format="text")
            print(wheel_viz)
            print()

        time.sleep(0.2)

    # Final comprehensive view
    print("Step 3: Final Environment Wheel Visualization")
    print("=" * 80)
    print()
    final_viz = canvas.get_wheel_visualization(format="text")
    print(final_viz)
    print()

    # Statistics
    print("Step 4: Wheel Statistics Summary")
    print("-" * 80)
    json_data = canvas.get_wheel_visualization(format="json")

    print(f"Total Agents: {json_data['total_agents']}")
    print(f"Wheel Rotation: {json_data['rotation_angle_degrees']:.2f} degrees")
    print(f"Total Updates: {json_data['update_count']}")
    print()

    print("Agent Distribution:")
    zone_counts = {}
    for agent in json_data["agents"]:
        zone = agent["zone"]
        zone_counts[zone] = zone_counts.get(zone, 0) + 1

    for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {zone:15s}: {count:2d} agents")
    print()

    print("Zone Activity:")
    for zone_name, zone_data in sorted(json_data["zones"].items()):
        if zone_data["agent_count"] > 0:
            print(
                f"  {zone_name:15s}: {zone_data['agent_count']:2d} agents, "
                f"activity {zone_data['activity_level']:.2f}"
            )
    print()

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Key Points:")
    print("  1. Each Canvas.route() call automatically tracks agents on the wheel")
    print("  2. Agents are placed in zones based on route path analysis")
    print("  3. The wheel continuously spins, showing movement and activity")
    print("  4. Visualization is available in ASCII text and JSON formats")
    print()


if __name__ == "__main__":
    asyncio.run(main())
