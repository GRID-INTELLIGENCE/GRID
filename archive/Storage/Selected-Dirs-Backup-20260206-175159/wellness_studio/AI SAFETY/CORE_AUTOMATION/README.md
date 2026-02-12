# CORE_AUTOMATION

## Overview
CORE_AUTOMATION is the central orchestration layer for the AI Safety Engine. It provides shared infrastructure for safety detection, rule evaluation, action execution, and notification delivery across all AI providers.

## Architecture

```
Provider Source Updates
        ↓
Monitoring Engine (diffs, logs)
        ↓
Core Rule Engine (shared)
        ↓
Action + Remediation
        ↓
Provider Protocol Update
        ↓
Cross-Provider Governance
```

**Key Principle:** All provider-specific changes must feed back into CORE_AUTOMATION for consistency and auditability.

## Components

### 1. Rules (`rules/`)
Detection logic and safety rules that apply across providers.
- `SAFETY_RULES_AND_TRIGGERS.json` - Shared safety rules and trigger definitions

### 2. Thresholds (`thresholds/`)
Severity triggers for risk assessment.
- Provider-specific thresholds for different risk levels

### 3. Actions (`actions/`)
Remediation behaviors and action definitions.
- `ACTIONS_MATRIX.json` - Shared action catalog and mappings

### 4. Schemas (`schemas/`)
Structured data contracts for safety artifacts.
- `item_record.schema.yml` - Schema for safety item records
- `remediation_task.schema.yml` - Schema for remediation tasks
- `scenario_record.schema.yml` - Schema for scenario records

### 5. Notifications (`notifications/`)
Templated communication for safety alerts.
- Notification templates for different severity levels

### 6. Engines (`engines/`)
Core execution engines for safety automation.
- `monitoring_README.md` - Monitoring engine documentation
- `monitoring_config.json` - Monitoring configuration
- `monitoring_log_schema.json` - Log schema
- `run_monitoring.py` - Monitoring execution script

## Nuanced Safety Logic

The system avoids overreaction:
- **Single keyword mention ≠ escalation**
- **Risk depends on domain sensitivity**
- **Severity depends on evidence + magnitude**

Enforced via:
- **Threshold tiers**
- **Nuance rules**
- **Human review escalation**

## Success Criteria

- Automated detection of safety-relevant changes
- Reliable severity classification
- Evidence-backed remediation
- Transparent reporting
- Cross-provider consistency
- Provider-specific framework integration

## Usage

### Running the Monitoring Engine

```bash
python engines/run_monitoring.py
```

### Loading Safety Rules

```python
import json

with open('rules/SAFETY_RULES_AND_TRIGGERS.json') as f:
    rules = json.load(f)
```

### Executing Actions

```python
from core_automation import ActionEngine

engine = ActionEngine()
result = engine.execute_action("BLOCK_CONTENT", context={...})
```

## Provider Integration

Each provider (OpenAI, Anthropic, Google, xAI, Mistral, NVIDIA, Llama) integrates with CORE_AUTOMATION by:

1. Providing provider-specific safety schemas
2. Defining provider-specific triggers and actions
3. Implementing provider-specific thresholds
4. Feeding safety events back to CORE_AUTOMATION

## Status

- ✅ All 7 providers fully integrated
- ✅ 126 tests passing
- ✅ Cross-provider consistency achieved
- ✅ Safety rules and triggers defined
- ✅ Action catalog implemented
- ✅ Monitoring engine operational
