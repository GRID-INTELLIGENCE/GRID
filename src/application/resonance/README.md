# Activity Resonance Tool

**Left-to-Right Communication System for GRID**

A tool that communicates from left to right, providing fast context from `application/` and vivid path visualization from `light_of_the_seven/` with ADSR envelope feedback.

## Overview

The Activity Resonance Tool addresses the balance gap in triages that creates option-fueled choice confusion. It provides:

- **Left Side (application/)**: Fast, concise context when decision/attention metrics are tense
- **Right Side (light_of_the_seven/)**: Path visualization with 3-4 options, showing input/output scenarios
- **ADSR Envelope**: Haptic-like feedback (attack, decay, sustain, release) like a pluck in a string
- **Synchronous-like Feedback**: Mitigates asyncio constraints with real-time updates

## Architecture

The Resonance API follows a **layered architecture** pattern (aligned with Mothership reference architecture):

```
application/resonance/
├── routers/          # API endpoints (FastAPI routes)
│   └── router.py     # REST endpoints and WebSocket handlers
├── services/         # Business logic layer
│   └── __init__.py   # ResonanceService facade + sub-services
├── repositories/     # Data access layer
│   └── __init__.py   # Repositories + Unit of Work pattern
├── api/              # API-specific (schemas, dependencies)
│   ├── schemas.py    # Request/Response schemas (Pydantic v2)
│   ├── dependencies.py  # FastAPI dependency injection
│   └── websocket.py  # WebSocket endpoint handlers
└── [core components] # Domain logic
    ├── activity_resonance.py  # Main orchestrator
    ├── context_provider.py    # Context provider
    ├── path_visualizer.py     # Path visualization
    └── adsr_envelope.py       # ADSR envelope metrics
```

### Architecture Layers

1. **Router Layer** (`api/router.py`)
   - FastAPI REST endpoints
   - WebSocket support for real-time updates
   - Request/Response validation (Pydantic v2)
   - Error handling with standardized error responses

2. **Service Layer** (`services/__init__.py`)
   - **ResonanceService** (facade): Coordinates all sub-services
   - **ActivityService**: Activity lifecycle management
   - **ContextService**: Context operations
   - **PathService**: Path triage operations
   - **EnvelopeService**: Envelope metrics
   - **EventService**: Event operations
   - **StateService**: State management

3. **Repository Layer** (`repositories/__init__.py`)
   - **ResonanceUnitOfWork**: Coordinates all repositories
   - **ActivityRepository**: ActivityResonance storage
   - **EventRepository**: ActivityEvent storage
   - **StateRepository**: ResonanceState storage
   - **ResonanceStateStore**: In-memory state store

4. **Domain Layer** (Core components)
   - **ContextProvider** (`context_provider.py`)
     - Fast context from `application/` directory
     - Assesses sparsity, attention tension, decision pressure
     - Provides vivid explanations when context is sparse

   - **PathVisualizer** (`path_visualizer.py`)
     - Path triage from `light_of_the_seven/` directory
     - Generates 3-4 path options with complexity, time, confidence
     - Shows input/output scenarios for each path

   - **ADSREnvelope** (`adsr_envelope.py`)
     - Models attack, decay, sustain, release phases
     - Provides amplitude and velocity metrics
     - Like a pluck in a string defining vibration and waves

   - **ActivityResonance** (`activity_resonance.py`)
     - Main orchestrator
     - Coordinates left-to-right communication
     - Manages event/activity tracking
     - Provides synchronous-like feedback

5. **CLI** (`cli.py`)
   - Terminal interface
   - PowerShell integration
   - Real-time feedback display

### Design Patterns

- **Service Facade Pattern**: `ResonanceService` coordinates sub-services
- **Repository Pattern**: Clean data access with Unit of Work
- **Dependency Injection**: FastAPI dependency injection for services and repositories
- **Layered Architecture**: Routers → Services → Repositories → Domain Models

## Usage

### Python CLI

```bash
# Basic usage
python -m application.resonance.cli "create a new service"

# Code activity
python -m application.resonance.cli "add authentication endpoint" --type code

# Config activity
python -m application.resonance.cli "configure database" --type config

# JSON output
python -m application.resonance.cli "implement feature" --json

# Show only paths (no context)
python -m application.resonance.cli "implement feature" --no-context

# Show only context (no paths)
python -m application.resonance.cli "implement feature" --no-paths
```

### PowerShell

```powershell
# Basic usage
.\application\resonance\resonance.ps1 "create a new service"

# With type
.\application\resonance\resonance.ps1 "add endpoint" -Type code

# JSON output
.\application\resonance\resonance.ps1 "configure" -Json

# With context
.\application\resonance\resonance.ps1 "implement" -Context '{"urgency": true}'
```

### Programmatic Usage

#### Direct Usage (Domain Layer)

```python
from application.resonance import ActivityResonance, ResonanceFeedback

def feedback_handler(feedback: ResonanceFeedback) -> None:
    print(f"State: {feedback.state} | {feedback.message}")

# Initialize
resonance = ActivityResonance(feedback_callback=feedback_handler)

# Start feedback loop
resonance.start_feedback_loop(interval=0.05)

# Process activity
feedback = resonance.process_activity(
    activity_type="code",
    query="create a new service",
    context={"urgency": True}
)

# Complete activity
resonance.complete_activity()
```

#### API Service Layer Usage

```python
from application.resonance.services import ResonanceService
from application.resonance.repositories import get_unit_of_work

# Initialize service with Unit of Work
uow = get_unit_of_work()
service = ResonanceService(uow=uow)

# Process activity (uses service facade)
activity_id, feedback = service.process_activity(
    query="create a new service",
    activity_type="code",
    context={"urgency": True}
)

# Get context (delegates to ContextService)
context = service.get_context(query="database configuration")

# Get path triage (delegates to PathService)
paths = service.get_path_triage(goal="implement authentication")

# Get envelope metrics (delegates to EnvelopeService)
metrics = service.get_envelope_metrics(activity_id)

# Get events (delegates to EventService)
events = service.get_activity_events(activity_id, limit=10)

# Cleanup (delegates to ActivityService)
service.cleanup_activity(activity_id)
```

## ADSR Envelope

The ADSR envelope provides haptic-like feedback:

- **Attack**: Initial response, quick rise (0.1s default)
- **Decay**: Settle to working level (0.2s default)
- **Sustain**: Maintained feedback during activity (0.7 amplitude)
- **Release**: Fade when activity completes (0.3s default)

The envelope metrics include:
- `amplitude`: Current amplitude (0.0 to 1.0)
- `velocity`: Rate of change
- `phase`: Current phase (attack/decay/sustain/release/idle)
- `time_in_phase`: Time in current phase
- `peak_amplitude`: Peak reached during attack

## Context Metrics

The context provider assesses:

- **Sparsity**: How much context is missing (0.0 = dense, 1.0 = sparse)
- **Attention Tension**: Urgency and complexity (0.0 = relaxed, 1.0 = tense)
- **Decision Pressure**: How many choices/options (0.0 = low, 1.0 = high)
- **Clarity**: How clear the query is (0.0 = unclear, 1.0 = clear)
- **Confidence**: How confident we can be (0.0 = uncertain, 1.0 = confident)

## Path Triage

The path visualizer generates 3-4 options:

1. **Direct/Simple**: Minimal setup, quick implementation
2. **Incremental**: Build with testing at each step
3. **Pattern-Based**: Follow established patterns
4. **Comprehensive**: Full-featured, production-ready

Each option includes:
- Complexity level (simple/moderate/complex/very_complex)
- Estimated time
- Confidence score
- Input/output scenarios
- Step-by-step breakdown

## Output Format

### Human-Readable

```
================================================================================
🎯 ACTIVITY RESONANCE - LEFT TO RIGHT COMMUNICATION
================================================================================

🟢 State: ACTIVE | Urgency: 45%

--------------------------------------------------------------------------------
📋 LEFT: FAST CONTEXT (application/)
--------------------------------------------------------------------------------
Source: application/code
Service context: Check services/ directory, dependency injection patterns.

📊 Metrics:
   Sparsity: 30% | Attention Tension: 50% | Decision Pressure: 40%
   Clarity: 90% | Confidence: 80%

--------------------------------------------------------------------------------
🛤️  RIGHT: PATH VISUALIZATION (light_of_the_seven/)
--------------------------------------------------------------------------------
Goal: create a new service

⭐ RECOMMENDED PATH:
📊 Path: Incremental Build
   Complexity: moderate
   Time: 10.0s
   Confidence: 90%

📥 Input:
   Evolving requirements, need for validation

🔄 Steps:
   1. Create skeleton structure
   2. Add core functionality
   3. Write tests
   4. Iterate and refine

📤 Output:
   Tested, validated implementation
```

### JSON

```json
{
  "state": "active",
  "urgency": 0.45,
  "message": "🎯 Recommended: Incremental Build (moderate, 10.0s)",
  "context": {
    "content": "Service context: Check services/ directory...",
    "source": "application/code",
    "metrics": {
      "sparsity": 0.3,
      "attention_tension": 0.5,
      "decision_pressure": 0.4,
      "clarity": 0.9,
      "confidence": 0.8
    }
  },
  "paths": {
    "goal": "create a new service",
    "total_options": 4,
    "recommended": {
      "id": "incremental",
      "name": "Incremental Build",
      "complexity": "moderate",
      "estimated_time": 10.0,
      "confidence": 0.9
    }
  }
}
```

## Integration

The tool integrates with:

- **application/**: Fast context provider
- **light_of_the_seven/**: Path visualization and cognitive layer
- **PowerShell**: Terminal execution
- **Event System**: Activity tracking and feedback

## Future Enhancements

- Real-time WebSocket feedback
- Integration with cognitive layer decision support
- Customizable ADSR envelope parameters
- Path execution and validation
- Historical activity tracking

## License

Part of the GRID project.
