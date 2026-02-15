# Development Discipline

Applies to: all work in this repository.

## Session Start Protocol
Before writing ANY new code in a session, run:
```
uv run python -m pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```
If tests fail, fix them before doing anything else. The wall must hold.

## Commit Discipline
- One commit, one concern. Security fixes separate from features separate from refactoring.
- Use conventional commits: `fix(security):`, `feat(cognition):`, `refactor(rag):`, `test(safety):`, `docs(adr):`
- Always verify tests pass before committing.

## Decision Logging
When making architectural decisions (new abstractions, pattern choices, dependency additions), append to `docs/decisions/DECISIONS.md`:
```
## YYYY-MM-DD — [Topic]
**Decision**: [What was decided]
**Why**: [One sentence rationale]
**Alternatives considered**: [What was rejected and why]
```

## Security Rotation (Weekly)
Rotate threat review focus:
- Week 1: `safety/` (detectors, middleware, escalation)
- Week 2: `security/` (network interceptor, forensics)
- Week 3: `boundaries/` (boundary engine, overwatch, refusal)
- Week 4: Cross-cutting (auth, rate limiting, audit trail integrity)

## Performance Budget
- Full test suite must complete in < 30 seconds.
- If exceeded, profile with `--durations=10` and fix before adding more tests.
- Single-module tests during development; full suite before commit.

## Complexity Check
Before adding a new abstraction, ask:
1. Does a similar abstraction already exist in the codebase?
2. Can this be done with existing patterns instead?
3. Will this be tested? If not testable, it shouldn't exist.
