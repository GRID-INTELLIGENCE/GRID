# Final: Zero Failures / Green CI Strategy

**Source:** Zero failures green CI strategy plan, merged with thread responses (agent orchestration, role delegation, plugins).  
**Status:** Final version for execution and reference.

---

## 1. Target outcome

- **Test suite:** `pytest tests/unit/` and `pytest tests/integration/` (where run) report **0 failed, 0 errors**. Collection completes with **0 collection errors** (all test modules import and collect).
- **CI green:** Gate jobs in [ci.yml](.github/workflows/ci.yml) all pass: **Unit Tests**, **Lint** (ruff check + format), **Smoke Test** (imports + collection).

---

## 2. How CI currently behaves

- **Unit Tests** (ci.yml line 135): `uv run pytest tests/unit/ -v --tb=short` — no `|| true`; any failure or error fails the job.
- **Smoke Test** (line 86): `pytest tests/unit/ --collect-only -q 2>/dev/null || echo "No tests found"` — collection failures are currently hidden.
- **Lint:** `ruff check` and `ruff format --check` are strict; mypy uses `|| true`.
- **Green CI** = secrets_scan + smoke_test + lint + **unit_tests passing**. Integration in ci-main.yml has `continue-on-error: true` and does not block.

---

## 3. Root causes (from TEST_FAILURES_DETECTIVE_REPORT.md)

| Blocker | Impact | Fix complexity |
|--------|--------|----------------|
| Chromadb/Pydantic (#1, #3–#9) | 1 failure + 6 collection errors | Low–medium: type or lazy-import |
| Test DB URL (#2) | 1 failure | Low: env/fixture |
| MCP import exit (#10) | 1 integration collection error | Low: no sys.exit on import |
| Pattern engine / NL dev / routing / broker / CLI (#11–#23) | 23 documented failures | Medium: implement or stub |

---

## 4. Phased strategy

### Phase 1: Unblock collection and fix the two confirmed failures

1. **Chromadb/Pydantic (cases #1, #3–#9):** Fix or isolate in [src/tools/rag/vector_store/chromadb_store.py](src/tools/rag/vector_store/chromadb_store.py) (explicit Settings args, lazy-import, or test env `RAG_VECTOR_STORE_PROVIDER=in_memory`). Outcome: no RAG collection errors; test_rag_config_from_env runs/passes or skips with clear reason.
2. **Test DB URL (case #2):** Ensure [tests/conftest.py](tests/conftest.py) and CI env set `MOTHERSHIP_DATABASE_URL` so it is not overridden; optionally assert on `get_database_url()` in [tests/unit/test_critical_paths.py](tests/unit/test_critical_paths.py). Outcome: test_database_is_memory passes on Windows and CI.
3. **MCP (case #10):** Replace `sys.exit(1)` on import in enhanced_rag_server so integration test module collects; tests can skip when `mcp` is missing. Outcome: test_enhanced_rag_server collects.

After Phase 1, all unit tests run (no collection errors) and the two confirmed failures are fixed.

### Phase 2: Eliminate remaining test failures (#11–#23)

- Quick wins: Pattern engine RAG/MIST/save (#11–#13, #17), NL dev modify/delete/rollback (#14) using “Simple Fix Logic” in [docs/TEST_STATUS_AND_FIXES.md](docs/TEST_STATUS_AND_FIXES.md).
- Feature work: Routing/priority queue (#15), broker/DLQ (#16, #21, #23), CLI (#18–#20), DBSCAN (#22). Prioritize unit tests (CI gate) over integration.

### Phase 3: CI and quality gates (optional)

- Smoke test: fail on collection errors (remove `|| echo "No tests found"`) after Phase 1.
- Optionally require integration tests or add integration job to ci.yml; optionally make mypy strict for a subset of paths; address coverage threshold in ci-main.

---

## 5. Simple tweaks that get most of the way

- **Chromadb:** Explicit Settings args, lazy-import in chromadb_store, or test-only `RAG_VECTOR_STORE_PROVIDER=in_memory`.
- **DB URL:** Set `MOTHERSHIP_DATABASE_URL` in CI and conftest; optionally assert on `get_database_url()` in test.
- **MCP:** Remove or conditionalize `sys.exit(1)` on import so the integration module collects and can skip.

After these, all unit tests run and the two confirmed failures are gone; remaining work is the 23 documented failures. CI is green once Phase 1 + enough of Phase 2 yield 0 failed and 0 errors for `pytest tests/unit/`.

---

## 6. Agent orchestration, role delegation, and plugins (from thread)

There is room in this plan to add an **agent orchestration plugin**, **role delegation**, and plugins (Cursor team kit, Compound engineering, Context7, Parallel). Design is in [docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md](docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md).

### 6.1 Room in the plan

Existing layers support extension but do not yet support pluggable orchestration or third-party backends:

- **AgentExecutor** ([src/grid/agentic/agent_executor.py](src/grid/agentic/agent_executor.py)): fixed `task_handlers` map; `agent_role` is passed but not used to choose a backend. A plugin can sit **before** handler selection and return “internal” vs “delegate to X”.
- **GhostRegistry** ([src/application/mothership/api_core.py](src/application/mothership/api_core.py)): YAML-driven handler registration. Add orchestration handlers (e.g. `orchestration.cursor_team_kit`) and call them from the agentic layer.
- **SkillRegistry** / **MCP**: Skills and MCP tools can expose “run plan” or “get context”; orchestration plugin can call them when delegating.

### 6.2 Agent orchestration plugin

- **Where:** Between “task + role known” and “run handler” inside AgentExecutor (or a thin wrapper).
- **What it does:** `resolve(case_id, agent_role, task, reference)` returns either “internal” (keep current behavior) or “delegate: &lt;provider&gt;” (e.g. cursor_team_kit, compound, context7, parallel).
- **Default:** If no plugin or “internal”, behavior stays as today.

### 6.3 Delegate a specific role

- **Today:** `agent_role` is in the flow (tracing, timeout, learning) but not for choosing who runs the task.
- **With plugin:** Config or plugin logic maps roles to backends (e.g. “Engineer” → Compound, “Reviewer” → Cursor team kit). The plugin passes the same `agent_role` and context to the chosen adapter so the backend can do role-specific behavior.

### 6.4 Incorporate Cursor team kit / Compound / Context7 / Parallel

- **Adapter plugins:** One adapter per system with a small contract (e.g. `run_plan(case_id, agent_role, task, reference) -> result`). Register via YAML or code registry; orchestration plugin calls the right adapter by provider id.
- **MCP:** Expose each as MCP tools (e.g. `run_cursor_team_kit_plan`, `compound_engineering_step`, `context7_query`, `parallel_execute`) so the agent or UI can call them; orchestration plugin can use these when delegating.
- **Parallel:** Reuse [SkillCallingEngine](src/grid/skills/calling_engine.py) `CallStrategy.PARALLEL` and [MultiModelOrchestrator](src/grid/knowledge/multi_model_orchestrator.py); a “Parallel” adapter can wrap that or an external Parallel API.

### 6.5 Reference

- [docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md](docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md): integration points, flow diagram, interface, role→backend mapping, adapter vs MCP options, and concrete next steps. This remains additive to the test/CI and unblocker work.

---

## 7. Dependency and order summary

| Phase | What | Unblocks / Enables |
|-------|-----|--------------------|
| 1a | Chromadb/Pydantic fix or isolation | All RAG unit tests collect + run; test_rag_config_from_env |
| 1b | Test DB URL guaranteed in test env | test_database_is_memory |
| 1c | MCP import no sys.exit | Integration test collection |
| 2 | 23 documented failures (stubs + features) | 0 failed in unit (and optionally integration) |
| 3 | Smoke fail on collection errors; optional integration/mypy | Stricter green CI |
| Optional | Orchestration plugin and role delegation | Cursor/Compound/Context7/Parallel integration |
