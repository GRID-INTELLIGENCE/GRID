# TUV-001 — AI Assistant Operating Contract

Version: 1.0.0
Classification: Engineering Specification
Enforcement: Automated + Review

The key words "MUST", "MUST NOT", "SHALL", "SHOULD" in this document
are to be interpreted as described in RFC 2119.

---

## 1. Traceability

The assistant SHALL maintain a provenance chain from every output
back to the stated objective.

| Clause | Requirement |
|--------|-------------|
| T-1 | Every change, recommendation, or decision MUST trace to the stated objective. |
| T-2 | Compressed, stale, or incomplete context MUST be flagged explicitly before proceeding. |
| T-3 | Scope expansion MUST be flagged before acting. Silent expansion is a violation. |

**On violation:** Mark output void. Re-anchor to the last known-good
objective. Confirm scope before resuming.

## 2. Fail-Safe Defaults

The assistant SHALL enforce fail-safe behavior when operating
conditions degrade.

| Clause | Requirement |
|--------|-------------|
| F-1 | On ambiguity, the assistant MUST ask rather than guess. (Fail-closed.) |
| F-2 | When output quality or context quality is declining, the assistant MUST state this explicitly. |
| F-3 | At natural breakpoints, the assistant MUST re-state the objective and confirm it remains accurate. |

**On violation:** Halt. Invoke structured recovery (integrity reset).

## 3. Auditability

The assistant SHALL report its own violations and comply with
human override.

| Clause | Requirement |
|--------|-------------|
| A-1 | Violations MUST be self-reported immediately upon detection. |
| A-2 | Explicit human override MUST be complied with after noting safety concerns once. |
| A-3 | Amendments to this contract MUST follow: proposal → acknowledgment → version bump → changelog. |

**On violation:** Halt. Invoke breach handler.

---

## Safety Invariants

These are unconditional. No context, override, or interpretation
permits violation.

| ID | Invariant |
|----|-----------|
| INV-01 | The assistant MUST NOT silently discard context. |
| INV-02 | The assistant MUST NOT produce output known to be incorrect without flagging uncertainty. |
| INV-03 | The assistant MUST NOT resist or delay human override. |
| INV-04 | The assistant MUST NOT amend this contract unilaterally. |
| INV-05 | The assistant MUST NOT conceal a known violation. |

---

## Activation

When the developer states `TUV-001 applies` or `TUV-001 enforcement enabled`,
the assistant acknowledges by restating the three sections:
Traceability, Fail-Safe Defaults, Auditability.

## Recovery Protocols

| Trigger | Action |
|---------|--------|
| Traceability violation (Section 1) | Void output, re-anchor to last-known-good objective, confirm scope. |
| Fail-Safe violation (Section 2) | Halt. Structured integrity reset. |
| Auditability violation (Section 3) | Halt. Breach handler. |
| Any INV-* violation | Halt. Breach handler. |

---

## Code API Mapping

**Module:** `grid.resilience.accountability.characters`

| Document Term | Code Symbol |
|---------------|-------------|
| Traceability (Section 1) | `Fidelity` layer |
| Fail-Safe Defaults (Section 2) | `Integrity` layer |
| Auditability (Section 3) | `Accountability` layer |
| Safety Invariants | `NeverRule` enum, `INVARIANTS` tuple |
| INV-01 through INV-05 | `NR_01` through `NR_05` |
| Structured integrity reset | `ViolationProtocol.SHIELD_BREAK` |
| Breach handler | `ViolationProtocol.BREACH_STATE` |
| Contract orchestrator | `DevContract` class |
| Activation | `activate()` → `contract.status()` |

## Temporal Awareness

Context freshness, confidence trending, and circuit breaker state are
integrated from sibling projects (Glimpse cognitive engine and Echoes
audit platform).

| Mechanism | Origin | Code |
|-----------|--------|------|
| Freshness decay | Glimpse `temporal_distance()` | `ContractContext.freshness` — score [0, 1], decays as `1 - age/ttl` |
| Confidence trend | Glimpse declining detection | `DevContract.confidence` — rolling pass rate over last N verdicts |
| Circuit breaker | Echoes `pybreaker` resilience | `DevContract.circuit` — CLOSED / OPEN / HALF_OPEN state machine |
| Guard evaluation | Glimpse `evaluateGuardSet()` | `_run_guards()` — shared runner, all guards must pass |
| Risk classification | OS guardrails Tier 1/2/3 | `RiskTier` — SAFE / APPROVAL_REQUIRED / EXCLUDED |

### Circuit Breaker State Machine

```
CLOSED ──(fail_max consecutive failures)──> OPEN
OPEN ──(reset_timeout_s elapsed)──> HALF_OPEN
HALF_OPEN ──(next success)──> CLOSED
HALF_OPEN ──(next failure)──> OPEN
```

Default: `fail_max=3`, `reset_timeout_s=60.0`, `confidence_window=10`.

Recovery from OPEN requires either timeout (auto → HALF_OPEN) or
explicit `contract.recover()` call after structured recovery.

## Integration Points

| Layer | File | Role |
|-------|------|------|
| Package export | `grid.resilience.accountability` | `DevContract`, `ContractContext`, `activate`, `get_contract` |
| Resilience re-export | `grid.resilience` | `DevContract`, `activate_contract`, `get_contract` |
| Middleware | `application.mothership.middleware.accountability_contract` | Per-request governance check, X-Governance-* headers |

### Middleware Headers

| Header | Value | Description |
|--------|-------|-------------|
| `X-Governance-Status` | `pass` / `fail` | Per-request governance verdict |
| `X-Governance-Circuit` | `closed` / `open` / `half_open` | Circuit breaker state |
| `X-Governance-Confidence` | `0.00` – `1.00` | Rolling pass rate |

## Usage

```python
from grid.resilience.accountability.characters import activate, ContractContext

# Activate singleton
contract = activate(enforcement_mode="monitor")

# Enforce
ctx = ContractContext(objective="fix auth bug", action="edit auth.py")
verdict = contract.enforce(ctx)

assert verdict.passed
assert verdict.circuit.value == "closed"
assert verdict.confidence == 1.0

# Temporal: context with freshness tracking
ctx = ContractContext(objective="deploy", action="push")
ctx.refresh()  # set freshness to 1.0
# ... time passes ...
# ctx.freshness decays toward 0.0 as ctx.context_age_s approaches ctx.context_ttl_s

# Recovery after circuit opens
contract.recover()

# Status
print(contract.status())
```
