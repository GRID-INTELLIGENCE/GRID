# Canvas - Comprehensive Routing System

## Overview

Canvas is a user-centric routing interface that orchestrates comprehensive routing through GRID's multi-directory structure. It combines similarity matching, metrics-driven relevance scoring, motivational adaptation from the resonance system, and integration state management.

## Architecture

```
Canvas
├── UnifiedRouter         - Similarity-based routing through directories
├── RelevanceEngine       - Metrics-driven relevance scoring
├── InterfaceBridge       - Integration with grid/interfaces/
├── ResonanceAdapter      - Motivational adaptation from resonance patterns
├── IntegrationStateManager - Integration state consistency management
└── Canvas API            - FastAPI endpoints for routing
```

## Key Features

1. **Similarity Matching**: Routes queries to relevant directories/files using semantic similarity
2. **Metrics-Driven Relevance**: Multi-factor scoring (semantic similarity, path complexity, context match, usage frequency, integration alignment)
3. **Interface Integration**: Bridges with `grid/interfaces/` (QuantumBridge, SensoryProcessor)
4. **Motivational Adaptation**: Uses ADSR envelope and path visualization from `application/resonance/`
5. **Integration State Consistency**: Maintains contact with `.windsurf/structural-intelligence/state/integration.json`

## Usage

### API Endpoints

#### POST `/api/v1/canvas/route`

Route a query through GRID's directory structure.

**Request:**
```json
{
  "query": "find agent routing system",
  "context": {"type": "code", "urgency": true},
  "max_results": 5,
  "enable_motivation": true
}
```

**Response:**
```json
{
  "query": "find agent routing system",
  "routes": [
    {
      "path": "grid/agentic/agentic_system.py",
      "similarity": 0.85,
      "complexity_penalty": 0.3,
      "context_boost": 0.8,
      "final_score": 0.88,
      "metadata": {"type": "file", "name": "agentic_system.py"}
    }
  ],
  "relevance_scores": [...],
  "confidence": 0.92,
  "integration_alignment": 0.9,
  "motivated_routing": {...}
}
```

#### GET `/api/v1/canvas/integration-state`

Get current integration state.

**Response:**
```json
{
  "state": {
    "generated_at": "2025-01-09T...",
    "total_integrations": 5,
    "open_mismatches": 0,
    "integrations_by_status": {...},
    "routing_history": [...]
  }
}
```

### Python API

```python
from pathlib import Path
from application.canvas import Canvas

# Initialize canvas
canvas = Canvas(workspace_root=Path.cwd())

# Route a query
result = await canvas.route(
    query="find agent routing system",
    context={"type": "code"},
    max_results=5,
    enable_motivation=True
)

# Access results
for route in result.routes:
    print(f"Route: {route.path}, Score: {route.final_score}")

# Get integration state
state = canvas.get_integration_state()
```

## Components

### UnifiedRouter

Routes queries using similarity matching across key directories:
- `grid/` - Core intelligence layer
- `application/` - Application layer
- `light_of_the_seven/` - Cognitive layer
- `tools/` - Tools and utilities
- `Arena/` - Arena simulation system

### RelevanceEngine

Calculates relevance using:
- **Semantic Similarity** (35%): Vector similarity between query and path
- **Path Complexity** (15%): Penalty for complex paths
- **Context Match** (25%): How well path matches context
- **Usage Frequency** (15%): Historical usage patterns
- **Integration Alignment** (10%): Alignment with integration state

### InterfaceBridge

Bridges with `grid/interfaces/`:
- **QuantumBridge**: For coherent state transfers
- **SensoryProcessor**: For multi-modal input processing

### ResonanceAdapter

Adapts patterns from `application/resonance/`:
- **ADSR Envelope**: Haptic-like feedback
- **PathVisualizer**: Path triage and visualization
- **ActivityResonance**: Left-right coordination

### IntegrationStateManager

Manages integration state consistency:
- Loads from `.windsurf/structural-intelligence/state/integration.json`
- Tracks routing history
- Checks integration alignment
- Updates state atomically

## Integration Points

- `grid/interfaces/bridge.py` - QuantumBridge for state transfer
- `grid/interfaces/sensory.py` - SensoryProcessor for sensory input
- `application/resonance/` - Resonance patterns for motivation
- `.windsurf/structural-intelligence/state/integration.json` - Integration state

## Configuration

Canvas automatically detects:
- Workspace root from current working directory
- Integration state from `.windsurf/structural-intelligence/state/integration.json`

Optional configuration:
- Custom workspace root path
- Custom integration.json path
- RAG system for enhanced embeddings
- Vector store for similarity search

## Examples

### Simple Routing

```python
result = await canvas.route("find API endpoints")
```

### With Context

```python
result = await canvas.route(
    query="find authentication system",
    context={
        "type": "code",
        "layer": "application",
        "urgency": True
    }
)
```

### Without Motivation

```python
result = await canvas.route(
    query="find database models",
    enable_motivation=False
)
```

## Performance

- Route discovery: <100ms for typical queries
- Relevance scoring: <50ms per route
- Integration state updates: <10ms
- Total routing time: ~200-300ms for 5 routes

## Environment Wheel Visualization

The Canvas includes an **Environment Wheel** - a spinning visual representation that tracks agent movement through GRID's directory structure. The wheel continuously rotates, showing agents as they move between zones (core, cognitive, application, tools, arena, agentic, interfaces, canvas).

### Wheel Zones

The wheel is divided into 8 zones representing GRID's architecture:
- **CORE** (0°) - `grid/` - Core intelligence layer
- **COGNITIVE** (45°) - `light_of_the_seven/` - Cognitive layer
- **APPLICATION** (90°) - `application/` - Application layer
- **TOOLS** (135°) - `tools/` - Tools and utilities
- **ARENA** (180°) - `Arena/` - Arena simulation
- **AGENTIC** (225°) - `grid/agentic/` - Agentic system
- **INTERFACES** (270°) - `grid/interfaces/` - Interface layer
- **CANVAS** (315°) - `application/canvas/` - Canvas routing

### Using the Wheel

```python
from application.canvas import Canvas

canvas = Canvas(workspace_root=Path.cwd())

# Get text visualization (ASCII art)
text_viz = canvas.get_wheel_visualization(format="text")
print(text_viz)

# Get JSON visualization (for rendering)
json_viz = canvas.get_wheel_visualization(format="json")
print(f"Rotation: {json_viz['rotation_angle_degrees']}°")
print(f"Agents: {json_viz['total_agents']}")

# Spin the wheel manually
canvas.spin_wheel(delta_time=0.1)
```

### API Endpoint

```
GET /api/v1/canvas/wheel?format=json|text|state
```

Returns visualization of the spinning environment wheel showing current agent positions and movement.

### Demo

Run the demo script to see the wheel in action:

```bash
python -m application.canvas.wheel_demo
```

## Future Enhancements

- Vector embeddings for better similarity matching
- Machine learning for relevance scoring
- Caching for frequently accessed routes
- Real-time routing updates via WebSocket
- Multi-agent routing coordination
- Interactive wheel visualization in web UI
- Agent trail visualization
- Zone activity heatmaps
