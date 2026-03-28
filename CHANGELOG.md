# Changelog

All notable changes to the GRID project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0] - 2026-03-28

### Highlights

**Admission Gate & Entity Persistence** — Top-of-stack ethical participation enforcement with 6 sequential gates, entity attribution with 3-tier penalty escalation, SQLite persistence, REST API (7 endpoints), and a full frontend dashboard.

### Added

- **Admission Gate Middleware** (`src/application/mothership/middleware/admission_gate.py`) — Pre-filter with 6 gates: Billboard → Banner → Budget → Origin → Structure/Context → Profit-mask. Configurable via `MOTHERSHIP_ADMISSION_GATE_ENABLED`, `MOTHERSHIP_ADMISSION_CALL_BUDGET`, `MOTHERSHIP_ADMISSION_BANNER_THRESHOLD`
- **Entity Attribution Engine** — Resolves requests to entities (X-Entity-Id → X-API-Key → IP), accumulates violations, auto-banners at threshold. Three penalty tiers: runtime_mistake (1x) → environment_pollution (1x compounding) → intentional_scheming (3x accelerated)
- **Policy Billboard** — Frozen ethical participation contract displayed at top of every execution chain, versioned and queryable
- **Admission REST API** (`src/application/mothership/routers/admission_enforcement.py`) — 7 endpoints under `/admission/*`: policy, stats, entity report, bannered list, compliance check, penalty apply (admin), penalty revoke (admin)
- **Entity Persistence** (`src/application/mothership/repositories/admission.py`) — SQLAlchemy async CRUD with aiosqlite, fire-and-forget persist hook, startup hydration from SQLite
- **Frontend Admission Dashboard** (`frontend/src/pages/Admission.tsx`) — Stats row (5 cards), rejection breakdown, policy billboard, bannered entities table with tier badges. TanStack Query hooks for live polling
- **Event Bus Compatibility Alias** (`src/infrastructure/event_bus/event_system.py`) — Re-exports from event_system_fixed with prometheus metric stubs
- **EssentialState.decay()** (`src/grid/essence/core_state.py`) — Bidirectional coherence degradation method
- **OpenAPI $schema Injection Script** (`scripts/inject_openapi_schema.py`) — Post-generation hook with `--check` dry-run mode

### Changed

- **Version bump** from 2.7.0 to 2.8.0
- **Middleware chain** expanded to 14 layers (admission gate is top-of-stack)
- **ContextStorage path validation** — Platform-conditional default roots, consistent `os.pathsep` splitting (fixes `E:/user_context` parsing on Linux)
- **RAG engine logging** — 4 bare `print()` calls replaced with `structlog` logger

### Fixed

- **Event bus test failures** — Rewrote 8 tests to match sync `event_system_fixed` API (was using nonexistent async methods)
- **Nomic embedding norm assertion** — Widened bound to 20.0 (nomic-embed-text-v2-moe norms reach ~14)
- **Path traversal security test** — Test fixture sets `GRID_CONTEXT_ALLOWED_ROOTS` via monkeypatch
- **Rate limit test regression** — Admission gate bannered entities after 60+ requests; gate now disabled in JWT rate-limit fixture

### Security

- **AdminAuth on penalty endpoints** — `POST /admission/penalty/apply` and `/revoke` require admin JWT
- **ContextStorage SecurityError** — Now raises instead of logging warning when context root is outside allowed bounds

## [2.7.0] - 2026-03-11

### Highlights

**Security Hardening & Search Guardrails** — Comprehensive API attack surface guardrails (Phases 1–4), sealed-envelope transition gate for cross-partition transfers, search engine with auth/security/safety guardrails, and CI pipeline hardening with git/config audit gates.

### Added

- **Search Engine with Guardrails** (`src/search/`) — Full search service with authentication, rate limiting, input sanitization, and admin-gated schema/index/delete routes
- **Transition Gate** (`boundaries/transition_gate/`) — Sealed-envelope handshake for cross-partition artifact transfers with HMAC-SHA256 fingerprinting, single-use nonces, timing-safe comparison, and 9-step verification pipeline
- **Reasoning Router** (`src/application/mothership/routers/reasoning.py`) — New reasoning endpoint with schema and unit tests
- **Pathways Adapter** (`src/unified_fabric/`) — User-ID anti-spoofing and tracing for Unified Fabric
- **CSV Data Processing Pipeline** (`src/tools/`) — Comprehensive CSV ingestion and transformation utilities
- **Signature-Based Authentication** — Narrowed accessibility scope with signature verification
- **CI Audit Gates** — `assert_no_debug` script, git hygiene checks (no untracked files in `src/` or `tests/`), and Phase 4 production gate in both Secrets Scan and Test jobs
- **SECURITY.md** — Added GitHub security policy with vulnerability reporting instructions

### Changed

- **Version bump** from 2.6.1 to 2.7.0
- **License classifier** fixed from `Other/Proprietary License` to `OSI Approved :: MIT License` in `pyproject.toml` to match actual MIT LICENSE file
- **README.md** — Updated project stats (1130+ CI tests passing, 3200+ total collected, 800+ source files), refreshed "What's New" section for March 2026, corrected badge references
- **CONTRIBUTING.md** — Updated linter commands, added test isolation guidelines, added `SECURITY.md` reference
- **Mothership hardening** — Config `__all__` export safety, lifespan shutdown cleanup (ParasiteGuard, rate limiter), health router async/sync Redis ping handling
- **Path validation** — Normalize backslashes and detect Windows absolute paths on Linux for cross-platform security
- **RAG runtime guards** — Cross-encoder compatibility under transformers 5.x; intent classifier torch/transformers import guard
- **Test isolation** — Replaced `importlib.reload()` in tests with `reload_settings()` to prevent dependency override identity mismatch; reset global singletons (circuit breaker, metrics, accountability) in streaming test fixtures

### Fixed

- **CI Test job failure** (run 22955473744) — Root cause: `importlib.reload()` on config/dependencies modules broke FastAPI `dependency_overrides` identity for `get_config`, causing `/health/security` to use real settings (rate limiting disabled) → HTTP 503. Fixed by using `reload_settings()` instead
- **Cross-platform path traversal** — Windows backslash normalization and absolute path detection on Linux
- **Dead code and platform configuration** cleanup across mothership routers
- **Pytest collection** restored across grid with import guards and lazy loading
- **Ecosystem audit** — Import guards, lazy loading, orphan module cleanup

### Security

- **CRIT-4/5 guardrails** — API attack surface hardening with mothership refactor
- **Phase 1–4 API guardrails** — Tests, CI integration, and documentation for comprehensive endpoint protection
- **Residual DEBUG prints** replaced with structured logger calls in RAG engine and indexer

## [2.6.1] - 2026-02-24

### Changed

- **Packaging** - Added `src/mycelium` to wheel packaging targets in `pyproject.toml` so Mycelium ships in distributable builds
- **Version alignment** - Synchronized package metadata and changelog for patch release consistency
- **CI metadata checks** - Added version/changelog consistency verification in CI and release workflows
- **Repository hygiene** - Removed tracked frontend coverage artifacts and transient release log artifacts from version control
- **Contributor guidance** - Added pipeline green checklist and release runbook documentation for consistent execution

## [2.6.0] - 2026-02-24

### Highlights

**Mycelium Frontend** â€” Interactive comprehension layer with adaptive synthesis, concept exploration, and accessibility-first design. Includes a full interactive page, a standalone demo/presentation page, and comprehensive test coverage.

### Added

- **MyceliumPage** (`frontend/src/pages/MyceliumPage.tsx`) â€” Main interactive page with text input, adaptive synthesis, keyword-driven concept exploration, feedback loop (Simpler/Deeper), concept browser panel, and accessibility settings
- **MyceliumDemo** (`frontend/src/pages/MyceliumDemo.tsx`) â€” Self-contained presentation page showcasing 3 personas, 3 source texts, 5 concept lenses with multi-lens switching
- **6 Mycelium components** (`frontend/src/components/mycelium/`) â€” OutputDisplay, LensCard, HighlightPill, FeedbackBar, DepthControl, SensoryPicker
- **useMycelium hook** (`frontend/src/hooks/use-mycelium.ts`) â€” useReducer FSM with 9 action types, bridge abstraction for Electron IPC/browser fallback
- **Type definitions** (`frontend/src/types/mycelium.ts`) â€” Full type coverage for synthesis results, navigation, personas, sensory profiles
- **Shared keyword extraction** (`frontend/src/lib/text-utils.ts`) â€” Deduplicated stop-word filtering and frequency counting utility
- **Browser shim** (`frontend/src/lib/browser-shim.ts`) â€” Extended with `window.mycelium` for consistent browser-mode demo data across all pages
- **Test suite** (`frontend/src/__tests__/MyceliumPage.test.tsx`) â€” 17 tests covering rendering, input validation, synthesis, keyboard shortcuts, error states, concept exploration, and feedback depth adjustment
- **Frontend routes** â€” `mycelium` and `mycelium-demo` routes added to `app.config.json`, `app-schema.ts`, and `schema/index.ts`

### Changed

- **Performance** â€” Bridge instance memoized with `useMemo`, all callbacks stabilized via destructured hook return, `filteredConcepts` wrapped in `useMemo`, textarea resize batched with `requestAnimationFrame`
- **Architecture** â€” `clearExplored` dispatch replaces wasteful `explore("")` IPC call; `eslint-disable` removed after fixing bridge stability
- **Frontend CI** (`.github/workflows/frontend.yml`) â€” Fixed self-referential path trigger from `frontend-ci.yml` to `frontend.yml`

## [2.5.1] - 2026-02-24

### Changed

- **Test reorganization** â€” Relocated tests into themed directories for improved discoverability; removed deprecated components and temporary artifacts
- **Codebase hygiene** â€” Cognitive architecture alignment pass; cleaned up stale modules and resolved structural inconsistencies

## [2.5.0] - 2026-02-24

### Highlights

**GRID Environmental Intelligence** â€” homeostatic middleware that sits between the round table facilitator and LLM providers. Monitors conversational balance across three dimensions (Practical, Legal, Psychological) and dynamically adjusts LLM generation parameters using Le Chatelier's Principle. Includes a full round table facilitation layer, frontend page, and comprehensive test coverage.

### Added

- **Grid Environment Engine** (`src/grid/agentic/grid_environment.py`) â€” `GridDimension`, `ArenaAmbiance`, `EnvironmentalShift`, `GridEnvironment`, and `EnvironmentalLLMProxy` classes implementing the homeostatic triad (Practical/Legal/Psychological) with negative feedback recalibration
- **Round Table Facilitator** (`src/grid/agentic/roundtable_facilitator.py`) â€” 4-phase orchestrator (open â†’ discuss â†’ synthesize â†’ close) that coordinates multi-agent round table discussions with environment-aware LLM parameter adjustment
- **Round Table Schemas** (`src/grid/agentic/roundtable_schemas.py`) â€” Pydantic models for round table sessions, contributions, and results
- **RoundTablePage** (`frontend/src/pages/RoundTablePage.tsx`) â€” Frontend page for initiating and visualizing round table discussions
- **Frontend route/schema** â€” `roundtable` route with `compass` icon added to `app.config.json`, `app-schema.ts`, and `schema/index.ts`
- **Test suite** â€” 43 environment tests (`tests/unit/test_grid_environment.py`) across 9 test classes + 17 round table facilitator tests (`tests/unit/test_roundtable_facilitator.py`); 60 new tests total
- `dev/navigation_graph.json` updated with round table route

### Changed

- **Agentic `__init__.py`** â€” Exports extended with `ArenaAmbiance`, `EnvironmentalLLMProxy`, `GridDimension`, `GridEnvironment`, `RoundTableFacilitator`, `RoundTableResult`

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

[2.7.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/v2.6.1...v2.7.0
[2.6.1]: https://github.com/GRID-INTELLIGENCE/GRID/compare/v2.6.0...v2.6.1
[2.6.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/v2.5.1...v2.6.0
[2.5.1]: https://github.com/GRID-INTELLIGENCE/GRID/compare/v2.5.0...v2.5.1
[2.5.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/ee0a497...v2.5.0
[2.4.1]: https://github.com/GRID-INTELLIGENCE/GRID/compare/17fa605...ee0a497
[2.4.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/222eae7...17fa605
[2.3.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/6534d65...222eae7
[2.2.0]: https://github.com/GRID-INTELLIGENCE/GRID/compare/HEAD~3...6534d65
