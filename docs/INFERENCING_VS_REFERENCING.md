# Inferencing vs. Referencing Architecture

## Core Distinction

### Inferencing
**What it does:** Generates a *new* conclusion from available signals.
**Mode:** "Given this context, what *follows*?"
**Risk:** Can hallucinate or over-extend if context is thin or skewed.
**In GRID:** Pattern engine, rules engine, relationship analyzer, scenario analyzer all sit here: they *infer* patterns, risks, relationships, scenarios.

### Referencing
**What it does:** Fetches or re-anchors to *existing evidence* before/while inferring.
**Mode:** "What has already been seen / logged / known that is relevant to this?"
**Risk:** If referencing is too shallow or biased, it can *support* bad inferences.
**In GRID:** RAG retrieval, temporal logs, retry history, embeddings, prior pattern matches, and the "rear-view mirror" checks.

**Both are justified methods:**
- Referencing is justified when it is anchored to reliable artifacts (docs, logs, traces, retry records).
- Inferencing is justified when it clearly exposes its supporting evidence and uncertainty.

---

## Why "Referencing as an Option" (Not a Replacement)

Referencing is not replacing inference; it's **making referencing a first-class option that supports inference**:

**Referencing is:**
- Optional but recommended.
- A *pre-step* or *subprocess* before making strong inferences.
- A way to cool the "fear/heat" in the system by checking context before acting.

**Inference still does the main reasoning work:**
- But now it runs **with** an explicit notion of:
  - "What did I just look at?"
  - "What did I ignore?"
  - "How many times did I fail before?"

This is exactly what GRID does with retries, temporal signals, and pattern_engine: **inference is no longer free-floating; it is constrained and informed by referencing**.

---

## Implementation: `<glimpse>` and `<revise>`

### `<glimpse>` — Lightweight Referencing (Supports Inference)

**Role:** A fast, cheap "rear-view mirror" check.

**Behavior:**
- Pulls a small set of relevant chunks / prior events / patterns (`top_k=1`).
- Does *not* fully reinterpret the world; just provides snapshots.
- Uses relaxed similarity threshold (`min_similarity=0.5`).

**When used:**
- Before an *early retry* (20-minute optional window).
- Before strong decisions when "fear" or ambiguity is elevated.

**Effect on inference:**
- Narrows the hypothesis space.
- Raises or lowers confidence before the main inference runs.
- Helps avoid blind inferencing on stale or incomplete state.

**Code Location:** `src/grid/pattern/engine.py::_glimpse_for_entity()`

```python
def _glimpse_for_entity(self, entity: Entity, top_k: int = 1) -> Optional[dict]:
    """Lightweight evidence retrieval (glimpse) used before explicit early retries."""
    # Quick RAG lookup with top_k=1, min_similarity=0.5
    # Returns condensed {"chunks": [...], "docs": [...]}
```

---

### `<revise>` — Heavy Referencing + Reframing

**Role:** A structured "re-think" subprocess.

**Behavior:**
- Reads the past attempts, error patterns, retry history.
- References earlier context, missed angles, temporal anomalies (`top_k=3`).
- Uses very relaxed threshold to catch more context (`min_similarity=0.4`).
- Then actively **reframes** the problem, prompt, or pipeline.

**When used:**
- After repeated failures or low-confidence outcomes (e.g. base retries exhausted, fear metric high).
- When the system needs to change *how* it is reasoning, not just *what* evidence it sees.

**Effect on inference:**
- Produces a new, better-shaped *input* to the next inference step.
- Can alter routes, weights, or modules involved in the pipeline.

**Code Location:** `src/grid/pattern/engine.py::_revise_entity()`

```python
def _revise_entity(self, entity: Entity, pattern_matches: list[dict], rag_context: Optional[dict]) -> Optional[dict]:
    """Lightweight revise subprocess: reframe the analysis around new context.

    This function behaves as a *referencing* subprocess (contrast to
    classic inferencing): it collects external evidence and suggests
    alternative contextual frames or references that can be used to
    reinterpret the entity.
    """
    # Deeper RAG lookup with top_k=3, min_similarity=0.4
    # Returns {"suggested_context": [...], "hint": "..."}
```

---

## Integration with Retry Policy & Temporal Signals

The retry policy and temporal fields give **structured hooks** for when to use each:

### Early Retry (20 min, explicit)
**Before granting it, call `<glimpse>`.**

This is referencing-as-sanity-check: "if we try again, do we at least have better evidence now?"

**Code:**
```python
if explicit_retry_request and self.retry_manager is not None:
    allowed, info = self.retry_manager.can_retry("entity", entity_id, explicit_request=True)
    if allowed:
        glimpse_ctx = self._glimpse_for_entity(entity, top_k=1)
        if glimpse_ctx:
            rag_context.setdefault("glimpse", []).append(glimpse_ctx)
```

### Base Retries Exhausted / Repeated Failures
**Trigger `<revise>`.**

Use retry records, pattern confidence, and RAG divergence as input. This is referencing-as-deep-diagnostic: "we've failed enough times; we must change the framing."

**Code:**
```python
if not success:
    attempt_count = int(updated.get("attempt_count", 0))
    base_retries = int(self.retry_manager.config.base_retries)
    if attempt_count >= base_retries:
        revision = self._revise_entity(entity, pattern_matches, rag_context)
        if revision:
            # Annotate output so callers/tests can see revise happened
            pattern_matches.append({
                "pattern_code": "REVISION_SUBPROCESS",
                "revise_triggered": True,
                "revision": revision
            })
```

---

## Simple Summary

- **Inference:** thinking.
- **Reference:** checking.

**`<glimpse>`** = "Check quickly, then think."
**`<revise>`** = "Check deeply, understand why past thinking failed, then think differently."

Both are **justified methods** that work together to create robust, evidence-grounded AI reasoning.
