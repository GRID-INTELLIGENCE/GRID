# GRID Reorganization Inventory & Move Map

## Path-Sensitive Files (MUST REMAIN AT ROOT)

These files are hardcoded in tests/scripts and must stay at repo root:

- `benchmark_metrics.json` - Hardcoded in `tests/test_grid_benchmark.py:268`
- `benchmark_results.json` - Hardcoded in `tests/test_grid_benchmark.py:289`
- `stress_metrics.json` - Default output in `async_stress_harness.py:99`

## Semantic Classification

### Runtime Core (Keep as-is)
- `grid/` - Core intelligence layer
- `application/` - FastAPI applications
- `src/` - Legacy/transitional runtime (kept for compatibility)
- `backend/server.py` - Server entrypoint

### Tooling (Keep as-is)
- `tools/` - Local RAG system
- `scripts/` - Developer automation
- `workflows/` - CI/CD workflows

### Research/Cognitive (Clean up)
- `light_of_the_seven/cognitive_layer/` - KEEP (active cognitive layer)
- `light_of_the_seven/{application,grid,tools,docs,etc}/` - ARCHIVE (duplicate repo copy)

### Frontend/Node (Resolve conflicts)
- Root `mothership/` - RENAME to `frontend/mothership_frontend_stub/`
- Root `node_modules/` - ARCHIVE or remove (orphan)
- `ui/node_modules/` - ARCHIVE or remove (orphan)

### Generated Artifacts (Keep at root)
- `benchmark_metrics.json`
- `benchmark_results.json`
- `stress_metrics.json`

### Documentation (Move to docs/ with stubs)
- Status reports, session summaries, research notes → `docs/reports/`
- Architecture docs → `docs/architecture/`
- Security docs → `docs/security/`
