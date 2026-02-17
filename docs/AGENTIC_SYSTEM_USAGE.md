# Agentic System - Usage Instructions

## Overview

The Event-Driven Agentic System implements a receptionist-lawyer-client workflow for processing user requests through structured case management, categorization, and agent execution with continuous learning.

## Quick Start

### 1. Start the API Server

```bash
# Start the FastAPI server
python -m application.mothership.main

# Or with uvicorn directly
uvicorn application.mothership.main:app --reload --port 8080
```

The agentic endpoints will be available at `/api/v1/agentic/*`

### 2. Create a Case (Receptionist Intake)

```bash
curl -X POST http://localhost:8080/api/v1/agentic/cases \
  -H "Content-Type: application/json" \
  -d '{
    "raw_input": "Add contract testing to CI pipeline",
    "examples": ["Similar setup in project X uses pytest"],
    "scenarios": ["Run tests on every PR, fail if schemas invalid"]
  }'
```

**Response:**
```json
{
  "case_id": "CASE-abc123def456",
  "status": "categorized",
  "category": "testing",
  "priority": "high",
  "confidence": 0.85,
  "reference_file_path": ".case_references/CASE-abc123def456_reference.json",
  "events": ["case.created", "case.categorized", "case.reference_generated"],
  "created_at": "2025-01-08T10:00:00Z"
}
```

### 3. Get Case Status

```bash
curl http://localhost:8080/api/v1/agentic/cases/CASE-abc123def456
```

### 4. Enrich Case (Optional)

```bash
curl -X POST http://localhost:8080/api/v1/agentic/cases/CASE-abc123def456/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "additional_context": "We use GitHub Actions for CI",
    "examples": ["See .github/workflows/test.yml"],
    "scenarios": ["Tests run on push and PR"]
  }'
```

### 5. Execute Case (Lawyer Processes Case)

```bash
curl -X POST http://localhost:8080/api/v1/agentic/cases/CASE-abc123def456/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_role": "Executor",
    "task": "/execute"
  }'
```

**Response:**
```json
{
  "case_id": "CASE-abc123def456",
  "status": "completed",
  "outcome": "success",
  "solution": "Added contract_test job to CI pipeline",
  "execution_time_seconds": 2.5,
  "events": ["case.created", "case.categorized", "case.reference_generated", "case.executed", "case.completed"]
}
```

### 6. Get Reference File

```bash
curl http://localhost:8080/api/v1/agentic/cases/CASE-abc123def456/reference
```

### 7. Get Agent Experience Summary

```bash
curl http://localhost:8080/api/v1/agentic/experience
```

**Response:**
```json
{
  "total_cases": 100,
  "success_rate": 0.85,
  "category_distribution": {
    "testing": 25,
    "architecture": 20,
    "bug_fix": 15
  },
  "experience_by_category": {
    "testing": {
      "total": 25,
      "successes": 22,
      "success_rate": 0.88
    }
  },
  "common_patterns": [],
  "learning_insights": [
    "Processed 100 cases total",
    "High success rate (85%) - system performing well"
  ]
}
```

## Python API Usage

### Using Processing Unit Directly

```python
from pathlib import Path
from tools.agent_prompts.processing_unit import ProcessingUnit

# Initialize processing unit
processing_unit = ProcessingUnit(
    knowledge_base_path=Path("tools/agent_prompts"),
    reference_output_path=Path(".case_references")
)

# Process input
result = processing_unit.process_input(
    raw_input="Add contract testing to CI",
    examples=["Similar setup in project X"],
    scenarios=["Run tests on every PR"]
)

print(f"Case ID: {result.case_id}")
print(f"Category: {result.category.value}")
print(f"Reference File: {result.reference_file_path}")
```

### Using Agentic System Directly

```python
from pathlib import Path
from grid.agentic import AgenticSystem
from grid.agentic.event_bus import get_event_bus

# Initialize agentic system
event_bus = get_event_bus()
agentic_system = AgenticSystem(
    knowledge_base_path=Path("tools/agent_prompts"),
    event_bus=event_bus,
    repository=None  # Or provide Databricks repository
)

# Execute case
result = await agentic_system.execute_case(
    case_id="CASE-abc123",
    reference_file_path=".case_references/CASE-abc123_reference.json",
    agent_role="Executor",
    task="/execute"
)

print(f"Outcome: {result['outcome']}")
print(f"Execution Time: {result['execution_time_seconds']}s")
```

### Using Event Bus

```python
from grid.agentic.event_bus import EventBus
from grid.agentic.events import CaseCreatedEvent

# Create event bus
event_bus = EventBus(use_redis=False)  # Set use_redis=True for distributed systems

# Subscribe to events
async def handle_case_created(event):
    print(f"Case created: {event['case_id']}")

await event_bus.subscribe("case.created", handle_case_created)

# Publish event
event = CaseCreatedEvent(
    case_id="CASE-001",
    raw_input="Test input"
)
await event_bus.publish(event.to_dict())
```

## Event Types

The system emits 5 event types:

1. **`case.created`**: Raw input received
2. **`case.categorized`**: Case filed and categorized
3. **`case.reference_generated`**: Reference file created
4. **`case.executed`**: Agent started execution
5. **`case.completed`**: Case resolved

## Case Categories

Cases are automatically categorized into one of 12 categories:

- `code_analysis` - Code analysis and review
- `architecture` - Architecture decisions
- `testing` - Testing and test infrastructure
- `documentation` - Documentation tasks
- `deployment` - Deployment and DevOps
- `security` - Security-related tasks
- `performance` - Performance optimization
- `bug_fix` - Bug fixes
- `feature_request` - New features
- `refactoring` - Code refactoring
- `integration` - Integration tasks
- `rare` - Rare/unusual cases

## Agent Roles

The system supports 6 agent roles:

- **Analyst**: Inventory and state report generation
- **Architect**: Interface and contract audit
- **Planner**: Prioritized backlog creation
- **Executor**: Code artifacts and PR generation
- **Evaluator**: Validation and metrics
- **SafetyOfficer**: Governance and risk assessment

## Tasks

Available tasks:

- `/inventory` - System discovery
- `/gapanalysis` - Gap identification
- `/plan` - Planning and backlog creation
- `/execute` - Code generation and execution
- `/validate` - Validation and testing
- `/safety review` - Safety and governance review

## Configuration

### Environment Variables

```bash
# Databricks (optional)
USE_DATABRICKS=true
DATABRICKS_SERVER_HOSTNAME=your-hostname.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your-token

# Redis (optional, for distributed event bus)
REDIS_HOST=localhost
REDIS_PORT=6379
USE_REDIS=true
```

### Database Setup

For Databricks integration, ensure your database is configured in `application/mothership/config.py`:

```python
database:
  use_databricks: true
  url: "databricks://token:your-token@your-hostname.cloud.databricks.com:443/default"
```

## Advanced Usage

### Custom Event Handlers

```python
from grid.agentic.event_handlers import BaseEventHandler

class CustomHandler(BaseEventHandler):
    async def handle(self, event):
        print(f"Handled event: {event['event_type']}")

# Register handler
from grid.agentic.event_handlers import EventHandlerRegistry

registry = EventHandlerRegistry()
registry.register("case.completed", CustomHandler())

# Handle event
await registry.handle_event(event_dict)
```

### Continuous Learning

```python
from tools.agent_prompts.databricks_learning import DatabricksLearningSystem
from application.mothership.repositories.agentic import AgenticRepository

# Initialize learning system
repository = AgenticRepository(session)
learning_system = DatabricksLearningSystem(repository)

# Record case completion
await learning_system.record_case_completion(
    case_id="CASE-001",
    structure=case_structure,
    solution="Solution applied",
    outcome="success",
    agent_experience={"time_taken": "2 hours"}
)

# Get recommendations
recommendations = await learning_system.get_recommendations(case_structure)
```

## Troubleshooting

### Case Not Found

If you get a 404 error, ensure:
- Case ID is correct
- Case was created successfully
- Database connection is working

### Event Bus Not Working

If events aren't being processed:
- Check event bus initialization
- Verify handlers are registered
- Check logs for errors

### Databricks Connection Issues

If Databricks integration fails:
- Verify credentials are correct
- Check network connectivity
- Ensure warehouse is running
- Check logs for detailed errors

## Performance Optimization

### Event Bus Performance

- Use Redis for distributed systems
- Batch event processing when possible
- Monitor event queue size

### Database Performance

- Use connection pooling
- Index frequently queried fields
- Use async operations

### Case Processing Performance

- Cache reference files
- Use async processing
- Batch similar cases

## Best Practices

1. **Always provide context**: Include examples and scenarios when creating cases
2. **Use appropriate categories**: Help the system categorize correctly
3. **Monitor events**: Subscribe to events for observability
4. **Track experience**: Use continuous learning for improvements
5. **Handle errors gracefully**: Implement proper error handling
6. **Use async operations**: Leverage async/await for better performance

## References

- **System Documentation**: `docs/AGENTIC_SYSTEM.md`
- **Case Filing Template**: `docs/CASE_FILING_TEMPLATE.md`
- **Event Architecture**: `docs/EVENT_DRIVEN_ARCHITECTURE.md`
- **API Reference**: `application/mothership/routers/agentic.py`
