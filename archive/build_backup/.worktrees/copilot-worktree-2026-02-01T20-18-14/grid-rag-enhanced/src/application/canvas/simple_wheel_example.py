"""Simple example showing ASCII wheel visualization."""

from pathlib import Path

from application.canvas import Canvas
from application.canvas.wheel import WheelZone

# Initialize canvas
canvas = Canvas(workspace_root=Path.cwd())

# Add some agents to demonstrate
canvas.wheel.add_agent("agent1", "Router Agent", WheelZone.CORE)
canvas.wheel.add_agent("agent2", "Navigation Agent", WheelZone.COGNITIVE)
canvas.wheel.add_agent("agent3", "Canvas Agent", WheelZone.CANVAS)
canvas.wheel.add_agent("agent4", "Agentic System", WheelZone.AGENTIC)

# Spin the wheel
canvas.spin_wheel(delta_time=0.2)

# Show ASCII visualization
print("\n" + "=" * 70)
print("GRID Environment Wheel - ASCII Visualization")
print("=" * 70)
print()
print(canvas.get_wheel_visualization(format="text"))
print()
print("=" * 70)
