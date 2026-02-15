# Codex SDK Diagnostics

Minimal Node-based diagnostics runner for Codex SDK threads.

## Setup

1. Ensure Node.js 18+ is installed.
2. From `e:\grid\scripts\codex-sdk`, install dependencies:

```bash
npm install
```

3. Add your API key in `e:\grid\.env`:

```
OPENAI_API_KEY=your_key_here
```

## Modes

### diagnose (default)

Parse an optional CI log, compose a prompt, and ask Codex to diagnose failures:

```bash
npm run diagnose -- --prompt "Diagnose CI failures" --followup "Implement the plan" --ci-log path/to/ci.log
```

### fix-plan

Parse a CI log, generate a structured remediation plan mapping failures to
concrete repo commands, then ask Codex to refine it:

```bash
npm run fix-plan -- --ci-log path/to/ci.log
```

In fix-plan mode `--prompt` is optional (a default is provided) and `--ci-log` is **required**.

## CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--mode <mode>` | `diagnose` or `fix-plan` | `diagnose` |
| `--prompt <text>` | Primary Codex prompt | *(required in diagnose)* |
| `--followup <text>` | Follow-up prompt | *(none)* |
| `--threadId <id>` | Resume a thread | *(new thread)* |
| `--out <path>` | Output JSON path | `output/latest.json` |
| `--ci-log <path>` | CI log file to parse | *(none)* |
| `--ci-context <n>` | Context lines per failure block | `8` |
| `--ci-max-blocks <n>` | Max failure blocks captured | `6` |

## Output

The script writes a JSON file containing the thread ID, CI parse results,
fix plan (if fix-plan mode), and Codex run history.

## VS Code Tasks

- **Codex: Diagnose CI** — runs diagnose mode with prompted inputs
- **Codex: Fix Plan** — runs fix-plan mode; prompts for CI log path

## Remediation Catalogue

The fix-plan mode maps CI indicators to repo commands:

| Indicator | Commands |
|-----------|----------|
| `gha_error` | `ruff check .`, `ruff check . --fix && black .` |
| `pytest_failures` | `pytest tests/ -v --tb=short`, `pytest --last-failed` |
| `traceback` | `pytest tests/ -v --tb=long` |
| `exception` | `mypy src/` |
| `npm_error` | `npm ci` (frontend), `npm run build` |
| `test_failure` | `pytest tests/ -v` |
| `exit_code` | `pytest tests/ -v --tb=short` |

Unmapped indicators fall back to lint + test + type-check.
