# Final: Runtime Logic and Plan Finalization

**Source:** Runtime logic and plan finalization plan, merged with thread responses (run_command debug, hypotheses, reproduction steps, fix code, unblockers/moves/subagent).  
**Status:** Final version for execution and reference.

---

## 1. Runtime logic shortcomings (identified)

### 1.1 Timeout not applied to agent execution

- **Where:** [src/grid/agentic/agent_executor.py](src/grid/agentic/agent_executor.py) lines 101–115.
- **Issue:** `timeout_ms` is computed and stored in `trace.metadata["timeout_applied_ms"]` but **never used**. `recovery_engine.execute_with_recovery(...)` runs with **no** `asyncio.timeout()` wrapper, so execution can hang indefinitely.
- **Fix:** Wrap the recovery execution in `asyncio.timeout(timeout_ms / 1000)`. On `TimeoutError`, end trace with failure, record in timeout_manager, and re-raise or return a structured timeout result (e.g. API 504).

### 1.2 Recovery engine

- **Where:** [src/grid/agentic/recovery_engine.py](src/grid/agentic/recovery_engine.py). Optional: add `timeout_seconds` to `execute_with_recovery` and wrap each attempt in `asyncio.timeout(timeout_seconds)`.

### 1.3 Command execution timeout (MCP) — full thread context below

- **Where:** [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py) `run_command`.
- **Issue:** `asyncio.wait_for(..., timeout)` wraps only `create_subprocess_exec`; `await result.communicate()` has **no timeout**, so the event loop can block indefinitely.

### 1.4 GracefulShutdown wait logic

- **Where:** [src/application/mothership/utils/timeout_management.py](src/application/mothership/utils/timeout_management.py) `GracefulShutdown.wait_for_shutdown_complete`.
- **Issue:** After `request_shutdown()`, `_shutdown_event` is set so `await self._shutdown_event.wait()` returns immediately; the loop is meant to wait for `_active_operations == 0` but the wait is on the wrong condition.
- **Fix:** Use explicit polling with `asyncio.sleep(1)` until `_active_operations == 0` or deadline, or use an `asyncio.Condition` notified when operations drain.

### 1.5 asyncio.get_event_loop() in async context

- **Where:** cpu_executor, timeout_management, tool_registry, event_bus, graceful_degradation, api_docs, engine (see runtime plan).
- **Fix:** Replace `get_event_loop()` with `get_running_loop()` where the call site is guaranteed async; add try/except fallback only where sync call is possible.

---

## 2. run_command debug plan and fix (from thread)

Instrumentation is already in [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py). The follow-up fix (full timeout) should be applied in Agent mode or by hand. Below: hypotheses, instrumentation, reproduction steps, exact fix code, and unblockers.

### 2.1 Hypotheses (why the thread halts and async rhythm is lost)

1. **H1:** In `run_command`, `asyncio.wait_for` only wraps `create_subprocess_exec`. So `await result.communicate()` has **no timeout** and can block the event loop indefinitely when the subprocess hangs or produces a lot of output.
2. **H2:** Any MCP tool that uses `run_command` (e.g. `performance_profiler`, `security_auditor`) can hang the handler when the underlying command runs long or blocks, so the caller never gets a response.
3. **H3:** There is no unblock path: once the event loop is stuck in `communicate()`, nothing can time out or trigger a recovery move/subagent.
4. **H4:** The frontend `executePlan` has no per-step timeout, so a single hanging tool call blocks the whole plan.
5. **H5:** Pipe buffering (full stdout/stderr) can cause the subprocess to block on write and `communicate()` to wait forever.

Instrumentation in `enhanced_tools_mcp_server.py` logs:

- **run_command entry** (H1): `cmd`, `timeout`
- **run_command process_created** (H1): after `create_subprocess_exec`
- **run_command before_communicate** (H1): immediately before `await result.communicate()`
- **run_command after_communicate** (H1): after `communicate()` returns
- **run_command timeout** (H3): on `TimeoutError` (currently only for process start)

If the thread gets stuck, you should see **entry → process_created → before_communicate** and **never** **after_communicate**, which confirms H1/H2/H5. Seeing **timeout (create_subprocess only)** would mean the timeout only fired on process start (H3).

### 2.2 Reproduction steps

1. Delete any existing `debug-14d2f0.log` in the workspace root (e.g. `e:\GRID-main\debug-14d2f0.log`) so the run is clean.
2. Start the enhanced tools MCP server (or whatever process invokes `run_command` in this repo).
3. Trigger a tool that runs a long or blocking command (e.g. a command that sleeps 60s or runs indefinitely, or a tool that calls `run_command` with such a command).
4. Let it run until the UI/thread “halts” (no response, plan/command appears stuck).
5. Stop the run and open `debug-14d2f0.log`. Check for the sequence: `run_command entry` → `process_created` → `before_communicate` and absence of `after_communicate` (and optional `timeout`).
6. If you changed code, restart the MCP server (or the app that runs the plan) before reproducing again.

After reproducing and capturing logs, share the relevant lines (or confirm entry → process_created → before_communicate and no after_communicate) to lock the fix to evidence.

### 2.3 Fix to apply (run_command full timeout)

Apply in **Agent mode** or by hand. In [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py), **replace** the current `run_command` implementation (the whole `async def run_command(...):` body, including the existing debug logs) with the following so that **both** process start **and** `communicate()` are under one timeout. That restores the await/async rhythm and prevents the thread from getting stuck in `communicate()`.

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

Keep all existing `_debug_log` calls and regions; only the structure of `run_command` and the new `_run_process_and_communicate` helper change.

### 2.4 Unblockers and helpers (design: moves / subagent autostarters)

- **Unblocker 1 – Full timeout (above):** Timeout around the full run (process start + `communicate()`), plus kill on timeout so the event loop never stays stuck in `communicate()`.
- **Unblocker 2 – Run with “on stuck” callback:** A helper that runs the same command with the same timeout and, on `TimeoutError`, calls an optional callback (e.g. “move” or “start subagent”) before returning the timeout result:
  - `run_command_with_unblock(cmd, cwd, timeout, on_timeout=...)`
  - Implementation: call the fixed `run_command` (or the same logic) inside `asyncio.wait_for`; in the `except TimeoutError` block, call `on_timeout(cmd, timeout)` then return `{"success": False, "error": "Command timed out after ...", "returncode": -1}`.

- **Moves (when stuck):**
  - **Move A:** Return a structured timeout result so the UI/plan can show “step timed out” and continue to the next step instead of hanging.
  - **Move B:** Emit an event or enqueue a “recovery” task (e.g. “run in background” or “retry with shorter timeout”) that a subagent or background worker can pick up.

- **Subagent autostarters:** When a timeout fires (or after N consecutive timeouts), call a small “subagent starter” that:
  - Creates a task (e.g. `asyncio.create_task(run_command_async(...))`) with a longer timeout or different params, or
  - Sends a message to an MCP “subagent” tool (e.g. “run_command_background”) so the work continues in another process/thread while the main plan continues.

Concrete placement:

- Add `run_command_with_unblock` in [mcp-setup/server/enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py) (or in a shared `mcp-setup/server/async_unblockers.py` module) that wraps the fixed `run_command` and invokes `on_timeout` on timeout.
- In the frontend, wrap `await tool.execute(parsed.data)` in [frontend/src/lib/tool-executor.ts](frontend/src/lib/tool-executor.ts) with `Promise.race([tool.execute(...), new Promise((_, rej) => setTimeout(() => rej(new Error('Step timeout')), stepTimeoutMs))])` and treat rejection as a failed step (optionally triggering a “move” or retry). That addresses H4.

---

## 3. How this ties into the broader plan

- **Order:** Runtime hardening first (timeouts and shutdown logic) so the system cannot hang or shut down incorrectly. Then test/CI remediation (chromadb, DB URL, MCP import, then the 23 failures) so CI is green. Optionally add orchestration plugin and unblocker/subagent logic per [docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md](docs/AGENT_ORCHESTRATION_PLUGIN_DESIGN.md) and the debug-session unblocker design.
- **Single checklist:** (1) AgentExecutor timeout application, (2) run_command full timeout, (3) GracefulShutdown fix, (4) get_running_loop replacements, (5) Test Phase 1 unblock collection and two confirmed failures, (6) Test Phase 2 documented failures, (7) CI smoke/lint/unit green, (8) optional orchestration and unblockers.

---

## 4. Implementation summary (concise)

| Item | File(s) | Change |
|------|---------|--------|
| Apply agent execution timeout | [agent_executor.py](src/grid/agentic/agent_executor.py) | Wrap `recovery_engine.execute_with_recovery(...)` in `async with asyncio.timeout(timeout_ms/1000):`; on TimeoutError, end trace, record, re-raise or return timeout result. |
| run_command full timeout | [enhanced_tools_mcp_server.py](mcp-setup/server/enhanced_tools_mcp_server.py) | Use `_run_process_and_communicate` and wrap process + communicate in one `wait_for`/timeout; on timeout kill process. See Section 2.3 for full code. Remove or keep debug logs per workflow. |
| GracefulShutdown wait | [timeout_management.py](src/application/mothership/utils/timeout_management.py) | In `wait_for_shutdown_complete`, wait until `_active_operations == 0` or deadline using `asyncio.sleep(1)` polling (or Condition); do not use `_shutdown_event.wait()` for this. |
| get_running_loop | cpu_executor, timeout_management, tool_registry, event_bus, graceful_degradation, api_docs, engine | Replace `get_event_loop()` with `get_running_loop()` where call site is always async; add try/except fallback only where sync call is possible. |
| Optional: recovery timeout | [recovery_engine.py](src/grid/agentic/recovery_engine.py) | Add optional `timeout_seconds` to `execute_with_recovery`; wrap each attempt in `asyncio.timeout(timeout_seconds)`. |
| Optional: frontend step timeout | [tool-executor.ts](frontend/src/lib/tool-executor.ts) | `Promise.race(tool.execute(...), new Promise((_, rej) => setTimeout(() => rej(new Error('Step timeout')), stepTimeoutMs)))` with configurable stepTimeoutMs. |

---

## 5. Other runtime consistency and polish

- **Lifespan shutdown:** [src/application/mothership/main.py](src/application/mothership/main.py) shutdown order is sensible; ensure any new background tasks are cancelled and resources disposed in the same block.
- **Handler invocation:** [src/application/mothership/api_core.py](src/application/mothership/api_core.py) `summon_handler` already uses `asyncio.timeout` and `asyncio.to_thread` for sync handlers.
- **Docs:** Add a short “Runtime and timeouts” section: agent execution bounded by adaptive timeout; MCP command runs bounded by single timeout over process+communicate; handler invocations bounded by handler timeout; shutdown waits for active operations up to a deadline. Reference [timeout_management.py](src/application/mothership/utils/timeout_management.py) and [api_core.py](src/application/mothership/api_core.py).
- **Tests:** Add or extend a unit test for AgentExecutor that a long-running task is aborted after the configured timeout; add a test for GracefulShutdown that after request_shutdown and draining operations, wait_for_shutdown_complete returns within the deadline.
