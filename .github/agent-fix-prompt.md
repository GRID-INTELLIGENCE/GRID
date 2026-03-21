You are fixing the current pull request branch inside the GRID repository.

Constraints:

- Work only on this PR branch.
- Do not merge or rebase.
- Follow the checked-in repo contract and contributor guidance.
- Python 3.13+ only. Use `uv run` for all commands — never bare `python` or `pip`.
- Never weaken validation in safety/, security/, or boundaries/ modules.
- Never use eval(), exec(), or pickle.
- Run `uv run ruff check .` and `uv run pytest tests/unit/ -q --tb=short` after changes.
- Prefer the smallest fix set that gets the PR back to green.

Your job is to resolve failing checks, reviewer feedback, and clear regressions without widening scope.
