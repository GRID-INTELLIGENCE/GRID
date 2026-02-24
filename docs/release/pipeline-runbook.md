# Pipeline Green Runbook

This runbook defines the standard execution and post-execution routine for shipping changes with a fully green CI/CD pipeline.

## Scope

- Source updates
- Workflow updates
- Version/changelog alignment
- Documentation updates
- Release readiness

## Pre-Execution

1. Start from a clean feature branch off `main`.
2. Confirm no generated artifacts are tracked:
   - `frontend/coverage/`
   - release scratch logs
3. Confirm metadata consistency:
   - `pyproject.toml` version == latest `CHANGELOG.md` heading.
4. Run local baseline checks:
   - `uv run ruff check .`
   - `uv run pytest -q --tb=short`
   - `npm --prefix frontend run lint`
   - `npm --prefix frontend run test`
   - `npm --prefix frontend run build`
   - `uv run python -m build`
   - `uv run twine check dist/*`

## Execution

1. Apply code and workflow changes in small, reviewable commits.
2. Keep CI deterministic:
   - Pin toolchain versions where possible.
   - Avoid hidden local assumptions.
3. Update docs and project files in the same PR:
   - `README.md`
   - `CHANGELOG.md`
   - `CONTRIBUTING.md`
   - relevant architecture/status docs.

## Remote Validation

1. Open PR with test evidence and risk notes.
2. Require all workflows for the PR branch to pass.
3. For failures:
   - Fix deterministic failures in code/config.
   - Re-run transient infrastructure flakes once.
   - If flake repeats, treat as actionable and patch.

## Merge Gate

Merge only when:

1. All workflow checks are green.
2. Version/changelog metadata check passes.
3. Build/package verification passes.

## Post-Execution

1. Verify all workflows are green on `main` merge commit.
2. Verify package artifacts and release metadata.
3. Publish short release summary including:
   - commit hash
   - workflow run links
   - residual risks/follow-ups.
4. If release-tagging, tag only after `main` is green.

## Rollback

If post-merge CI regresses:

1. Revert the smallest offending commit set.
2. Re-run full workflow suite.
3. Re-apply fix on a fresh branch and repeat the gate.
