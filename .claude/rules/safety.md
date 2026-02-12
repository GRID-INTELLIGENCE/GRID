# Safety & Security Rules

Applies to: `safety/**`, `security/**`, `boundaries/**`

> ⚠️ These modules enforce THE GRID's security invariants. Extra caution required.

## Golden Rules
- **Never** remove or weaken existing validation logic
- **Never** add bypass paths or "dev mode" shortcuts
- **Always** maintain backward compatibility — these are deployed safety contracts
- **Always** add tests for any changes: `uv run pytest safety/tests -q --tb=short`
- **Always** preserve audit trail integrity — never modify log formats without review

## Architecture
- `safety/` — AI safety: detectors, escalation, guardian, audit logging, observability
- `security/` — Network monitoring, forensic analysis, incident response
- `boundaries/` — Boundary contracts (ownership transfer), overwatch, refusal logic

## Review Checklist
Before modifying any file here, consider:
1. Does this change weaken any security invariant?
2. Are existing tests still passing?
3. Is the audit trail preserved?
4. Could this introduce a bypass path?
