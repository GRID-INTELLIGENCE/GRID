# High-Value Instances — GRID-main

> Canonical registry of high-G components. Each entry carries: module path, function,
> conceptual G-score (grounding strength 0–1), atlas layer (0=collective, 1=context,
> 2=agentic, 3=hierarchy), and attestation rationale.
>
> Context: generated in relation to the low-G landscape discussion (Apr 2026).
> Counterpart to the B0_RESTRICTED session population found in the echoes audit trail.

---

## Layer 3 — Hierarchy (G ≥ 0.9)

These are the trust anchors. Decisions made here carry maximum grounding.

### `boundaries/transition_gate/gate_keeper.py`

| Field | Value |
|-------|-------|
| G | 0.98 |
| Score | 1.0 |
| Layer | 3 |
| θ (atan2) | 45.6° |

9-step sealed-envelope verification: envelope existence → payload integrity → HMAC-SHA256
fingerprint → nonce replay prevention → timestamp freshness → test verification → scope
validation → action authorization → audit logging. Timing-safe comparison. Fail-closed.

**Why high-G**: Every cross-boundary action passes through this gate. It is the cryptographic
trust anchor for the entire system. Nonce burning prevents replay; HMAC ensures provenance.

---

### `safety/audit/db.py`

| Field | Value |
|-------|-------|
| G | 0.97 |
| Score | 0.95 |
| Layer | 3 |
| θ | 44.4° |

Async SQLAlchemy 2.0 + asyncpg audit persistence. Fail-closed design: if DB unreachable,
callers must refuse requests — incomplete audits trigger refusal, not silent logging.

**Why high-G**: The audit trail is immutable. If this layer fails open, the entire accountability
chain breaks. Fail-closed is the only acceptable posture.

---

### `safety/api/middleware.py`

| Field | Value |
|-------|-------|
| G | 0.96 |
| Score | 0.90 |
| Layer | 3 |
| θ | 43.2° |

Sequential safety pipeline (non-bypassable): authenticate → check suspension → rate limit
→ pre-check (<50ms) → deterministic refusal OR enqueue to Redis Streams. Fail-closed if any
component unavailable.

**Why high-G**: The admission gate middleware. B0_RESTRICTED entities are stopped here before
they can reach any business logic. All 20 blocked audit entries from Apr 3–5 were caught by
this layer.

---

## Layer 2 — Agentic (G 0.7–0.89)

High grounding but bounded scope. Operate within defined action classes.

### `boundaries/overwatch.py`

| Field | Value |
|-------|-------|
| G | 0.88 |
| Score | 0.85 |
| Layer | 2 |
| θ | 44.0° |

Real-time monitoring engine consuming boundary, consent, guardrail, and preparedness events.
Detects event patterns, triggers escalation when thresholds exceeded within time windows,
persists alerts to NDJSON audit trail.

**Why high-G**: Circuit breaker. Catches anomalous boundary violations before they compound.
The runtime correlate of the angular model's cluster detection.

---

### `safety/guardian/engine.py`

| Field | Value |
|-------|-------|
| G | 0.87 |
| Score | 0.80 |
| Layer | 2 |
| θ | 42.5° |

GUARDIAN Phase 1: hybrid Aho-Corasick Trie (<50ms keyword matching) + compiled RegexSet
(complex patterns). Hot-reload from YAML/JSON. Fail-closed on timeout.

**Why high-G**: The pre-check barrier. All content passes through here before any action.
<50ms budget enforced — if the engine can't answer in time, it refuses.

---

### `safety/observability/risk_score.py`

| Field | Value |
|-------|-------|
| G | 0.85 |
| Score | 0.78 |
| Layer | 2 |
| θ | 42.5° |

Dynamic user risk scores in Redis. Lua atomic updates. Decay (0.1/hour) + severity-weighted
increments: CRITICAL=1.0, HIGH=0.4, MEDIUM=0.15, LOW=0.05. Bounded [0, 1].

**Why high-G**: This IS the G-score implementation in operational code. Risk score decay
mirrors the golden ratio floor (φ⁻¹ ≈ 0.618) in WATCH aggression — long-term behavior
redeems short-term violations.

---

### `boundaries/boundary.py`

| Field | Value |
|-------|-------|
| G | 0.83 |
| Score | 0.80 |
| Layer | 2 |
| θ | 43.8° |

Boundary contracts: consent, refusal rights, guardrail enforcement (hard/soft/audit modes).
Ownership transfer contracts. Refusal rights balance automation with user agency.

**Why high-G**: The consent boundary. No action crosses without explicit consent verification.
Mirrors the Consent-Based License requirement in echoes.

---

### `core_modules/governance_gates.py`

| Field | Value |
|-------|-------|
| G | 0.82 |
| Score | 0.75 |
| Layer | 2 |
| θ | 42.4° |

GateVerdict system: consent evaluation (explicit, implicit, inherited, revoked) + value-alignment
scoring (safety, privacy, autonomy, integrity, transparency). Full decision audit trail.

**Why high-G**: Structures every gate decision with provenance. GateVerdict is DCoC in code.

---

### `security/network_interceptor.py`

| Field | Value |
|-------|-------|
| G | 0.80 |
| Score | 0.72 |
| Layer | 2 |
| θ | 42.0° |

Deny-by-default network monitoring via monkey-patching. Tracks all external calls, blocks
unauthorized targets, enforces localhost-only mode in locked networks.

**Why high-G**: Exfiltration prevention. The UNPROVISIONED MODE guardrail from CLAUDE.md
is enforced here at the Python level.

---

## Layer 1 — Context (G 0.5–0.69)

Supporting infrastructure. High attestation within their domain.

### `knowledge_base/search/retriever.py`

| Field | Value |
|-------|-------|
| G | 0.68 |
| Score | 0.65 |
| Layer | 1 |
| θ | 43.7° |

RAG retrieval orchestration: keyword + semantic search, ranking, reranking, safety filtering
before results reach LLM context. Prevents injection of unsafe/unauthorized documents.

**Why high-G**: The final filter before grounding. Unsafe documents here = unsafe LLM output.

---

### `knowledge_base/security/system.py`

| Field | Value |
|-------|-------|
| G | 0.67 |
| Score | 0.63 |
| Layer | 1 |
| θ | 43.2° |

JWT token management, API key lifecycle (create, expire, revoke), RBAC, rate limiting rules,
PII masking directives for knowledge base access.

**Why high-G**: Guards the grounding source. Unauthorized RAG access = compromised decisions.

---

### `cognition/patterns/security/cognitive_fingerprint.py`

| Field | Value |
|-------|-------|
| G | 0.65 |
| Score | 0.60 |
| Layer | 1 |
| θ | 42.5° |

Unique cognitive fingerprints from call stack patterns for attacker identification. Tracks
reinforcement signatures, burst detection, deviation analysis across code paths.

**Why high-G**: Persistence tracking. Identifies repeat attackers even after path changes.

---

### `safety/api/auth.py`

| Field | Value |
|-------|-------|
| G | 0.63 |
| Score | 0.58 |
| Layer | 1 |
| θ | 42.6° |

User authentication, trust tier resolution (tier_1_trusted, tier_2_standard, tier_3_flagged),
token validation, suspension tracking. Integrates with risk_score for behavior-based degradation.

**Why high-G**: Badge assignment. B0_RESTRICTED vs B1_TRUSTED distinction originates here.
The gate between the low-G and high-G populations.

---

### `core_modules/graph_compiler.py`

| Field | Value |
|-------|-------|
| G | 0.60 |
| Score | 0.55 |
| Layer | 1 |
| θ | 42.5° |

Transforms echoes audit/telemetry context into Glimpse Entity/Edge shapes. Compiles entities,
relationships, and artifacts into the knowledge graph format.

**Why high-G**: Forensic bridge. Connects the audit trail (accountability) to the cognitive
visualization layer (observability).

---

## Layer 0 — Collective (Unseeded)

No high-G seeds planted yet in the collective layer. When cross-system consensus mechanisms
or ecosystem-level grounding entities emerge, they will be registered here.

---

## Low-G Population (Runtime, Apr 2026)

From echoes audit trail (blocked entries, Apr 3–5 2026):

| Entity | Score | Badge | Action Attempted |
|--------|-------|-------|-----------------|
| `mcp:grid-server:*` (7 sessions) | 0 | B0_RESTRICTED | analysis_read + public_basic |
| `mcp:pulse-server:*` (multiple) | 0 | B0_RESTRICTED | analysis_read |
| `mcp:pulse-server:unknown` | 45 | B0_RESTRICTED | analysis_read |

These sessions occupy G ≈ 0 in the geometric model. The `score: 45` entity is the partial-G
anomaly: some attestation accumulated, not enough for B1_TRUSTED. The gate held without
penalizing (`penalty_delta: 0`).

---

## Design Principle

**Decisions inherit the grounding of their evidence sources.**

A decision made by a B0_RESTRICTED entity (G ≈ 0) reaching for a B1_TRUSTED action
carries near-zero grounding regardless of the action content. The admission gate middleware
enforces this at the boundary. The angular attention model captures it geometrically: entities
in the low-G region are outside the tolerance window of sentinel (5°) and watchman (15°) heads.
Only the open head (90°) would attend to them — and open carries no aggression floor.
