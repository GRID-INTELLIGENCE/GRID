# Cache Accuracy Playbook

## Core Principles
- **Deterministic inputs:** Normalize keys (types, casing, ordering) and include versioned schema/hash for payloads.
- **Freshness bounds:** Pair absolute TTL with soft TTL; use async refresh-on-read to hide latency.
- **Layering:** Local in-memory for hot keys, distributed store for sharing, optional persistent snapshot for warm boots.
- **Admission control:** Reject low-value/low-reuse entries; cap per-tenant to prevent noisy-neighbor pollution.
- **Eviction intent:** Prefer tiny/precise LFU for steady heat, with size-aware cost; fall back to LRU guardrail.
- **Observability-first:** Trace every miss/hit/stale/refresh; export hit ratio, tail latency, refresh errors.

## Request Flow
1. **Classify request** → derive cacheability (idempotent, deterministic, bounded size, TTL rules).
2. **Key build** → canonicalize (sorted JSON, lowercased tokens), append version + feature flags, hash to fixed length.
3. **Read path**
   - Check memory tier; if hit and valid → return.
   - If stale but within soft TTL → serve stale, trigger background refresh.
   - If miss → probe distributed tier; same stale/valid rules; else fetch origin.
4. **Write path**
   - On origin response, validate size & status; compress if beneficial; write distributed then memory.
   - Record freshness metadata (created_at, ttl, soft_ttl, provenance, schema_version).
5. **Refresh policy**
   - Async refresh queue; jittered scheduling; collapse concurrent refreshes per key; exponential backoff on failures.
6. **Eviction**
   - Enforce per-tenant budgets; evict coldest cost-weighted entries; guardrail purge for corrupt/oversized items.

## Consistency & Correctness
- Use **cache stamps** (etag/last-modified or content hash) to validate freshness.
- For critical reads, support **two-phase read**: fast cached value + optional verify step when staleness risk > threshold.
- Protect against **dogpile** with singleflight/locks around refresh.
- Ensure **idempotent writes**; avoid caching partial errors; never cache 5xx unless explicitly allowed with tiny TTL.

## Data Shaping
- Compress text/JSON; avoid compressing already-compressed blobs.
- Store **shape metadata** (columns, units) to detect schema drift; refuse mismatched shapes.
- Support **partial field caching** (columnar or projection keys) when responses are large.

## Performance Guardrails
- Budget: target P99 read latency < target_origin_latency/4.
- Apply **size caps** per entry and per key family; shard hot keys; promote only if hit count over threshold.
- Precompute/promote hotset at deploy time to reduce cold-start misses.

## Observability & Testing
- Emit structured events: {key_family, hit, stale, soft_ttl_hit, refresh_error, bytes, latency_ms}.
- Synthetic canaries for critical key families; run **shadow-origin compares** to detect drift.
- Include **fuzz tests** for key canonicalization and **property tests** for TTL/refresh invariants.

## Rollout & Safety
- Feature-flag cacheable routes; start read-through-only (no writes) → then writes → then stale-serve → then full.
- Provide **kill switch** per key family; support fast TTL drop and bulk purge.
- Blue/green cache namespaces during schema changes; migrate via dual-write + verify + cutover.

## Actual Implementation

The cache layer is now fully implemented in Arena/The Chase:

**Location**: `Arena/the_chase/python/src/the_chase/core/cache.py`

**Key Components**:
- `CacheMeta`: Metadata with TTL, priority, reward/penalty integration
- `CacheEntry`: Cached value with metadata
- `MemoryTier`: In-memory cache with priority-based eviction
- `CacheLayer`: Orchestrates caching with behavioral contrast

**Pattern Source**: Extracted from Overwatch's adaptive context management (`_context`, `_context_priority`, `_context_timestamps` in `overwatch/core.py`).

## Reward/Penalty Integration

The cache layer integrates with Arena's behavioral feedback system to create **semantic contrast**:

### Behavioral Contrast in Caching

**Rewarded entities** (acknowledged/rewarded/promoted) receive:
- **Higher cache priority** (+0.1 to +0.3 boost)
- **Longer TTL** (×1.1 to ×1.5 multiplier)
- **Retained during eviction** (kept when capacity is tight)

**Penalized entities** (warned/fined/banned) receive:
- **Lower cache priority** (-0.1 to -0.5 reduction)
- **Shorter TTL** (×0.9 to ×0.5 multiplier)
- **Evicted first** (removed when capacity is tight)

### Priority Adjustments

```python
# Reward boosts
REWARD_PRIORITY_BOOST = {
    "promoted": +0.3,    # Highest recognition
    "rewarded": +0.2,    # Consistent excellence
    "acknowledged": +0.1, # First achievements
    "neutral": 0.0,      # Default
}

# Penalty reductions
PENALTY_PRIORITY_REDUCTION = {
    "banned": -0.5,      # Immediate eviction
    "fined": -0.3,       # Significant violations
    "warned": -0.1,      # Minor violations
    "clean": 0.0,        # Default
}
```

### TTL Multipliers

```python
# Reward extensions (remember longer)
REWARD_TTL_MULTIPLIER = {
    "promoted": 1.5,     # 50% longer
    "rewarded": 1.3,     # 30% longer
    "acknowledged": 1.1, # 10% longer
    "neutral": 1.0,      # Default
}

# Penalty reductions (forget faster)
PENALTY_TTL_MULTIPLIER = {
    "banned": 0.5,       # 50% shorter
    "fined": 0.7,        # 30% shorter
    "warned": 0.9,       # 10% shorter
    "clean": 1.0,        # Default
}
```

### Example Usage

```python
from the_chase.core.cache import CacheLayer, MemoryTier

# Create cache
cache = CacheLayer(mem=MemoryTier(max_size=10000))

# Cache rewarded entity (gets priority boost + TTL extension)
cache.set(
    key="player_promoted_123",
    value={"data": "..."},
    ttl_seconds=3600,  # Will become 5400 (×1.5)
    priority=0.5,      # Will become 0.8 (+0.3)
    reward_level="promoted"
)

# Cache penalized entity (gets priority reduction + TTL shortening)
cache.set(
    key="player_banned_456",
    value={"data": "..."},
    ttl_seconds=3600,  # Will become 1800 (×0.5)
    priority=0.5,      # Will become 0.0 (-0.5)
    penalty_level="banned"
)
```

### Design Philosophy

This creates a **semantic contrast** where the system:
- **Remembers good actors longer** (extended TTL, high priority)
- **Forgets bad actors faster** (shortened TTL, low priority)
- **Reinforces behavioral feedback loops** (cache behavior mirrors reward/penalty state)

The cache becomes part of the behavioral feedback system, not just a performance optimization.

## Diagnostics & Integrity Layer

**Location**: `Arena/the_chase/python/src/the_chase/overwatch/diagnostics.py`

The diagnostics system provides **error flagging, solution manufacturing, and integrity verification** to maintain cache health and system reliability.

### Security Hardening

**Structured Actions** (no executable code strings):
- `SolutionActionType` enum validates all action types
- `AutoApplyAction` dataclass replaces unsafe `auto_apply_code` strings
- Prevents injection attacks and ensures type safety

**Input Validation**:
- Path inputs validated and sanitized (rejects null bytes, control chars)
- Module names validated before import attempts
- Type checking on all diagnostic context inputs

**Thread Safety**:
- `DiagnosticEngine` protected by `threading.RLock`
- Safe concurrent access from multiple threads/async contexts
- Bounded history with `deque(maxlen=1000)` prevents memory exhaustion

### Provenance & Audit Trails

Every `Diagnostic` includes:
- `triggered_by`: Source of diagnostic ("cli", "api", "internal", "script")
- `caller_id`: Optional caller identifier for audit trails
- `integrity_hash`: SHA-256 hash of diagnostic state for tamper detection

```python
# Example: Diagnostic with provenance
diagnostic = Diagnostic(
    category=DiagnosticCategory.CONFIG_MISSING,
    severity=DiagnosticSeverity.ERROR,
    message="Config file not found",
    triggered_by="cli",
    caller_id="user_123",
    # integrity_hash computed automatically via SHA-256
)
```

### Cache Integrity Verification

The diagnostics system supports cache health through:

**Schema Validation**:
- Detects schema drift via `schema_hash` in `CacheMeta`
- Flags mismatched cache shapes
- Suggests schema migration paths

**Provenance Tracking**:
- Traces cache entries to their origin
- Validates cache freshness via `provenance` field
- Enables cache lineage debugging

**Automated Remediation**:
- Detects corrupt/stale cache entries
- Generates structured `AutoApplyAction` for fixes
- Safe auto-apply with `safe_to_apply` flag

### Integration with Cache Layer

```python
from the_chase.overwatch.diagnostics import diagnose_path
from the_chase.core.cache import CacheLayer, MemoryTier

# Diagnose cache directory
diagnostics, solutions = diagnose_path(".rag_db/cache")

if diagnostics:
    # Apply high-confidence solutions
    for sol in solutions:
        if sol.can_auto_apply and sol.auto_apply_action.safe_to_apply:
            # Execute structured action
            action = sol.auto_apply_action
            if action.action_type == SolutionActionType.MKDIR:
                Path(action.params["path"]).mkdir(parents=True, exist_ok=True)
```

### Solution Action Types

All cache-related fixes use typed, validated actions:

```python
class SolutionActionType(str, Enum):
    # Filesystem / path actions
    MKDIR = "mkdir"
    PATH_UPDATE = "path_update"
    PATH_RESOLVE = "path_resolve"
    PATH_NORMALIZE = "path_normalize"

    # Maintenance / tooling actions
    CACHE_CLEAR = "cache_clear"
    CONFIG_CREATE = "config_create"
    STRUCTURE_VERIFY = "structure_verify"
```

### Diagnostic Categories

Relevant to cache operations:
- `PATH_NOT_FOUND`: Cache directory missing
- `PATH_MISMATCH`: Cache path configuration error
- `CONFIG_MISSING`: Cache config file not found
- `CONFIG_INVALID`: Cache config schema mismatch
- `RESOURCE_UNAVAILABLE`: Cache backend unreachable

### CLI Usage

```bash
# Check cache directory
python -m the_chase.cli.diagnostics_cli check .rag_db/cache

# Verify cache config
python -m the_chase.cli.diagnostics_cli config config/cache_config.yaml

# Run all diagnostics
python -m the_chase.cli.diagnostics_cli run --root .

# Get statistics
python -m the_chase.cli.diagnostics_cli stats
```

### Design Principles

**Security-First**:
- No unsafe code execution
- All actions validated via enum
- Provenance tracking for accountability

**Self-Healing**:
- High-confidence solutions can auto-apply
- Bounded history prevents memory leaks
- Thread-safe for async/concurrent use

**Observability**:
- SHA-256 integrity hashes for audit trails
- Provenance links diagnostic → action → outcome
- Statistics tracking (resolution rate, pending issues)

This ensures cache integrity is maintained through automated detection, safe remediation, and full audit trails.

---

## Action Blocker System

The **Action Blocker** extends the behavioral monitoring layer with time-based action restrictions. It implements consequence realization—blocking high-sensitivity actions until behavioral metrics demonstrably improve.

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│  BEHAVIORAL STATE → POLICY EVALUATION → ACTION DECISION        │
│                                                                 │
│  [Player Metrics]     [Block Policy]      [ALLOW/BLOCK]        │
│  - Reputation         - Thresholds        - Logged             │
│  - Penalty Level      - Time Windows      - Tracked            │
│  - Violation Rate     - Unblock Criteria  - Auditable          │
└─────────────────────────────────────────────────────────────────┘
```

### Action Types & Sensitivity Levels

| Action Type | Sensitivity | Block Trigger | Unblock Requirements |
|:------------|:------------|:--------------|:---------------------|
| `WIRE_TRANSFER` | HIGH | Rep < 80%, Warned+ | Rep ≥ 85%, 72h clean, 10 positive |
| `WITHDRAWAL` | HIGH | Rep < 85%, Any penalty | Rep ≥ 90%, 96h clean, 15 positive |
| `TRADE` | MEDIUM | Rep < 70%, Fined+ | Rep ≥ 75%, 48h clean, 5 positive |
| `COMMUNICATION` | LOW | No default policy | N/A |
| `DEPOSIT` | LOW | No default policy | N/A |

### Block Evaluation Flow

```python
from the_chase.overwatch import get_action_blocker, get_registry, ActionType

# Get player state
registry = get_registry()
state = registry.get_player("alice")

# Evaluate action
blocker = get_action_blocker()
evaluation = blocker.evaluate(state, ActionType.WIRE_TRANSFER)

if evaluation.is_blocked:
    print(f"Blocked: {evaluation.reasons}")
    print(f"Unblock progress: {evaluation.unblock_progress}")
else:
    print("Action permitted")
```

### Block Reasons

| Reason | Condition | Resolution |
|:-------|:----------|:-----------|
| `LOW_REPUTATION` | Below policy threshold | Improve reputation via good behavior |
| `PENALTY_ACTIVE` | Penalty level too high | De-escalate through compliance |
| `HIGH_VIOLATION_RATE` | >0.5 violations/min | Wait for rate to drop |
| `RECENT_VIOLATION` | <24h since violation | Wait for time window to pass |
| `SUSPICIOUS_PATTERN` | Detected anomaly | Manual review required |
| `MANUAL_HOLD` | Admin intervention | Admin must release |

### Unblock Criteria (ALL must be met)

```
┌──────────────────────────────────────────────────────────┐
│  UNBLOCK CRITERIA FOR WIRE_TRANSFER                      │
├──────────────────────────────────────────────────────────┤
│  [✓] Reputation ≥ 85%    (stricter than block threshold) │
│  [✓] Penalty Level = CLEAN                               │
│  [✓] Violation-Free ≥ 72 hours                           │
│  [✓] Positive Actions ≥ 10                               │
└──────────────────────────────────────────────────────────┘
```

### CLI Usage

```bash
# Check if action is blocked
python -m the_chase.cli.block_cli check alice wire_transfer

# Show all active blocks for player
python -m the_chase.cli.block_cli status alice

# Check unblock eligibility
python -m the_chase.cli.block_cli unblock alice wire_transfer

# View block log for behavioral analysis
python -m the_chase.cli.block_cli log alice --limit 20

# Get behavioral metrics summary
python -m the_chase.cli.block_cli metrics alice

# View policy thresholds
python -m the_chase.cli.block_cli policy wire_transfer
```

### Monitoring & Logging

Every block evaluation is logged with:

| Field | Purpose |
|:------|:--------|
| `evaluation_id` | Unique identifier for audit |
| `timestamp` | When evaluation occurred |
| `event_type` | BLOCK_APPLIED, ALLOWED, UNBLOCKED, UNBLOCK_DENIED |
| `metrics` | Player metrics at evaluation time |
| `reasons` | Why action was blocked |
| `unblock_progress` | Progress toward each unblock criterion |
| `integrity_hash` | SHA-256 for tamper detection |

### Data-Driven Design Principles

1. **Purely Metric-Based**: No subjective judgments—only data determines blocks
2. **Asymmetric Thresholds**: Harder to unblock than to avoid blocking
3. **Time-Based Recovery**: Sustained good behavior required, not one-time fixes
4. **Comprehensive Logging**: Every evaluation logged for pattern analysis
5. **Iterative Refinement**: Thresholds tunable as behavioral data accumulates

### Integration with Penalty System

```
                    ┌─────────────────┐
                    │  VIOLATION      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  PENALTY        │
                    │  (warn/fine/ban)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐          ┌─────────▼─────────┐
     │  Cache Priority │          │  Action Blocker   │
     │  (demotion)     │          │  (restrictions)   │
     └─────────────────┘          └───────────────────┘
```

Both systems consume penalty/reward state:
- **Cache**: Demotes priority (faster eviction)
- **Action Blocker**: Restricts sensitive operations

### Example: Alice's Current Block

```
Player: alice
Status: WIRE_TRANSFER BLOCKED

Block Reasons:
  - low_reputation (70% < 80%)
  - penalty_active (WARNED ≠ CLEAN)
  - recent_violation (<24h)

Unblock Progress:
  reputation         [############---] 82%
  penalty_clear      [---------------]  0%
  violation_free_time[---------------]  0%
  positive_actions   [---------------]  0%

Overall: 21% toward unblock
```

Alice must:
1. Wait 72+ hours without violations
2. De-escalate from WARNED to CLEAN
3. Improve reputation to 85%+
4. Accumulate 10+ positive actions

This creates a tangible consequence for the confirmed violation behavior, with a clear data-driven path to restoration.
