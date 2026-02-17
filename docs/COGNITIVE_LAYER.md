# Cognitive Layer (Light of the Seven) — High-Clarity Guide

This guide documents GRID’s **cognitive decision support layer**: what it is, how it’s structured, and how to use it in practice.

It is designed to help you answer questions like:
- “Should this interaction be **System 1** or **System 2**?”
- “How do we **reduce cognitive load** without hiding important facts?”
- “How do we detect **mental model mismatches** and explain them?”

## What it is (in one sentence)

The cognitive layer is a set of **local-only utilities** (Pydantic schemas + deterministic helpers) that adapt processing and presentation to
human constraints: bounded rationality, cognitive load, and user mental models.

## Where it lives (canonical path)

- **Python import path (canonical):** `light_of_the_seven.cognitive_layer`
- **Source code (canonical):** `light_of_the_seven/light_of_the_seven/cognitive_layer/`

There is also a top-level directory `light_of_the_seven/cognitive_layer/` in the repo which is **not** the importable package; treat it as
organizational/legacy scaffolding unless explicitly wired.

## High-level components

The cognitive layer is organized into four modules:

- **Schemas** (`.../schemas/`): Pydantic models describing cognitive state, decision context, and user profile
- **Decision support** (`.../decision_support/`): bounded rationality, dual-process routing, decision matrices, choice architecture
- **Cognitive load** (`.../cognitive_load/`): load estimation, chunking, scaffolding/progressive disclosure
- **Mental models** (`.../mental_models/`): model tracking and alignment checking
- **Integration** (`.../integration/`): adapters that enrich context and wrap pipeline stages

## Quickstart (minimal working example)

This example shows the most common flow: build a user profile + decision context, route System 1/2, and apply bounded rationality.

```python
from light_of_the_seven.cognitive_layer import (
    BoundedRationalityEngine,
    ChoiceArchitecture,
    CognitiveLoadEstimator,
    DecisionContext,
    DualProcessRouter,
    UserCognitiveProfile,
)

user = UserCognitiveProfile(user_id="u_123")

decision = DecisionContext(
    decision_id="pick_storage",
    description="Pick a persistence store for offline-first RAG metadata",
    options=[
        {"id": "sqlite", "risk": 0.2, "potential": 0.6, "recommendation_score": 0.9, "description": "Simple, local, low ops"},
        {"id": "postgres", "risk": 0.4, "potential": 0.9, "recommendation_score": 0.8, "description": "Scales, more ops"},
    ],
    complexity=0.6,
    familiarity=0.7,
    stakes=0.5,
)

# 1) Decide System 1 vs System 2
router = DualProcessRouter()
processing_mode = router.get_processing_mode(decision, user)

# 2) Reduce choice overload (framing, defaults, progressive disclosure)
choice = ChoiceArchitecture()
decision_reduced = choice.reduce_cognitive_load(decision, user)
default = choice.suggest_default(decision_reduced.options, decision_reduced, user)

# 3) Bounded rationality selection (satisficing / best-available)
engine = BoundedRationalityEngine(default_satisficing_threshold=user.satisficing_tendency)
selection = engine.evaluate_with_bounded_rationality(
    decision_reduced,
    decision_reduced.options,
    lambda o: float(o.get("recommendation_score", 0.0)),
)

# 4) Estimate load (useful for presentation shaping)
load = CognitiveLoadEstimator().estimate_load(
    {"complexity": decision.complexity, "novelty": 1.0 - decision.familiarity, "information_density": 0.6},
    user,
)

result = {
    "processing_mode": processing_mode,
    "estimated_load": load,
    "default_option": default,
    "selection": selection,
}
```

## Core schemas (what to pass around)

- `UserCognitiveProfile`: user preferences & capacity
  - expertise (`expertise_level`)
  - decision preferences (`decision_style`, `satisficing_tendency`, `risk_tolerance`)
  - capacity (`working_memory_capacity`, `cognitive_load_tolerance`)
- `DecisionContext`: the situation being decided
  - `options`: list of dict options
  - `complexity`, `familiarity`, `stakes`, `urgency`
  - bounded rationality controls: `satisficing_threshold`, `max_search_depth`
- `CognitiveState`: a computed snapshot
  - load (0–10), working memory usage (0–1)
  - processing mode (System 1/2)
  - mental model alignment + mismatches

## Decision support: when to use what

### Dual-process routing (`DualProcessRouter`)

Use this to choose between:
- **System 1**: fast, default-safe, pattern-based
- **System 2**: slower, analytical, high-stakes or low-familiarity situations

Typical usage:
- Route early in request handling (API/CLI) to decide whether to run “fast path” vs “deep explanation path”

### Bounded rationality (`BoundedRationalityEngine`)

Use this when you have “too many options” or “no time to fully optimize”.

What you get:
- `method="satisficing"` when an option crosses a threshold quickly
- `method="best_available"` when nothing satisfies threshold

### Choice architecture (`ChoiceArchitecture`)

Use this for output shaping (especially UI/API response shaping):
- framing (gain/loss/neutral)
- suggest a default based on user decision style
- nudges (reorder/highlight)
- progressive disclosure (show a few, keep the rest)

## Cognitive load: shaping outputs for humans

### Estimate load (`CognitiveLoadEstimator`)

This gives you:
- **estimated_load** (0–10)
- **load_type**: intrinsic/extraneous/germane
- **working_memory_usage** (0–1)
- reduction suggestions

Use this to drive presentation:
- high load ⇒ fewer details + stronger defaults + chunking
- low load & expert ⇒ show deeper detail, more options, more trace evidence

### Chunking (`InformationChunker`) and scaffolding (`ScaffoldingManager`)

Use these for “results formatting”:
- chunk large lists into working-memory-friendly groups
- scaffold explanations for novices (examples/hints/step-by-step), fade scaffolding as performance improves

## Mental models: alignment and mismatch explanations

### Track mental model (`MentalModelTracker`)

Use this to:
- infer mental model features from interaction data
- track model evolution over time (versions + change detection)

### Check alignment (`AlignmentChecker`)

Use this to compare:
- **expected behavior** (what user believes the system does)
- **actual behavior** (what happened)

Output:
- `alignment_score`, `is_aligned`, list of mismatches
- suggested explanations for mismatches

## Integration: how to connect this to GRID

The cognitive layer is intentionally “bolt-on”: it can be used independently or wrapped around pipeline stages.

### Enrich a context dict (`ContextEnricher`)

This is the lowest-friction integration and works well with API request contexts.

```python
from light_of_the_seven.cognitive_layer import ContextEnricher, CognitiveLoadEstimator, UserCognitiveProfile

user = UserCognitiveProfile(user_id="u_123")
op = {"complexity": 0.8, "novelty": 0.7, "information_density": 0.8, "time_pressure": 0.4}
state = CognitiveLoadEstimator().create_cognitive_state(op, user)

base_context = {"request_id": "r_1", "context_window": 20}
enriched = ContextEnricher().enrich_full(base_context, cognitive_state=state, user_profile=user)
```

### Wrap a stage (`PipelineAdapter`)

Use this when you have callable “stages” and you want to auto-tune parameters based on cognitive state:

```python
from light_of_the_seven.cognitive_layer import CognitiveLoadEstimator, PipelineAdapter, UserCognitiveProfile

user = UserCognitiveProfile(user_id="u_123")
state = CognitiveLoadEstimator().create_cognitive_state({"complexity": 0.9, "information_density": 0.8}, user)

adapter = PipelineAdapter()
adapter.set_user_profile(user)
adapter.set_cognitive_state(state)

def ner(text: str, max_entities: int = 50, simplify: bool = False) -> dict:
    return {"entities": [], "max_entities": max_entities, "simplify": simplify}

ner_cognitive = adapter.wrap_pipeline_stage("ner", ner)
result = ner_cognitive("Hello world")
```

## Status / expectations

- The cognitive layer **is implemented** (schemas + helper modules + integration adapters).
- Full end-to-end wiring into the main GRID pipeline may be **selectively enabled** depending on the entry point
  (API/CLI/services) and performance requirements.

## Suggested next step (if you want “real” integration)

If you want the cognitive layer to affect production behavior (not just be available), the safest staged rollout is:
- enrich request context in API/CLI entry points (no behavior change, just metadata)
- apply scaffolding/chunking only at the response formatting boundary
- wrap only non-critical pipeline stages (or behind a feature flag) to avoid SLA regressions
