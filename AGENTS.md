# AGENTS.md — AI Agent Guidelines for GRID

Keep .gitignore and env docs aligned with workspace baseline: **E:\\Seeds\\ECOSYSTEM_BASELINE.md**.

For build, test, lint, and commit conventions, see repository root **E:\\AGENTS.md** and **docs/CONFIG_CONSOLIDATION_REPORT.md**.

**Dependency groups (pyproject.toml):** Default dev setup: `uv sync --group dev --group test`. Optional: `--group finetuning` for torch/transformers (RAG intent classifier model); without it, intent classification uses rule-based fallback. Wheel packages: grid, application, cognitive, tools, mycelium, search, infrastructure, unified_fabric, vection.
