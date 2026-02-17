---
description: No Matter Core Principle and Tool Attributes
---

# No Matter Principle (Core)

The **No Matter** principle is a core design pattern in this repo:

> When the environment is noisy or overwhelming, separate signal from noise,
> compress it into a small structured core, and keep moving through clear
> phases, with detection kept separate from presentation.

This shows up in multiple places:

- `scripts/no_mattter.py`: message extraction + Compass engine
- `context_refiner.py`: pronoun/phrase reduction and context tightening
- `no_mattter.py`: numeric profiles for flows (loan and corridor)
- `scripts/analyze_dependencies.py`: dependency graph cross-referencing
- `scripts/build_websocket_safety.py`: WebSocket safety profile builder
- `train_ner.py`: NER training data and pattern extraction

All of these tools now have a small, shared description in terms of
`core.tool_attributes`.

---

## ToolAttributes: shared vocabulary for tools

`core/tool_attributes.py` defines a small vocabulary to describe what a tool
does, at a high level:

- **AccessMode**: `read_only`, `write`, `read_write`, `simulate_only`
- **ScopeMode**: `single_target`, `multi_target`, `partial`, `full`
- **DepthMode**: `literal`, `structural`, `semantic`, `temporal`
- **TransformMode**: `none`, `summarize`, `compress`, `translate`, `normalize`, `cross_reference`
- **InteractionMode**: `synchronous`, `streaming`, `batch`

The `ToolAttributes` dataclass groups these together, and `ToolProperty` offers
common presets (e.g., `read_only()`, `read_simulate()`, `transform()`,
`cross_reference()`).

Each high‑level script exposes a module‑level `TOOL_ATTRIBUTES` value so that
orchestrators or CLI helpers can understand what kind of operation it performs.

### Current tool annotations

These scripts now define `TOOL_ATTRIBUTES`:

- **`no_mattter.py`**
  - `TOOL_ATTRIBUTES = ToolProperty.read_simulate()`
  - Interpreted as: simulate/normalize profiles (read input, compute in memory,
    no external writes).

- **`context_refiner.py`**
  - `TOOL_ATTRIBUTES = ToolProperty.transform()`
  - Interpreted as: semantic, normalizing transform on a single text.

- **`scripts/analyze_dependencies.py`**
  - `TOOL_ATTRIBUTES = ToolProperty.cross_reference()`
  - Interpreted as: read‑only, multi‑target, semantic cross‑reference over
    modules and their dependencies.

- **`scripts/build_websocket_safety.py`**
  - `TOOL_ATTRIBUTES = ToolProperty.read_simulate()`
  - Interpreted as: read/simulate WebSocket safety profiles (construct
    configuration objects without opening real connections).

- **`train_ner.py`**
  - `TOOL_ATTRIBUTES = ToolProperty.transform()`
  - Interpreted as: semantic transform from domain text and entities into
    training data and extracted patterns.

These annotations do **not** change runtime behavior. They only provide a
machine‑ and human‑readable description of what each script does.

---

## Listing tool attributes

The helper script `scripts/list_tool_attributes.py` prints the
`TOOL_ATTRIBUTES` for a handful of important tools.

Run from the repo root (`e:\grid`):

```bash
python -m scripts.list_tool_attributes
```

Example output shape:

```text
no_mattter:
  access      = simulate_only
  scope       = single_target
  depth       = semantic
  transform   = normalize
  interaction = synchronous

context_refiner:
  access      = read_write
  scope       = single_target
  depth       = semantic
  transform   = normalize
  interaction = synchronous

scripts.analyze_dependencies:
  access      = read_only
  scope       = multi_target
  depth       = semantic
  transform   = cross_reference
  interaction = synchronous

...
```

This script is intentionally small and read‑only. It is meant as both a
self‑check (to confirm tools are tagged correctly) and a live reference for the
"No Matter" core vocabulary.

---

## How this ties back to "No Matter"

The **No Matter** principle is not just about one file; it is a pattern:

- **Separate signal from noise** (e.g., message extractor, context refiner,
  dependency analyzer, NER patterns).
- **Compress into a structured core** (e.g., `MessageCore`, loan/corridor
  profiles, dependency summaries, NER training artifacts).
- **Keep moving through phases** (e.g., Compass engine states, pipeline steps),
  even when the environment is noisy.
- **Separate detection from presentation** (e.g., Smeller vs Seer; risk checks
  vs reporting).

`core.tool_attributes` and `TOOL_ATTRIBUTES` make that pattern visible and
machine‑navigable across different parts of the codebase.
