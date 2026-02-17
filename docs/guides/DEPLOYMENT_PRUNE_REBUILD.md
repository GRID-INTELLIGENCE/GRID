# Deployment: Collection of Pre-existing Patterns, Overheads, and Clean Prune-Rebuild

This guide explains where **pre-existing reward-hacking patterns and overheads** are collected at deployment, and how to **prune and rebuild** deployment so it stays clean.

---

## 1. What “reward hacking” and “overheads” mean here

- **Reward-hacking patterns:** Config or code that **optimizes for a signal** (build passes, lint green, coverage OK) without fixing root causes. Examples: adding another `extend-ignore` or `per-file-ignores` instead of fixing the violation; expanding `exclude` or `mypy.overrides` so more code is hidden from checks; suppressing warnings globally instead of fixing the issue.
- **Overheads at deployment:** Accumulated configuration that makes the **build and deploy** heavier and harder to reason about: long exclude lists, many mypy overrides, duplicated or obsolete paths, and tool-specific ignores that pile up over time.

The **collection process** is simply: every time we work around a failure by adding an exclude, an override, or an ignore, that entry is “collected” into `pyproject.toml` (and sometimes `.cursor`/CI). Over time this becomes a large, opaque set of rules that can hide real issues and make deployment and CI slower and noisier.

---

## 2. Where these are collected (single place: `pyproject.toml` + related)

| Layer | Section | What gets collected | Effect at deployment |
|-------|---------|---------------------|----------------------|
| **Wheel build** | `[tool.hatch.build.targets.wheel]` | `packages` + `exclude` | Only `src/grid`, `src/application`, `src/cognitive`, `src/tools` are packaged; everything in `exclude` is left out of the wheel. Redundant or overly broad excludes add mental overhead and can hide accidental includes. |
| **Ruff** | `[tool.ruff]` `exclude` | Dirs/files not linted | Grows when we exclude whole trees to “fix” lint. |
| **Ruff** | `[tool.ruff.lint]` `extend-ignore` | Rules turned off globally | Grows when we disable rules instead of fixing. |
| **Ruff** | `[tool.ruff.lint.per-file-ignores]` | Per-path rule exceptions | Grows when we add one more path/pattern instead of fixing. |
| **Mypy** | `[[tool.mypy.overrides]]` | Modules with `ignore_missing_imports` or relaxed checks | Grows when we add overrides for third-party or internal modules instead of typing them. |
| **Pytest** | `filterwarnings` | Warnings suppressed | Hides deprecations or other warnings instead of fixing. |
| **Coverage** | `omit` / `exclude_lines` | Code not measured | Can hide untested code if overused. |

Deployment (e.g. `uv build` or `pip install -e .`) uses the same `pyproject.toml`; the **wheel** is what gets built and installed. The other sections don’t change the wheel contents but add **maintenance and cognitive overhead** and can mask quality/reward-hacking (e.g. “we’re green because we excluded it”).

---

## 3. Collection process (how it accumulates)

1. **Build or CI fails** (lint, typecheck, test, import).
2. **Quick fix:** Add an exclude, override, or ignore in `pyproject.toml` (or rarely in a separate config).
3. **No cleanup:** Old excludes/overrides are rarely removed when code is removed or refactored.
4. **Result:** A growing list of path-based or rule-based exceptions that nobody audits, some redundant or obsolete (“reward hacking”: we “succeed” by excluding or ignoring more).

---

## 4. Prune-rebuild: how to keep deployment clean

### 4.1 Principles

- **Prefer fix over exclude/ignore:** Before adding an exclude or ignore, prefer fixing the underlying issue (typing, lint, test).
- **One place:** All deployment- and tool-relevant exclusions/overrides live in `pyproject.toml`; avoid scattering them in multiple config files.
- **Document rationale:** For each major exclude or override, a short comment or this doc should explain *why* (e.g. “third-party untyped”, “legacy script”, “generated code”).
- **Prune periodically:** As part of release or cleanup, remove entries for code that no longer exists and consolidate duplicates.

### 4.2 Prune checklist (before a clean rebuild)

- [ ] **Hatch `exclude`:** Remove paths that don’t exist or are already covered by a parent exclude (e.g. `core/` vs `core/**`). Keep only what’s needed so the wheel contains exactly `src/grid`, `src/application`, `src/cognitive`, `src/tools` and no unwanted trees.
- [ ] **Ruff `exclude`:** Same idea: drop obsolete dirs; avoid excluding more than needed so that new code under `src/` is linted by default.
- [ ] **Ruff `extend-ignore` / `per-file-ignores`:** Prefer fixing violations; if an ignore stays, document why. Remove per-file ignores for files that no longer exist.
- [ ] **Mypy overrides:** Merge duplicate module entries; remove overrides for code that was deleted. Prefer typing new code over adding more `ignore_missing_imports`.
- [ ] **Pytest `filterwarnings`:** Keep only what’s necessary (e.g. known third-party deprecations); fix or file issues for own code instead of suppressing.
- [ ] **Coverage `omit` / `exclude_lines`:** Don’t expand just to hit a target; remove omits for code that no longer exists.

### 4.3 Clean rebuild (verify deployment)

After pruning:

```bash
# From repo root
uv build
# Or: python -m build
```

Then:

- Install the built wheel in a clean env and run a minimal smoke test (e.g. `grid --help`, or import `grid`, `tools.runtime_policy`).
- Confirm no unintended code is included (e.g. no `api/`, `cli/`, `core/` in the wheel if they are excluded by design).

Optional: add a small CI step that builds the wheel and runs one import or CLI check so “clean deployment” is asserted on every run.

**Quick clean-rebuild check (after pruning):**

```bash
uv build
uv run python -c "import grid; import tools.runtime_policy; print('OK')"
```

---

## 5. Current deployment shape (summary)

- **Included in wheel:** `src/grid`, `src/application`, `src/cognitive`, `src/tools` (see `[tool.hatch.build.targets.wheel]` in `pyproject.toml`).
- **Excluded from wheel:** All entries under `exclude` (e.g. `src/api/**`, `src/core/**`, …). These are the main “collection” of paths that were intentionally kept out of deployment; pruning here keeps the list minimal and understandable.
- **Policy/runtime:** `config/policy.yaml` and `tools.runtime_policy` are part of the repo and can be loaded at runtime from the install; they are not packaged inside the wheel but live in the project tree (or env) where the app runs.

---

## 6. Relation to principles

- **Transparency:** Keeping a single, documented place for exclusions and overrides (pyproject) and pruning them so deployment is auditable aligns with transparent policy.
- **Openness:** Avoiding “reward hacking” (green build by excluding/ignoring more) keeps the bar for quality and openness high; prune-rebuild keeps deployment clean and intentional.

---

**Last updated:** 2026-02-17
