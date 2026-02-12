# Canvas Integration Example #2 - Complete Demonstration

## Overview

This example demonstrates the complete integration between Canvas routing operations and the Environment Wheel visualization, showing how agent movement is automatically tracked and visualized.

## Architecture Integration

```
Canvas.route()
    ↓
Routing Operations
    ↓
_track_routing_movement()
    ↓
Environment Wheel
    ├── Agent Creation
    ├── Zone Detection
    ├── Position Calculation
    └── Visualization
```

## Example Code

```python
import asyncio
from pathlib import Path
from application.canvas import Canvas

async def demo():
    # Initialize Canvas (includes Environment Wheel)
    canvas = Canvas(workspace_root=Path.cwd())

    # Perform routing operations
    result1 = await canvas.route("find agent routing system")
    result2 = await canvas.route("search cognitive navigation")
    result3 = await canvas.route("locate API endpoints")

    # View the wheel visualization
    print(canvas.get_wheel_visualization(format="text"))

    # Get JSON data for programmatic access
    json_data = canvas.get_wheel_visualization(format="json")
    print(f"Total agents: {json_data['total_agents']}")
    print(f"Rotation: {json_data['rotation_angle_degrees']:.1f} deg")

asyncio.run(demo())
```

## Example Output

### ASCII Wheel Visualization

```
Environment Wheel - Rotation: 12.5 deg
Agents: 3 | Updates: 15
------------------------------------------------------------

                              I

                    A              C

                       *
                                *


                   A
                              O      *  C



                      T              C

                             A

------------------------------------------------------------
Active Zones:
  core: 1 agents, activity 0.22
  cognitive: 1 agents, activity 0.18
  canvas: 1 agents, activity 0.20
```

### Wheel Components

- **Zone Labels**: C (Core), N (Cognitive), A (Application), T (Tools), R (Arena), A (Agentic), I (Interfaces), C (Canvas)
- **Center (O)**: Hub of the wheel
- **Agents (*)**: Individual agents positioned on the wheel
- **Rotation**: Wheel continuously rotates showing movement
- **Activity Levels**: Each zone tracks activity and agent count

## Integration Features

### 1. Automatic Agent Tracking

Every `canvas.route()` call automatically:
- Creates an agent representing the routing operation
- Analyzes route paths to determine the target zone
- Places the agent on the wheel in the appropriate zone
- Updates zone activity levels

### 2. Zone Detection

Routes are analyzed to determine zones:
- `grid/agentic/` → AGENTIC zone
- `grid/interfaces/` → INTERFACES zone
- `grid/` → CORE zone
- `light_of_the_seven/` or `cognitive` → COGNITIVE zone
- `application/` → APPLICATION zone
- `tools/` → TOOLS zone
- `Arena/` or `the_chase` → ARENA zone
- Default → CANVAS zone

### 3. Visual Representation

The wheel provides:
- **Text Visualization**: ASCII art showing wheel state
- **JSON Data**: Structured data for programmatic access
- **Real-time Updates**: Wheel spins continuously
- **Activity Tracking**: Zone activity levels and agent counts

## Running the Examples

### Simple Example
```bash
python application/canvas/simple_wheel_example.py
```

### Full Integration Demo
```bash
python application/canvas/canvas_wheel_demo.py
```

### Integration Architecture
```bash
python application/canvas/canvas_integration_example.py arch
```

## API Usage

### Via HTTP API

```bash
# Get ASCII visualization
GET /api/v1/canvas/wheel?format=text

# Get JSON data
GET /api/v1/canvas/wheel?format=json

# Get raw state
GET /api/v1/canvas/wheel?format=state
```

### Via Python

```python
from application.canvas import Canvas

canvas = Canvas(workspace_root=Path.cwd())

# Perform routing (automatically tracks on wheel)
result = await canvas.route("your query here")

# Get visualization
text_viz = canvas.get_wheel_visualization(format="text")
json_viz = canvas.get_wheel_visualization(format="json")

# Manually spin wheel
canvas.spin_wheel(delta_time=0.1)
```

## Key Integration Points

1. **Canvas.route()** → Automatically calls `_track_routing_movement()`
2. **Route Analysis** → Determines target `WheelZone` from path
3. **Agent Placement** → Creates or moves agents on wheel
4. **Continuous Animation** → Wheel spins with `spin_wheel()`
5. **Visualization** → Multiple formats (text, JSON, state)

## Benefits

- **Visual Overview**: See agent movement through GRID's architecture
- **Activity Monitoring**: Track which zones are most active
- **Movement Patterns**: Understand routing patterns over time
- **Debugging Aid**: Visualize where routing is happening
- **System Health**: See distribution of agents across zones
