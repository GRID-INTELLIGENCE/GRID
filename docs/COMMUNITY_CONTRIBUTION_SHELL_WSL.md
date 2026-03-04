# Community contribution: Shell integration & WSL documentation

How this checkpoint’s docs relate to the broader community and where they can be referenced (e.g. GitHub, VS Code).

---

## 1. What we contributed (in this repo)

| Document | Content | Community relevance |
|----------|--------|---------------------|
| **SHELL_INTEGRATION_SCRIPT_REPORT.md** | SHA256 verification, authenticity, safety, alignment with VS Code docs and PowerShell best practices | No official hash/integrity doc exists; this fills the gap for Cursor/VS Code users and enterprises |
| **WSL_STATUS_AND_PENDING_STEPS.md** | WSL status checks, E: mount fix, optional Python/uv in WSL | Reusable checklist for “full install from WSL” |
| **LINUX_BASH_SCOPE.md** | Linux/Bash install, WSL, script reference, recommendations | Single reference for GRID + generic Linux/Bash in VS Code/Cursor workflows |

---

## 2. GitHub / VS Code context (enterprise-grade search)

### Relevant VS Code issues (microsoft/vscode)

| Issue | Title | State | Relevance |
|-------|--------|--------|------------|
| [#235298](https://github.com/microsoft/vscode/issues/235298) | `shellIntegration.ps1` adds additional errors to `$Error` | Closed (not_planned), locked | Our report documents this as “$Error pollution” and cites the issue |
| [#267344](https://github.com/microsoft/vscode/issues/267344) | Terminal Shell Integration breaks multi-line commands in PowerShell | Closed (duplicate), locked | Workaround in profile (F12,c → AddLine); our report doesn’t change this |
| [#266674](https://github.com/microsoft/vscode/issues/266674) | (Parent for Shift+Enter) | — | Duplicate chain for multi-line PowerShell |

**Finding:** No open issue or doc in VS Code for “how to verify shell integration script integrity (hash)”. Our report is complementary: it doesn’t fix the script but gives users and enterprises a way to verify the file and understand safety.

### Where this can be shared

- **VS Code Discussions:** “Terminal” or “Documentation” — post a short note and link to the report (e.g. in your fork or repo) for “verifying shell integration script integrity (SHA256, safety).”
- **Cursor / VS Code community:** Same idea — “community doc for script verification and safety” with link.
- **PR to microsoft/vscode-docs:** Optional. The [Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration) page could add a short “Verifying script integrity” subsection (hash + reproducibility commands). Our report can be the source text for that.

---

## 3. Quality and relevance (aligned with “enterprise-grade” run)

- **Verification:** SHA256 and multiple reproducibility commands (PowerShell, cmd, certutil, WSL).
- **Safety:** LanguageMode, no eval of untrusted input, env handling, known issues ($Error, AllSigned) documented.
- **Alignment:** Matches VS Code shell integration docs (OSC 633, behavior); clarifies “no OSC 7 fallback” and Windows-specific behavior.
- **Actionable:** Steps for re-verification after updates, execution policy, and enterprise handling.

---

## 4. Push as community contribution

1. **Push your branch** (after local commit per `COMMIT_PLAN_SHELL_WSL_DOCS.md`):
   ```bash
   git push origin <your-branch-name>
   ```
2. **Optional: open a PR** to the main GRID repo (e.g. `main` or `develop`) with title like:  
   `docs: shell integration integrity report, WSL status, Linux/Bash scope`.
3. **Optional: VS Code community**  
   - In [VS Code Discussions](https://github.com/microsoft/vscode/discussions), post in “Documentation” or “Terminal” with a short summary and a link to your report (e.g. raw or rendered in your fork).  
   - Or propose a small doc change to [vscode-docs](https://github.com/microsoft/vscode-docs) (e.g. “Verifying shell integration script integrity”) using text from our report.

---

## 5. One-line summary

**We added verification and safety documentation for the Cursor/VS Code PowerShell shell integration script (SHA256, authenticity, best practices) and consolidated WSL/Linux-Bash docs; these can be pushed as a docs-only commit and shared with the VS Code/Cursor community as a reference for integrity and safety.**

---

*References: SHELL_INTEGRATION_SCRIPT_REPORT.md, WSL_STATUS_AND_PENDING_STEPS.md, LINUX_BASH_SCOPE.md, COMMIT_PLAN_SHELL_WSL_DOCS.md.*
