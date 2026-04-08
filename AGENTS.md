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

## Debugging scope windows

Treat `GRID-main` as four separate debugging/refactor surfaces. Do not widen scope unless a contract change forces it.

- **Python service window:** `src/<domain>` plus the matching `tests/<domain>` and only the minimum related `config/` or `schemas/` files.
- **Frontend renderer window:** `frontend/src` only. Start with `make frontend-typecheck`, then `make test-frontend`.
- **Electron window:** `frontend/electron` and Electron-specific config only. Use `make electron-build` after renderer checks are green.
- **Landing window:** `landing/` and its brand-generation scripts only. Use `make landing-validate`.

Default debugging order:

1. Reproduce inside one window only.
2. Run the smallest real gate for that window.
3. Fix the failing layer before widening to adjacent surfaces.
4. Re-run the narrow gate, then the full window gate.

Practical notes from the current workspace snapshot:

- `frontend` is the heaviest application surface in the repo; most of its size is `frontend/node_modules`.
- The frontend test runner is Vitest. Use plain `npm test`; do not use Jest-only flags such as `--runInBand`.
- Root `make test` is a backend safety slice, not full-repo confidence.

## Coverage integrity workflow

Use these commands as the canonical coverage diagnostics:

- `make coverage-backend` for the core backend slice (`tests/unit`, `tests/security`, `tests/api`) and root `coverage.json`.
- `make coverage-mycelium` for focused module validation (`src/mycelium`).

If a module appears unexpectedly low or `0%`, run focused module coverage before assuming tests are missing.
For example, `tests/mycelium` currently validates high module coverage even when broader slice artifacts can under-represent it.

### Git hygiene and source protection

- Honor each repo’s **`.gitignore`** and **`core.excludesfile`** (`~/.config/git/ignore` when configured). Treat ignored paths as non-source; do not `git add` generated artifacts (`dist/`, `build/`, `.next/`, `coverage/`, `.venv/`, `node_modules/`, `*.tsbuildinfo`), caches, local env files, or IDE scratch unless the human explicitly overrides.
- Be deliberate with git: use **`git status`** / **`git diff`** before staging; avoid blind **`git add .`**. Do not **force-push** or rewrite **history** unless the human asks. For **GRID-main** under CascadeProjects, follow this repo’s GRID/submodule rules in `CLAUDE.md`.
- **Source vs generated:** Edit source trees and generators; do not hand-edit `dist/` or lockfiles without clear intent.
- **Secrets:** Never commit API keys, tokens, or `.env` secrets. If something sensitive is tracked or staged, stop, flag it, add ignore rules, and involve the human for **`git rm --cached`** or history cleanup / rotation.
- **Templates / audit:** `~/seed/templates/gitignore-*.template`, `~/scripts/gitignore-audit.sh`.

