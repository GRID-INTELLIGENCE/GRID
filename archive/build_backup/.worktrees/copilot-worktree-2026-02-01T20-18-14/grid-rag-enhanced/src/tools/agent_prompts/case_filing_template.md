# Case Filing Template

Comprehensive template for case filing that combines all documentation elements from the agent evolution system, processing unit system, and agentic system.

## Template Structure

This template combines elements from:

- **System Prompt** (`tools/agent_prompts/system_prompt.md`) - System context and mission
- **Role Templates** (`tools/agent_prompts/role_templates.md`) - Role mappings and responsibilities
- **Task Prompts** (`tools/agent_prompts/task_prompts.md`) - Task definitions and workflows
- **Processing Unit System** (`docs/PROCESSING_UNIT_SYSTEM.md`) - Receptionist workflow
- **Agent Evolution System** (`docs/AGENT_EVOLUTION_SYSTEM.md`) - Evolution workflow
- **Agentic System** (`grid/agentic/`) - Event-driven processing

## Template Sections

### 1. Case Metadata

**Required Fields:**
- `case_id`: Unique identifier (format: `CASE-{hash}`)
- `timestamp`: ISO8601 timestamp
- `raw_input`: Original user input
- `user_id`: Optional user identifier

**Example:**
```json
{
  "case_id": "CASE-abc123def456",
  "timestamp": "2025-01-08T10:00:00Z",
  "raw_input": "Add contract testing to CI pipeline",
  "user_id": "user123"
}
```

### 2. Input Data

**Fields:**
- `raw_input`: Original user input
- `user_context`: Additional user context (examples, scenarios, phenomena)
- `examples`: User-provided examples
- `scenarios`: User-provided scenarios

**Example:**
```json
{
  "raw_input": "Add contract testing to CI pipeline",
  "user_context": {
    "examples": ["Similar setup in project X uses pytest"],
    "scenarios": ["Run tests on every PR, fail if schemas invalid"]
  }
}
```

### 3. Structured Data

**Fields:**
- `category`: Case category (from CaseCategory enum)
- `priority`: Priority level (low, medium, high, critical)
- `confidence`: Classification confidence (0.0-1.0)
- `keywords`: Extracted keywords
- `entities`: Extracted entities
- `relationships`: Detected relationships
- `labels`: Generated labels
- `logging_iterations`: Iterative logging data

**Example:**
```json
{
  "structured_data": {
    "category": "testing",
    "priority": "high",
    "confidence": 0.85,
    "keywords": ["test", "ci", "contract", "pipeline"],
    "entities": ["CI", "Pipeline"],
    "relationships": [],
    "labels": ["category:testing", "priority:high"],
    "logging_iterations": [
      {"iteration": 1, "keywords": ["test", "ci"]},
      {"iteration": 2, "category": "testing", "confidence": 0.85}
    ]
  }
}
```

### 4. Reference Mapping

**Fields:**
- `comprehensive_suite_mapping`: Mapping to agent evolution system
- `recommended_roles`: Recommended agent roles
- `recommended_tasks`: Recommended tasks
- `recommended_workflow`: Recommended workflow steps

**Example:**
```json
{
  "comprehensive_suite_mapping": {
    "category_mappings": {
      "roles": ["Executor", "Evaluator"]
    },
    "keyword_mappings": {
      "tasks": ["/inventory", "/execute", "/validate"]
    }
  },
  "recommended_roles": ["Executor", "Evaluator"],
  "recommended_tasks": ["/inventory", "/execute", "/validate"],
  "recommended_workflow": [
    "1. Run /inventory to discover system state",
    "2. Run /execute to generate artifacts",
    "3. Run /validate to verify changes"
  ]
}
```

### 5. Agent Context

**Field:**
- `context_for_agent`: Formatted context string for agent

**Example:**
```json
{
  "context_for_agent": "Case Category: testing\nPriority: high\nConfidence: 0.85\n\nKeywords: test, ci, contract, pipeline\n\nRecommended Roles: Executor, Evaluator\nRecommended Tasks: /inventory, /execute, /validate"
}
```

### 6. Event History

**Field:**
- `event_history`: List of events emitted

**Example:**
```json
{
  "event_history": [
    "case.created",
    "case.categorized",
    "case.reference_generated"
  ]
}
```

### 7. Execution Data

**Fields (filled after execution):**
- `agent_role`: Agent role used
- `task`: Task executed
- `solution`: Solution applied
- `outcome`: Outcome (success, partial, failure)
- `execution_time_seconds`: Execution time

**Example:**
```json
{
  "execution_data": {
    "agent_role": "Executor",
    "task": "/execute",
    "solution": "Added contract_test job to CI pipeline",
    "outcome": "success",
    "execution_time_seconds": 2.5
  }
}
```

### 8. Learning Data

**Fields (filled after completion):**
- `experience_metrics`: Aggregated experience metrics
- `patterns`: Common patterns identified
- `recommendations`: Recommendations from similar cases

**Example:**
```json
{
  "learning_data": {
    "experience_metrics": {
      "total_cases": 100,
      "success_rate": 0.85,
      "category_distribution": {"testing": 25}
    },
    "patterns": [
      {
        "category": "testing",
        "pattern_type": "solution",
        "pattern": "Add pytest tests",
        "frequency": 15
      }
    ],
    "recommendations": [
      {
        "case_id": "CASE-xyz789",
        "similarity": 0.8,
        "recommended_solution": "Use pytest for contract tests",
        "expected_outcome": "success"
      }
    ]
  }
}
```

## Complete Example

See `case_filing_template.json` for the complete JSON schema.

## Usage

### Creating a Case File

```python
from tools.agent_prompts.processing_unit import ProcessingUnit

processing_unit = ProcessingUnit(
    knowledge_base_path=Path("tools/agent_prompts"),
    reference_output_path=Path(".case_references")
)

result = processing_unit.process_input(
    raw_input="Add contract testing to CI",
    examples=["Similar setup in project X"],
    scenarios=["Run tests on every PR"]
)

# Reference file is automatically created at result.reference_file_path
```

### Loading a Case File

```python
import json
from pathlib import Path

reference_file = Path(".case_references/CASE-abc123_reference.json")
with open(reference_file) as f:
    case_data = json.load(f)

# Access structured data
category = case_data["structured_data"]["category"]
recommended_roles = case_data["recommended_roles"]
```

## Integration with Agent Evolution System

The template integrates with:

1. **System Prompt**: Provides mission and constraints context
2. **Role Templates**: Maps cases to agent roles
3. **Task Prompts**: Maps cases to executable tasks
4. **Processing Unit**: Creates structured data from raw input
5. **Agentic System**: Executes tasks using reference file
6. **Continuous Learning**: Records outcomes and learns patterns

## Validation

Use the JSON schema (`case_filing_template.json`) to validate case files:

```python
import jsonschema
import json

schema = json.load(open("tools/agent_prompts/case_filing_template.json"))
case_data = json.load(open(".case_references/CASE-abc123_reference.json"))

jsonschema.validate(case_data, schema)
```
