# Staging & commit plan: Shell integration + WSL docs checkpoint

Tailored plan to stage and commit the documentation checkpoint, then push as community contribution.

---

## 1. Scope of this commit (one concern)

**Theme:** Documentation checkpoint — shell integration integrity report, WSL status, Linux/Bash scope, and project acknowledgement.

**Files to include:**

| Path | Purpose |
|------|--------|
| `docs/SHELL_INTEGRATION_SCRIPT_REPORT.md` | Integrity, safety, authenticity, SHA256, reproducibility commands |
| `docs/WSL_STATUS_AND_PENDING_STEPS.md` | WSL status check results and pending steps for full install |
| `docs/LINUX_BASH_SCOPE.md` | Linux/Bash installation, recommendations, script reference |
| `docs/project/ACKNOWLEDGEMENT.md` | Checkpoint entry under Additional Acknowledgements |

**Exclude from this commit:** All other modified/untracked files (search guardrail, memory roadmap, finetuning, etc.) so this commit stays single-concern.

---

## 2. Pre-commit verification (already run)

- [x] `scripts\quick_diagnostic.ps1` — ran successfully (WSL + E: checks)
- [x] No changes to application code in this set; unit tests not required for docs-only

---

## 3. Staging commands

From repo root (`E:\Seeds\GRID-main`):

```powershell
git add docs/SHELL_INTEGRATION_SCRIPT_REPORT.md
git add docs/WSL_STATUS_AND_PENDING_STEPS.md
git add docs/LINUX_BASH_SCOPE.md
git add docs/project/ACKNOWLEDGEMENT.md
git status
```

Confirm only these four files are staged.

---

## 4. Commit message (conventional)

```
docs: shell integration integrity report, WSL status, Linux/Bash scope, acknowledgement checkpoint

- SHELL_INTEGRATION_SCRIPT_REPORT: SHA256, authenticity, safety, best practices, reproducibility commands
- WSL_STATUS_AND_PENDING_STEPS: command-line check results, pending E: mount and optional Python/uv steps
- LINUX_BASH_SCOPE: consolidated Linux/Bash install, WSL, scripts reference, recommendations
- ACKNOWLEDGEMENT: documentation checkpoint (March 2026) for shell integration and WSL docs
```

One-line variant (if preferred):

```
docs: shell integration report, WSL status, Linux/Bash scope, and acknowledgement checkpoint
```

---

## 5. Commit

```powershell
git commit -m "docs: shell integration integrity report, WSL status, Linux/Bash scope, acknowledgement checkpoint

- SHELL_INTEGRATION_SCRIPT_REPORT: SHA256, authenticity, safety, best practices, reproducibility commands
- WSL_STATUS_AND_PENDING_STEPS: command-line check results, pending E: mount and optional Python/uv steps
- LINUX_BASH_SCOPE: consolidated Linux/Bash install, WSL, scripts reference, recommendations
- ACKNOWLEDGEMENT: documentation checkpoint (March 2026) for shell integration and WSL docs"
```

---

## 6. After local commit: push and community contribution

- Push branch to origin: `git push origin feature/search-service-guardrail` (or your branch name).
- See `docs/COMMUNITY_CONTRIBUTION_SHELL_WSL.md` for GitHub issue search summary and how to reference this work (e.g. in VS Code discussions or community docs).

---

*Plan created for single-concern docs commit; adjust branch name and remote as needed.*
