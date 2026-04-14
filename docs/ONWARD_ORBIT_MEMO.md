# Onward orbit memo (one screen)

**Orbit legend:** Green = pushed + lint green + scoped tests green. Yellow = pushed but full `make test` still failing elsewhere on main. Red = do not execute until triaged.

## Pointers (path | branch | unpushed | last gate)

**Canonical procedure (OIS):** `roots/python-craft/docs/INTEGRITY_SYNC_BATCH_ALGORITHM.md` — integrity → sync → push → memo row; **Part 2.1** is git-grounded (overrides seeds/dashboard lag for these four paths).

| Repo                                 | Branch        | Unpushed                      | Last gate                                                                                                                                                          |
| ------------------------------------ | ------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CascadeProjects/Projects/GRID-main` | main          | **0 / 0** vs `origin/main` (clean) | Memo/OIS commits **pushed**; `make lint` OK; `make test` still **5 failures** (sandbox + auth 401) per last full run — subset `TestRAGEngineBasic` + `test_rag_init` OK |
| `CascadeProjects/Projects/Vision`    | main          | 0 / 0 vs `origin/main`        | Dirty (tracked + untracked `docs/`, workflow, tests); `uv run pytest` not re-run for this memo row                                                                 |
| `roots/python-craft`                 | main          | **0 / 0** vs `origin/main` (clean) | OIS runbook **pushed** on `origin/main`; `uv run pytest` collects **0** tests (no suite yet); `ruff check` reports pre-existing issues in `src/craft/` (lock-in smoke, not blocking docs) |
| `CascadeProjects` (monorepo root)    | hogsmade      | **0 / 0** vs `origin/hogsmade` | **Lock-in:** rebased + **pushed** (`pull --rebase --autostash` after `stash` failure). **Submodule:** `Projects/GRID-main` tracks this repo’s **`origin/main`**; concrete gitlink + hogsmade bump SHAs live in **OIS Part 2.1** (single checkpoint, avoids memo drift). Tracked clean; optional untracked GATE JSON + viz HTML only |


## Post-push checks (this batch)

**RAG `where` + hybrid:** `[src/tools/rag/rag_engine.py](../src/tools/rag/rag_engine.py)` — if `use_hybrid` and `where` are both set, a **warning** is logged and the filter is **ignored** (non-vector hybrid path). Vector path passes `where` through `vector_store.query`.

**RAG MCP sessions:** store is `Path.home() / ".rag-sessions" / "sessions.json"` — **outside the repo**; ensure home perms and **no API keys** in session metadata before sharing disks.

## Ecosystem sweep (classify next)

- **Vision:** modified CONTRIBUTING/README/pyproject/cli/tests + new `docs/`, `ci-ocr-smoke.yml`, `test_ui_ux_surface_reference.py` — commit as small PRs or one docs+tests PR.
- **python-craft:** OIS runbook **published** on `origin/main` (lock-in); refresh **OIS Part 2.1** after future edits.
- **CascadeProjects:** `hogsmade` **synced** (0/0); submodule **tracks GRID `origin/main`** — see **OIS Part 2.1** for pinned SHAs. Untracked GATE/viz only if you choose to track them; never blind `git add .`.

## Remote note

GitHub reported Dependabot vulnerabilities on default branch after push; track via repo Security tab (not blocking push).