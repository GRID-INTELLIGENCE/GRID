# Resonance API ("Canvas Flip" Communication Layer)

This module is the *communication* glue that answers:

- **"What is this?"**
- **"Where do these features connect?"**
- **"What is the main function of this update?"**

It frames the system as a stage performance where the work is intentionally free-form/chaotic until a mid-process checkpoint flips the canvas and reveals structure.

## What is the "definitive" step?

The **definitive step** is a checkpoint (default **~65% progress**) that:

- Captures **fast context** (left side)
- Produces **path triage** (right side: left/right/straight)
- Runs **skills** to:
  - refine (optional)
  - transform text into a **target schema**
  - compress into an **audience-readable one-liner**
  - cross-reference the metaphor into an API/system explanation
- Optionally enriches with **local-first RAG**

In code this is exposed as:

- `POST /api/v1/resonance/definitive`

## Endpoints

Base path when running the Mothership backend:

- `/api/v1/resonance`

### `POST /api/v1/resonance/process`

Orchestrates the baseline resonance loop:

- **Context** snapshot (fast)
- **Path triage** (3-4 options)
- **Envelope** metrics (ADSR-like feedback)

### `POST /api/v1/resonance/definitive`

Runs the "canvas flip" checkpoint.

#### Request

```json
{
  "query": "Where do these features connect and what is the main function of this update?",
  "activity_type": "general",
  "context": {},
  "progress": 0.65,
  "target_schema": "context_engineering",
  "use_rag": false,
  "use_llm": false,
  "max_chars": 200
}
```

#### Response (shape)

- `canvas_before` / `canvas_after`: the flip narrative
- `summary`: compressed audience one-liner
- `faq`: "what is this / what are participants doing" answers
- `use_cases`: communication/market scenarios
- `api_mechanics`: pointers to the entry points
- `structured`: schema transform output (from `transform.schema_map`)
- `choices`: left/right/straight labeled options (derived from path triage)
- `skills`: raw skill outputs for inspection
- `rag`: optional RAG payload

## How it connects to Skills

The definitive step calls the skills registry (`grid.skills.registry.default_registry`) and runs:

- `transform.schema_map` (primary)
- `compress.articulate` (audience summary)
- `cross_reference.explain` (metaphor bridge)
- `context.refine` (only used as transform input when `use_llm=true`)
- `rag.query_knowledge` (optional)

This is the "library" / "collective" interface: it converts a mid-process ambiguity into a structured response.

## How to run

### Run API server

```powershell
.\.venv\Scripts\python.exe -m application.mothership.main
```

Then open:

- `http://localhost:8080/docs` (if development settings enable it)

### Test the resonance API

```powershell
.\.venv\Scripts\python.exe -m pytest tests\api\test_router.py -q
```

## Notes

- The resonance router is mounted in the Mothership API aggregator under `/api/v1/resonance`.
- The ADSR envelope has a guard for the initial time-resolution edge case so it won't crash on `progress==0` during the attack phase.

---

## Non-Goals and Limitations

This section documents what the Resonance API **will not do** (negative-space definition).

### What the API Does NOT Support

| Non-Goal | Rationale |
|----------|-----------|
| **Streaming responses** | The definitive step is a synchronous checkpoint, not a real-time stream. Use WebSocket `/ws/{activity_id}` for real-time feedback. |
| **Multi-tenant isolation** | All requests share a singleton service instance. For multi-tenant deployments, run separate instances. |
| **External LLM calls** | Only local Ollama models are used (`use_llm=true`). No OpenAI/Anthropic/cloud APIs. |
| **Persistent state across restarts** | Activity state is in-memory. Restart clears all activities. |
| **Large payload processing** | Query limited to 4KB (`max_length=4000`). For larger documents, chunk and process iteratively. |

### SLA Exclusions

- **No guaranteed latency SLA** during heuristic-only mode. LLM-backed mode (`use_llm=true`) depends on local Ollama performance.
- **No retry/idempotency guarantees** at the API level. Clients should implement their own retry logic with exponential backoff.
- **No rate limiting** is enforced by default in development mode. Production deployments should enable rate limiting via `RateLimited` dependency.

### Payload Constraints

| Constraint | Value | Enforced By |
|------------|-------|-------------|
| Max query length | 4,000 characters | Pydantic schema validation |
| Max context object | No explicit limit; recommended < 10KB | Best practice |
| Max summary chars | 2,000 | `max_chars` field (default: 280) |
| Progress range | 0.0 - 1.0 | Pydantic schema validation |

### Deferred Features (Backlog)

- Batch processing of multiple queries in a single request
- Webhook callbacks for async processing
- Query result caching with TTL
- Custom schema registration via API
