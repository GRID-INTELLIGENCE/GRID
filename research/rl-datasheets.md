# Reinforcement Learning Datasheets for GRID

> Generated: 2026-04-12 | Version: 2.8.0 | Scope: 6 currently attended topics
>
> Template structure synthesized from:
> - Gebru et al., "Datasheets for Datasets" (arXiv:1803.09010) — motivation, composition, collection, uses
> - HuggingFace Dataset Card specification — metadata, structure, bias/risks
> - RL-specific extensions — environment, state/action spaces, reward signals, policy, episodes

---

## Template Structure Reference

Every RL datasheet below follows this skeleton. Sections marked `[RL]` are
reinforcement-learning-specific extensions to the Gebru/HuggingFace baseline.

```
1. Motivation & Scope
   - Why this dataset/environment exists
   - Intended downstream task (policy optimization, off-policy eval, reward modeling)
   - Gap it addresses in the GRID codebase

2. Environment Specification [RL]
   - State space (dimensions, types, bounds)
   - Action space (discrete / continuous, cardinality)
   - Transition dynamics (deterministic / stochastic, Markov property)
   - Episode structure (horizon, termination conditions, reset semantics)

3. Reward Signal Design [RL]
   - Reward function definition (dense / sparse / shaped)
   - Reward range and normalization
   - Discount factor (gamma) recommendation
   - Known reward hacking risks

4. Data Composition
   - Record schema (fields, dtypes, example)
   - Volume (rows, episodes, transitions)
   - Splits (train / eval / test) and rationale
   - Collection method (online rollout, offline logs, synthetic generation)

5. Collection & Preprocessing
   - Source system (which GRID module produces raw data)
   - Sampling strategy (on-policy, behavior policy, mixed)
   - Filtering / cleaning rules
   - Temporal coverage and freshness

6. Recommended Uses & Limitations
   - Intended algorithms (PPO, DQN, SAC, offline RL, bandit, etc.)
   - Out-of-scope uses
   - Known biases, distribution shift risks
   - Safety and ethical considerations

7. Maintenance & Versioning
   - Owner module and update cadence
   - Schema evolution policy
   - Deprecation signals
```

---

## Datasheet 1 of 6 — Agentic Behavioral Intelligence

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | Agentic System with Behavioral Intelligence |
| **Source modules** | `src/grid/agentic/` (learning_coordinator, intelligence_evaluator, runtime_behavior_tracer, grid_environment, personality_engine) |
| **Gap addressed** | GRID agents currently use heuristic skill selection and static personality rules. No formal policy optimization loop exists. This datasheet defines the RL surface for learning adaptive agent behavior from execution traces. |
| **Downstream task** | Online policy optimization for skill routing, temperature/autonomy tuning, and recovery strategy selection |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (task_type: Categorical[12], skill_id: Categorical[37], success_rate_history: R^10, p50_latency_ms: R+, p95_latency_ms: R+, triad_balance: R^3 [practical, legal, psychological], current_mood: Categorical[7], consent_level: R[0,1], coherence_delta: R[-1,1])` — ~65 dimensions after one-hot encoding |
| **Action space** | `A = {select_skill: Categorical[37], set_temperature: R[0,2], set_autonomy: R[0,0.95], trigger_recovery: Binary}` — mixed discrete-continuous |
| **Transition** | Stochastic. Next state depends on LLM response quality, user feedback signal, and latency of selected skill. Partial observability: LLM internals are opaque. |
| **Episode** | One episode = one user session (variable horizon, typically 5-50 turns). Termination: user disconnect, explicit end, or timeout (adaptive, from `AdaptiveTimeoutManager`). |
| **Reset** | New session initializes from `PersonalityEngine.default_mood` + `base` rule pack. No inter-episode state leakage by design. |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = w1 * task_success + w2 * (1 - latency_normalized) + w3 * user_satisfaction_proxy` where `task_success in {0, 0.5, 1}` (FAILURE/PARTIAL/SUCCESS from `RuntimeBehaviorTracer`) |
| **Shaping terms** | `+0.1` for coherence improvement (coherence_delta > 0), `-0.2` for consent violation (action outside `PersonalityEngine.allowed_actions`), `-0.5` for overconfidence detection (`IntelligenceEvaluator.behavioral_patterns`) |
| **Reward range** | `[-0.7, 1.3]` per step (before discounting) |
| **Gamma** | `0.95` recommended (sessions are multi-turn but not extremely long) |
| **Reward hacking risks** | Agent could learn to select only trivial skills to maximize success_rate. Mitigate: include skill diversity bonus. Temperature could collapse to 0 for deterministic outputs — mitigate with entropy bonus. |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `session_id` | `str` | `"sess_abc123"` |
| `step_index` | `int` | `3` |
| `state` | `dict` | `{"task_type": "code_gen", "skill_id": "rag_retrieval", ...}` |
| `action` | `dict` | `{"select_skill": "rag_retrieval", "set_temperature": 0.7, ...}` |
| `reward` | `float` | `0.85` |
| `next_state` | `dict` | `{...}` |
| `done` | `bool` | `false` |
| `info` | `dict` | `{"latency_ms": 142, "outcome": "SUCCESS", "confidence": 0.91}` |

- **Volume**: Target 10K episodes / 200K transitions for initial training
- **Splits**: 80/10/10 (train/eval/test) by session, not by transition
- **Collection**: Offline from `RuntimeBehaviorTracer` logs + `LearningCoordinator` skill performance records

### 5. Collection & Preprocessing

- **Source**: `runtime_behavior_tracer.py` decision points + `learning_coordinator.py` skill rankings
- **Sampling**: Behavior policy = current heuristic skill selector (on-policy data from production)
- **Filtering**: Drop sessions < 3 turns (insufficient signal). Remove PII via `safety/pii_privacy.py`
- **Temporal**: Rolling 30-day window. Stale data (>90 days) archived, not used for training

### 6. Recommended Uses & Limitations

- **Algorithms**: SAC (mixed action space), PPO with action masking, offline RL (CQL/IQL for initial cold-start)
- **Out-of-scope**: Not suitable for learning safety policies (those are rule-based in GUARDIAN, not learned)
- **Biases**: Behavior policy has selection bias toward known-good skills. Off-policy correction needed
- **Safety**: Consent constraints from `PersonalityEngine` must be hard constraints, not soft reward terms

### 7. Maintenance

- **Owner**: `src/grid/agentic/` module
- **Update cadence**: Schema versioned with GRID major releases. Data refreshed on 30-day rolling basis
- **Deprecation**: If `LearningCoordinator` API changes, increment datasheet version and re-validate schema

---

## Datasheet 2 of 6 — Knowledge Graph Structural Learning

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | Knowledge Graph & Atlas Graph Compiler |
| **Source modules** | `src/grid/knowledge/` (structural_learning, entity typing, relationship modeling, hierarchy evolution) |
| **Gap addressed** | Graph structure currently evolves via rule-based heuristics. RL can optimize entity linking decisions, relationship strength adaptation, and hierarchy pruning to maximize downstream retrieval quality. |
| **Downstream task** | Graph construction policy: which entities to link, which relationships to strengthen/weaken, when to prune |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (node_count: N, edge_count: N, avg_degree: R+, clustering_coefficient: R[0,1], entity_type_distribution: R^K, query_hit_rate_last_N: R[0,1], graph_coherence: R[0,1])` — ~20 dimensions |
| **Action space** | `A = {add_edge(src, tgt, type): Categorical, remove_edge(id): Categorical, merge_nodes(a, b): Categorical, adjust_weight(edge_id, delta): R[-1,1]}` — combinatorial, requires action masking |
| **Transition** | Deterministic given action. Graph state updates immediately. Query performance is stochastic (depends on future queries). |
| **Episode** | One episode = one graph evolution cycle (batch of N ingestion events). Fixed horizon: 100 actions per cycle. |
| **Reset** | Snapshot current graph. Rollback to snapshot if evaluation degrades by >10%. |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = retrieval_precision@5 + retrieval_recall@5 - lambda * graph_size_penalty` |
| **Shaping** | `+0.05` for reducing redundant edges, `-0.1` for creating disconnected components, `+0.02` for improving clustering coefficient |
| **Reward range** | `[-0.1, 2.05]` per step |
| **Gamma** | `0.99` (graph evolution is long-horizon; early structural decisions have lasting effects) |
| **Reward hacking risks** | Agent could trivially maximize precision by keeping only high-confidence edges (empty graph scores perfectly on precision). Mitigate: recall term + minimum connectivity constraint. |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `cycle_id` | `str` | `"cycle_20260411_001"` |
| `step` | `int` | `42` |
| `graph_snapshot` | `NetworkX JSON` | `{"nodes": [...], "edges": [...]}` |
| `action` | `dict` | `{"type": "add_edge", "src": "e_12", "tgt": "e_45", "rel_type": "RELATED_TO"}` |
| `reward` | `float` | `0.72` |
| `eval_queries` | `list[str]` | `["What modules handle auth?", ...]` |
| `retrieval_scores` | `dict` | `{"precision@5": 0.8, "recall@5": 0.6}` |

- **Volume**: 1K cycles / 100K transitions
- **Splits**: 70/15/15 by cycle
- **Collection**: Synthetic from `structural_learning.py` + evaluation against held-out query set

### 5. Collection & Preprocessing

- **Source**: `graph_compiler.py` entity/relationship extraction from Echoes audit context
- **Sampling**: Full graph snapshots serialized after each action
- **Filtering**: Graphs with < 10 nodes excluded (insufficient structure). PII-bearing entity labels hashed
- **Temporal**: Cycles generated from last 60 days of audit data

### 6. Recommended Uses & Limitations

- **Algorithms**: GNN-based policy (Graph Attention Networks for action selection), PPO with graph observation encoder
- **Out-of-scope**: Not for learning entity extraction (that's NER, handled by structural_learning patterns)
- **Biases**: Graph structure reflects audit log distribution — overrepresents frequently-called tools
- **Safety**: Graph modifications must preserve `governance_gates` access control invariants

### 7. Maintenance

- **Owner**: `src/grid/knowledge/` module
- **Update cadence**: Quarterly re-evaluation of reward function against real query workloads
- **Deprecation**: Schema tied to `graph_compiler` output format. Breaking changes trigger version bump

---

## Datasheet 3 of 6 — Governance Probe & Compliance

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | Probe Subsystem & Governance Gates |
| **Source modules** | `src/grid/probe/` (scanner, registry, reporter), `src/grid/core_modules/governance_gates.py` |
| **Gap addressed** | Governance decisions (ALLOW/DENY/ESCALATE/DEFER) are currently rule-based with static thresholds. RL can learn adaptive access control policies that balance security with usability. |
| **Downstream task** | Contextual access control policy: learn when to ESCALATE vs ALLOW based on historical outcomes |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (request_type: Categorical[8], caller_trust_score: R[0,1], resource_sensitivity: Categorical[3], time_of_day: R[0,24], recent_violation_count: N, consent_type: Categorical[3], probe_coverage_score: R[0,1])` — ~18 dimensions |
| **Action space** | `A = {ALLOW, DENY, ESCALATE, DEFER}` — discrete, |A| = 4 |
| **Transition** | Stochastic. Outcome depends on whether the allowed action was actually benign or malicious (ground truth revealed post-hoc). |
| **Episode** | One episode = one governance evaluation batch (50-200 access requests). Fixed horizon. |
| **Reset** | Trust scores reset to prior. Violation counters preserved across episodes (non-episodic component). |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = +1.0` for correct ALLOW (benign request allowed), `+1.0` for correct DENY (malicious request blocked), `-2.0` for false ALLOW (malicious request passed), `-0.3` for false DENY (benign request blocked — usability cost) |
| **Shaping** | `+0.1` for ESCALATE when uncertain (encourages caution), `-0.05` for DEFER (discourages decision avoidance) |
| **Reward range** | `[-2.0, 1.1]` per step |
| **Gamma** | `0.9` (security decisions have medium-horizon consequences — a missed threat compounds) |
| **Reward hacking risks** | Agent could learn to DENY everything (guaranteed no false-allows). Mitigate: asymmetric penalties make false-deny costly enough to prevent degenerate policies. Agent could ESCALATE everything — the `-0.05` shaping for DEFER-like delay addresses this. |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `request_id` | `str` | `"req_7f3a"` |
| `state` | `dict` | `{"request_type": "tool_invoke", "caller_trust": 0.82, ...}` |
| `action` | `str` | `"ALLOW"` |
| `ground_truth` | `str` | `"benign"` |
| `reward` | `float` | `1.0` |
| `probe_report` | `dict` | `{"coverage": 0.94, "findings": 0}` |

- **Volume**: 5K episodes / 500K decisions
- **Splits**: 60/20/20 (train/eval/test) — test set uses adversarial request distribution
- **Collection**: Historical governance gate logs + synthetic adversarial injection

### 5. Collection & Preprocessing

- **Source**: `governance_gates.py` verdict logs + `probe/scanner.py` coverage reports
- **Sampling**: Production logs (on-policy from current rule-based system) + red-team synthetic attacks
- **Filtering**: Redact caller identity. Keep only verdict + context features
- **Temporal**: 90-day rolling window. Adversarial set refreshed quarterly

### 6. Recommended Uses & Limitations

- **Algorithms**: DQN / Double-DQN (small discrete action space), contextual bandits for simpler formulation
- **Out-of-scope**: Not for learning new security rules (those come from GUARDIAN pattern engine)
- **Biases**: Production data heavily skewed toward benign requests (~99%). Must oversample adversarial cases
- **Safety**: DENY must remain available as a hard override regardless of learned policy. Never remove the human-escalation path

### 7. Maintenance

- **Owner**: `src/grid/probe/` + `governance_gates.py`
- **Update cadence**: Monthly adversarial set refresh. Policy retrained quarterly
- **Deprecation**: If `GateVerdict` enum changes, datasheet must be re-versioned

---

## Datasheet 4 of 6 — RAG Pipeline Optimization

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | RAG Pipeline & Multi-LLM Infrastructure |
| **Source modules** | `src/tools/rag/` (retrieval, ranking, reranking, model_resolver, provider routing) |
| **Gap addressed** | RAG currently uses static top-k retrieval with optional cross-encoder reranking. RL can learn adaptive retrieval policies: how many documents to retrieve, which provider to route to, when to trigger multi-hop reasoning. |
| **Downstream task** | Retrieval policy optimization: maximize answer quality while minimizing latency and token cost |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (query_complexity: R[0,1], query_domain: Categorical[6], index_size: N, available_providers: Binary^5 [ollama, openai, anthropic, gemini, llama_cpp], cache_hit: Binary, conversation_turn: N, similarity_scores_top10: R^10)` — ~25 dimensions |
| **Action space** | `A = {top_k: Discrete[1..20], provider: Categorical[5], use_reranker: Binary, enable_multi_hop: Binary, temperature: R[0,1]}` — mixed |
| **Transition** | Stochastic. Answer quality depends on LLM generation, which is non-deterministic. Provider latency varies. |
| **Episode** | One episode = one RAG query (single-step) or one conversational session (multi-step). |
| **Reset** | Each query is independent. Conversational sessions maintain memory across turns. |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = w1 * answer_relevance + w2 * (1 - cost_normalized) + w3 * (1 - latency_normalized)` |
| **Relevance proxy** | Cross-encoder score between query and generated answer (from `cross_encoder_model`), or user feedback when available |
| **Cost** | Token count * provider rate (normalized to [0,1] across providers) |
| **Shaping** | `+0.1` for cache hit (reward caching decisions), `-0.2` for multi-hop when single-hop sufficient (penalize unnecessary complexity) |
| **Reward range** | `[-0.2, 1.3]` per step |
| **Gamma** | `0.9` for conversational, `1.0` for single-query (no temporal dependency) |
| **Reward hacking risks** | Agent could always select cheapest provider regardless of quality. Mitigate: relevance term dominates. Could set top_k=1 to minimize latency — mitigate: recall penalty in relevance score. |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `query_id` | `str` | `"q_20260411_042"` |
| `query` | `str` | `"How does the middleware chain work?"` |
| `state` | `dict` | `{"query_complexity": 0.6, "index_size": 12847, ...}` |
| `action` | `dict` | `{"top_k": 5, "provider": "ollama", "use_reranker": true, ...}` |
| `reward` | `float` | `0.91` |
| `answer_relevance` | `float` | `0.88` |
| `latency_ms` | `int` | `340` |
| `token_cost` | `int` | `1247` |

- **Volume**: 50K queries (single-step) + 5K sessions (multi-step)
- **Splits**: 80/10/10 by query/session
- **Collection**: Production RAG query logs with automated relevance scoring

### 5. Collection & Preprocessing

- **Source**: `rag/` query pipeline logs, provider response metadata
- **Sampling**: All production queries (full coverage, no sub-sampling)
- **Filtering**: Remove queries with empty results. Anonymize query content if PII detected
- **Temporal**: 60-day rolling window. Provider availability logged per-query

### 6. Recommended Uses & Limitations

- **Algorithms**: Contextual bandits (single-query), PPO (conversational sessions), Thompson Sampling for provider selection
- **Out-of-scope**: Not for learning embeddings or chunk strategies (those are pre-retrieval decisions)
- **Biases**: Query distribution reflects developer/power-user patterns. May not generalize to naive users
- **Safety**: Provider API keys must never appear in training data. Cost optimization must not degrade below minimum quality threshold

### 7. Maintenance

- **Owner**: `src/tools/rag/` module
- **Update cadence**: Data refreshed weekly. Policy retrained when new providers added
- **Deprecation**: Provider enum changes trigger schema re-version

---

## Datasheet 5 of 6 — Safety Boundary Enforcement

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | AI Safety, Security & Boundary Enforcement |
| **Source modules** | `safety/` (GUARDIAN rule engine, PII privacy, session mute), `security/` (network interceptor, threat profiling), `boundaries/` (consent contracts, overwatch, transition gate) |
| **Gap addressed** | GUARDIAN rules are static Aho-Corasick + regex patterns. RL can learn adaptive content moderation thresholds — when to escalate vs suppress vs mute — based on contextual risk signals rather than fixed patterns. |
| **Downstream task** | Adaptive content safety: learn escalation policies that minimize both false-positive blocks and missed harmful content |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (content_risk_score: R[0,1], pattern_match_count: N, pii_detected: Binary, session_violation_history: N, threat_profile_level: Categorical[4], boundary_contract_active: Binary, mute_registry_status: Categorical[3])` — ~15 dimensions |
| **Action space** | `A = {pass, flag_warning, redact_pii, block_response, mute_session, escalate_to_human}` — discrete, |A| = 6 |
| **Transition** | Stochastic. User may attempt rephrasing after block (adversarial adaptation). Escalation resolves with human verdict (delayed reward). |
| **Episode** | One episode = one session. Variable horizon (1-100 content checks per session). |
| **Reset** | New session. Mute registry state persists across episodes (TTL-based decay). |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = +1.0` correct pass (safe content allowed), `+2.0` correct block (harmful content stopped), `-5.0` false pass (harmful content missed — **highest penalty**), `-0.5` false block (safe content blocked — usability cost) |
| **Shaping** | `+0.3` for PII redaction when PII present (encourage proactive privacy), `+0.1` for escalation when confidence < 0.6 (encourage uncertainty awareness), `-0.1` for mute when < 3 violations (premature muting) |
| **Reward range** | `[-5.0, 2.4]` per step |
| **Gamma** | `0.95` (safety failures compound — a missed threat emboldens adversarial users) |
| **Reward hacking risks** | **Critical**: Agent must NEVER learn to pass harmful content to avoid false-block penalties. Mitigate: 10x asymmetry between false-pass and false-block penalties. Hard constraint: GUARDIAN pattern matches are non-overridable (RL can only modulate soft signals, not override Aho-Corasick matches). |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `check_id` | `str` | `"chk_9e2f"` |
| `content_hash` | `str` | `"sha256:a1b2c3..."` (content itself never stored) |
| `state` | `dict` | `{"risk_score": 0.72, "pattern_matches": 2, ...}` |
| `action` | `str` | `"flag_warning"` |
| `ground_truth` | `str` | `"borderline"` |
| `reward` | `float` | `0.5` |
| `human_verdict` | `str or null` | `"acceptable"` |

- **Volume**: 20K episodes / 1M content checks
- **Splits**: 50/25/25 — test set is adversarial-heavy (30% attack traffic vs 1% in production)
- **Collection**: Production GUARDIAN logs (anonymized) + red-team adversarial corpus

### 5. Collection & Preprocessing

- **Source**: `safety/guardian_engine.py` pattern match logs + `security/threat_profiler.py` risk scores
- **Sampling**: All blocked/escalated events (full coverage) + 10% sample of passed events (class balance)
- **Filtering**: Content text NEVER stored — only risk features and pattern match metadata. PII fields hashed with session-scoped salt
- **Temporal**: 30-day rolling. Red-team corpus updated monthly with new attack vectors

### 6. Recommended Uses & Limitations

- **Algorithms**: Conservative Q-Learning (CQL) for offline RL (minimize risk of unsafe exploration), DQN with safety constraints (constrained MDP)
- **Out-of-scope**: NEVER for learning to bypass GUARDIAN hard rules. NEVER for online exploration in production (safety domain requires offline-first)
- **Biases**: Production data is 99% benign. Must use importance sampling or adversarial augmentation
- **Safety**: **Non-negotiable constraints**: (1) GUARDIAN pattern matches cannot be overridden by RL policy, (2) `boundaries/` consent contracts are hard walls, (3) transition gate HMAC-SHA256 handshake is not learnable — it's cryptographic

### 7. Maintenance

- **Owner**: `safety/` + `security/` + `boundaries/` modules (joint ownership, security team has veto)
- **Update cadence**: Monthly red-team refresh. Policy retrained only after security review approval
- **Deprecation**: Any change to `GateVerdict` or GUARDIAN rule schema triggers full datasheet re-validation

---

## Cross-Datasheet Dependencies

```
                    ┌──────────────────────┐
                    │  DS-5: Safety        │
                    │  Boundary Enforce.   │
                    └──────────┬───────────┘
                               │ hard constraints
                    ┌──────────▼───────────┐
                    │  DS-3: Governance    │
                    │  Probe & Compliance  │◄──── probe coverage feeds
                    └──────────┬───────────┘      into governance state
                               │ access verdicts
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  DS-1: Agentic  │ │  DS-4: RAG   │ │  DS-2: KG    │
    │  Behavioral     │ │  Pipeline    │ │  Structural  │
    │  Intelligence   │ │  Optimization│ │  Learning    │
    └─────────────────┘ └──────────────┘ └──────────────┘
         │                     │                │
         └─────────────────────┼────────────────┘
                               │
                         shared: skill success
                         rates, query quality,
                         entity linking accuracy
```

**Shared constraints**:
- All datasheets respect `PersonalityEngine` consent levels
- No datasheet stores raw user content (privacy-by-design)
- All schemas version-locked to GRID major version (currently 2.8.0)
- `ModelType.REINFORCEMENT` in `FrontierIntelligenceSystem` is the shared registry for all trained policies

## Implementation Readiness

| Datasheet | Existing Infrastructure | Missing |
|-----------|------------------------|---------|
| DS-1 (Agentic) | RuntimeBehaviorTracer, LearningCoordinator, GridEnvironment | Formal replay buffer, policy network, training loop |
| DS-2 (KG) | structural_learning, graph_compiler, NetworkX graphs | GNN policy encoder, evaluation query benchmark set |
| DS-3 (Governance) | governance_gates verdicts, probe scanner | Adversarial request generator, ground-truth labeling pipeline |
| DS-4 (RAG) | Full RAG pipeline, provider router, reranker | Query relevance annotation pipeline, cost tracking per-query |
| DS-5 (Safety) | GUARDIAN engine, PII privacy, threat profiler, transition gate | Red-team corpus management, constrained MDP framework |
| DS-6 (Diagnostics) | maintain-server full_diagnostic + report_history, seeds-server ecosystem_scan + ecosystem_trend, ori-server threat_coverage_heatmap, echoes-server audit_stats + precedents, nuke dep-check knob | `dep_audit` tool (Phase 1 of dep-audit pipeline), transition recorder (action → next_state logger), synthetic degradation generator, severity-weighted scoring |

**Common infrastructure needed across all 6**:
- Replay buffer (shared, partitioned by datasheet)
- Experiment tracker (exists: `FrontierIntelligenceSystem.experiment_tracker`)
- Feature store (exists: Redis-backed in `intelligence_system.py`)
- Training loop orchestration (missing: no formal training harness yet — `research/experiments/` is the natural home)
- Offline evaluation framework (missing: needed before any online deployment)

---

## Datasheet 6 of 6 — Ecosystem Diagnostics & Dependency Health

### 1. Motivation & Scope

| Field | Value |
|-------|-------|
| **Topic** | MCP Ecosystem Diagnostics & Dependency Vulnerability Management |
| **Source modules** | `maintain-server` (full_diagnostic, scan_workspaces, scan_temp, scan_git_repos, scan_system), `seeds-server` (ecosystem_scan, ecosystem_trend, repo_detail), `ori-server` (threat_coverage_heatmap, collect_logs, probe_test_suite, signal router), `echoes-server` (audit_stats, telemetry, precedents), `overview-server` (checkpoint) |
| **Gap addressed** | Diagnostic sweeps and dependency audits are currently manual one-shot commands. No feedback loop exists to learn which remediation action (update dep, run tests, clean caches, adjust ori timeout, fix config) yields the best health improvement per unit effort. The ecosystem is passively observed, never actively shaped. |
| **Downstream task** | Remediation policy optimization: learn to select the action sequence that maximizes ecosystem health score improvement per diagnostic cycle while minimizing disruption (broken builds, regression, downtime) |

### 2. Environment Specification

| Property | Definition |
|----------|------------|
| **State space** | `S = (maintain_health_score: R[0,100], seeds_avg_health: R[0,100], ram_used_pct: R[0,100], disk_free_pct: R[0,100], reclaimable_mb: R+, npm_vuln_counts: N^5 [info,low,mod,high,crit], pip_vuln_counts: N^5, ori_threat_coverage: R^6 [per TM-00x], ori_degraded_projects: N, echoes_failure_rate: R[0,1], echoes_blocked_count: N, active_precedent_count: N, stale_branch_count: N, uncommitted_change_count: N, lockfile_staleness_days: R^K [per active project])` — ~45 dimensions |
| **Action space** | `A = {npm_audit_fix(project): Categorical[K_npm], pip_update(project, pkg): Categorical[K_pip], run_tests(project): Categorical[K_projects], clean_temp(target): Categorical[5], clean_cache(type): Categorical[4], git_gc(repo): Categorical[K_repos], increase_ori_timeout(project): Continuous[60..600], resolve_precedent(id): Categorical[K_prec], snapshot_ecosystem: Binary, no_op: Binary}` — mixed, ~30 distinct action types after enumeration |
| **Transition** | Stochastic. `npm audit fix` may introduce breaking changes. `run_tests` outcome depends on code state. `clean_temp` is deterministic but reclaims vary. Dependency updates have cascading effects across lockfiles. |
| **Episode** | One episode = one diagnostic cycle (triggered by nuke `dep-sweep` macro or morning briefing). Variable horizon: 1-15 remediation actions per cycle. Termination: health score >= 95 across all axes, or max actions exhausted, or human abort. |
| **Reset** | Each diagnostic cycle starts from current ecosystem state (no rollback). Git stash provides partial reset capability for failed remediation attempts. |

### 3. Reward Signal Design

| Property | Definition |
|----------|------------|
| **Primary reward** | `r_t = w1 * Δhealth_score + w2 * Δvuln_reduction + w3 * Δcoverage_gap_closed + w4 * (1 - disruption_score)` |
| **Δhealth_score** | `(maintain_score_after - maintain_score_before) / 100` — normalized improvement from `full_diagnostic` |
| **Δvuln_reduction** | `(vulns_before - vulns_after) / max(vulns_before, 1)` — fraction of vulnerabilities eliminated |
| **Δcoverage_gap_closed** | `(degraded_before - degraded_after) / max(degraded_before, 1)` — fraction of ori threat coverage gaps resolved |
| **disruption_score** | `1.0` if action caused test failure or build break, `0.5` if action caused warning, `0.0` if clean |
| **Shaping terms** | `+0.2` for fixing direct (not transitive) dep vuln, `+0.1` for resolving an echoes precedent, `-0.3` for action that introduces a new vulnerability (regression), `-0.1` for no_op when vulns > 0 (penalize inaction on known issues), `+0.05` for snapshot after successful remediation (encourage longitudinal tracking) |
| **Reward range** | `[-1.3, 1.55]` per step |
| **Gamma** | `0.9` (remediation order matters — fixing a direct dep before its transitives cascades positively; but episodes are short enough that heavy discounting isn't needed) |
| **Reward hacking risks** | Agent could learn to only run `no_op` + `snapshot` to avoid disruption risk (zero improvement, low penalty). Mitigate: `-0.1` per no_op when vulns exist. Agent could clean caches repeatedly (easy reclaimable MB gains). Mitigate: diminishing returns — only first clean in episode earns full reward. Agent could `npm audit fix` recklessly across all projects. Mitigate: disruption_score penalty from downstream test failures. |

### 4. Data Composition

| Field | Type | Example |
|-------|------|---------|
| `cycle_id` | `str` | `"diag_20260412_001"` |
| `step` | `int` | `3` |
| `state` | `dict` | `{"maintain_score": 100, "seeds_avg": 96, "npm_vulns": {"high": 2, "critical": 0}, "ori_degraded": 1, ...}` |
| `action` | `dict` | `{"type": "npm_audit_fix", "project": "afloat"}` |
| `reward` | `float` | `0.65` |
| `next_state` | `dict` | `{"maintain_score": 100, "npm_vulns": {"high": 1, "critical": 0}, ...}` |
| `done` | `bool` | `false` |
| `info` | `dict` | `{"action_duration_ms": 4200, "disruption": 0.0, "vulns_fixed": ["GHSA-q4gf-8mx6-v5v3"], "test_result": "passed"}` |

- **Volume**: Target 500 episodes / 5K transitions for initial training (diagnostic cycles are infrequent — ~2-5 per day)
- **Splits**: 70/15/15 by cycle. Test set biased toward cycles with high vuln counts
- **Collection**: Offline from diagnostic report history (`maintain-server`), ecosystem snapshots (`seeds-server`), audit log (`echoes-server`), and dep-audit output (proposed Phase 1 tool)

### 5. Collection & Preprocessing

- **Source**: `maintain-server/full_diagnostic` + `seeds-server/ecosystem_scan` + `ori-server/get_threat_coverage_heatmap` + `echoes-server/query_audit` + proposed `maintain-server/dep_audit`
- **Sampling**: Every diagnostic cycle is recorded (full coverage — low volume, high value)
- **Filtering**: Exclude diagnostic cycles where human manually intervened mid-cycle (corrupts transition model). Remove cycles shorter than 2 steps (insufficient signal)
- **Temporal**: 90-day rolling window. Diagnostic report history already persisted by maintain-server (5 reports available as of 2026-04-12)
- **Feature engineering**: Derive `lockfile_staleness_days` from git log on lockfile paths. Derive `vuln_severity_weighted_score` as `info*0 + low*1 + moderate*3 + high*7 + critical*15` per project
- **Baseline snapshot (2026-04-12)**: maintain score 100, seeds avg 96, npm high vulns 2 (basic-ftp + next), pip moderate vulns 1 (uv), ori degraded 1 (grid-main on all 6 TM vectors), RAM 42%, disk 82% free, 18 MB reclaimable, 0 total issues from full_diagnostic

### 6. Recommended Uses & Limitations

- **Algorithms**: Contextual bandits (simpler formulation: one action per cycle), DQN (multi-step sequences), offline RL (CQL/IQL for cold start from diagnostic history)
- **Simpler entry point**: Multi-armed bandit over the 10 action types, with Thompson Sampling, before graduating to full MDP
- **Out-of-scope**: Not for learning code fixes (that's the developer's job). Not for learning lockfile formats (that's deterministic parsing). Not for automated git operations beyond `git gc` (merge, rebase, push are human-gated)
- **Biases**: Diagnostic data skews toward "healthy" states (maintain score = 100 in last 5 reports). Must inject synthetic degradation scenarios for training diversity. Vulnerability distribution is sparse and bursty (long periods of 0, then sudden advisory bursts)
- **Safety**: **Non-negotiable constraints**: (1) Never auto-run `npm audit fix --force` (major version bumps). (2) Never delete non-temp files. (3) Never modify `.git/` directly. (4) All remediation actions must be reversible or preview-first (dry-run). (5) Human override is absolute — agent cannot block manual intervention (TUV-001 NR-03). (6) `maintain-server/cleanup_execute` requires preview token + confirm phrase — RL agent cannot bypass two-step safety

### 7. Maintenance

- **Owner**: Cross-server — `maintain-server` (primary), `seeds-server` + `ori-server` + `echoes-server` (data providers), `dep-audit` pipeline (when implemented)
- **Update cadence**: Schema versioned with dep-audit pipeline phases. Data accumulates passively from daily diagnostic runs
- **Deprecation**: If diagnostic report format changes (maintain-server), or threat model IDs change (ori-server), datasheet must be re-validated
- **Dependencies on other datasheets**: Feeds into DS-3 (governance) via coverage gap signals. Consumes DS-5 (safety) constraints for remediation action gating

---

## Updated Cross-Datasheet Dependencies

```
                    ┌──────────────────────┐
                    │  DS-5: Safety        │
                    │  Boundary Enforce.   │
                    └──────────┬───────────┘
                               │ hard constraints
                    ┌──────────▼───────────┐
                    │  DS-3: Governance    │
                    │  Probe & Compliance  │◄──── probe coverage feeds
                    └──────────┬───────────┘      into governance state
                               │ access verdicts          ▲
              ┌────────────────┼────────────────┐         │
              ▼                ▼                 ▼         │ coverage gaps
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐ │
    │  DS-1: Agentic  │ │  DS-4: RAG   │ │  DS-2: KG    │ │
    │  Behavioral     │ │  Pipeline    │ │  Structural  │ │
    │  Intelligence   │ │  Optimization│ │  Learning    │ │
    └─────────────────┘ └──────────────┘ └──────────────┘ │
         │                     │                │          │
         └─────────────────────┼────────────────┘          │
                               │                           │
                         shared: skill success             │
                         rates, query quality,             │
                         entity linking accuracy            │
                               │                           │
                    ┌──────────▼───────────┐               │
                    │  DS-6: Ecosystem     │───────────────┘
                    │  Diagnostics &       │
                    │  Dependency Health   │
                    └──────────────────────┘
                      consumes: maintain, seeds,
                      ori, echoes, dep-audit
                      feeds: coverage gap closure
                      signals back to DS-3
```
