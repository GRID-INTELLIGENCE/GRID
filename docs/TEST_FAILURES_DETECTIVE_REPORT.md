# First-Person Detective Report: Remaining Test Failures & Errors

**Case file:** GRID test suite — remaining failures and errors  
**Date:** 2025-02-24  
**Objective:** Column/row inventory for investigation.

---

## 1. Confirmed failures and errors (current run)

Collected from a live pytest run (unit tests, with some modules excluded due to collection errors). These are the **confirmed** failures and collection errors.

### 1.1 Test failures (executed and failed)

| # | Test ID | File:Line | Evidence | Lead |
|---|--------|-----------|----------|------|
| 1 | `TestRAGEngineBasic::test_rag_config_from_env` | `tests/unit/test_critical_paths.py` (≈520) | `pydantic.v1.errors.ConfigError: unable to infer type for attribute "chroma_server_nofile"` — triggered when importing `tools.rag.config.RAGConfig` (chain pulls in chromadb → pydantic v1 Settings). | Chromadb/Pydantic incompatibility (Python 3.14 / pydantic v1 inference on `chroma_server_nofile`). |
| 2 | `TestEnvironmentIsolation::test_database_is_memory` | `tests/unit/test_critical_paths.py:640` | `AssertionError: assert ('memory' in 'sqlite+aiosqlite:///e:/GRID-main/data/mothership.db' or ... == '')` — test expects DB URL to contain `"memory"` or be empty. | Test env not forcing in-memory DB; `DATABASE_URL` or app config points at file `data/mothership.db` in test run. |

### 1.2 Collection errors (test not run; import/setup failed)

| # | Affected test/file | Error type | Evidence | Lead |
|---|--------------------|------------|----------|------|
| 3 | `tests/unit/rag/test_embedding_provider.py` | Collection ERROR | Same chromadb/pydantic chain as #1. | Chromadb `Settings` + pydantic v1 on Python 3.14. |
| 4 | `tests/unit/rag/test_phase3.py` | Collection ERROR | Same as #1. | Same as #3. |
| 5 | `tests/unit/test_chromadb_store.py` | Collection ERROR | Direct `import chromadb` → config.py Settings. | Same chromadb/pydantic root cause. |
| 6 | `tests/unit/test_databricks_manifest.py` | Collection ERROR | Import of `tools.rag` pulls in chromadb. | Same as #3. |
| 7 | `tests/unit/test_databricks_store.py` | Collection ERROR | Same RAG/chromadb import chain. | Same as #3. |
| 8 | `tests/unit/test_vector_store_registry.py` | Collection ERROR | Same RAG/chromadb import chain. | Same as #3. |
| 9 | `tests/unit/test_embedding_providers_comprehensive.py` | Collection ERROR | Import of `tools.rag.embeddings.huggingface` → RAG → chromadb. | Same as #3. |
| 10 | `tests/integration/test_enhanced_rag_server.py` | Collection ERROR | `from grid.mcp.enhanced_rag_server import ...` → module does `sys.exit(1)` when `mcp` not installed. | Missing `mcp` package or optional dependency; server exits on import. |

---

## 2. Documented remaining failures (from TEST_STATUS_AND_FIXES)

These are the **23 failures + 6 errors** previously documented. In the current run, some of these tests are **skipped** (e.g. missing CLI/legacy_src, or by marker); when they are not skipped, they are the known failing cases below. Use this table to trace by category and file.

| # | Category | Test file | Test name(s) | Type | Root cause (lead) |
|---|----------|-----------|--------------|------|-------------------|
| 11 | Pattern Engine RAG/MIST | `tests/unit/test_pattern_engine_rag.py` | `test_pattern_engine_with_rag_context`, `test_pattern_engine_rag_failure_falls_back` | FAIL | PatternEngine missing `retrieve_rag_context()` and RAG integration in analysis. |
| 12 | Pattern Engine RAG/MIST | `tests/unit/test_pattern_engine_mist.py` | `test_mist_detected_when_no_patterns`, `test_mist_returns_none_when_patterns_exist` | FAIL | PatternEngine missing `detect_mist_pattern()` for “unknowable” when no matches. |
| 13 | Pattern Engine RAG/MIST | `tests/unit/test_pattern_engine_matching.py` | (1) pattern matching when RAG/MIST needed | FAIL | Same as #11–12. |
| 14 | NL Dev file ops | `tests/unit/test_nl_dev.py` | `test_generate_modify_file_success`, `test_generate_delete_file_success`, `test_rollback` | FAIL | CodeGenerator missing `generate_modify_file()`, `generate_delete_file()`, and `rollback()`. |
| 15 | Routing & priority queue | `tests/unit/test_intelligent_routing.py` | `test_priority_queue_ordering`, `test_heuristic_router_logic`, `test_pipeline_applies_heuristics` | FAIL | PriorityQueue ordering (e.g. heapq max-heap) and HeuristicRouter pipeline integration not implemented. |
| 16 | Message broker retry/DLQ | `tests/unit/test_message_broker_retry_persistence.py` | (1 failure) | FAIL | Retry tracking and dead-letter-queue persistence not implemented in bus. |
| 17 | Pattern matching save | `tests/unit/test_pattern_engine_matching.py` | `test_save_pattern_matches_success`, `test_save_pattern_matches_invalid_format_raises` | FAIL | PatternEngine missing `save_pattern_matches()` with validation and DB save. |
| 18 | CLI/Services | `tests/unit/test_cli.py` | `test_list_events` | FAIL | CLI missing `list_events` command. |
| 19 | CLI/Services | (doc: test_cli_commands.py) | `test_task_create_calls_service` | FAIL | Task service not wired for create via CLI or missing method. |
| 20 | CLI/Services | `tests/unit/test_contribution_tracker.py` | `test_start_and_stop_session` | FAIL | Contribution tracker missing proper `start_session`/`stop_session` behavior. |
| 21 | Other | `tests/unit/test_integration_pipeline_robustness.py` | (2 failures) | FAIL | Pipeline retry and DLQ behavior. |
| 22 | Other | `tests/unit/test_pattern_engine_dbscan.py` | (3 failures) | FAIL | DBSCAN clustering / concept scoring not implemented or incompatible. |
| 23 | Other | `tests/unit/test_retry_persistence_across_restart.py` | (1 failure) | FAIL | Retry state not persisted across restarts. |

---

## 3. Summary counts

| Kind | Count | Notes |
|------|-------|------|
| Confirmed test failures (run and failed) | 2 | critical_paths RAG config + DB isolation |
| Collection errors (chromadb/pydantic) | 6 | Same root cause in RAG/chromadb path |
| Collection errors (MCP) | 1 | enhanced_rag_server import / exit |
| Documented failures (from TEST_STATUS_AND_FIXES) | 23 | Pattern engine, NL dev, routing, broker, CLI, pipeline, DBSCAN, retry |
| Documented errors (from TEST_STATUS_AND_FIXES) | 6 | Previously reported as errors in full run |

---

## 4. Detective checklist (next steps)

- [ ] **Chromadb/Pydantic:** Fix or isolate chromadb config (e.g. type for `chroma_server_nofile`, or skip chromadb import in test env / use adapter).
- [ ] **Test env DB:** Force in-memory DB in test (e.g. `DATABASE_URL` or test fixture) so `test_database_is_memory` passes.
- [ ] **MCP:** Install `mcp` or make enhanced_rag_server import optional so integration tests can collect.
- [ ] **Pattern engine:** Implement RAG context, MIST detection, and `save_pattern_matches()` per TEST_STATUS_AND_FIXES.
- [ ] **NL dev:** Implement modify/delete/rollback in CodeGenerator.
- [ ] **Routing:** Implement priority queue ordering and heuristic router pipeline integration.
- [ ] **Broker/DLQ:** Implement retry record and DLQ persistence; wire into pipeline and restart persistence.

Use the table rows above as case numbers when referring to a specific failure or error during investigation.
