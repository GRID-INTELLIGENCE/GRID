# Probe Entity Catalog

Reference catalog of governance entities discovered during the Phase 2.1 audit. These are pre-seeded in `config/probe/entities.yaml` and augmented at runtime by the probe scanner.

## Middleware Chain (Execution Order)

| # | Entity ID | Label | Domain | Conditional | Source |
|---|-----------|-------|--------|-------------|--------|
| 1 | `ent-admission-gate` | AdmissionGateMiddleware | governance | Yes (`admission_gate_enabled`) | `middleware/admission_gate.py` |
| 2 | `ent-parasite-guard` | ParasiteGuardMiddleware | security | Yes (`parasite_guard_enabled`) | `infrastructure/parasite_guard/middleware.py` |
| 3 | `ent-safety` | SafetyMiddleware | safety | **No (MANDATORY)** | `safety/api/middleware.py` |
| 4 | `ent-accountability-contract` | AccountabilityContractMiddleware | governance | Yes (`accountability_enabled`) | `middleware/accountability_contract.py` |
| 5 | `ent-drt` | UnifiedDRTMiddleware | security | Yes | `middleware/drt_middleware_unified.py` |
| 6 | `ent-data-corruption` | DataCorruptionDetectionMiddleware | security | Yes | `middleware/data_corruption.py` |
| 7 | `ent-stream-monitor` | StreamMonitorMiddleware | request_pipeline | Yes | `middleware/stream_monitor.py` |
| 8 | `ent-security-headers` | SecurityHeadersMiddleware | security | No | `middleware/__init__.py` |
| 9 | `ent-error-handling` | ErrorHandlingMiddleware | request_pipeline | No | `middleware/__init__.py` |
| 10 | `ent-security-enforcer` | SecurityEnforcerMiddleware | security | No | `middleware/security_enforcer.py` |
| 11 | `ent-circuit-breaker` | CircuitBreakerMiddleware | request_pipeline | No | `middleware/circuit_breaker.py` |
| 12 | `ent-request-logging` | RequestLoggingMiddleware | request_pipeline | No | `middleware/__init__.py` |
| 13 | `ent-timing` | TimingMiddleware | request_pipeline | No | `middleware/__init__.py` |
| 14 | `ent-accountability` | AccountabilityMiddleware | governance | No | `middleware/accountability.py` |
| 15 | `ent-request-id` | RequestIDMiddleware | request_pipeline | No | `middleware/__init__.py` |
| 16 | `ent-versioning` | VersioningMiddleware | request_pipeline | No | `middleware/versioning.py` |
| 17 | `ent-request-size` | RequestSizeLimitMiddleware | security | No | `middleware/request_size.py` |
| 18 | `ent-usage-tracking` | UsageTrackingMiddleware | request_pipeline | No | `middleware/usage_tracking.py` |
| 19 | `ent-rate-limit` | APIGuardRateLimitMiddleware | throttling | No | `middleware/apiguard_adapter.py` |

## Authentication & Authorization

| Entity ID | Label | Domain | Source |
|-----------|-------|--------|--------|
| `ent-auth-base` | Auth | authentication | `dependencies.py` |
| `ent-auth-required` | RequiredAuth | authentication | `dependencies.py` |
| `ent-auth-admin` | AdminAuth | authentication | `dependencies.py` |
| `ent-rbac` | RBAC System | authentication | `src/grid/auth/rbac.py` |
| `ent-merit-standing` | Merit Standing Engine | governance | `security/merit_standing.py` |

## Governance Gates

| Entity ID | Label | Domain | Source |
|-----------|-------|--------|--------|
| `ent-governance-gate` | GovernanceGate | governance | `src/grid/core_modules/governance_gates.py` |
| `ent-governance-engine` | GovernanceEngine | governance | `src/grid/legal/governance.py` |
| `ent-gatekeeper` | GateKeeper | governance | `boundaries/transition_gate/` |
| `ent-boundary-engine` | BoundaryEngine | governance | `boundaries/boundary.py` |

## Domain Summary

| Domain | Entity Count | Weight |
|--------|-------------|--------|
| governance | 7 | 1.5 |
| security | 6 | 1.4 |
| authentication | 4 | 1.3 |
| safety | 1 | 1.3 |
| request_pipeline | 8 | 1.2 |
| throttling | 1 | 1.1 |
