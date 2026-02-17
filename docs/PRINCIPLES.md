# Core Values and Principles

THE GRID maintains the following as **non-negotiable** values. Configuration and tooling must align with them.

---

## Transparency

- **Policy is visible:** Where access to tools (e.g. external API, network) is defined—access is the default, restriction the exception—in version-controlled config, not hidden in runtime or proprietary layers.
- **Single source of truth:** Dev programs policy lives in [`.cursor/devprograms/GLOBAL_CONFIG.md`](../.cursor/devprograms/GLOBAL_CONFIG.md); changes are reviewable and auditable.
- **Verification is automated:** [tests/config/test_devprograms_external_api_access.py](../tests/config/test_devprograms_external_api_access.py) asserts that external API and network access are not blocked, so regressions are caught in CI.

---

## Openness

- **Freedom to think and open-source principles:** We practice access to ideas, AI providers, and the open web as core rights and values. Restricting external API, network, web search, or fetch capabilities would violate these principles; we do not block them by default.
- **Access to AI providers worldwide:** Normal function and access to AI providers globally are design goals. Config must not block `external_api` or `network` in a way that prevents RAG, agents, or services from using OpenAI, Anthropic, or other providers where the project intends to allow it.
- **Open config over hidden defaults:** Prefer explicit allow/block lists and documented rationale (e.g. comments in `GLOBAL_CONFIG.md`) over implicit or undocumented restrictions.
- **Principles are documented:** This document and linked config/reports are the canonical statement of these values; new contributors and automation can rely on them.

---

## How this is enforced

| Principle    | Where it lives | How it’s checked |
|-------------|----------------|-------------------|
| Transparency | `.cursor/devprograms/GLOBAL_CONFIG.md`, `docs/reports/` | Config review reports; Cursor rule [`.cursor/rules/external-api-policy.mdc`](../.cursor/rules/external-api-policy.mdc) |
| Openness     | Same config; no blocking of external_api/network by default | Pytest [tests/config/test_devprograms_external_api_access.py](../tests/config/test_devprograms_external_api_access.py) |
| **Runtime behavior** | [config/policy.yaml](../config/policy.yaml) (machine-readable) | Loaded by [tools.runtime_policy](../src/tools/runtime_policy.py); tests in [tests/config/test_runtime_policy.py](../tests/config/test_runtime_policy.py). Use `is_network_allowed()`, `is_external_api_allowed()`, `is_tool_allowed(name)` to drive runtime reach. |

Run the verification test (open-source principles and freedom to think as core rights and values):

```bash
uv run pytest tests/config/test_devprograms_external_api_access.py -v
```

These tests assert: no blocking of `external_api`, `network`, `web_search`, `mcp_web_fetch`, `fetch`, `http`, or `requests` (access to ideas, AI providers, and the open web are protected as core rights); only permitted blockers (e.g. `system_access`) allowed; `docs/PRINCIPLES.md` exists and enshrines transparency, openness, and access; global code_quality uses ruff and 120-char line length; and GLOBAL_CONFIG states core principles.

---

**Last updated:** 2026-02-17
