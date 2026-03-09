# AGENTS.md — AI Agent Guidelines for GRID

Keep .gitignore and env docs aligned with workspace baseline: **E:\\Seeds\\ECOSYSTEM_BASELINE.md**.

For build, test, lint, and commit conventions, see repository root **E:\\AGENTS.md** and **docs/CONFIG_CONSOLIDATION_REPORT.md**.

**Dependency groups (pyproject.toml):** Default dev setup: `uv sync --group dev --group test`. Optional: `--group finetuning` for torch/transformers (RAG intent classifier model); without it, intent classification uses rule-based fallback. Wheel packages: grid, application, cognitive, tools, mycelium, search, infrastructure, unified_fabric, vection.

## Security guardrails

API and app attack-surface guardrails (auth, input sanitization, no debug in production, webhook signature, etc.) are defined and tracked in **E:\\docs\\API_ATTACK_SURFACE_GUARDRAILS_AND_TODOS.md**. Endpoint inventory and debug-audit references: **E:\\Seeds\\ENDPOINT_INVENTORY.md**, **E:\\Seeds\\DEBUG_AUDIT.md**.

Key controls:
- **Auth:** All agentic routes require `RequiredAuth`. Admin routes use `AdminAuth`. Search admin uses `_require_admin` with identity list.
- **Body limits:** Mothership 10 MB (`RequestSizeLimitMiddleware`), Safety 50 KB, Knowledge Base 5 MB, RAG Chat 1 MB.
- **Timeouts:** Knowledge Base 60 s, RAG Chat 30 s per request.
- **Error handling:** Generic 500 in production — no `str(e)` to client (G8).
- **Debug flags:** `scripts/assert_no_debug_in_prod.py` — wire into CI and Session Verify to block DEBUG/ENABLE_DEV_TOKEN in production.
- **Outbound URLs:** Any outbound HTTP to user- or config-supplied URLs (webhooks, callbacks, redirects) must call `application.mothership.utils.validate_url_allowlist` before requesting (SSRF mitigation).
- **Tests:** `uv run pytest tests/api/test_phase3_security_guardrails.py tests/security/test_attack_surface_guardrails.py tests/api/test_security_governance.py -v`
