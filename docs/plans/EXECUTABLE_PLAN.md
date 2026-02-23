# Executable Plan: Runtime, Zero Failures, Green CI

**Merged from:** Final Zero Failures Green CI Strategy + Final Runtime and Plan Finalization.  
**Execution order:** Runtime hardening first, then test/CI unblock and fixes, then optional extensions.

---

## Todo list (check off in order)

### Runtime hardening (do first)

- [x] **R1** Apply agent execution timeout in [src/grid/agentic/agent_executor.py](src/grid/agentic/agent_executor.py): wrap `recovery_engine.execute_with_recovery(...)` in `async with asyncio.timeout(timeout_ms/1000):`; on TimeoutError end trace, record, re-raise or return timeout result.
- [x] **R2** run_command full timeout in [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py): add `_run_process_and_communicate`, wrap process + communicate in one `wait_for`/timeout; on timeout kill process. (Full code in Section A.3 below.)
- [x] **R3** GracefulShutdown wait fix in [src/application/mothership/utils/timeout_management.py](src/application/mothership/utils/timeout_management.py): in `wait_for_shutdown_complete` wait until `_active_operations == 0` or deadline using `asyncio.sleep(1)` polling (or Condition); do not use `_shutdown_event.wait()` for this.
- [x] **R4** Replace `get_event_loop()` with `get_running_loop()` in: cpu_executor, tool_registry, event_bus, graceful_degradation, api_docs, engine; timeout_management already fixed in R3. Engine uses get_running_loop() + except RuntimeError so schema init is skipped when no loop.
- [ ] **R5** (Optional) Add optional `timeout_seconds` to [src/grid/agentic/recovery_engine.py](src/grid/agentic/recovery_engine.py) `execute_with_recovery`; wrap each attempt in `asyncio.timeout(timeout_seconds)`.
- [ ] **R6** (Optional) Frontend step timeout in [frontend/src/lib/tool-executor.ts](frontend/src/lib/tool-executor.ts): `Promise.race(tool.execute(...), new Promise((_, rej) => setTimeout(() => rej(new Error('Step timeout')), stepTimeoutMs)))` with configurable stepTimeoutMs.

### Test/CI — unblock collection and two confirmed failures

- [x] **T1** Chromadb/Pydantic (cases #1, #3–#9): lazy-import chromadb in [chromadb_store.py](src/tools/rag/vector_store/chromadb_store.py); set `RAG_VECTOR_STORE_PROVIDER=in_memory` in [tests/conftest.py](tests/conftest.py) and CI. Outcome: no RAG collection errors; test_rag_config_from_env passes.
- [x] **T2** Test DB URL (case #2): [tests/conftest.py](tests/conftest.py) and [.github/workflows/ci.yml](.github/workflows/ci.yml) set `MOTHERSHIP_DATABASE_URL`. Outcome: test_database_is_memory passes on Windows and CI.
- [x] **T3** MCP (case #10): replaced `sys.exit(1)` with `raise ImportError(...)` in [src/grid/mcp/enhanced_rag_server.py](src/grid/mcp/enhanced_rag_server.py) so integration test module collects; tests skip when `mcp` is missing.

### Test/CI — eliminate remaining failures (#11–#23)

- [ ] **T4** Pattern engine RAG/MIST/save (#11–#13, #17): implement or stub per [docs/TEST_STATUS_AND_FIXES.md](docs/TEST_STATUS_AND_FIXES.md) “Simple Fix Logic”.
- [ ] **T5** NL dev modify/delete/rollback (#14): implement in CodeGenerator.
- [ ] **T6** Routing/priority queue (#15): implement priority queue ordering and HeuristicRouter pipeline integration.
- [ ] **T7** Broker/DLQ (#16, #21, #23): implement retry record and DLQ persistence; wire into pipeline and restart persistence.
- [ ] **T8** CLI (#18–#20): add `list_events`; wire task create; fix contribution tracker start_session/stop_session.
- [ ] **T9** DBSCAN and other (#22): implement or fix DBSCAN clustering / concept scoring and remaining unit tests.

### Test/CI — quality gates

- [ ] **T10** Smoke test: in [.github/workflows/ci.yml](.github/workflows/ci.yml) make `pytest tests/unit/ --collect-only -q` fail on non-zero exit (remove `|| echo "No tests found"`). Do after T1–T3 so collection is clean.
- [ ] **T11** (Optional) Integration in CI: remove `continue-on-error: true` for integration step in ci-main or add integration job to ci.yml; optionally mypy strict for subset of paths; address coverage threshold.

### Optional extensions

- [ ] **O1** Add `run_command_with_unblock(cmd, cwd, timeout, on_timeout=...)` in [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py) (or async_unblockers.py); call on_timeout on TimeoutError before returning timeout result.
- [ ] **O2** Agent orchestration plugin and role delegation per [docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md](docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md): add resolve/delegate layer before AgentExecutor handler selection; optional adapters for Cursor team kit, Compound, Context7, Parallel.

### Verification and docs

- [ ] **V1** Run `pytest tests/unit/ -v --tb=short` and confirm 0 failed, 0 errors (after T1–T9 as needed).
- [ ] **V2** Confirm CI (ci.yml) green: secrets_scan, smoke_test, lint, unit_tests all pass.
- [ ] **V3** Add short “Runtime and timeouts” section to dev/architecture doc: agent execution, MCP command, handler invocation, shutdown; reference timeout_management.py and api_core.py.
- [ ] **V4** (Optional) Unit test: AgentExecutor task aborted after configured timeout; GracefulShutdown wait_for_shutdown_complete returns within deadline after drain.

---

## Target outcome

- **Runtime:** No logical shortcomings: agent execution and MCP run_command bounded by timeout; shutdown waits for active operations; event loop API correct where async.
- **Test suite:** `pytest tests/unit/` and `pytest tests/integration/` (where run) report **0 failed, 0 errors**; **0 collection errors**.
- **CI green:** [ci.yml](.github/workflows/ci.yml) gate jobs pass: Unit Tests, Lint, Smoke Test.

---

## Appendix A: run_command fix (for R2)

### A.1 Why it hangs

- **H1:** `asyncio.wait_for` only wraps `create_subprocess_exec`; `await result.communicate()` has no timeout and can block the event loop.
- **H2:** MCP tools using `run_command` (e.g. performance_profiler, security_auditor) can hang the handler.
- **H3:** No unblock path once stuck in `communicate()`.
- **H4:** Frontend executePlan has no per-step timeout (optional fix R6).
- **H5:** Pipe buffering can cause subprocess to block and `communicate()` to wait forever.

### A.2 Reproduction (optional before applying R2)

1. Delete `debug-14d2f0.log` in workspace root.
2. Start enhanced tools MCP server; trigger a tool that runs a long or blocking command.
3. Let it halt; open `debug-14d2f0.log`. Expect: `run_command entry` → `process_created` → `before_communicate` and no `after_communicate`.

### A.3 Code for R2 (replace run_command body in enhanced_tools_mcp_server.py)

```python
async def _run_process_and_communicate(
    cmd: list[str], cwd: Path | None, timeout: int
) -> tuple[asyncio.subprocess.Process, bytes, bytes]:
    """Run subprocess and communicate; entire operation must complete within timeout (unblocks stuck communicate)."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd or session.workspace_root,
    )
    # region agent log
    _debug_log("run_command process_created", {"pid": process.pid}, "H1")
    _debug_log("run_command before_communicate", {}, "H1")
    # endregion
    try:
        async with asyncio.timeout(timeout):
            stdout, stderr = await process.communicate()
    except TimeoutError:
        process.kill()
        await process.wait()
        raise
    # region agent log
    _debug_log("run_command after_communicate", {"returncode": process.returncode}, "H1")
    # endregion
    return process, stdout or b"", stderr or b""


async def run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 30) -> dict[str, Any]:
    """Run command with timeout and error handling. Timeout covers both process start and communicate (avoids stuck thread)."""
    # region agent log
    _debug_log("run_command entry", {"cmd": cmd, "timeout": timeout}, "H1")
    # endregion
    try:
        process, stdout, stderr = await asyncio.wait_for(
            _run_process_and_communicate(cmd, cwd, timeout),
            timeout=timeout,
        )
        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="ignore"),
            "stderr": stderr.decode("utf-8", errors="ignore"),
        }
    except TimeoutError:
        # region agent log
        _debug_log("run_command timeout (full)", {"timeout": timeout}, "H3")
        # endregion
        return {"success": False, "error": f"Command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "error": str(e), "returncode": -1}
```

Keep existing `_debug_log` and regions; only the structure of `run_command` and the new helper change.

---

## Appendix B: Test/CI reference

- **Root causes:** [docs/TEST_FAILURES_DETECTIVE_REPORT.md](docs/TEST_FAILURES_DETECTIVE_REPORT.md) (case numbers #1–#23).
- **Simple fix logic:** [docs/TEST_STATUS_AND_FIXES.md](docs/TEST_STATUS_AND_FIXES.md).
- **CI behavior:** ci.yml Unit Tests (line 135) fails on any failure/error; Smoke (86) currently hides collection failures; Lint is strict; mypy uses `|| true`.

---

## Appendix C: Orchestration (optional O2)

- **Design:** [docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md](docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md).
- **Placement:** Between “task + role known” and “run handler” in AgentExecutor; `resolve(case_id, agent_role, task, reference)` returns “internal” or “delegate: &lt;provider&gt;”.
- **Role delegation:** Config maps roles to backends (e.g. Engineer → Compound, Reviewer → Cursor team kit).
- **Plugins:** Adapters (run_plan contract) and/or MCP tools for Cursor team kit, Compound, Context7, Parallel; Parallel can reuse SkillCallingEngine CallStrategy.PARALLEL and MultiModelOrchestrator.
