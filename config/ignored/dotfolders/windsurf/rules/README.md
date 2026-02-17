# Grid Windsurf Rules

> **Governance layer for AI-assisted development in the Grid workspace.**

These rules define how Cascade (and other AI assistants) should interact with the Grid codebase, particularly around exhibits, sensory layers, and canonical content.

---

## Rules Index

| Rule File | Scope | Description |
|-----------|-------|-------------|
| [`grid-canon-policy.md`](./grid-canon-policy.md) | `light_of_the_seven/**`, `docs/**` | Canon vs tooling separation, citation discipline |
| [`grid-sensory-layers.md`](./grid-sensory-layers.md) | `schemas/**`, `tools/**` | Sound/Vision layer integration rules |
| [`grid-exhibit-governance.md`](./grid-exhibit-governance.md) | `**/visualizations/**` | Museum-style exhibit management |
| [`grid-platform-integration.md`](./grid-platform-integration.md) | `integrations/**`, `schemas/**` | Cross-platform resonance and branch hierarchy |

---

## Quick Reference

### Canon Policy (from `grid-canon-policy.md`)

- **Two Layers**: Canon (🏛️📜) = immutable docs with citations; Tooling (🪄🧪) = mutable code
- **Citations Required**: `[Source, Chapter "Title"]` format
- **Headers Required**: Non-canon code must have `NON-CANONICAL` disclaimer

### Sensory Layers (from `grid-sensory-layers.md`)

- **Sound**: Pitch (Hz), Loudness (dB), Timbre (0-1 normalized)
- **Vision**: Nodes (id, label, type), Edges (source, target, relationship)
- **Colors**: Supportive=#4CAF50, Neutral=#9E9E9E, Adversarial=#F44336

### Exhibit Governance (from `grid-exhibit-governance.md`)

- **Required Files**: `exhibit.json`, `README.md`
- **Optional Files**: `CANON_POLICY.md`, `SOURCES.md`, `grid_bridge.py`
- **Workspace Icons**: 🏛️=Root, 📜=Canon, 🪄=Tools, 🧪=Tests

---

## How Rules Are Applied

1. **Manual Invocation**: Reference rules when asking Cascade about exhibits, canon, or sensory layers
2. **Workflow Integration**: `/grid-exhibit` workflow respects these rules automatically
3. **Context Loading**: Rules are available in `.windsurf/rules/` for AI context

---

## Related Files

| File | Purpose |
|------|---------|
| `../.claude/SYSTEM_CONTEXT.md` | AI context overview |
| `../AGENTS.md` | Agent operating protocol |
| `../schemas/exhibit_manifest_schema.json` | Exhibit manifest validation |
| `../light_of_the_seven/full_datakit/visualizations/Hogwarts/CANON_POLICY.md` | Example canon policy |

---

## Workflows Using These Rules

| Workflow | Rules Applied |
|----------|---------------|
| `/grid-exhibit` | All three rule files |
| `/grid-organize` | `grid-exhibit-governance.md` |
| `/grid-report` | `grid-canon-policy.md` (for documentation) |
| `/grid-optimize-performance` | N/A (performance-focused) |

---

## Enforcement

These rules are **advisory** for AI assistants and enforced through:

- **Code Review**: Human verification of canon claims
- **Schema Validation**: `exhibit.json` checked against schema
- **CI Checks**: Test suite validates exhibit structure
- **Windsurf Workflows**: Automated compliance checking

---

## Adding New Rules

1. Create a new `.md` file in this directory
2. Include YAML frontmatter with `name`, `description`, `scope`, `version`
3. Update this README index
4. Reference in relevant workflows

### Template

```yaml
---
name: grid-new-rule
description: What this rule governs
version: 1.0.0
scope:
  - path/to/affected/**
---

# Rule Title

## Rule 1: ...
## Rule 2: ...
```

---

*"Information has structure. Structure requires governance. Governance enables trust."*
