"""Canvas Integration Example - Demonstrates Canvas routing with Wheel visualization."""

import asyncio
from pathlib import Path

from application.canvas import Canvas


async def canvas_wheel_integration_demo():
    """Demonstrate Canvas integration with Environment Wheel."""

    print("\n" + "=" * 80)
    print(" " * 20 + "CANVAS & WHEEL INTEGRATION DEMO")
    print("=" * 80)
    print()
    print("This example demonstrates how Canvas routing operations")
    print("automatically track and visualize agent movement on the Environment Wheel.")
    print()

    # Initialize Canvas (which includes the wheel)
    print("1. Initializing Canvas with Environment Wheel...")
    canvas = Canvas(workspace_root=Path.cwd())
    print("   [OK] Canvas initialized")
    print(f"   [OK] Wheel created with {len(canvas.wheel.state.agents)} initial agents")
    print()

    # Show initial wheel state
    print("2. Initial Wheel State:")
    print("-" * 80)
    initial_viz = canvas.get_wheel_visualization(format="text")
    print(initial_viz)
    print()

    # Perform routing operations that create agents on the wheel
    print("3. Performing Canvas Routing Operations:")
    print("-" * 80)
    print()

    routing_queries = [
        {
            "query": "find agent routing system",
            "description": "Searching for agent routing in grid/agentic/",
            "expected_zone": "AGENTIC",
        },
        {
            "query": "search cognitive navigation agents",
            "description": "Looking for navigation in cognitive layer",
            "expected_zone": "COGNITIVE",
        },
        {
            "query": "locate API endpoints in application",
            "description": "Finding API routers in application/",
            "expected_zone": "APPLICATION",
        },
        {
            "query": "find integration state management",
            "description": "Searching canvas integration state",
            "expected_zone": "CANVAS",
        },
        {"query": "search tools and utilities", "description": "Looking in tools/ directory", "expected_zone": "TOOLS"},
        {
            "query": "find grid core interfaces",
            "description": "Searching grid/interfaces/",
            "expected_zone": "INTERFACES",
        },
    ]

    for i, routing_task in enumerate(routing_queries, 1):
        print(f"   Operation {i}: {routing_task['description']}")
        print(f'   Query: "{routing_task["query"]}"')

        # Perform routing
        result = await canvas.route(query=routing_task["query"], max_results=3, enable_motivation=False)

        # Show routing results
        if result.routes:
            top_route = result.routes[0]
            print(f"   [OK] Found {len(result.routes)} routes")
            print(f"   [OK] Top route: {top_route.path}")
            print(f"   [OK] Relevance score: {result.relevance_scores[0].final_score:.2f}")
        else:
            print("   [WARN] No routes found")

        # Spin wheel to show movement
        canvas.spin_wheel(delta_time=0.15)

        # Show wheel state after this routing
        print(f"   => Agents on wheel: {len(canvas.wheel.state.agents)}")
        print()

        # Small delay for visibility
        await asyncio.sleep(0.3)

    # Show final wheel state
    print("4. Final Wheel Visualization After All Routing Operations:")
    print("=" * 80)
    print()

    final_viz = canvas.get_wheel_visualization(format="text")
    print(final_viz)
    print()

    # Show detailed wheel statistics
    print("5. Wheel Statistics:")
    print("-" * 80)
    json_viz = canvas.get_wheel_visualization(format="json")

    print(f"   Rotation Angle: {json_viz['rotation_angle_degrees']:.2f}°")
    print(f"   Rotation Velocity: {json_viz['rotation_velocity']:.3f} rad/s")
    print(f"   Total Agents: {json_viz['total_agents']}")
    print(f"   Total Updates: {json_viz['update_count']}")
    print()

    print("   Agent Distribution by Zone:")
    zone_counts = {}
    for agent in json_viz["agents"]:
        zone = agent["zone"]
        zone_counts[zone] = zone_counts.get(zone, 0) + 1

    for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     {zone:15s}: {count:2d} agents")
    print()

    # Show zone activity levels
    print("   Zone Activity Levels:")
    active_zones = [
        (zone, data["agent_count"], data["activity_level"])
        for zone, data in json_viz["zones"].items()
        if data["agent_count"] > 0 or data["activity_level"] > 0.05
    ]

    for zone_name, agent_count, activity in sorted(active_zones, key=lambda x: x[2], reverse=True):
        bar_length = int(activity * 40)
        bar = "#" * bar_length + "." * (40 - bar_length)
        print(f"     {zone_name:15s}: [{bar}] {activity:.2f} ({agent_count} agents)")
    print()

    # Show agent details
    print("6. Agent Details:")
    print("-" * 80)
    for agent in json_viz["agents"][:10]:  # Show first 10 agents
        print(f"   - {agent['agent_name']:30s}")
        print(
            f"     Zone: {agent['zone']:15s} | Angle: {agent['angle_degrees']:6.1f} deg | Radius: {agent['radius']:.2f}"
        )
        if agent.get("metadata", {}).get("query"):
            print(f"     Query: {agent['metadata']['query'][:60]}")
        print()

    if len(json_viz["agents"]) > 10:
        print(f"   ... and {len(json_viz['agents']) - 10} more agents")
        print()

    # Demonstrate real-time wheel spinning
    print("7. Real-time Wheel Animation (5 frames):")
    print("-" * 80)
    print()

    for frame in range(5):
        canvas.spin_wheel(delta_time=0.2)
        frame_viz = canvas.get_wheel_visualization(format="text")
        print(f"Frame {frame + 1} (Rotation: {canvas.wheel.state.rotation_angle:.2f} rad):")
        print(frame_viz)
        print()
        await asyncio.sleep(0.5)

    print("=" * 80)
    print("Integration Demo Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Performed {len(routing_queries)} routing operations")
    print(f"  - Created {len(canvas.wheel.state.agents)} agents on the wheel")
    print(f"  - Wheel rotated {json_viz['rotation_angle_degrees']:.1f} degrees")
    print(f"  - {len([z for z in json_viz['zones'].values() if z['agent_count'] > 0])} zones are active")
    print()


def show_integration_architecture():
    """Show the integration architecture diagram."""

    print("\n" + "=" * 80)
    print(" " * 25 + "INTEGRATION ARCHITECTURE")
    print("=" * 80)
    print()
    print("""
    +-------------------------------------------------------------------+
    |                         CANVAS ROUTING                            |
    |                                                                   |
    |  User Query -->                                                   |
    |                |                                                  |
    |                +--> UnifiedRouter --> Similarity Matching         |
    |                |                                                  |
    |                +--> RelevanceEngine --> Metrics Scoring           |
    |                |                                                  |
    |                +--> Route Results -->                            |
    |                                     |                             |
    +-------------------------------------+-----------------------------+
                                          |
                                          v
    +-------------------------------------------------------------------+
    |                    ENVIRONMENT WHEEL TRACKING                     |
    |                                                                   |
    |  Route Results --> Agent Creation/Movement                        |
    |                     |                                            |
    |                     +--> Zone Detection (from route path)         |
    |                     |                                            |
    |                     +--> Position Calculation                     |
    |                     |                                            |
    |                     +--> Wheel Visualization                      |
    |                                                                   |
    |  +------------------------------------------------------------+  |
    |  |                    SPINNING WHEEL                          |  |
    |  |                                                            |  |
    |  |           C (Core)                                        |  |
    |  |              *                                            |  |
    |  |         *        *                                        |  |
    |  |    I *              * N                                   |  |
    |  |   (Interfaces)      (Cognitive)                           |  |
    |  |         O              *                                  |  |
    |  |    (Center)          A                                    |  |
    |  |     *                 (Application)                       |  |
    |  |  A      T                                               |  |
    |  | (Agentic)  (Tools)                                       |  |
    |  |     *                                                    |  |
    |  |        R                                                 |  |
    |  |      (Arena)                                             |  |
    |  |                                                            |  |
    |  |  * = Agents moving through zones                          |  |
    |  +------------------------------------------------------------+  |
    |                                                                   |
    +-------------------------------------------------------------------+

    KEY INTEGRATION POINTS:

    1. Canvas.route() automatically calls _track_routing_movement()
    2. Route paths are analyzed to determine target WheelZone
    3. Agents are created or moved on the wheel based on routing results
    4. Wheel continuously spins and updates agent positions
    5. Visualization available in text (ASCII) and JSON formats
    """)
    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "arch":
        show_integration_architecture()
    else:
        asyncio.run(canvas_wheel_integration_demo())
