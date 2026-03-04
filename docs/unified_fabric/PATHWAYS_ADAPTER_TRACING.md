# Pathways Adapter — Tracing Documentation

This document supports tracing the Pathways integration adapter and the user_id security fix for audits, reviews, and future changes.

---

## 1. Overview

| Item | Value |
|------|--------|
| **Component** | Pathways Integration Adapter (GRID ↔ Pathways/Networks) |
| **Location** | `src/unified_fabric/pathways_adapter.py` |
| **Tests** | `tests/unified_fabric/test_pathways_adapter.py` |
| **Security fix** | Safety/audit `user_id` no longer taken from `signal.metadata` (anti-spoofing) |

---

## 2. Change History (Traceable)

### 2.1 Initial adapter (Horizontal Connection plan)

- **Purpose:** Integrate Pathways/Networks semantic resonance with unified fabric.
- **Artifacts:** `pathways_adapter.py`, `ResonanceSignal`, `PathwaysIntegrationAdapter`, `process_resonance()`, `get_pathways_adapter()`, `init_pathways_adapter()`.
- **Related:** Domain routing, event schemas, and cross-project validator include `pathways`; see `domain_routing.py`, `event_schemas.py`, `cross_project_validator.py`.

### 2.2 User_id spoofing fix (security)

- **Problem:** `SafetyContext.user_id` was set from `signal.metadata.get("user_id", "pathways-system")`, allowing any caller that could supply a `ResonanceSignal` to control the identity used for safety validation and audit (user-id spoofing, false attribution).
- **Fix:** `user_id` is never read from `signal.metadata`. It is either:
  - the literal `"pathways-system"` (default), or
  - a caller-supplied `trusted_user_id` when the adapter is invoked from trusted, authenticated context.
- **API change:** `process_resonance(signal, trusted_user_id: str | None = None)`. Callers must pass `trusted_user_id` only when they have already authenticated the user; `signal.metadata` is not used for safety/audit.
- **Verification:** Tests `test_process_resonance_uses_pathways_system_when_no_trusted_user_id` and `test_process_resonance_uses_trusted_user_id_when_provided` in `tests/unified_fabric/test_pathways_adapter.py` assert the behavior.

---

## 3. How to Trace

### 3.1 Code references

- **Adapter:** `src/unified_fabric/pathways_adapter.py`
  - `process_resonance()` — safety validation and broadcast; `user_id` set from `trusted_user_id` or `"pathways-system"` only.
  - Module and method docstrings describe the no-metadata rule for safety/audit identity.
- **Tests:** `tests/unified_fabric/test_pathways_adapter.py`
  - Default identity: `test_process_resonance_uses_pathways_system_when_no_trusted_user_id` (ensures `metadata["user_id"]` is ignored).
  - Trusted caller: `test_process_resonance_uses_trusted_user_id_when_provided`.

### 3.2 Downstream usage

- **Safety bridge:** `SafetyContext` passed to `get_safety_bridge().validate()` includes `user_id`; used for routing and audit.
- **Event bus:** `_broadcast_resonance_event()` publishes `pathways.resonance.detected`; payload does not include `user_id` (event payload is content-only).

### 3.3 Verification commands

```bash
cd E:\Seeds\GRID-main
uv run pytest tests/unified_fabric/test_pathways_adapter.py -v
uv run ruff check src/unified_fabric/pathways_adapter.py
uv run black --check src/unified_fabric/pathways_adapter.py
```

---

## 4. Related docs and plans

- **Evolution plan:** Horizontal Connection (GRID-main ↔ Pathways/Networks); Phase 1 adapter layer.
- **Security plan:** Pathways user_id spoofing fix (plan: use fixed system identity and optional `trusted_user_id`; do not use `signal.metadata` for safety/audit).
- **Unified fabric:** `docs/` and `src/unified_fabric/` for event schemas, domain routing, and safety bridge.

---

## 5. Maintenance notes

- When adding new callers of `process_resonance()`, ensure they pass `trusted_user_id` only when the user has been authenticated by trusted code; never forward `signal.metadata["user_id"]` into this parameter.
- Any future use of `signal.metadata` for security or audit must be documented and validated to avoid reintroducing spoofing or false attribution.
