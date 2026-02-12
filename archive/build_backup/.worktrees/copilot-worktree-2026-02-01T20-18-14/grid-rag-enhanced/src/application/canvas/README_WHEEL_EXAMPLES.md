# Canvas Wheel - ASCII Visualization Examples

## Simple Example

```python
from pathlib import Path
from application.canvas import Canvas
from application.canvas.wheel import WheelZone

# Initialize canvas
canvas = Canvas(workspace_root=Path.cwd())

# Add agents to different zones
canvas.wheel.add_agent("agent1", "Router Agent", WheelZone.CORE)
canvas.wheel.add_agent("agent2", "Navigation Agent", WheelZone.COGNITIVE)
canvas.wheel.add_agent("agent3", "Canvas Agent", WheelZone.CANVAS)

# Spin the wheel
canvas.spin_wheel(delta_time=0.2)

# Display ASCII visualization
print(canvas.get_wheel_visualization(format="text"))
```

## Example Output

```
======================================================================
GRID Environment Wheel - ASCII Visualization
======================================================================

Environment Wheel - Rotation: 12.5 deg
Agents: 4 | Updates: 3
------------------------------------------------------------


                                 I

                    A                  C

                       *
                                *



               A
                            O      *  C




                               *

                   T                  C


                          A




------------------------------------------------------------
Active Zones:
  core: 1 agents, activity 0.18
  cognitive: 1 agents, activity 0.18
  agentic: 1 agents, activity 0.18
  canvas: 1 agents, activity 0.18
```

## Legend

- **O** = Center of the wheel
- **C** = Core zone (grid/)
- **N** = Cognitive zone (light_of_the_seven/)
- **A** = Application zone (application/)
- **T** = Tools zone (tools/)
- **R** = Arena zone (Arena/)
- **A** = Agentic zone (grid/agentic/)
- **I** = Interfaces zone (grid/interfaces/)
- **C** = Canvas zone (application/canvas/)
- **\*** = Agent position

## Integration with Canvas Routing

When you perform routing operations, agents are automatically created and moved on the wheel:

```python
# Routing automatically tracks agents
result = await canvas.route("find agent routing system")

# View the wheel after routing
print(canvas.get_wheel_visualization(format="text"))
```

Each routing operation creates an agent on the wheel in the appropriate zone based on the route paths found.

## Running Examples

### Simple Wheel Example
```bash
python application/canvas/simple_wheel_example.py
```

### Full Integration Example
```bash
python application/canvas/canvas_integration_example.py
```

### Architecture Diagram
```bash
python application/canvas/canvas_integration_example.py arch
```

## API Endpoint

You can also get the wheel visualization via API:

```bash
# ASCII text format
curl http://localhost:8080/api/v1/canvas/wheel?format=text

# JSON data format
curl http://localhost:8080/api/v1/canvas/wheel?format=json

# Raw state format
curl http://localhost:8080/api/v1/canvas/wheel?format=state
```
