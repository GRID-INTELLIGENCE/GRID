# Policy and Principles as Code Context

Policy and principles from [docs/PRINCIPLES.md](../PRINCIPLES.md) and [.cursor/devprograms/GLOBAL_CONFIG.md](../../.cursor/devprograms/GLOBAL_CONFIG.md) are available as **machine-readable config** that **changes runtime behavior** and the project's reach of networks and calls.

---

## Config: `config/policy.yaml`

Single source of truth for runtime:

- **Principles:** `principles.transparency`, `principles.openness`, `principles.freedom_to_think`, `principles.access_default`, `network_and_external_api_allowed_by_default`
- **Network reach:** `network.allowed` — when `true`, runtime may perform outbound network calls
- **External API reach:** `external_api.allowed` — when `true`, runtime may call external AI providers (OpenAI, Anthropic, etc.)
- **Tool policy:** `blocked_tools`, `protected_tools`, `blocked_tools_allowlist` — which tools may be blocked and which must never be blocked

Edit `config/policy.yaml` to change runtime behavior; keep it in sync with PRINCIPLES.md and GLOBAL_CONFIG.md.

---

## Code context: `tools.runtime_policy`

Load policy in code and branch on it:

```python
from tools.runtime_policy import (
    get_policy,
    is_network_allowed,
    is_external_api_allowed,
    is_tool_allowed,
    get_blocked_tools,
    get_protected_tools,
    get_principles,
)

# Change runtime behavior from config
if is_network_allowed():
    # allow outbound HTTP / network calls
    ...

if is_external_api_allowed():
    # allow calls to OpenAI, Anthropic, etc.
    ...

if is_tool_allowed("external_api"):
    # allow use of external_api tool
    ...

# Full context for agents or middleware
ctx = get_policy()
# ctx["network"]["allowed"], ctx["external_api"]["allowed"], ctx["blocked_tools"], ...
```

- **Config path:** By default `config/policy.yaml` under repo root. Override with env `GRID_POLICY_PATH` (file path or directory; if directory, `config/policy.yaml` under it is used).
- **Caching:** Policy is cached; use `load_policy(reload=True)` or `clear_cache()` to re-read the file.

---

## Tests

- [tests/config/test_devprograms_external_api_access.py](../../tests/config/test_devprograms_external_api_access.py) — asserts GLOBAL_CONFIG.md does not block external API/network (doc-level).
- [tests/config/test_runtime_policy.py](../../tests/config/test_runtime_policy.py) — asserts `config/policy.yaml` loads and that `is_network_allowed()`, `is_external_api_allowed()`, protected tools not blocked, etc.

Run both:

```bash
uv run pytest tests/config/ -v
```

---

## Activation and persistence

- **Active:** Policy is active whenever this repo is used. On first use of `tools.runtime_policy` (e.g. `is_network_allowed()`, `is_external_api_allowed()`), `config/policy.yaml` is loaded and cached. No separate "activation" step is required; the presence of `config/policy.yaml` and the runtime_policy module makes policy effective.
- **Persistent:** Practices are kept persistent by CI. The Minimal CI workflow (`.github/workflows/minimal-ci.yml`) runs on every push to `main` and every pull request and **must** pass:
  - Policy and governance tests: `tests/config/test_devprograms_external_api_access.py`, `tests/config/test_runtime_policy.py`, `tests/test_external_llm_provider.py`
  - Ruff lint on `src/`, `safety/`, `security/`, `boundaries/`
  Any change that blocks external API/network by default or removes policy tests will fail CI. Do not bypass these checks; they enforce transparency and openness.

---

## Flow

```text
PRINCIPLES.md + GLOBAL_CONFIG.md (human-facing)
        |
        v
config/policy.yaml (machine-readable, single source for runtime)
        |
        v
tools.runtime_policy (load + expose is_network_allowed, is_tool_allowed, ...)
        |
        v
Agents, MCP, API, CLI use these to allow or deny network/external calls and tools
```

---

**Last updated:** 2026-02-17
