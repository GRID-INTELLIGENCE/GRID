# Agentic System - Complete Documentation

## Overview

The Agentic System is an event-driven, request-response system that implements the receptionist-lawyer-client scenario. It provides structured processing of user input, categorization, reference file generation, and agent execution with continuous learning.

## Architecture

The system follows a layered architecture:

```
Client Layer (User)
    ↓
FastAPI REST API
    ↓
Processing Layer (Receptionist)
    ↓
Agent Layer (Lawyer)
    ↓
Event Layer (Event Bus)
    ↓
Data Layer (Databricks)
```

## Core Components

### 1. Event System (`grid/agentic/events.py`)

Event definitions for case lifecycle:

- **CaseCreatedEvent**: Raw input received
- **CaseCategorizedEvent**: Case filed and categorized
- **CaseReferenceGeneratedEvent**: Reference file created
- **CaseExecutedEvent**: Agent started execution
- **CaseCompletedEvent**: Case resolved

### 2. Event Bus (`grid/agentic/event_bus.py`)

Async event bus with Redis pub-sub support:

- Async event publishing
- Event subscription (by type or all events)
- Event history and replay
- In-memory queue fallback

### 3. Event Handlers (`grid/agentic/event_handlers.py`)

Handlers for case lifecycle events:

- **CaseCreatedHandler**: Store case in Databricks
- **CaseCategorizedHandler**: Update case status
- **CaseReferenceGeneratedHandler**: Notify agent system
- **CaseExecutedHandler**: Track execution start
- **CaseCompletedHandler**: Store solution and update learning

### 4. Agentic System (`grid/agentic/agentic_system.py`)

Main orchestrator:

- Receives reference files
- Executes agent tasks
- Emits events
- Integrates with repository and learning system

### 5. Agent Executor (`grid/agentic/agent_executor.py`)

Executes agent tasks:

- Loads reference files
- Determines agent role and task
- Executes task handlers
- Returns execution results

### 6. Databricks Integration

**Models** (`application/mothership/db/models_agentic.py`):
- `AgenticCase`: SQLAlchemy model for cases

**Repository** (`application/mothership/repositories/agentic.py`):
- `create_case()`: Insert new case
- `get_case()`: Retrieve case by ID
- `update_case_status()`: Update case status
- `find_similar_cases()`: Query similar cases
- `get_agent_experience()`: Aggregate experience metrics

### 7. FastAPI REST API (`application/mothership/routers/agentic.py`)

Endpoints:

- `POST /api/v1/agentic/cases` - Create case
- `GET /api/v1/agentic/cases/{case_id}` - Get case status
- `POST /api/v1/agentic/cases/{case_id}/enrich` - Enrich case
- `POST /api/v1/agentic/cases/{case_id}/execute` - Execute case
- `GET /api/v1/agentic/cases/{case_id}/reference` - Get reference file
- `GET /api/v1/agentic/experience` - Get agent experience

### 8. Continuous Learning (`tools/agent_prompts/databricks_learning.py`)

Databricks-backed learning system:

- Records case completions in Databricks
- Queries Databricks for similar cases
- Provides recommendations
- Tracks agent experience metrics

## Workflow

### Standard Case Processing

```
1. User sends POST /api/v1/agentic/cases
   ↓
2. Processing Unit receives raw input
   ↓
3. Case Filing System categorizes input
   ↓
4. Reference Generator creates reference file
   ↓
5. Events emitted: case.created, case.categorized, case.reference_generated
   ↓
6. User calls POST /api/v1/agentic/cases/{case_id}/execute
   ↓
7. Agentic System executes case
   ↓
8. Events emitted: case.executed, case.completed
   ↓
9. Learning System records completion
```

### Event Flow

```
Processing Unit → Event Bus → Event Handlers → Databricks Repository
                                    ↓
                            Continuous Learning
```

## Usage Examples

### Create Case

```python
import requests

response = requests.post(
    "http://localhost:8080/api/v1/agentic/cases",
    json={
        "raw_input": "Add contract testing to CI pipeline",
        "examples": ["Similar setup in project X"],
        "scenarios": ["Run tests on every PR"]
    }
)

case = response.json()
case_id = case["case_id"]
```

### Execute Case

```python
response = requests.post(
    f"http://localhost:8080/api/v1/agentic/cases/{case_id}/execute",
    json={
        "agent_role": "Executor",
        "task": "/execute"
    }
)

result = response.json()
```

### Get Experience

```python
response = requests.get(
    "http://localhost:8080/api/v1/agentic/experience"
)

experience = response.json()
print(f"Total cases: {experience['total_cases']}")
print(f"Success rate: {experience['success_rate']:.1%}")
```

## Integration Points

### With Processing Unit

The processing unit emits events during case processing:

```python
from grid.agentic.event_bus import get_event_bus
from tools.agent_prompts.processing_unit import ProcessingUnit

event_bus = get_event_bus()
processing_unit = ProcessingUnit(
    knowledge_base_path=Path("tools/agent_prompts"),
    reference_output_path=Path(".case_references"),
    event_bus=event_bus
)
```

### With Databricks

Cases are stored in Databricks `agentic_cases` table:

```python
from application.mothership.repositories.agentic import AgenticRepository
from application.mothership.db.engine import get_async_sessionmaker

sessionmaker = get_async_sessionmaker()
async with sessionmaker() as session:
    repository = AgenticRepository(session)
    case = await repository.get_case("CASE-001")
```

### With Continuous Learning

Learning system queries Databricks for recommendations:

```python
from tools.agent_prompts.databricks_learning import DatabricksLearningSystem

learning_system = DatabricksLearningSystem(repository)
recommendations = await learning_system.get_recommendations(structure)
```

## Event Schema

All events follow this structure:

```json
{
  "event_type": "case.created",
  "case_id": "CASE-abc123",
  "timestamp": "2025-01-08T10:00:00Z",
  "metadata": {}
}
```

## Database Schema

The `agentic_cases` table stores:

- Case metadata (ID, timestamps, status)
- Input data (raw_input, user_id)
- Categorization (category, priority, confidence)
- Structured data (JSON)
- Execution data (agent_role, task, outcome, solution)
- Learning data (agent_experience JSON)

## Testing

Run tests:

```bash
pytest tests/test_agentic_system.py
pytest tests/test_event_bus.py
pytest tests/test_event_handlers.py
pytest tests/test_agentic_api.py
pytest tests/test_databricks_agentic.py
```

## Configuration

### Environment Variables

- `USE_DATABRICKS`: Enable Databricks (true/false)
- `DATABRICKS_SERVER_HOSTNAME`: Databricks hostname
- `DATABRICKS_HTTP_PATH`: HTTP path
- `DATABRICKS_ACCESS_TOKEN`: Access token

### Event Bus Configuration

- `REDIS_HOST`: Redis hostname (optional)
- `REDIS_PORT`: Redis port (optional)
- `USE_REDIS`: Enable Redis pub-sub (optional)

## References

- **Processing Unit System**: `docs/PROCESSING_UNIT_SYSTEM.md`
- **Agent Evolution System**: `docs/AGENT_EVOLUTION_SYSTEM.md`
- **Case Filing Template**: `docs/CASE_FILING_TEMPLATE.md`
- **Event-Driven Architecture**: `docs/EVENT_DRIVEN_ARCHITECTURE.md`
