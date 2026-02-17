# GRID Architecture Enhancements

## Overview

This document describes the comprehensive enhancements made to GRID's architecture, focusing on real-time optimization, multi-org/multi-user support, source tracing, custom prompts, quantized architecture, extended senses, and periodic processing.

## Key Features

### 1. Source Tracing System (`grid/tracing/`)

Comprehensive action origin tracking with full auditability:

- **ActionTrace**: Complete action trace with provenance
- **TraceContext**: Context information (user, org, session, source location)
- **TraceManager**: Coordinates tracing across the system
- **TraceStore**: Persists traces with date-based organization

**Usage:**
```python
from grid.tracing import TraceManager, TraceOrigin

trace_manager = TraceManager()
with trace_manager.trace_action(
    action_type="api_request",
    action_name="process_data",
    origin=TraceOrigin.API_REQUEST,
    user_id="user123",
    org_id="org456"
) as trace:
    # Your code here
    trace.complete(success=True, output_data=result)
```

### 2. Multi-Org/Multi-User System (`grid/organization/`)

Complete organization and user management with discipline:

- **Organizations**: OpenAI, NVIDIA, Walt Disney Pictures (deep focus)
- **Users**: Role-based access (admin, manager, developer, analyst, viewer, guest)
- **Discipline**: Rules, violations, penalties, and automatic enforcement
- **Permissions**: Feature-based access control with org-specific settings

**Usage:**
```python
from grid.organization import OrganizationManager, OrganizationRole, UserRole

org_manager = OrganizationManager()
user = org_manager.create_user("john", org_id="openai", role=UserRole.DEVELOPER)
org_manager.check_user_permission(user.user_id, "feature_name", "openai")
```

### 3. Custom Prompts System (`grid/prompts/`)

User custom prompts as the primary source of truth:

- **Priority Order**: User custom > Org default > System default
- **Context Matching**: Operation type, domain, user/org context
- **Template Support**: Variable substitution and defaults
- **Usage Tracking**: Success rate and usage statistics

**Usage:**
```python
from grid.prompts import PromptManager, PromptSource, PromptPriority

prompt_manager = PromptManager()
prompt = prompt_manager.add_prompt(
    name="data_analysis",
    content="Analyze the following data: {data}",
    user_id="user123",
    source=PromptSource.USER_CUSTOM,
    priority=PromptPriority.HIGH
)
best_prompt = prompt_manager.get_prompt("data_analysis", user_id="user123")
```

### 4. Quantized Architecture (`grid/quantum/`)

Precise, dynamic, quantized architecture with locomotion:

- **Quantization Levels**: Coarse, Medium, Fine, Ultra-fine
- **State Transitions**: Discrete steps with parent-child relationships
- **Locomotion**: Movement in state space (forward, backward, left, right, up, down, rotate, scale)
- **Obstacle Avoidance**: Obstacle detection and navigation

**Usage:**
```python
from grid.quantum import QuantumEngine, QuantizationLevel, MovementDirection

engine = QuantumEngine(default_level=QuantizationLevel.FINE)
state = engine.initialize_state("state1", {"x": 0.0, "y": 0.0, "z": 0.0})
result = engine.move(MovementDirection.FORWARD, distance=1.0)
```

### 5. Extended Cognitive Senses (`grid/senses/`)

Support for extended cognitive senses beyond visual and audio:

- **Traditional**: Visual, Audio, Text
- **Extended**: Smell, Touch, Taste
- **Abstract**: Temperature, Pressure, Vibration, Proximity
- **Processing**: Type-specific processors for each sense

**Usage:**
```python
from grid.senses import SensoryInput, SensoryType, SensoryProcessor

processor = SensoryProcessor()
smell_input = SensoryInput(
    sensory_type=SensoryType.SMELL,
    data={"scent": "roses", "notes": "fresh"},
    intensity=0.8,
    quality="pleasant"
)
processed = processor.process(smell_input)
```

### 6. Periodic Processing (`grid/processing/`)

Periodic processing as default, with emergency real-time flows:

- **PeriodicProcessor**: Configurable intervals, batch processing, queue management
- **EmergencyRealtimeProcessor**: Throttled real-time processing for rare occasions
- **Flow Types**: Emergency, Alert, Critical Update, System Failure

**Usage:**
```python
from grid.processing import PeriodicProcessor, ProcessingSchedule, EmergencyRealtimeProcessor, RealtimeFlow

# Periodic processing (default)
schedule = ProcessingSchedule(interval_seconds=60.0, batch_size=100)
processor = PeriodicProcessor(schedule=schedule)
processor.set_processor(my_processing_function)
await processor.start()

# Emergency real-time (rare occasions)
realtime = EmergencyRealtimeProcessor()
realtime.register_handler(RealtimeFlow.EMERGENCY, emergency_handler)
result = realtime.process(RealtimeFlow.EMERGENCY, data, force=False)
```

### 7. Optimized Entry Points (`grid/entry_points/`)

Clean, readable entry points with full tracing:

- **APIEntryPoint**: FastAPI request handling with tracing
- **CLIEntryPoint**: CLI command handling with tracing
- **ServiceEntryPoint**: Service call handling with tracing

**Usage:**
```python
from grid.entry_points import APIEntryPoint

entry = APIEntryPoint()
result = await entry.handle_request(request, "process_data", data)
```

## Integration Example

```python
from grid import (
    TraceManager, OrganizationManager, PromptManager,
    QuantumEngine, SensoryProcessor, PeriodicProcessor,
    APIEntryPoint
)

# Initialize systems
trace_manager = TraceManager()
org_manager = OrganizationManager()
prompt_manager = PromptManager()
quantum_engine = QuantumEngine()
sensory_processor = SensoryProcessor()
periodic_processor = PeriodicProcessor()

# Create API entry point
api_entry = APIEntryPoint(
    trace_manager=trace_manager,
    org_manager=org_manager
)

# Use in FastAPI route
@app.post("/api/v1/process")
async def process_data(request: Request, data: dict):
    return await api_entry.handle_request(request, "process_data", data)
```

## Architecture Principles

1. **Source Tracing**: Every action is traced with full provenance
2. **Multi-Org Discipline**: Strict rules with automatic penalties
3. **Custom Prompts Priority**: User custom prompts are the primary source
4. **Quantized Locomotion**: Discrete state transitions with movement
5. **Extended Senses**: Full cognitive sensory support
6. **Periodic First**: Periodic processing default, real-time only for emergencies
7. **Clean Entry Points**: All entry points are optimized and readable

## File Organization

```
grid/
├── tracing/          # Source tracing system
├── organization/     # Multi-org/multi-user management
├── prompts/          # Custom prompts system
├── quantum/          # Quantized architecture
├── senses/           # Extended cognitive senses
├── processing/       # Periodic and real-time processing
└── entry_points/     # Optimized entry points
```

## Next Steps

1. Integrate tracing into existing services
2. Configure organization-specific rules
3. Set up user custom prompts
4. Implement quantized state transitions
5. Add sensory input processing
6. Configure periodic processing schedules
7. Update entry points in existing code
