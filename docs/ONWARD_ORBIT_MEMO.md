# Onward orbit memo (one screen)

**Orbit legend:** Green = pushed + lint green + scoped tests green. Yellow = pushed but full `make test` still failing elsewhere on main. Red = do not execute until triaged.

## Pointers (path | branch | unpushed | last gate)

**Canonical procedure (OIS):** `roots/python-craft/docs/INTEGRITY_SYNC_BATCH_ALGORITHM.md` — integrity → sync → push → memo row; includes dated checkpoint table and `hogsmade` worked example.

| Repo                                 | Branch        | Unpushed                      | Last gate                                                                                                                                                          |
| ------------------------------------ | ------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CascadeProjects/Projects/GRID-main` | main          | 0 (pushed `d5ca8cd..1bd212f`) | `make lint` OK; `make test` **5 failures** (sandbox in-process env + auth refresh 401) — not RAG-commit blockers; subset `TestRAGEngineBasic` + `test_rag_init` OK |
| `CascadeProjects/Projects/Vision`    | main          | 0 / 0 vs `origin/main`        | Dirty (tracked + untracked `docs/`, workflow, tests); `uv run pytest` not re-run for this memo row                                                                 |
| `roots/python-craft`                 | main          | 0 / 0 vs `origin/main`        | OIS runbook `docs/INTEGRITY_SYNC_BATCH_ALGORITHM.md` tracked locally; **push** `roots/python-craft` to publish; `uv run pytest` collects **0** tests (no suite yet) |
| `CascadeProjects` (monorepo root)    | hogsmade      | **8 / 1** vs `origin/hogsmade` | Dirty: glimpse-artifact, shared-types, echoes/eligibility; untracked GATE JSON + viz HTML — **OIS:** `S=stash_all` then rebase train (see OIS Part 2.2)          |


## Post-push checks (this batch)

**RAG `where` + hybrid:** `[src/tools/rag/rag_engine.py](../src/tools/rag/rag_engine.py)` — if `use_hybrid` and `where` are both set, a **warning** is logged and the filter is **ignored** (non-vector hybrid path). Vector path passes `where` through `vector_store.query`.

**RAG MCP sessions:** store is `Path.home() / ".rag-sessions" / "sessions.json"` — **outside the repo**; ensure home perms and **no API keys** in session metadata before sharing disks.

## Ecosystem sweep (classify next)

- **Vision:** modified CONTRIBUTING/README/pyproject/cli/tests + new `docs/`, `ci-ocr-smoke.yml`, `test_ui_ux_surface_reference.py` — commit as small PRs or one docs+tests PR.
- **python-craft:** OIS runbook under `docs/` committed on `main` locally — **push** to publish; no `.cursor/` noise on current snapshot.
- **CascadeProjects:** `hogsmade` **ahead 1 / behind 8** + dirty tree — **no blind `git add .`**; use OIS stash → `pull --rebase` → `stash pop` → push; submodule pointer commits only with explicit `P`.

## Remote note

GitHub reported Dependabot vulnerabilities on default branch after push; track via repo Security tab (not blocking push).