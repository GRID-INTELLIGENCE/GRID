# Changelog

All notable changes to grid-safety (Cognitive Privacy Shield and safety layer) are documented here.

## [1.0.1] - 2026-02-13

### Changed — Hardening Batch

- `MaskResult.original` field renamed to `original_hash` — stores `sha256[:16]` via `_hash_value()` helper instead of plaintext PII.
- `pre_check.py` fully migrated from legacy `rules/engine.py` to `GuardianEngine.evaluate()` with backward-compatible reason codes (`_GUARDIAN_REASON_PREFIX_MAP`).
- `SafetyRuleManager.evaluate_request()` now returns `SafetyEvalResult` dataclass instead of `(bool, list)` tuple; lazy singleton with thread-safe init.
- All `str, Enum` classes migrated to `StrEnum` (Python 3.13): `TrustTier`, `Severity`, `AuditStatus`, `PrivacyPreset`, `PrivacyAction`.
- `quick_block()` return type changed from `(bool, str | None)` to a result object with `.blocked` and `.reason_code`.

### Removed

- Deleted legacy `safety/rules/engine.py` (superseded by `safety/guardian/engine.py`).
- Deleted legacy `safety/test_guardian.py` ad-hoc script (replaced by proper pytest suite).
- Deleted `safety/detectors/pre_check_guardian.py` bridge module.

### Fixed

- 46 ruff lint violations resolved across `safety/` — unused imports, unsorted imports, `asyncio.TimeoutError` → `TimeoutError`, unused variables, loop-variable shadowing `field` import.
- `worker_utils.get_redis()` now uses async double-checked locking (`_redis_lock`).
- Test isolation for `test_escalation.py` hardened with `patch.object(_handler, "_get_redis", ...)` to survive DEGRADED_MODE monkey-patching.

### Added

- `safety/tests/unit/test_guardian.py` — 13 tests (evaluate, quick_check, cache, singleton, thread safety).
- `safety/tests/unit/test_escalation.py` — 8 tests (is_user_suspended, _suspend_user, _check_misuse).
- `safety/tests/unit/test_masking.py` — 26 tests (all strategies, engine, compliance presets, original_hash integrity).
- `safety/tests/unit/test_security_headers.py` — 14 tests (headers, CSRF, CORS, exempt paths).

## [1.0.0] - 2026-02-13

### Added

- Initial PyPI release as `grid-safety`.
- Cognitive Privacy Shield: PII detection, masking, compliance presets (GDPR, HIPAA, PCI-DSS, etc.).
- Privacy engine with singular and collaborative modes; ASK/MASK/FLAG/BLOCK/LOG actions.
- `/privacy/detect`, `/privacy/mask`, `/privacy/batch` API endpoints.
- Safety enforcement middleware (auth, rate limit, pre-check, Privacy Shield step for `/infer`).
- `safety-api` console script to run the Safety API server.
- Metrics (Prometheus) and structured logging.
