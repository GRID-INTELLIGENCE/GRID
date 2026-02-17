# Cognitive Layer

This `light_of_the_seven/cognitive_layer/` directory contains the cognitive architecture for GRID, providing decision support, mental models, and navigation capabilities.

## Directory Structure

```
cognitive_layer/
├── cognitive_load/      # Cognitive load assessment and management
├── decision_support/    # Decision-making assistance
├── integration/         # Integration utilities
├── mental_models/       # Mental model representations
├── navigation/          # Navigation Agent System (NEW)
│   ├── agents/          # Agent implementations
│   ├── learning/        # Learning infrastructure
│   └── schemas/         # Pydantic input schemas
└── schemas/             # General cognitive schemas
```

## Navigation Agent System

The Navigation Agent System provides adaptive path optimization with learning capabilities, targeting 95%+ path selection accuracy through continuous learning.

### Key Components

- **NavigationRequest**: Structured input schema for navigation goals
- **EnhancedPathNavigator**: Learning-enabled path navigation
- **PathOptimizationAgent**: Agent for adaptive path scoring
- **AgentRegistry**: Centralized agent lifecycle management
- **LearningStorage**: Persistent storage for learning data
- **AdaptiveScorer**: Multi-factor scoring with learned weights
- **EventBusAdapter**: Integration with GRID's EventBus

### Quick Start

```python
from light_of_the_seven.cognitive_layer.navigation import (
    EnhancedPathNavigator,
    NavigationRequest,
    NavigationGoal,
    NavigationContext,
    GoalType,
    UrgencyLevel,
)

# Simple string input (backward compatible)
navigator = EnhancedPathNavigator()
plan = navigator.navigate_simple("Create a new API endpoint for authentication")

# Structured input
goal = NavigationGoal(
    goal_type=GoalType.DEVELOPMENT,
    primary_objective="Implement user authentication API",
    success_criteria=["JWT token generation", "Password validation"]
)
context = NavigationContext(urgency=UrgencyLevel.HIGH)
request = NavigationRequest(goal=goal, context=context)
plan = navigator.navigate(request)

print(f"Recommended path: {plan.recommended_path.name}")
print(f"Confidence: {plan.confidence_scores[plan.recommended_path.id]:.1%}")
```

### Using the Path Optimization Agent

```python
from light_of_the_seven.cognitive_layer.navigation import (
    PathOptimizationAgent,
    AgentRegistry,
)

# Create and register agent
registry = AgentRegistry()
agent = PathOptimizationAgent()
registry.register(agent, auto_start=True)

# Process request (async)
result = await agent.execute(request)
print(f"Recommended: {result.recommended_path_id}")
print(f"Confidence: {result.confidence:.1%}")

# Learn from outcome
agent.learn({
    "request_id": request.request_id,
    "success": True,
    "selected_path_id": result.recommended_path_id,
    "execution_time_ms": 1500.0,
    "user_rating": 5,
})
```

### Input Formats

The navigation system supports multiple input formats:

1. **Simple String**: Natural language goal description
2. **Dictionary**: Structured dict with goal and context
3. **NavigationRequest**: Full Pydantic-validated request

```python
from light_of_the_seven.cognitive_layer.navigation import NavigationInputProcessor

processor = NavigationInputProcessor()

# String input
request = processor.process("Fix the memory leak in data processing")

# Dictionary input
request = processor.process({
    "goal": {
        "goal_type": "debugging",
        "primary_objective": "Fix memory leak in module X",
    },
    "context": {"urgency": "high"}
})
```

### Goal Types

- `DEVELOPMENT`: Code creation/modification
- `ANALYSIS`: Data processing/inspection
- `DEBUGGING`: Error resolution
- `OPTIMIZATION`: Performance improvement
- `INTEGRATION`: System connection
- `MAINTENANCE`: Updates/fixes
- `EXPLORATION`: Discovery/research
- `REFACTORING`: Code restructuring

### Success Metrics

The Navigation Agent System targets:
- **Path selection accuracy**: >95%
- **Learning effectiveness**: Measurable improvement over time
- **User satisfaction**: >4.0/5.0

## Canonical Import Paths

- **Navigation**: `light_of_the_seven.cognitive_layer.navigation`
- **Decision Support**: `light_of_the_seven.cognitive_layer.decision_support`
- **Cognitive Load**: `light_of_the_seven.cognitive_layer.cognitive_load`
- **Mental Models**: `light_of_the_seven.cognitive_layer.mental_models`

## Documentation

- **Main Guide**: `docs/COGNITIVE_LAYER.md`
- **Navigation Scaffold**: `Scaffold Path Optimization Agent.md`
- **Architecture**: `docs/architecture.md`

## Related Modules

- **PathVisualizer**: `application/resonance/path_visualizer.py`
- **ContextProvider**: `application/resonance/context_provider.py`
- **EventBus**: `Arena/the_chase/python/src/the_chase/core/event_bus.py`
