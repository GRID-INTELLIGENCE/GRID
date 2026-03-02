# Search Service – Deferred Items

Baseline contract: [search-service-baseline-contract.json](./search-service-baseline-contract.json)

## Phase 4 (partial)

- [x] **Admin gating** – Gate schema, index, delete routes behind admin role (done)
- [ ] **SEARCH_FULL_PIPELINE** – Implement optional fusion/ranking/facets when flag is false
- [ ] **AccessControl** – Implement real index/field allowlists (replace stub)

## Phase 5 (pending)

- [ ] **Guardrail default** – Set `GUARDRAIL_ENABLED=true` by default; document migration path
