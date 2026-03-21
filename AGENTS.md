# AGENTS.md — AI Agent Guidelines for GRID

Keep .gitignore and env docs aligned with workspace baseline: **docs/ECOSYSTEM_BASELINE.md** (or the seed-level copy).

For build, test, lint, and commit conventions, see this file and **docs/CONFIG_CONSOLIDATION_REPORT.md**.

**Dependency groups (pyproject.toml):** Default dev setup: `uv sync --group dev --group test`. Optional: `--group finetuning` for torch/transformers (RAG intent classifier model); without it, intent classification uses rule-based fallback. Wheel packages: grid, application, cognitive, tools, mycelium, search, infrastructure, unified_fabric, vection.

## Security guardrails

API and app attack-surface guardrails (auth, input sanitization, no debug in production, webhook signature, etc.) are defined and tracked in **docs/API_ATTACK_SURFACE_GUARDRAILS_AND_TODOS.md**. Endpoint inventory and debug-audit references: **docs/ENDPOINT_INVENTORY.md**, **docs/DEBUG_AUDIT.md**.

Key controls:
- **Auth:** All agentic routes require `RequiredAuth`. Admin routes use `AdminAuth`. Search admin uses `_require_admin` with identity list.
- **Body limits:** Mothership 10 MB (`RequestSizeLimitMiddleware`), Safety 50 KB, Knowledge Base 5 MB, RAG Chat 1 MB.
- **Timeouts:** Knowledge Base 60 s, RAG Chat 30 s per request.
- **Error handling:** Generic 500 in production — no `str(e)` to client (G8).
- **Debug flags:** `scripts/assert_no_debug_in_prod.py` — wire into CI and Session Verify to block DEBUG/ENABLE_DEV_TOKEN in production.
- **Outbound URLs:** Any outbound HTTP to user- or config-supplied URLs (webhooks, callbacks, redirects) must call `application.mothership.utils.validate_url_allowlist` before requesting (SSRF mitigation).
- **Tests:** `uv run pytest tests/api/test_phase3_security_guardrails.py tests/security/test_attack_surface_guardrails.py tests/api/test_security_governance.py -v`

## Weekly git / coverage audit

Run periodically (e.g. weekly or pre-release) to keep tracked vs untracked and .gitignore accurate:

1. **Quick check:** `git status --porcelain` and `git check-ignore -v` for paths under `src/`, `tests/`, `.cursor/skills/`, `.cursor/rules/`, `.cursor/agents/`.
2. **Skill:** Use the **git-repo-audit** skill (`.cursor/skills/git-repo-audit/`) for a repeatable audit and short report.
3. **Subtractive analyst:** Invoke the subtractive-analyst subagent with a prompt focused on git tracked vs untracked and .gitignore recommendations.
4. **CI:** The pipeline already runs a "Git hygiene" step (no untracked in `src/` or `tests/`); fix any failures before merge.
