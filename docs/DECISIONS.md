# Decision Log

> Machine-readable explicit decision tracking for GRID project.
> Format: YAML frontmatter in each entry for automated parsing.

---

## Format Specification

Each decision follows this structure:

```yaml
---
id: DEC-XXX
date: YYYY-MM-DD
category: ARCHITECTURE | PROCESS | DEPENDENCY | SECURITY | TESTING
status: PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED
impact: LOW | MEDIUM | HIGH | CRITICAL
reversible: true | false
supersedes: DEC-XXX  # optional
---
```

---

## Decisions

### DEC-001: Establish Structured Decision Log

```yaml
---
id: DEC-001
date: 2025-12-05
category: PROCESS
status: ACCEPTED
impact: LOW
reversible: true
---
```

**Context**: Project decisions were implicit and scattered across commits.

**Decision**: Create `DECISIONS.md` with machine-readable YAML frontmatter.

**Rationale**:
- Enables automated auditing and compliance checks
- Provides clear traceability for architectural choices
- Reduces knowledge loss when team members change

**Consequences**:
- All significant decisions must be logged here
- Automation scripts can parse and validate decisions
- Historical decisions remain searchable

---

### DEC-002: Single Source of Truth for Pytest Config

```yaml
---
id: DEC-002
date: 2025-12-05
category: TESTING
status: ACCEPTED
impact: MEDIUM
reversible: true
---
```

**Context**: Pytest configuration was duplicated between `pytest.ini` and `pyproject.toml`.

**Decision**: `pyproject.toml` is the authoritative source for pytest markers, addopts, and testpaths. `pytest.ini` only contains settings not supported by pyproject.toml.

**Rationale**:
- Reduces configuration drift
- Single file to update for test settings
- Follows Python packaging best practices

**Consequences**:
- Developers update `pyproject.toml` for test config
- `pytest.ini` is supplementary only (norecursedirs, filterwarnings)

---

### DEC-003: Grid Namespace for All Imports

```yaml
---
id: DEC-003
date: 2025-12-05
category: ARCHITECTURE
status: ACCEPTED
impact: HIGH
reversible: false
---
```

**Context**: Legacy code used `vinci_code.*` namespace, new code uses `grid.*`.

**Decision**: Standardize on `grid.*` namespace for all imports.

**Rationale**:
- Consistent import paths across codebase
- Matches package name in pyproject.toml
- Reduces confusion for new contributors

**Consequences**:
- Legacy `vinci_code` references must be migrated
- Import errors indicate namespace violation

---

### DEC-004: Structured JSON Logging

```yaml
---
id: DEC-004
date: 2025-12-05
category: ARCHITECTURE
status: ACCEPTED
impact: MEDIUM
reversible: true
---
```

**Context**: Logging was inconsistent across modules.

**Decision**: Implement structured JSON logging with correlation IDs.

**Rationale**:
- Machine-readable logs for automated analysis
- Request tracing via correlation IDs
- Log aggregation compatibility (ELK, Datadog, etc.)

**Consequences**:
- All modules use `config.logging_config.get_logger()`
- JSON logs in `logs/grid.json.log`
- Human-readable console output preserved

---

## Index

| ID | Date | Category | Status | Summary |
|----|------|----------|--------|---------|
| DEC-001 | 2025-12-05 | PROCESS | ACCEPTED | Structured decision log |
| DEC-002 | 2025-12-05 | TESTING | ACCEPTED | Pytest config in pyproject.toml |
| DEC-003 | 2025-12-05 | ARCHITECTURE | ACCEPTED | Grid namespace standardization |
| DEC-004 | 2025-12-05 | ARCHITECTURE | ACCEPTED | Structured JSON logging |
