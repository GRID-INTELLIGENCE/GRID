# Motion AI Integration Plan — GRID & EUFLE
**Status:** Implemented | **Date:** 2026-01-21

---

## Overview

This document describes the complete Motion AI Integration across GRID and EUFLE, including:

- **GRID**: Trajectory diffusion for geometric pattern recognition and motion planning
- **EUFLE**: Flow diffusion for TUI interaction sequences with task-aware guidance
- **Shared Foundation**: Cost-guided sampling, B-spline encoding, diffusion priors

All modules are based on Motion Planning Diffusion (MPD) research and reference implementations from:
- Carvalho et al. 2023 (arXiv:2308.01557)
- Chi et al. 2023 (Diffusion Policy)
- Janner et al. 2022 (Planning with Diffusion)

---

## GRID: Trajectory Diffusion for Motion Planning

### Module Location
```
e:\grid\src\grid\motion\
├── __init__.py                    # Package exports
├── trajectory_diffusion.py        # Core implementation
├── config.yaml                    # Configuration
```

### Key Components

#### 1. **TrajectoryConfig** (Dataclass)
Configuration container for trajectory diffusion parameters.

**Fields:**
- `enabled` (bool): Enable/disable motion diffusion
- `model_path` (str): Path to pre-trained MPD model
- `bspline_order` (int): B-spline order (typically 4)
- `num_control_points` (int): Number of control points (default 16)
- `sampling_steps` (int): Diffusion sampling steps (default 50)
- `guidance_scale` (float): Guidance strength (default 0.7)
- `cost_weights` (dict): Collision, smoothness, goal-reaching weights

**Example:**
```python
from grid.motion import TrajectoryConfig

config = TrajectoryConfig(
    enabled=True,
    bspline_order=4,
    num_control_points=16,
    cost_weights={
        "collision": 1.0,
        "smoothness": 0.5,
        "goal_reaching": 2.0,
    }
)
```

#### 2. **BSplineEncoder**
Encodes discrete trajectories to continuous B-spline representations and vice versa.

**Methods:**
- `encode(trajectory: np.ndarray) → np.ndarray`: Trajectory → Control points
- `decode(control_points: np.ndarray, num_points: int) → np.ndarray`: Control points → Dense trajectory

**Example:**
```python
from grid.motion import BSplineEncoder
import numpy as np

encoder = BSplineEncoder(order=4, num_control_points=16)

# Encode a trajectory to control points
trajectory = np.random.randn(100, 2)  # 100 points, 2D
control_points = encoder.encode(trajectory)  # Shape: (16, 2)

# Decode back to dense representation
reconstructed = encoder.decode(control_points, num_points=100)
```

#### 3. **CostGuidedSampler**
Samples trajectories from diffusion priors and ranks them by explicit cost functions.

**Cost Functions:**
- `compute_smoothness_cost()`: Penalizes jerky/accelerated motions
- `compute_collision_cost()`: Penalizes collisions with obstacles
- `compute_goal_reaching_cost()`: Penalizes failure to reach goal
- `compute_total_cost()`: Weighted combination

**Methods:**
- `sample(num_samples, trajectory_length, trajectory_dim, goal, collision_map)`: Generate ranked trajectories

**Example:**
```python
from grid.motion import CostGuidedSampler
import numpy as np

sampler = CostGuidedSampler(cost_weights={
    "collision": 1.0,
    "smoothness": 0.5,
    "goal_reaching": 2.0,
})

goal = np.array([5.0, 5.0])
trajectories, costs = sampler.sample(
    num_samples=32,
    trajectory_length=50,
    trajectory_dim=2,
    goal=goal,
)

# trajectories: list of 32 numpy arrays (ranked by cost)
# costs: sorted list of costs
```

#### 4. **TrajectoryPrior** (Abstract Base)
Interface for loading pre-trained diffusion models.

**Methods:**
- `load(model_path: str)`: Load model from disk
- `encode(trajectories: np.ndarray) → torch.Tensor`: Encode to latent space
- `decode(latents: torch.Tensor) → np.ndarray`: Decode from latent space

**Implementation Note:**
Concrete implementations should load pre-trained MPD models from model repositories. Currently, a stub is provided that raises `NotImplementedError`.

#### 5. **TrajectoryDiffusionPipeline**
Main pipeline orchestrating the full trajectory generation workflow.

**Methods:**
- `sample_trajectories()`: Generate and rank trajectories
- `encode_trajectory()`: Encode to B-spline representation
- `decode_trajectory()`: Decode from B-spline representation

**Example:**
```python
from grid.motion import TrajectoryDiffusionPipeline
import numpy as np

# Initialize pipeline (loads config from file or defaults)
pipeline = TrajectoryDiffusionPipeline(
    config_path="e:\\grid\\src\\grid\\motion\\config.yaml"
)

# Sample trajectories
trajectories, costs = pipeline.sample_trajectories(
    num_samples=32,
    trajectory_length=50,
    trajectory_dim=2,
    goal=np.array([5.0, 5.0]),
)

# Best trajectories are first
best_trajectory = trajectories[0]
```

### Configuration (`config.yaml`)

```yaml
motion_diffusion:
  enabled: true
  model_path: "models/mpd_7dof_pretrained.pt"
  bspline_order: 4
  num_control_points: 16
  sampling_steps: 50
  guidance_scale: 0.7
  cost_weights:
    collision: 1.0
    smoothness: 0.5
    goal_reaching: 2.0
```

### Integration Points

#### 1. **Pattern Recognition** (`grid/patterns/recognition.py`)
```python
from grid.motion import TrajectoryDiffusionPipeline
import numpy as np

# In pattern matching algorithm
pipeline = TrajectoryDiffusionPipeline(config_path="grid/motion/config.yaml")

# Generate candidate trajectories for pattern matching
candidates, costs = pipeline.sample_trajectories(
    num_samples=64,
    trajectory_length=pattern_length,
    trajectory_dim=2,
    goal=goal_position,
)

# Use top-ranked trajectories for pattern matching
for trajectory in candidates[:10]:  # Top 10
    match_score = pattern_matcher.score(trajectory)
```

#### 2. **Clustering Analysis** (`grid/analysis/clustering.py`)
```python
from grid.motion import BSplineEncoder

encoder = BSplineEncoder(order=4, num_control_points=16)

# Convert discrete patterns to continuous representations
encoded_patterns = []
for pattern in patterns:
    control_points = encoder.encode(pattern)
    # Use control points as feature vectors for clustering
    encoded_patterns.append(control_points.flatten())

# Cluster encoded patterns
clusters = clustering_algorithm(encoded_patterns)
```

#### 3. **Geometric Layout Optimization**
```python
from grid.motion import CostGuidedSampler
import numpy as np

sampler = CostGuidedSampler(cost_weights={
    "collision": 2.0,      # Avoid obstacles
    "smoothness": 0.3,     # Prefer smooth paths
    "goal_reaching": 3.0,  # Reach target layout
})

# Sample smooth layout trajectories
layouts, costs = sampler.sample(
    num_samples=128,
    trajectory_length=100,
    trajectory_dim=num_layout_dimensions,
    goal=target_layout,
    collision_map=obstacle_map,
)
```

### Testing

Run unit tests:
```powershell
pytest e:\grid\tests\unit\test_trajectory_diffusion.py -v
```

Tests cover:
- Configuration loading and defaults
- B-spline encoding/decoding roundtrips
- Cost computation (smoothness, collision, goal-reaching)
- Trajectory sampling and ranking
- Pipeline integration

---

## EUFLE: Flow Diffusion for Interaction Sequences

### Module Location
```
e:\EUFLE\eufle\motion\
├── __init__.py                # Package exports
├── flow_diffusion.py          # Core implementation
├── config.yaml                # Configuration
```

### Key Components

#### 1. **FlowConfig** (Dataclass)
Configuration for flow diffusion in TUI interactions.

**Fields:**
- `enabled` (bool): Enable/disable flow diffusion
- `model_type` (str): Diffusion model type ("discrete_ddpm", "autoregressive", etc.)
- `sequence_length` (int): Length of interaction sequences
- `embedding_dim` (int): State embedding dimensionality
- `vocab_size` (int): Number of distinct states/interactions
- `inference_steps` (int): Sampling steps
- `temperature` (float): Sampling temperature
- `cost_weights` (dict): Continuity, user preference, task completion weights

**Example:**
```python
from eufle.motion import FlowConfig

config = FlowConfig(
    enabled=True,
    model_type="discrete_ddpm",
    sequence_length=32,
    embedding_dim=128,
    cost_weights={
        "continuity": 1.0,
        "user_preference": 1.5,
        "task_completion": 2.0,
    }
)
```

#### 2. **ConditionalFlowSampler**
Generates interaction flow suggestions conditioned on current TUI state.

**Methods:**
- `register_state(state_name: str, embedding: np.ndarray)`: Register a TUI state
- `compute_continuity_cost()`: Cost of disrupting user flow
- `compute_user_preference_cost()`: Cost based on user preferences
- `compute_task_completion_cost()`: Cost of not reaching task goal
- `compute_total_flow_cost()`: Weighted total cost
- `sample()`: Generate ranked flow suggestions

**Example:**
```python
from eufle.motion import ConditionalFlowSampler
import numpy as np

sampler = ConditionalFlowSampler(
    sequence_length=32,
    embedding_dim=128,
    cost_weights={
        "continuity": 1.0,
        "user_preference": 1.5,
        "task_completion": 2.0,
    }
)

# Register TUI states with embeddings
sampler.register_state("budget_overview", np.random.randn(128))
sampler.register_state("expense_detail", np.random.randn(128))
sampler.register_state("settings", np.random.randn(128))

# Sample flow suggestions
flows, costs = sampler.sample(
    num_suggestions=5,
    current_state="budget_overview",
    preferred_states={"budget_overview", "expense_detail"},
    target_state="settings",
)

# flows: list of 5 interaction sequences
# costs: sorted costs (lower is better)
```

#### 3. **InteractionCostFunction**
Defines costs for user interaction flow transitions and paths.

**Methods:**
- `register_transition(from_state, to_state)`: Define valid transitions
- `set_state_cost(state, cost)`: Set intrinsic state cost
- `is_valid_transition()`: Check transition validity
- `compute_transition_cost()`: Cost of single transition
- `compute_path_cost()`: Total cost of a state sequence

**Example:**
```python
from eufle.motion import InteractionCostFunction

cost_fn = InteractionCostFunction()

# Define valid transitions
cost_fn.register_transition("budget_overview", "expense_detail")
cost_fn.register_transition("budget_overview", "settings")
cost_fn.register_transition("expense_detail", "budget_overview")

# Set state preferences
cost_fn.set_state_cost("budget_overview", 0.1)  # Preferred
cost_fn.set_state_cost("expensive_report", 1.0)  # Avoided

# Compute path cost
path = ["budget_overview", "expense_detail", "budget_overview"]
path_cost = cost_fn.compute_path_cost(path)
```

#### 4. **FlowPrior** (Abstract Base)
Interface for pre-trained interaction sequence models.

**Methods:**
- `load(model_path)`: Load model
- `encode(sequences)`: Encode to latent space
- `decode(latents)`: Decode from latent space
- `sample(num_samples, condition)`: Sample conditioned sequences

**Implementation Note:**
Concrete implementations should load pre-trained flow models from model repositories.

#### 5. **FlowDiffusionPipeline**
Main pipeline orchestrating flow generation and suggestion.

**Methods:**
- `suggest_flows()`: Generate interaction flow suggestions
- `register_state()`: Register TUI states
- `register_transition()`: Define valid transitions
- `set_state_cost()`: Set state preferences

**Example:**
```python
from eufle.motion import FlowDiffusionPipeline
import numpy as np

# Initialize pipeline
pipeline = FlowDiffusionPipeline(
    config_path="e:\\EUFLE\\eufle\\motion\\config.yaml"
)

# Register TUI states
for state_name in ["budget_overview", "expense_detail", "settings"]:
    embedding = np.random.randn(pipeline.config.embedding_dim)
    pipeline.register_state(state_name, embedding)

# Register transitions
pipeline.register_transition("budget_overview", "expense_detail")
pipeline.register_transition("budget_overview", "settings")

# Set preferences
pipeline.set_state_cost("budget_overview", 0.1)

# Get suggestions
flows, costs = pipeline.suggest_flows(
    num_suggestions=5,
    current_state="budget_overview",
    target_state="settings",
)
```

### Configuration (`config.yaml`)

```yaml
flow_diffusion:
  enabled: true
  model_type: "discrete_ddpm"
  sequence_length: 32
  embedding_dim: 128
  vocab_size: 256
  inference_steps: 50
  temperature: 0.8
  cost_weights:
    continuity: 1.0
    user_preference: 1.5
    task_completion: 2.0
```

### Integration Points

#### 1. **TUI Main Loop** (`eufle.py`)
```python
from eufle.motion import FlowDiffusionPipeline
import numpy as np

# In main TUI initialization
flow_pipeline = FlowDiffusionPipeline(
    config_path="eufle/motion/config.yaml"
)

# Register available TUI states/screens
tui_states = {
    "budget_overview": np.random.randn(128),
    "expense_detail": np.random.randn(128),
    "budget_edit": np.random.randn(128),
    "settings": np.random.randn(128),
}

for state_name, embedding in tui_states.items():
    flow_pipeline.register_state(state_name, embedding)

# In TUI interaction loop
def display_interaction_suggestions(current_state):
    flows, costs = flow_pipeline.suggest_flows(
        num_suggestions=3,
        current_state=current_state,
        preferred_states=user_preferences.get("preferred_states"),
        target_state=current_task.get("target_state"),
    )
    
    # Display top 3 suggestions to user
    for i, flow in enumerate(flows[:3]):
        print(f"Suggestion {i+1}: {' → '.join(flow[:5])}")
```

#### 2. **Budget Automation** (`scripts/budget_automation_refactored.py`)
```python
from eufle.motion import FlowDiffusionPipeline

# Initialize flow-guided task sequencing
flow_pipeline = FlowDiffusionPipeline()

# Define task-specific states and transitions
automation_states = {
    "data_load": 0.1,
    "analysis": 0.2,
    "budget_generation": 0.15,
    "validation": 0.3,
    "export": 0.25,
}

for state, cost in automation_states.items():
    flow_pipeline.set_state_cost(state, cost)

# Define workflow
flow_pipeline.register_transition("data_load", "analysis")
flow_pipeline.register_transition("analysis", "budget_generation")
flow_pipeline.register_transition("budget_generation", "validation")
flow_pipeline.register_transition("validation", "export")

# Get optimal flow for automation
flows, costs = flow_pipeline.suggest_flows(
    num_suggestions=1,
    current_state="data_load",
    target_state="export",
)

optimal_flow = flows[0]
for state in optimal_flow:
    execute_automation_step(state)
```

#### 3. **User Learning & Adaptation**
```python
from eufle.motion import InteractionCostFunction

# Track user preferences over time
cost_fn = InteractionCostFunction()

# Update costs based on user behavior logs
for state, usage_count in user_behavior.state_usage.items():
    # More frequently used states are cheaper (preferred)
    cost = 1.0 / (1.0 + usage_count)
    cost_fn.set_state_cost(state, cost)

# Suggest flows aligned with user's actual patterns
preferred_flows = cost_fn.find_low_cost_paths(start="budget_overview", end="export")
```

### Testing

Run unit tests:
```powershell
pytest e:\EUFLE\tests\test_flow_diffusion.py -v
```

Tests cover:
- Configuration loading
- State registration and embeddings
- Cost computations (continuity, preference, task completion)
- Transition validity and path costs
- Flow suggestion sampling and ranking
- Pipeline integration

---

## OpenCode Model Integration (Planned)

### Overview
The `opencode` model will be integrated to provide:
- **Enhanced trajectory prior learning**: Better diffusion priors from code motion patterns
- **Semantic flow understanding**: Code-aware interaction flow suggestions
- **Task-aware planning**: Code completion context for motion planning

### Integration Architecture

#### 1. **OpenCodePrior** (Planned Implementation)
A concrete `TrajectoryPrior` that loads pre-trained opencode models for motion planning.

**Planned Location:** `e:\grid\src\grid\motion\opencode_prior.py`

```python
from grid.motion.trajectory_diffusion import TrajectoryPrior
import pickle

class OpenCodePrior(TrajectoryPrior):
    """TrajectoryPrior using OpenCode big pickle model."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        
    def load(self, model_path: str) -> None:
        """Load pre-trained opencode model from pickle."""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def encode(self, trajectories: np.ndarray) -> torch.Tensor:
        """Encode trajectories using opencode model."""
        # Implementation with opencode model
        pass
    
    def decode(self, latents: torch.Tensor) -> np.ndarray:
        """Decode latents using opencode model."""
        # Implementation with opencode model
        pass
```

#### 2. **OpenCodeFlowPrior** (Planned Implementation)
A concrete `FlowPrior` for code-aware interaction sequences.

**Planned Location:** `e:\EUFLE\eufle\motion\opencode_flow_prior.py`

```python
from eufle.motion.flow_diffusion import FlowPrior

class OpenCodeFlowPrior(FlowPrior):
    """FlowPrior using OpenCode model for code-aware interaction sequences."""
    
    def load(self, model_path: str) -> None:
        """Load opencode model."""
        pass
    
    def sample(self, num_samples: int, condition: Optional[str] = None) -> np.ndarray:
        """Sample code-aware interaction sequences."""
        pass
```

#### 3. **Configuration Updates**

Update `grid/motion/config.yaml`:
```yaml
motion_diffusion:
  ...
  prior:
    type: "opencode"  # Use opencode model
    model_path: "models/opencode_big_pickle.pkl"
```

Update `eufle/motion/config.yaml`:
```yaml
flow_diffusion:
  ...
  prior:
    type: "opencode"
    model_path: "models/opencode_flow_model.pkl"
```

### Integration Steps

1. **Load opencode model architecture**
   - Verify pickle format and model structure
   - Create data loading utilities

2. **Implement OpenCodePrior**
   - Load from pickle file
   - Adapt to TrajectoryPrior interface
   - Test with GRID pipeline

3. **Implement OpenCodeFlowPrior**
   - Load from pickle file
   - Adapt to FlowPrior interface
   - Test with EUFLE pipeline

4. **Update configurations**
   - Point to opencode model paths
   - Set cost weights for opencode-specific costs

5. **Integration tests**
   - Test loading opencode models
   - Verify trajectory/flow generation with opencode priors
   - Performance benchmarking

---

## Running the Integration

### GRID Trajectory Diffusion

```powershell
# Basic usage
python -c "
from grid.motion import TrajectoryDiffusionPipeline
import numpy as np

pipeline = TrajectoryDiffusionPipeline('e:\grid\src\grid\motion\config.yaml')
trajectories, costs = pipeline.sample_trajectories(
    num_samples=32,
    trajectory_length=50,
    trajectory_dim=2,
    goal=np.array([5.0, 5.0])
)
print(f'Generated {len(trajectories)} trajectories')
print(f'Best cost: {costs[0]:.4f}')
"
```

### EUFLE Flow Diffusion

```powershell
# Basic usage
python -c "
from eufle.motion import FlowDiffusionPipeline
import numpy as np

pipeline = FlowDiffusionPipeline('e:\EUFLE\eufle\motion\config.yaml')

# Register states
for i in range(5):
    pipeline.register_state(f'state_{i}', np.random.randn(128))

flows, costs = pipeline.suggest_flows(
    num_suggestions=5,
    current_state='state_0'
)
print(f'Generated {len(flows)} flow suggestions')
"
```

### Run Tests

```powershell
# GRID tests
pytest e:\grid\tests\unit\test_trajectory_diffusion.py -v

# EUFLE tests
pytest e:\EUFLE\tests\test_flow_diffusion.py -v

# Combined
pytest e:\grid\tests\unit\test_trajectory_diffusion.py e:\EUFLE\tests\test_flow_diffusion.py -v
```

---

## Dependencies

Ensure the following packages are installed:

```
numpy>=1.21.0
torch>=1.9.0
pyyaml>=5.4
einops>=0.4.0
scipy>=1.7.0
pytest>=6.2.0
```

Install with:
```powershell
pip install numpy torch pyyaml einops scipy pytest
```

---

## Next Steps

1. ✅ Create GRID trajectory diffusion module
2. ✅ Create EUFLE flow diffusion module
3. ✅ Create configuration files
4. ✅ Create unit tests
5. ⏳ Integrate opencode model (awaiting model details)
6. ⏳ Add visualization tools (trajectory plots, flow diagrams)
7. ⏳ Performance benchmarking
8. ⏳ Integration with grid/patterns and scripts/budget_automation

---

## References

- **Motion Planning Diffusion**: Carvalho et al. (2023), arXiv:2308.01557
- **Diffusion Policy**: Chi et al. (2023)
- **Planning with Diffusion**: Janner et al. (2022)
- **3D Diffuser Actor**: https://github.com/nickgkan/3d_diffuser_actor
- **Diffusion Policy**: https://github.com/columbia-ai-robotics/diffusion_policy
- **Diffuser**: https://github.com/jannerm/diffuser
