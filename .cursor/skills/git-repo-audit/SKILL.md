---
name: git-repo-audit
description: Run a repeatable git vs non-git audit and report untracked-but-should-track files under .cursor/skills, .cursor/rules, .cursor/agents, and scripts allowlist. Use when the user asks for git audit, repo audit, what's not tracked, or session verify in a git sense.
---

# Git and repo audit

Produce a short markdown report on tracked vs untracked state and scripts allowlist.

## Steps

1. **Status and ignore check**
   - Run `git status --porcelain`.
   - For key paths, run `git check-ignore -v <path>` (e.g. `src/`, `tests/`, `.cursor/skills/`, `.cursor/rules/`, `.cursor/agents/`, `scripts/assert_no_debug_in_prod.py`).

2. **Compare with .gitignore**
   - Confirm `.cursor/skills/`, `.cursor/rules/`, `.cursor/agents/` are tracked (negated in .gitignore).
   - Confirm `scripts/*.py` is ignored except the allowlist (see .gitignore "SCRIPTS" section).

3. **List untracked in shared Cursor dirs**
   - From `git status --porcelain`, list any untracked (??) files under `.cursor/skills/`, `.cursor/rules/`, `.cursor/agents/` that might be intended for sharing.

4. **Scripts allowlist**
   - Remind that `scripts/assert_no_debug_in_prod.py` and other allowlisted scripts must be tracked; if a script is used in CI or Makefile, it must be in the allowlist and committed.

## Output format

Short markdown report:

```markdown
# Git repo audit (YYYY-MM-DD)

## Status
- Clean / Uncommitted changes: [summary]

## Untracked in .cursor (trackable)
- .cursor/skills/: [list or "none"]
- .cursor/rules/: [list or "none"]
- .cursor/agents/: [list or "none"]

## Scripts allowlist
- assert_no_debug_in_prod.py: [tracked/allowlisted]
- [any other CI/Makefile script]: [status]

## Recommendations
- [Any action: add to allowlist, commit, or document as local-only]
```

## References

- docs/TOOL_INVENTORY.md — tracked scripts and tools
- docs/CONFIG_CONSOLIDATION_REPORT.md — .gitignore and .cursor coverage
- AGENTS.md — "Weekly git / coverage audit" section
