# Search Service – Deferred Items

Baseline contract: [search-service-baseline-contract.json](./search-service-baseline-contract.json)

## Phase 4 (complete)

- [x] **Admin gating** – Gate schema, index, delete routes behind admin role (done)
- [x] **SEARCH_FULL_PIPELINE** – `search_full_pipeline` flag implemented in `SearchConfig`
  and wired through `SearchEngine.search()`. When `False`, the engine runs keyword-only
  retrieval without fusion, cross-encoder ranking, or facets. When `True`, the full
  hybrid pipeline (BM25 + semantic fusion → LTR ranking → facets) is activated.
  Toggle via env var `SEARCH_SEARCH_FULL_PIPELINE=true`.
- [x] **AccessControl** – `access_control_tool` in `guardrail/tools/access_control.py`
  enforces index allowlists (`profile.allowed_indices`) and per-index field allowlists
  (`profile.allowed_fields`) for both filter fields and facet fields. Profiles are
  loaded from `GuardrailPolicy` (YAML/JSON or `GuardrailPolicy.default()`).

## Phase 5 (complete)

- [x] **Guardrail default** – `guardrail_enabled: bool = True` is the hardcoded default
  in `SearchConfig`. The env var `SEARCH_GUARDRAIL_ENABLED=false` can disable it.
  No migration needed — the default was always `True` in the released config.

## Remaining / Future

- [x] **Custom validator support** – `DataValidationRule.custom_validator` field
  (format: `module.path:function_name`) is now fully invoked in `_validate_data`.
  The validator is loaded via `importlib.import_module`, called with the field value,
  and may return `True`/`None` (pass), `False` (generic fail), or a `str` (fail with
  that message). Import/attribute errors and runtime exceptions are each caught and
  surfaced as distinct error codes (`custom_validator_unavailable`, `custom_validation_error`).
  *(Implemented in `src/grid/resilience/accountability/contracts.py`.)*
- [ ] **SEARCH_FULL_PIPELINE — production embedding backend** – The full pipeline
  requires a live embedding provider. In CI/test environments the `SimpleEmbedding`
  fallback is used. Wire a real provider (HuggingFace or Ollama) via env before
  enabling `SEARCH_SEARCH_FULL_PIPELINE=true` in production.
- [ ] **LTR model** – `ltr_model_path` defaults to `None`; without a trained model
  the ranking pipeline falls back to BM25+vector score blending. Train and register
  a model to unlock full LTR scoring.
- [ ] **Guardrail admin identities** – `guardrail_admin_identities` defaults to `[]`,
  which means the header-only admin check is used. Populate this list (or set via
  `SEARCH_GUARDRAIL_ADMIN_IDENTITIES`) for production identity-pinned admin gating.