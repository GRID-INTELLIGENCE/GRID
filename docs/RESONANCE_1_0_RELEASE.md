# Resonance API v1.0.0 Release Notes

**Release Date**: January 2026
**API Version**: 1.0.0
**Status**: Stable

---

## Overview

The Resonance API v1.0.0 is the first stable release of the "canvas flip" communication layer. This release introduces the **definitive step** endpoint - a mid-process checkpoint (~65% progress) that transforms chaotic, free-form work into coherent, audience-aligned explanations.

---

## New Features

### Definitive Step Endpoint

**`POST /api/v1/resonance/definitive`**

The centerpiece of this release. The definitive step:

- Captures **fast context** from the application layer
- Produces **path triage** with left/right/straight options
- Runs **skills** for schema transformation, compression, and cross-referencing
- Optionally enriches with **local-first RAG** (no external API calls)

**Example Request**:
```json
{
  "query": "Where do these features connect?",
  "activity_type": "general",
  "progress": 0.65,
  "target_schema": "context_engineering",
  "use_rag": false,
  "use_llm": false,
  "max_chars": 200
}
```

### Full Endpoint Suite

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/resonance/process` | POST | Process activity with resonance feedback |
| `/api/v1/resonance/definitive` | POST | Canvas flip checkpoint |
| `/api/v1/resonance/context` | GET | Fast context retrieval |
| `/api/v1/resonance/paths` | GET | Path triage options |
| `/api/v1/resonance/envelope/{activity_id}` | GET | ADSR envelope metrics |
| `/api/v1/resonance/complete/{activity_id}` | POST | Complete activity |
| `/api/v1/resonance/events/{activity_id}` | GET | Activity event history |
| `/api/v1/resonance/ws/{activity_id}` | WebSocket | Real-time feedback |

---

## Stabilization Enhancements

This release includes comprehensive stabilization work:

### Contract Hardening
- OpenAPI specification exported to `schemas/resonance_api_openapi.json`
- Version tagged (`1.0.0`)
- Request/response examples added to Pydantic schemas
- Clear validation constraints (max 4KB query, progress 0.0-1.0)

### Security
- Auth dependency integration (`Auth`, `RateLimited`)
- Rate limiting support via Mothership dependencies
- Input sanitization via Pydantic

### Observability
- Tracing integration with `grid.tracing.trace_manager`
- Structured logging with latency metrics
- Runbook created: `docs/runbooks/RESONANCE_RUNBOOK.md`

### Testing
- 30+ API tests covering:
  - Happy path scenarios
  - Edge cases (progress=0.0, progress=1.0)
  - Boundary testing (max_chars limits)
  - Idempotency verification
  - Error handling
- 13 skill contract tests ensuring output compatibility

### Operational Safety
- Feature flag: `RESONANCE_DEFINITIVE_ENABLED`
- Rollback script: `scripts/rollback_resonance.py`
- Kill-switch returns HTTP 501 when disabled

### Performance
- Load test script: `tests/performance/test_resonance_load.py`
- Baseline metrics capture (p50/p95/p99 latency)

---

## Breaking Changes

None. This is the initial stable release.

---

## Non-Goals (Explicit Exclusions)

The following are explicitly out of scope for this release:

- **Streaming responses** - Use WebSocket for real-time
- **Multi-tenant isolation** - Single service instance
- **External LLM calls** - Local Ollama only
- **Persistent state** - In-memory activities only
- **Batch processing** - One query per request

See `docs/RESONANCE_API.md` for full non-goals documentation.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RESONANCE_DEFINITIVE_ENABLED` | `true` | Feature flag for definitive endpoint |

### Skill Dependencies

The definitive step uses these skills from `grid.skills.registry`:

| Skill | Version | Required |
|-------|---------|----------|
| `transform.schema_map` | 1.0.0 | Yes |
| `compress.articulate` | 1.0.0 | Yes |
| `context.refine` | 1.0.0 | Optional (LLM mode) |
| `cross_reference.explain` | 1.0.0 | Optional |
| `rag.query_knowledge` | 1.0.0 | Optional (RAG mode) |

---

## How to Upgrade

1. Pull the latest code
2. Run tests: `pytest tests/api/test_router.py -q`
3. Start the server: `python -m application.mothership.main`
4. Verify: `GET http://localhost:8080/health`

---

## Documentation

- [Resonance API Guide](RESONANCE_API.md)
- [Quick Start](../application/resonance/QUICK_START.md)
- [Runbook](runbooks/RESONANCE_RUNBOOK.md)
- [Skills Quickstart](SKILLS_RAG_QUICKSTART.md)

---

## Known Issues

1. **Pydantic deprecation warnings** - `json_encoders` deprecated; will be addressed in future release
2. **FastAPI deprecation** - `regex` parameter deprecated in Query; will migrate to `pattern`

---

## Contributors

- GRID Platform Team

---

## License

Proprietary - GRID Project
