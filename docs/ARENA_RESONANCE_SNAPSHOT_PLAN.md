# Arena ↔ Resonance Snapshot/Policy Plan (Keyword-Linked)

## 0) Intent
This document captures a production-oriented plan for implementing a **snapshot → policy → execution → narrative** architecture across:

- `src/application/resonance/*` (Resonance API + explanation checkpoint)
- `Arena/the_chase/python/src/the_chase/*` (Arena simulation + Overwatch + event bus)

The target outcome is a **shared vocabulary + shared primitives** so:

- Arena can emit structured “decision state” snapshots (Overwatch/referee intelligence)
- Resonance can explain/visualize those snapshots (human-facing checkpoint artifacts)
- Tuning/thresholding remains **explicit and testable**, not scattered heuristics

This is *not* a “docstrings” plan; it is documentation with **semantic keyword matching** and **code-context anchors**.

---

## 1) High-level Architecture

### 1.1 Canonical loop
**Snapshot → Policy → Execution → Narrative**

- **Snapshot layer**
  - Pure measurement of current state and decision conditions.
  - Output: immutable snapshot objects (timestamped, loggable).

- **Policy layer**
  - Deterministic rules or threshold tables that turn snapshots into actions.
  - Output: policy decisions (“mode”, “intervention”, “next step”).

- **Execution layer**
  - Performs actions (apply intervention, enqueue events, trigger abilities, stream updates).
  - Owns retries and failure containment.

- **Narrative layer**
  - Human-facing explanations of “what happened” and “why”.
  - Can be requested explicitly (checkpoint) or streamed incrementally.

---

## 2) Keyword → Code Anchor Map (semantic matching)

Use these keywords in documentation and logs so readers can jump into code quickly.

### 2.1 Resonance (API + explanation)
- **Keywords**
  - `ContextSnapshot`, `ContextMetrics`, `decision_pressure`, `attention_tension`, `sparsity`, `clarity`, `confidence`
  - `definitive`, `canvas flip`, `FAQ`, `UseCase`, `skills`, `use_rag`
  - `PathTriage`, `recommended`, `choices` (left/right/straight)
  - `EnvelopeMetrics`, `ADSR`, `phase`, `urgency`

- **Anchors**
  - `src/application/resonance/context_provider.py`
    - `ContextMetrics`
    - `ContextSnapshot`
    - `provide_context()`
  - `src/application/resonance/activity_resonance.py`
    - `ActivityResonance.process_activity()`
    - urgency calculation (weighted metrics)
  - `src/application/resonance/api/router.py`
    - `POST /api/v1/resonance/process`
    - `POST /api/v1/resonance/definitive` (FAQ/use-cases/mechanics/skills)

### 2.2 Arena / The Chase (simulation + referee intelligence)
- **Keywords**
  - `threshold`, `meter`, `Alive Meter`, `MeterThreshold`, `MeterState`, `MeterDelta`
  - `snapshot`, `state_before`, `state_after`, `TurnRecord`, `state_hash`
  - `EventBus`, `EventCategory`, `EventPriority`, `EventPhase`
  - `Overwatch`, `fairness_threshold`, `cascade_alert_threshold`, `intervention_threshold`, `OverwatchState`
  - `PipelineStep` (15-step deterministic pipeline)

- **Anchors**
  - `Arena/the_chase/python/src/the_chase/engine/meter.py`
    - threshold levels (`THRESHOLD_*`)
    - `MeterDelta`, `MeterState.threshold`
  - `Arena/the_chase/python/src/the_chase/engine/history.py`
    - `TurnRecord.state_before/state_after`
    - state hashing and replay
  - `Arena/the_chase/python/src/the_chase/core/event_bus.py`
    - publish/subscribe, priority queue, history
  - `Arena/the_chase/python/src/the_chase/overwatch/core.py`
    - `OverwatchConfig` thresholds
    - states: `ALERT`, `INTERVENTION`, `OVERLOAD`
  - `Arena/the_chase/python/src/the_chase/engine/pipeline.py`
    - `PipelineStep` and `PipelineResult` (deterministic flow)

---

## 3) What exists today (ground truth)

### 3.1 Resonance already has “snapshot + narrative”
- Snapshot primitive: `ContextSnapshot(metrics + content + timestamp)`
- Narrative primitive: `/resonance/definitive` emits:
  - `faq[]`
  - `use_cases[]`
  - `api_mechanics[]`
  - optional skills orchestration + optional RAG payload

### 3.2 Arena already has “thresholds + bus + state snapshots”
- Threshold primitive: Alive Meter thresholds in `engine/meter.py`
- Bus primitive: `core/event_bus.py`
- Snapshot primitive (state): `engine/history.py` turn records
- Deterministic pipeline: `engine/pipeline.py` (15-step resolution)
- Offline tuning: `simulation/balance_tuner.py`

**Missing link**: Arena lacks an explicit **decision snapshot** for Overwatch-style referee judgement (analogous to Resonance decision-state metrics).

---

## 4) Plan: Implement Arena Decision Snapshots (Overwatch-first)

### 4.1 Define an Arena decision snapshot (naming)
Introduce a new snapshot type (name can vary):
- `OverwatchSnapshot` or `ArenaDecisionSnapshot`

**Design constraints**
- Immutable / serializable
- Timestamped
- Small fixed schema

### 4.2 Proposed snapshot fields (v0)
These should mirror Arena’s existing threshold vocabulary.

- `timestamp`
- `overwatch_state` (e.g., `ACTIVE`, `ALERT`, `INTERVENTION`)
- `fairness_score` (0..1)
- `cascade_risk` (0..1)
- `overload_risk` (0..1)
- `intent_confidence` (0..1 or enum compatible with `IntentConfidence`)
- `active_thresholds` (resolved thresholds currently “hot”)
  - e.g., `alive_meter_threshold` (0..5)
  - e.g., `intervention_threshold` crossed?

### 4.3 Ownership
- Snapshot *generation* should be owned by:
  - `Arena/the_chase/python/src/the_chase/overwatch/core.py`

### 4.4 Emission
- Publish snapshots to `EventBus` as events:
  - category suggestion: `EventCategory.SAFETY` or `EventCategory.ATTENTION`
  - priority suggestion: `EventPriority.HIGH` when in ALERT/INTERVENTION

### 4.5 Storage
- Phase 1: rely on EventBus history for recent snapshots
- Phase 2: write to `engine/history.py` alongside `TurnRecord` events (optional)

---

## 5) Plan: Policy tables (threshold snapshots → actions)

### 5.1 Why policy tables
Avoid scattering thresholds across modules.

A single “policy table” makes:
- tuning explicit
- tests easier
- behavior reproducible

### 5.2 Policy decisions (examples)
- if `cascade_risk >= cascade_alert_threshold` → set `OverwatchState.ALERT`
- if `cascade_risk >= intervention_threshold` → generate `InterventionType` action
- if `overload_risk high` → reduce tick rate / shrink context window (Overwatch config already supports adaptive sizing)

### 5.3 Placement
- Start in `overwatch/core.py` (local cohesion)
- Later extract into `overwatch/policy.py` if it grows

---

## 6) Plan: Resonance as a narrative/explanation adapter for Arena

### 6.1 Goal
Resonance should be able to explain Arena/Overwatch snapshots in a human-facing way:

- “What happened?”
- “Why did Overwatch intervene?”
- “What thresholds were crossed?”
- “What are the safe next options?”

### 6.2 Minimal coupling strategy
- Keep Arena as the producer of snapshots
- Resonance consumes snapshots via:
  - in-process adapter (dev mode)
  - or later: a thin API boundary

### 6.3 Semantic mapping
Map Arena fields into Resonance narrative artifacts:

- `cascade_risk` → “attention_tension” analogue
- `fairness_score` deviation → “decision_pressure” analogue
- `overload_risk` → “sparsity/clarity” analogue (system struggling)

---

## 7) Documentation style guideline (20% code-context)

For any feature doc, aim for:
- 80% concept, motivation, guarantees
- 20% anchored code-context via:
  - explicit keyword list
  - file paths + function/class names
  - minimal snippets only when essential

### Example template
- **Keywords**: `OverwatchSnapshot`, `EventBus`, `PipelineStep`, `TurnRecord`
- **Where in code**:
  - `the_chase/overwatch/core.py` → snapshot + policy
  - `the_chase/core/event_bus.py` → routing
  - `the_chase/engine/history.py` → persistence/replay

---

## 8) Validation & rollout

### 8.1 Non-breaking rollout phases
1. Add snapshot type + event emission (no behavior change)
2. Add policy table but run it in “observe only” mode (log decisions)
3. Enable interventions gradually

### 8.2 Verification checklist
- Smoke:
  - emit snapshot each tick/turn without perf collapse
- Determinism:
  - same inputs → same policy decisions
- Offline metrics:
  - aggregate snapshot distributions in batch runs (BalanceTuner)

---

## 9) Open decisions
- Snapshot naming: `OverwatchSnapshot` vs `ArenaDecisionSnapshot`
- Event category: `SAFETY` vs `ATTENTION`
- Where to expose narrative: keep inside Arena tooling vs expose via Resonance endpoints
