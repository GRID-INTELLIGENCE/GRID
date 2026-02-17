# GRID Mapping Intelligence Module

**Bird's Eye Sharp & Precise Mapping Intelligence**

Adapted from [pollinate_sunflower](https://github.com/princedaemontargaryen02/pollinate_sunflower) for GRID.

---

## Overview

The Mapping Intelligence module provides quantum-inspired and neural network-based optimization for:

- **Entity relationship mapping** - Analyze and cluster entities in multi-dimensional space
- **Decision pathway optimization** - Find optimal paths through decision trees
- **Market/competitive landscape analysis** - Map competitive terrain with zones
- **Codebase structure navigation** - Navigate complex code structures

---

## Architecture

```
circuits/mapper/
├── __init__.py          # Module exports
├── quantum_mapper.py    # Quantum-inspired optimization
├── neural_mapper.py     # Neural path optimization
├── terrain.py           # Terrain/zone intelligence
└── engine.py            # Main integration engine
```

### Components

| Component | Purpose |
|-----------|---------|
| `QuantumMapOptimizer` | Superposition, entanglement, wavefunction collapse for mapping |
| `NeuralPathOptimizer` | Neural network activation propagation and path finding |
| `TerrainIntelligence` | Zone management, safety assessment, clustering |
| `MappingEngine` | Unified interface combining all components |

---

## CLI Commands

### `grid mapper analyze`

Analyze landscape of entities with configurable clustering.

```bash
# Default (adaptive clustering)
grid mapper analyze

# With custom entities (format: id:x:y:z)
grid mapper analyze entity1:0:0:0 entity2:3:4:1 entity3:7:2:0

# With specific cluster mode
grid mapper analyze --cluster-mode visual
grid mapper analyze --cluster-mode influence
grid mapper analyze --cluster-mode graph
grid mapper analyze --cluster-mode adaptive
grid mapper analyze --cluster-mode distance

# With custom thresholds
grid mapper analyze --cluster-threshold 3.0 --connect-threshold 8.0

# JSON output
grid mapper analyze --format json
```

### Clustering Modes

| Mode | Description |
|------|-------------|
| `visual` | X/Y only, ignores Z (bird's eye view) |
| `influence` | Larger threshold (≥5.0) for grouping nearby points |
| `graph` | Connected components from connectivity graph |
| `adaptive` | Threshold calculated from radius/density (default) |
| `distance` | Original 3D Euclidean distance-based |

### `grid mapper path`

Find optimal path between positions.

```bash
grid mapper path --start 0:0:0 --end 10:10:0
grid mapper path -s 0:0:0 -e 10:10:0 --format json
```

### `grid mapper optimize`

Find optimal mapping through multiple targets.

```bash
# Default demo targets
grid mapper optimize

# Custom targets (format: id:x:y:z:priority)
grid mapper optimize target1:3:4:0:high target2:7:2:1:normal target3:5:8:0:urgent

# With custom origin
grid mapper optimize --origin 1:1:0 target1:5:5:0 target2:10:10:0
```

### `grid mapper momentum`

Calculate angular momentum of entities around a center.

```bash
grid mapper momentum
grid mapper momentum e1:1:2:0 e2:3:1:1 e3:2:4:0
grid mapper momentum --center 0:0:0 e1:1:0:0 e2:0:1:0
```

---

## Python API

### Basic Usage

```python
from circuits.mapper import MappingEngine, Position, Zone, ZoneType

# Create engine
engine = MappingEngine(seed=42)

# Add restricted zones
engine.add_zone(Zone(
    id="high_risk",
    center=Position(5, 5, 0),
    radius=2.0,
    zone_type=ZoneType.RISK,
    intensity=0.8,
))

# Analyze landscape
entities = [
    {"id": "e1", "x": 0, "y": 0, "z": 0},
    {"id": "e2", "x": 3, "y": 4, "z": 1},
    {"id": "e3", "x": 7, "y": 2, "z": 0},
]

analysis = engine.analyze_landscape(
    entities,
    cluster_mode="adaptive",  # or "visual", "influence", "graph", "distance"
    cluster_threshold=2.0,
    connect_threshold=5.0,
)

print(f"Clusters: {analysis['cluster_count']}")
print(f"Density: {analysis['density']['density']:.4f}")
```

### Finding Optimal Paths

```python
from circuits.mapper import MappingEngine, Position, MappingMode

engine = MappingEngine()

origin = Position(0, 0, 0)
targets = [
    {"id": "t1", "x": 3, "y": 4, "z": 0, "priority": "high"},
    {"id": "t2", "x": 7, "y": 2, "z": 1, "priority": "normal"},
    {"id": "t3", "x": 5, "y": 8, "z": 0, "priority": "urgent"},
]

result = engine.find_optimal_mapping(
    origin,
    targets,
    mode=MappingMode.HYBRID,
    max_iterations=50,
)

print(f"Path: {len(result.path)} nodes")
print(f"Distance: {result.total_distance:.2f}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Quantum states explored: {result.quantum_states_explored}")
print(f"Neural nodes processed: {result.neural_nodes_processed}")
```

### Quantum Optimizer Direct Access

```python
from circuits.mapper import QuantumMapOptimizer, Position, StateType

optimizer = QuantumMapOptimizer(seed=42)

origin = Position(0, 0, 0)
targets = [
    {"id": "q1", "x": 2, "y": 3, "z": 0, "priority": "high"},
    {"id": "q2", "x": 5, "y": 1, "z": 1, "priority": "normal"},
]

# Create superposition
states = optimizer.create_superposition(origin, targets, StateType.ENTITY)

# Apply entanglement optimization
optimized = optimizer.apply_entanglement(states, max_iterations=20)

# Measure (collapse to best state)
best = optimizer.measure(optimized)
print(f"Best state: {best.id}, energy={best.energy:.4f}")
```

### Neural Path Optimizer Direct Access

```python
from circuits.mapper import NeuralPathOptimizer

optimizer = NeuralPathOptimizer(seed=42)

entities = [
    {"id": "n0", "x": 0, "y": 0, "z": 0},
    {"id": "n1", "x": 2, "y": 3, "z": 0},
    {"id": "n2", "x": 5, "y": 1, "z": 0},
]

# Build network
nodes = optimizer.build_network(entities, distance_threshold=10.0)

# Find path
path = optimizer.find_optimal_path(nodes[0], nodes[-1], nodes)

# Get metrics
metrics = optimizer.calculate_path_metrics(path)
print(f"Distance: {metrics['total_distance']:.2f}")
print(f"Coherence: {metrics['path_coherence']:.2f}")
```

---

## Zone Types

| Zone Type | Description |
|-----------|-------------|
| `SAFE` | No restrictions |
| `CAUTION` | Minor risk, proceed carefully |
| `RISK` | Significant risk, consider alternatives |
| `RESTRICTED` | Do not enter |
| `OPPORTUNITY` | High-value area |
| `DENSE` | High entity concentration |
| `SPARSE` | Low entity concentration |

---

## Mapping Modes

| Mode | Description |
|------|-------------|
| `ENTITY` | Map entities and relationships |
| `DECISION` | Map decision pathways |
| `MARKET` | Map competitive landscape |
| `CODE` | Map codebase structure |
| `HYBRID` | Combine multiple modes (default) |

---

## Key Concepts

### Position (X, Y, Z)

- **X**: Primary axis (time, sequence, market segment)
- **Y**: Secondary axis (value, importance, risk)
- **Z**: Depth axis (complexity, penetration, detail level)

### Quantum Optimization

1. **Superposition**: Create multiple possible states for targets
2. **Entanglement**: States interact and combine toward optimal solutions
3. **Wavefunction Collapse**: Converge to best states
4. **Measurement**: Return highest probability × coherence state

### Neural Path Finding

1. **Network Building**: Auto-connect nearby entities
2. **Activation Propagation**: BFS with decay from target
3. **Gradient Following**: Follow activation gradient to find paths
4. **Hopfield Memory**: Associative pattern recall

### Angular Momentum

Measures the "spin" or tendency of a system around a center point:

```
L = Σ (r × p)
```

Where `r` is distance from center and `p` is probability × energy.

---

## Testing

```bash
python -m pytest tests/test_mapper.py -v
```

---

## Origin

Adapted from [pollinate_sunflower](https://github.com/princedaemontargaryen02/pollinate_sunflower) IDEA (Intelligent Drone Routing & Delivery System).

Key adaptations:
- Geographic routing → Entity/relationship mapping
- Drone delivery → Decision pathway optimization
- No-fly zones → Restricted/risk zones
- TSP optimization → Nearest neighbor with activation weighting
