# Agent Orchestration Plugin and Role Delegation

**Purpose:** Outline where and how to add an **agent orchestration plugin**, **role delegation**, and external plugins (Cursor team kit, Compound engineering, Context7, Parallel) into the current plan and codebase.

---

## 1. Is there room? Yes.

The existing architecture already has clear extension points; none of them currently support pluggable orchestration or third-party team/context backends.

| Layer | Current behavior | Room for orchestration plugin |
|-------|------------------|-------------------------------|
| **AgentExecutor** ([src/grid/agentic/agent_executor.py](src/grid/agentic/agent_executor.py)) | Fixed `task_handlers` map (e.g. `/plan` → `_execute_plan`). Role is passed as `agent_role` but not used to select backend. | Plugin can sit **before** `_execute_task_by_type`: by (task, agent_role) choose “internal handler” vs “delegate to plugin”. |
| **Mothership GhostRegistry** ([src/application/mothership/api_core.py](src/application/mothership/api_core.py)) | Handlers loaded from YAML (`load_handlers_from_config`). Key + module + attr. | Add orchestration handlers (e.g. `orchestration.cursor_team_kit`) and call them from agentic router or executor. |
| **SkillRegistry** ([src/grid/skills/registry.py](src/grid/skills/registry.py)) | Discovers and registers skills from `grid.skills`. | Optional: discover “orchestration skills” that implement a small interface (e.g. `delegate(case_id, role, task, context)`) and register as backends. |
| **MCP** (e.g. [mcp-setup/server](mcp-setup/server)) | Tools exposed via MCP; Cursor/Windsurf can invoke them. | Cursor team kit / Compound / Context7 / Parallel can be wrapped as **MCP tools** (e.g. “run_team_plan”, “get_compound_context”) and invoked by the agent or by a thin orchestration plugin. |

So: there is room at the **agent execution layer** (plugin that chooses who runs the task) and at the **integration layer** (MCP or HTTP adapters to external systems).

---

## 2. Agent orchestration plugin – where it fits

```text
  Request (case_id, agent_role, task)
       |
       v
  [AgentExecutor.execute_task]
       |
       v
  [NEW: OrchestrationPlugin.resolve(case_id, agent_role, task, reference)]
       |
       +-- returns "internal" --> use existing _execute_task_by_type (current behavior)
       |
       +-- returns "delegate: cursor_team_kit" --> call Cursor team kit adapter
       +-- returns "delegate: compound"         --> call Compound adapter
       +-- returns "delegate: context7"         --> call Context7 adapter
       +-- returns "delegate: parallel"          --> call Parallel adapter
       v
  Execute (internal handler or plugin adapter), then continue with trace/timeout/recovery as today.
```

- **Placement:** Between “task + role known” and “run handler”. One clear place is inside `AgentExecutor`: after determining `agent_role` and `task`, call an **orchestration plugin** (or registry of plugins) that returns either “use internal handler” or “delegate to &lt;plugin_id&gt;”.
- **Interface (conceptual):**
  - `resolve(case_id, agent_role, task, reference) -> Literal["internal"] | DelegationTarget`
  - `DelegationTarget = { "provider": "cursor_team_kit" | "compound" | "context7" | "parallel", "params": {...} }`
- **Default:** If no plugin is configured or plugin returns “internal”, keep current behavior (existing task_handlers map).

This preserves the current plan (test/CI, unblockers, fixes) and adds a single, optional delegation step.

---

## 3. Delegate a specific role

- **Today:** `agent_role` is already passed through: [AgentExecutor.execute_task](src/grid/agentic/agent_executor.py) (and from API [routers/agentic.py](src/application/mothership/routers/agentic.py)) and used for tracing, timeout, and learning. It is **not** used to select a different execution backend.
- **With orchestration plugin:**
  - **Role → backend mapping:** e.g. in config or inside the plugin: “Analyst” → internal, “Engineer” → Compound, “Reviewer” → Cursor team kit, “Research” → Context7, “Parallel” → Parallel.
  - **Delegate a specific role:** When the plugin resolves to a delegation target, it passes the same `agent_role` (and optionally `reference`, `case_id`, `task`) to the adapter. The adapter is responsible for translating that into the external system’s notion of role/team (e.g. Cursor “agent”, Compound “workflow”, etc.).
- So “delegate a specific role” = orchestration plugin selects **which** backend runs the task for that role; the backend receives the role and does role-specific behavior on its side.

---

## 4. Incorporate Cursor team kit, Compound, Context7, Parallel

Two main integration patterns:

### A. Adapter plugins (recommended for “compound engineering / context7 / parallel”)

- **Interface:** Each external system has an adapter that implements a small contract, e.g.:
  - `run_plan(case_id, agent_role, task, reference, context) -> dict`
  - or `get_context(case_id, query) -> dict` and `execute_step(step_spec) -> dict`
- **Registration:** Either:
  - **Config-driven:** In the same style as GhostRegistry, add a YAML (or env) that lists orchestration backends: `cursor_team_kit`, `compound`, `context7`, `parallel` with module path and enabled roles/tasks; orchestration plugin loads and calls the right adapter.
  - **Code registry:** A simple `OrchestrationBackendRegistry` that maps provider id → adapter instance; the orchestration plugin calls `registry.get(provider_id).run_plan(...)`.
- **Cursor team kit / Compound / Context7 / Parallel:** Implement one adapter per system. Each adapter talks to the external API or CLI (Cursor team kit, Compound engineering, Context7, Parallel) and normalizes the response so the rest of GRID still sees a single “task result” shape.

### B. Expose as MCP tools

- **Use case:** When the integration is “the agent (or user) chooses when to call this” rather than “orchestrator always delegates this role to this backend”.
- **How:** Add MCP tools, e.g.:
  - `run_cursor_team_kit_plan` (inputs: case_id, role, plan_json)
  - `compound_engineering_step` (inputs: step_spec, context)
  - `context7_query` (inputs: query, scope)
  - `parallel_execute` (inputs: steps[], strategy)
- The agent (or a thin “orchestration” skill) can then call these tools when it decides to delegate. The orchestration plugin can still **decide** to “delegate” and then invoke the corresponding MCP tool internally so that role-based delegation remains centralized.

### C. Compound / parallel execution (already partially present)

- **SkillCallingEngine** ([src/grid/skills/calling_engine.py](src/grid/skills/calling_engine.py)) already has `CallStrategy.PARALLEL` and `asyncio.gather` for parallel skill execution.
- **MultiModelOrchestrator** ([src/grid/knowledge/multi_model_orchestrator.py](src/grid/knowledge/multi_model_orchestrator.py)) does parallel expert inquiry.
- An orchestration plugin could:
  - Map a task like “parallel_review” to a “Parallel” adapter that uses the same pattern (e.g. spawn N steps in parallel, aggregate).
  - Or wrap “Compound” so that a single “compound” step is implemented by calling multiple sub-steps in parallel or in a DAG, reusing existing parallel patterns.

---

## 5. Concrete next steps (within the current plan)

1. **Define the orchestration plugin interface** (e.g. in `grid.agentic.orchestration`): `resolve(...)` and optional `run_delegated(...)` so that the executor can call one place for “who runs this?” and “run it.”
2. **Add a single “internal” plugin** that always returns “internal” (current behavior) and register it as default so no behavior change until explicitly configured.
3. **Add one adapter** (e.g. Cursor team kit or Compound) as a proof of concept: implement the adapter interface, register it, and add a role → “delegate: cursor_team_kit” (or compound) mapping in config.
4. **Optionally expose the same backends as MCP tools** so that Cursor/Windsurf or other clients can call them directly when not using role-based delegation.
5. **Document** role → backend mapping and how to add new plugins (Cursor team kit, Compound, Context7, Parallel) in a short “Orchestration plugins” section in the main docs.

This keeps the existing plan (tests, CI, unblockers, run_command fix) intact and adds a clear, optional path for agent orchestration, role delegation, and external plugins.
