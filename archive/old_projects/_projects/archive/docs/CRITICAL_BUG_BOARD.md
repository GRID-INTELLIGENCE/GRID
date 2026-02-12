# Critical Bug Board

## Overview
This board tracks all open critical issues that must be resolved before the next release. Updated automatically from GitHub issues labeled `critical`.

## Current Critical Issues

<!-- This section should be populated by running:
gh issue list --label critical --state open --json number,title,assignees,createdAt,updatedAt -q '.[] | {number, title, assignees: (.assignees | map(.login) | join(", ")), created: .createdAt, updated: .updatedAt}'
-->

| Issue # | Title | Assignees | Created | Updated | Status |
|---------|-------|-----------|---------|---------|--------|
| #XXX | [Placeholder] Critical issue title | Unassigned | YYYY-MM-DD | YYYY-MM-DD | Open |
| #YYY | [Placeholder] Another critical issue | Unassigned | YYYY-MM-DD | YYYY-MM-DD | Open |

## Resolution Process
1. **Triage**: Assign owner and priority within 24 hours
2. **Analysis**: Root cause identified within 2 days
3. **Fix**: Implementation completed within 5 days
4. **Testing**: Regression tests added and CI passes
5. **Close**: Issue tagged as `triaged` and closed

## Metrics
- **Total Critical**: 2
- **Open**: 2
- **Resolved This Sprint**: 0
- **Average Resolution Time**: TBD

## Commands
```bash
# Export current list
gh issue list --label critical --state open --json number,title,assignees,createdAt,updatedAt > critical_issues.json

# Update this file
python scripts/update_critical_board.py
```

## Last Updated
2025-10-11 21:18 UTC
