# Plaza -> GRID Guided Tour

Audience: operators entering from Plaza and needing a direct path into live GRID execution.

North star: move from orientation to a real execution loop touching Admission, Resonance/Canvas, Retrieval, and UI feedback.

## Runtime Targets

| Surface | Default | Role |
| --- | --- | --- |
| Mothership API | `http://localhost:8080` | Primary execution surface |
| API Gateway (optional) | `http://localhost:8000` | Routed facade |
| Frontend UI | `http://localhost:<vite-port>` | Operator dashboard |

## 7-Stage Tour

| Stage | Objective | Proof of completion |
| --- | --- | --- |
| 1 | Orientation | You can map Plaza -> Admission/Resonance/Retrieval/UI |
| 2 | Bring-up | `GET /health` returns 200 |
| 3 | Admission | `GET /admission/policy` or `/admission/stats` returns 200 |
| 4 | Resonance | `POST /api/v1/resonance/process` returns structured payload |
| 5 | Canvas Flip | `POST /api/v1/resonance/definitive` includes `canvas_before` and `canvas_after` |
| 6 | Retrieval + UI | Retrieval route responds; UI reflects API state |
| 7 | Closure | One end-to-end trace is documented with next-step actions |

## Stage 1: Orientation

- Confirm Plaza entry material and objective.
- Map each user-facing promise to a concrete surface:
  - Governance -> Admission Gate
  - Meaning synthesis -> Resonance + Canvas Flip
  - Knowledge response -> Retrieval stack
  - Operator visibility -> Frontend dashboard

Completion signal: the operator can name where each promise executes.

## Stage 2: Bring-up and Connectivity

```bash
cd <GRID_REPO_ROOT>
make run
```

```bash
export GRID_BASE="${GRID_BASE:-http://localhost:8080}"
curl -sS "${GRID_BASE}/health"
curl -sS "${GRID_BASE}/openapi.json" -o /tmp/grid-openapi.json
```

Completion signal: health and API contract are reachable.

## Stage 3: Admission Gate Check

Acquire auth according to your environment, then run:

```bash
curl -sS "${GRID_BASE}/admission/policy" -H "Authorization: Bearer ${ACCESS_TOKEN}"
curl -sS "${GRID_BASE}/admission/stats" -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Completion signal: one policy/stats endpoint returns valid JSON.

## Stage 4: Resonance Process Check

```bash
curl -sS -X POST "${GRID_BASE}/api/v1/resonance/process" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plaza to GRID execution check",
    "activity_type": "general",
    "context": {}
  }'
```

Completion signal: response includes stable workflow fields (for example `activity_id` and state indicators).

## Stage 5: Canvas Flip Check

```bash
curl -sS -X POST "${GRID_BASE}/api/v1/resonance/definitive" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize what changed and why it matters for operators.",
    "activity_type": "general",
    "context": {},
    "progress": 0.65,
    "target_schema": "context_engineering",
    "use_rag": false,
    "use_llm": false,
    "max_chars": 280
  }'
```

Completion signal: `canvas_before` and `canvas_after` are both present.

## Stage 6: Retrieval and UI Pass

- Hit one retrieval endpoint enabled in your environment (for example `GET /api/v1/rag/stats`).
- Start frontend with `VITE_API_URL` pointing to the same API base.
- Confirm UI network calls map to the same Admission/Resonance/Retrieval routes.

Completion signal: API response and UI state agree for at least one retrieval action.

## Stage 7: Feedback Closure

- Save one `activity_id` from Resonance/Definitive.
- Record any notable friction (auth, rate-limit, route mismatch, model availability).
- Tag one improvement candidate for the experience loop.

Completion signal: one full Plaza -> GRID execution trace is documented.

## Completion Checklist

- [ ] Plaza mapping complete (all four surfaces identified).
- [ ] API reachable and healthy.
- [ ] Admission Gate visibility confirmed.
- [ ] Resonance process endpoint verified.
- [ ] Canvas Flip definitive endpoint verified.
- [ ] Retrieval and UI alignment verified.
- [ ] One traced run captured with next actions.
