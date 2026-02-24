# Changelog

All notable changes to the GRID project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-02-24

### Highlights

**GRID Environmental Intelligence** — homeostatic middleware that sits between the round table facilitator and LLM providers. Monitors conversational balance across three dimensions (Practical, Legal, Psychological) and dynamically adjusts LLM generation parameters using Le Chatelier's Principle. Includes a full round table facilitation layer, frontend page, and comprehensive test coverage.

### Added

- **Grid Environment Engine** (`src/grid/agentic/grid_environment.py`) — `GridDimension`, `ArenaAmbiance`, `EnvironmentalShift`, `GridEnvironment`, and `EnvironmentalLLMProxy` classes implementing the homeostatic triad (Practical/Legal/Psychological) with negative feedback recalibration
- **Round Table Facilitator** (`src/grid/agentic/roundtable_facilitator.py`) — 4-phase orchestrator (open → discuss → synthesize → close) that coordinates multi-agent round table discussions with environment-aware LLM parameter adjustment
- **Round Table Schemas** (`src/grid/agentic/roundtable_schemas.py`) — Pydantic models for round table sessions, contributions, and results
- **RoundTablePage** (`frontend/src/pages/RoundTablePage.tsx`) — Frontend page for initiating and visualizing round table discussions
- **Frontend route/schema** — `roundtable` route with `compass` icon added to `app.config.json`, `app-schema.ts`, and `schema/index.ts`
- **Test suite** — 43 environment tests (`tests/unit/test_grid_environment.py`) across 9 test classes + 17 round table facilitator tests (`tests/unit/test_roundtable_facilitator.py`); 60 new tests total
- `dev/navigation_graph.json` updated with round table route

### Changed

- **Agentic `__init__.py`** — Exports extended with `ArenaAmbiance`, `EnvironmentalLLMProxy`, `GridDimension`, `GridEnvironment`, `RoundTableFacilitator`, `RoundTableResult`

## [2.4.1] - 2026-02-24

### Highlights

Consolidation cycle completed on `main` with merge-mitigation review and snapshot integrity verification.

### Changed

- **Main branch consolidation** finalized with explicit mitigation for unsafe branch deltas
- **Snapshot validation** confirmed for hierarchy and landscape snapshot capture flows
- **Async skill runtime hardening** ensured sync wrappers resolve awaitables in both non-running and running loop contexts
- **RAG test collection resilience** improved by skipping tests cleanly when optional `chromadb` import fails due to environment-level incompatibility
- **Decision logging** updated with branch rejection record in `docs/decisions/DECISIONS.md`

### Added

- `tests/unit/test_skills_base_async.py` for regression coverage on async skill handler resolution

### Fixed

- Ruff import-order issue in `src/grid/skills/base.py`
- Test collection crash in `tests/test_rag.py` and `tests/test_rag_contracts.py` when `chromadb` is importable but unusable

## [2.4.0] - 2026-02-17

### Highlights

Full lint remediation: **664 ruff errors reduced to 0** across 251 files (748 source files total).
Repository cleanup: removed tracked artifacts, updated `.gitignore`, refreshed documentation.

### Changed

- **Version bump** from 2.3.0 to 2.4.0
- **StrEnum modernization** (UP042): 122 classes converted from `class Foo(str, Enum)` to `class Foo(StrEnum)` across 78 files
- **Timezone modernization** (UP017): `datetime.utcnow()` replaced with `datetime.now(datetime.UTC)` throughout
- **PEP 695 generics**: `deduplicate[T]` in `src/application/mothership/utils/__init__.py` uses modern type parameter syntax
- **List comprehension optimization** (PERF401): 85 manual `for`-loop `append` patterns converted to comprehensions or `list.extend()`
- **ContextVar safety** (B039): Mutable default `[]` changed to `None` in `src/grid/security/parasite_tracer.py`
- **Import hygiene**: 18 undefined names (F821) resolved by adding missing imports; unused imports cleaned
- **Exception handling**: Bare `except:` replaced with `except Exception:` (E722); type comparisons use `is` (E721)
- **Security annotations**: Intentional patterns (S110/S112/S324/S311/S603/S607/S104/S108) annotated with `noqa` and justification
- **SQL query builders**: S608 suppressed via per-file-ignores in `pyproject.toml` for internal query files
- **Async patterns**: ASYNC109/110/250 annotated where timeout/polling/blocking is intentional

### Removed

- `tmp_scan_async_blocking.py`, `tmp_scan_async_blocking_v2.py` (temporary scan scripts)
- `bandit-report.json` (272 KB generated report)
- `resonance_telemetry_events.jsonl` (335 KB telemetry dump)
- `config.secrets.baseline` (71 KB secrets baseline)

### Fixed

- F821 undefined names in `payment.py`, `rag_streaming.py`, `plan_to_reference.py`, `trace_manager.py`, `gateway.py`, `mesh.py`, `sanitizer.py`, `drt_monitoring.py`
- F841 unused variables in `main_unified.py`, `health.py`, `module_utils.py`, `precision_validator.py`
- F402 import shadowing in `contracts.py` (loop variable renamed)
- E722 bare excepts in `middleware.py`, `sanitizer.py`

### Insights

- **PERF401 was the highest-impact manual fix category** (85 instances). Most were straightforward `for`-loop `append` to comprehension conversions, but ~35 required careful handling of multi-line expressions, nested loops, and conditional logic.
- **S608 cannot be suppressed inline on multi-line f-strings** because `# noqa` inside an f-string becomes part of the string literal. Per-file-ignores in `pyproject.toml` is the correct approach.
- **Async `for` loops preclude list comprehensions** (PERF401). Python has no `async` list comprehension syntax that works with `async for` iterators in all contexts, so these require `noqa` suppression.
- **Grammar is a safety feature**: All safety pattern annotations follow the Trust Layer nominalization rules (descriptive nouns, not imperative verbs).

---

## [2.3.0] - 2026-02-16

### Changed

- Async-first I/O modernization
- RBAC centralization
- Test infrastructure fixes
- Enum bug fixes
- Initial lint compliance pass

---

## [2.2.0] - 2026-02-15

### Changed

- Async modernization across core modules
- Enum bug fix in security subsystem
- Initial lint compliance work

---

[2.5.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/ee0a497...HEAD
[2.4.1]: https://github.com/GRID-INTELLIGENCE/GRID/compare/17fa605...ee0a497
[2.4.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/222eae7...17fa605
[2.3.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/6534d65...222eae7
[2.2.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/HEAD~3...6534d65
