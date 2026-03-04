# Audit Report Contract

This document defines the **complete JSON-Schema contract** for gap/audit reports (diagnostics, errors, warnings, action items, verification commands, knowledge-graph relationships), optional YAML/TOML config snippets, and the **next-step for Action A1**.

## 1. Full contract (JSON Schema)

The canonical contract is:

- **Schema file:** `schemas/audit-report.schema.json`
- **$id:** `https://grid.dev/schemas/audit-report.schema.json`

The schema requires six top-level arrays/objects:

| Field | Type | Description |
|-------|------|-------------|
| `diagnostics` | array of diagnostic | Structured findings from audit/verification (category, severity, impact, location). |
| `errors` | array of error_entry | Validation failures, exceptions (code, message, severity, recoverable). |
| `warnings` | array of warning_entry | Non-blocking advisories (id, message, severity, impact). |
| `action_items` | array of action_item | Recommended fixes (id, title, priority, impact, fix, related_diagnostic_ids). |
| `verification_commands` | array of verification_command | Commands to re-run after fixes (id, command, expected_outcome, related_action_id). |
| `knowledge_graph` | object { nodes, edges } | Relationships between nodes (file, symbol, diagnostic, action) and edges (addresses, causes, depends_on, references, verified_by, part_of). |

Optional: `executive_summary` (total_gaps, *_count, generated_at).

---

## 2. Six discrete input → output items

Each row is one **input** (what you start with) and its **output** (what the contract expects).

| # | Input | Output |
|---|--------|--------|
| 1 | Raw audit/verification output (e.g. IDE verification, ruff, mypy) | **diagnostics** — array of `diagnostic` with id, category, message, severity, impact, optional source/location. |
| 2 | Validation failures, exceptions, or hard failures | **errors** — array of `error_entry` with code, message, severity, optional source, location, recoverable. |
| 3 | Non-blocking findings (advisories, style hints) | **warnings** — array of `warning_entry` with id, message, severity, optional impact, source, location. |
| 4 | Recommended fixes or next steps (from gap analysis) | **action_items** — array of `action_item` with id, title, priority, impact, optional fix, related_diagnostic_ids, status. |
| 5 | Commands to run to confirm fixes (e.g. re-run tests, list extensions) | **verification_commands** — array of `verification_command` with id, command, optional description, expected_outcome, related_action_id. |
| 6 | References and dependencies (plan-to-reference, file/symbol links) | **knowledge_graph** — object with `nodes` (id, type, label, path) and `edges` (from_id, to_id, relation: addresses | causes | depends_on | references | verified_by | part_of). |

**Total: six discrete items** (six input→output pairs).

---

## 3. Optional YAML/TOML snippets

### YAML — config that drives report generation

```yaml
# config/audit-report.yaml
audit_report:
  schema_ref: "https://grid.dev/schemas/audit-report.schema.json"
  outputs:
    - diagnostics
    - errors
    - warnings
    - action_items
    - verification_commands
    - knowledge_graph
  severity_map:
    critical: 1
    high: 2
    medium: 3
    low: 4
  default_impact: degrading
```

### TOML — same in pyproject or dedicated config

```toml
# pyproject.toml [tool.grid.audit_report] or audit-report.toml
[tool.grid.audit_report]
schema_ref = "https://grid.dev/schemas/audit-report.schema.json"
outputs = ["diagnostics", "errors", "warnings", "action_items", "verification_commands", "knowledge_graph"]
default_impact = "degrading"

[tool.grid.audit_report.severity_map]
critical = 1
high = 2
medium = 3
low = 4
```

---

## 4. Next-step: apply Action A1

**Action A1:** Validate all generated audit/gap reports against the contract schema and ensure every report includes all six sections (diagnostics, errors, warnings, action_items, verification_commands, knowledge_graph).

1. **Validate** existing report JSON files:
   - Use a JSON-Schema validator (e.g. `jsonschema` in Python, or `ajv` CLI) with `schemas/audit-report.schema.json`.
   - Run: `python -c "import json, jsonschema; d=json.load(open('path/to/report.json')); jsonschema.validate(d, json.load(open('schemas/audit-report.schema.json')))"` (after `pip install jsonschema`).

2. **Emit** reports that conform: ensure any script or skill that produces gap/audit output (e.g. IDE verification skill, plan-to-reference) writes JSON that satisfies the schema.

3. **Optional:** Add a CI or Make target that validates `artifacts/*.json` or a designated report path against `schemas/audit-report.schema.json`.

---

## References

- Schema: `schemas/audit-report.schema.json`
- IDE verification (gap report format): `.cursor/skills/ide-verification/SKILL.md`
- Plan-to-reference (reference map, verification chain): `.cursor/skills/plan-to-reference/SKILL.md`
