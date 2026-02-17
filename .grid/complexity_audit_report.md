# Complexity Audit Report

Generated: 2026-02-16

## Critical Complexity (F/E grade — CC > 30)

| File | Function | CC | Grade |
|---|---|---|---|
| `src/grid/skills/transform_schema_map.py` | `_heuristic_custom_schema` | 119 | F |
| `src/tools/rag/indexing/indexer.py` | `update_index` | 94 | F |
| `src/tools/rag/indexing/indexer.py` | `index_repository` | 93 | F |
| `src/tools/rag/embeddings.py` | `OllamaEmbeddingProvider.embed` | 42 | F |
| `src/application/mothership/main.py` | `lifespan` | 38 | E |
| `src/tools/rag/indexer/distributed_spark_indexer.py` | `PydanticV2Migrator._add_missing_imports` | 35 | E |
| `src/application/mothership/routers/stripe_connect_demo.py` | `payment_webhook` | 35 | E |
| `src/grid/skills/topic_extractor.py` | `_extract_topics` | 34 | E |

## High Complexity (D grade — CC 21-30)

| File | Function | CC |
|---|---|---|
| `src/grid/skills/ai_safety/actions.py` | `definitive_step` | 29 |
| `src/grid/interfaces/metrics_collector.py` | `_extract_sensory_metrics_from_trace` | 26 |
| `src/cognitive/interaction_tracker.py` | `detect_patterns` | 26 |
| `src/application/mothership/routers/health.py` | `run_diagnostics` | 26 |
| `src/grid/agentic/agentic_system.py` | `execute_case` | 25 |
| `src/application/mothership/config/__init__.py` | `SecuritySettings.validate` | 25 |
| `src/grid/security/input_sanitizer.py` | `sanitize_text_full` | 24 |
| `src/grid/security/startup.py` | `harden_environment` | 24 |
| `src/grid/resilience/accountability/contracts.py` | `_validate_data` | 24 |
| `src/grid/agentic/agentic_system.py` | `iterative_execute` | 23 |
| `src/application/mothership/routers/health.py` | `get_statistics` | 23 |
| `src/grid/senses/sensory_store.py` | `query_inputs` | 22 |
| `src/application/mothership/main.py` | `create_app` | 22 |
| `src/application/mothership/middleware/__init__.py` | `setup_middleware` | 21 |
| `src/cognitive/function_calling/evaluator.py` | `_eval_node` | 21 |

## Maintainability Index — Worst Files (C grade)

- `src/application/mothership/routers/stripe_connect_demo.py`
- `src/cognitive/patterns/recognition.py`
- `src/grid/skills/transform_schema_map.py`
- `src/tools/rag/indexing/indexer.py`

## 36 total functions with D/E/F complexity grades across src/

## Key Refactoring Targets (by impact)

1. **`transform_schema_map.py::_heuristic_custom_schema`** (CC=119) — Extract sub-functions for each schema type
2. **`indexer.py::update_index`/`index_repository`** (CC=94/93) — Break into pipeline stages
3. **`main.py::lifespan`** (CC=38) — Extract service init/shutdown into separate functions
4. **`input_sanitizer.py::sanitize_text_full`** (CC=24) — Extract per-rule sanitizers
5. **`agentic_system.py::execute_case`** (CC=25) — Extract decision branches
