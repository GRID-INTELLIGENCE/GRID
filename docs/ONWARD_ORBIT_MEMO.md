# Onward orbit memo (one screen)

**Orbit legend:** Green = pushed + lint green + scoped tests green. Yellow = pushed but full `make test` still failing elsewhere on main. Red = do not execute until triaged.

## Pointers (path | branch | unpushed | last gate)

| Repo | Branch | Unpushed | Last gate |
|------|--------|----------|-----------|
| `CascadeProjects/Projects/GRID-main` | main | 0 (pushed `d5ca8cd..1bd212f`) | `make lint` OK; `make test` **5 failures** (sandbox in-process env + auth refresh 401) — not RAG-commit blockers; subset `TestRAGEngineBasic` + `test_rag_init` OK |
| `CascadeProjects/Projects/Vision` | (local dirty) | many | not run this session |
| `roots/python-craft` | (local dirty) | n/a | `.cursor/` untracked |
| `CascadeProjects` (monorepo root) | — | submodule + files | mixed; see `git status` |

## Post-push checks (this batch)

**RAG `where` + hybrid:** [`src/tools/rag/rag_engine.py`](../src/tools/rag/rag_engine.py) — if `use_hybrid` and `where` are both set, a **warning** is logged and the filter is **ignored** (non-vector hybrid path). Vector path passes `where` through `vector_store.query`.

**RAG MCP sessions:** store is `Path.home() / ".rag-sessions" / "sessions.json"` — **outside the repo**; ensure home perms and **no API keys** in session metadata before sharing disks.

## Ecosystem sweep (classify next)

- **Vision:** modified CONTRIBUTING/README/pyproject/cli/tests + new `docs/`, `ci-ocr-smoke.yml`, `test_ui_ux_surface_reference.py` — commit as small PRs or one docs+tests PR.
- **python-craft:** `pyproject.toml`/`uv.lock` + untracked `.cursor/`, `tests/` — decide track vs gitignore for `.cursor/commands` if desired in-repo.
- **CascadeProjects:** submodule `Projects/GRID-main`, shared-types, MCP servers, untracked GATE/viz — **no blind `git add .`**; submodule pointer update **after** confirming remote GRID matches local (done).

## Remote note

GitHub reported Dependabot vulnerabilities on default branch after push; track via repo Security tab (not blocking push).
