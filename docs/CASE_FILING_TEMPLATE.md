# Case Filing Template - Complete Guide

## Overview

The Case Filing Template provides a comprehensive structure for case filing that combines all documentation elements from the agent evolution system, processing unit system, and agentic system.

## Template Structure

The template combines elements from:

1. **System Prompt** (`tools/agent_prompts/system_prompt.md`)
2. **Role Templates** (`tools/agent_prompts/role_templates.md`)
3. **Task Prompts** (`tools/agent_prompts/task_prompts.md`)
4. **Processing Unit System** (`docs/PROCESSING_UNIT_SYSTEM.md`)
5. **Agent Evolution System** (`docs/AGENT_EVOLUTION_SYSTEM.md`)
6. **Agentic System** (`grid/agentic/`)

## JSON Schema

The template is defined in `tools/agent_prompts/case_filing_template.json` with the following structure:

### Required Fields

- `case_id`: Unique case identifier
- `timestamp`: ISO8601 timestamp
- `raw_input`: Original user input
- `structured_data`: Structured case data

### Optional Fields

- `user_id`: User identifier
- `comprehensive_suite_mapping`: Mapping to agent evolution system
- `recommended_roles`: Recommended agent roles
- `recommended_tasks`: Recommended tasks
- `recommended_workflow`: Recommended workflow steps
- `context_for_agent`: Formatted context string
- `user_context`: User-provided context
- `metadata`: Case metadata
- `event_history`: List of events
- `execution_data`: Execution data
- `learning_data`: Learning data
- `advanced_protocols`: Advanced protocol data
- `reference_file_path`: Path to reference file
- `user_enrichments`: User enrichments

## Template Sections

### 1. Case Metadata

Basic case information:

```json
{
  "case_id": "CASE-abc123def456",
  "timestamp": "2025-01-08T10:00:00Z",
  "raw_input": "Add contract testing to CI pipeline",
  "user_id": "user123"
}
```

### 2. Structured Data

Categorized and structured input:

```json
{
  "structured_data": {
    "category": "testing",
    "priority": "high",
    "confidence": 0.85,
    "keywords": ["test", "ci", "contract"],
    "entities": ["CI", "Pipeline"],
    "relationships": [],
    "labels": ["category:testing", "priority:high"]
  }
}
```

### 3. Reference Mapping

Mapping to agent evolution system:

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

### 4. Agent Context

Formatted context for agent:

```json
{
  "context_for_agent": "Case Category: testing\nPriority: high\nConfidence: 0.85\n\nKeywords: test, ci, contract\n\nRecommended Roles: Executor, Evaluator"
}
```

### 5. Event History

Events emitted for this case:

```json
{
  "event_history": [
    "case.created",
    "case.categorized",
    "case.reference_generated"
  ]
}
```

### 6. Execution Data

Data filled after execution:

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

### 7. Learning Data

Data filled after completion:

```json
{
  "learning_data": {
    "experience_metrics": {
      "total_cases": 100,
      "success_rate": 0.85
    },
    "recommendations": [
      {
        "case_id": "CASE-xyz789",
        "similarity": 0.8,
        "recommended_solution": "Use pytest for contract tests"
      }
    ]
  }
}
```

## Usage

### Creating a Case File

```python
from tools.agent_prompts.processing_unit import ProcessingUnit
from pathlib import Path

processing_unit = ProcessingUnit(
    knowledge_base_path=Path("tools/agent_prompts"),
    reference_output_path=Path(".case_references")
)

result = processing_unit.process_input(
    raw_input="Add contract testing to CI",
    examples=["Similar setup in project X"],
    scenarios=["Run tests on every PR"]
)

# Reference file created at result.reference_file_path
```

### Loading a Case File

```python
import json
from pathlib import Path

reference_file = Path(".case_references/CASE-abc123_reference.json")
with open(reference_file) as f:
    case_data = json.load(f)

# Access data
category = case_data["structured_data"]["category"]
recommended_roles = case_data["recommended_roles"]
```

### Validating a Case File

```python
import jsonschema
import json

schema = json.load(open("tools/agent_prompts/case_filing_template.json"))
case_data = json.load(open(".case_references/CASE-abc123_reference.json"))

jsonschema.validate(case_data, schema)
```

## Integration

The template integrates with:

1. **Processing Unit**: Creates structured data
2. **Reference Generator**: Maps to comprehensive suite
3. **Agentic System**: Uses reference file for execution
4. **Event System**: Tracks event history
5. **Continuous Learning**: Records learning data

## References

- **JSON Schema**: `tools/agent_prompts/case_filing_template.json`
- **Markdown Template**: `tools/agent_prompts/case_filing_template.md`
- **Processing Unit**: `docs/PROCESSING_UNIT_SYSTEM.md`
- **Agentic System**: `docs/AGENTIC_SYSTEM.md`
