# Tool and script inventory

Short reference for main tools and scripts and whether they are tracked in git. See [CONFIG_CONSOLIDATION_REPORT.md](CONFIG_CONSOLIDATION_REPORT.md) for .gitignore and config alignment.

## Tracked scripts (root `scripts/`)

These are explicitly allowlisted in `.gitignore` (negated after `scripts/*.py`):

| Script | Purpose |
|--------|---------|
| `scripts/assert_no_debug_in_prod.py` | Production guard: exit non-zero if DEBUG/ENABLE_DEV_TOKEN etc. when GRID_ENV=production. Used by CI and `make guard-no-debug`. |
| `scripts/track_commit.py` | Commit tracking / session hygiene. |
| `scripts/validate_venv.py` | Virtual environment health check. |
| `scripts/validate_security.py` | Security validation (auth, sanitization, parasite guard, etc.). |
| `scripts/migrate_secrets_to_gcp.py` | Migrate secrets to GCP. |
| `scripts/deploy_security_config.py` | Deploy security configuration. |
| `scripts/setup.py` | Project setup. |
| `scripts/__init__.py` | Package marker. |
| `scripts/agent_setup.ps1` | Agent setup (PowerShell). |

All other `scripts/*.py` files are **ignored** by default (ad-hoc or local-only).

## Source packages (`src/`)

All code under `src/` is tracked unless matched by a specific .gitignore rule. Main tool-related packages:

| Path | Purpose |
|------|---------|
| `src/tools/rag/` | RAG engine: indexing, retrieval, embeddings, LLM adapters, chat CLI. |
| `src/tools/forensics/` | Log analysis, simulated attacks, filesystem monitoring. |
| `src/tools/security/` | Vulnerability scanner, security monitoring. |
| `src/tools/slash_commands/` | Slash command sync and CI helpers. |
| `src/tools/agent_prompts/` | Agent prompts, case filing, processing units. |
| `src/tools/interfaces_dashboard/` | Interfaces dashboard and collector. |
| `src/tools/crypto/` | Crypto utilities (e.g. grid_bet). |
| `src/tools/` (root) | RAG engine entry, runtime policy, databricks connector, inventory, etc. |

## Cursor and IDE

| Path | Tracked | Purpose |
|------|---------|---------|
| `.cursor/skills/` | Yes | Shared agent skills. |
| `.cursor/rules/` | Yes | Shared rules (.mdc). |
| `.cursor/agents/` | Yes | Shared subagent definitions. |
| `.cursor/commands/` | No | Local-only; not in allowlist. |
| `.vscode/extensions.json`, `.vscode/tasks.json` | Yes | Recommended extensions and tasks. |

## Verification

- **Scripts allowlist:** See `.gitignore` section "SCRIPTS" (around lines 596–611). When adding a new tracked script, add `!scripts/<name>.py` (or `.ps1`).
- **Weekly audit:** See [AGENTS.md](../AGENTS.md) section "Weekly git / coverage audit".
