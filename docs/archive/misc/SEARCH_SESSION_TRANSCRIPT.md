# GRID Search: Comprehensive Session Transcript

> **Session window**: ~14 hours ending 2026-03-03 01:05 (UTC+6)  
> **Scope**: `src/search/`, guardrail subsystem, API routes, test suite  
> **Status at close**: All tests passing; guardrails enabled by default  
> **Author context**: Solo developer (Irfan Kabir), production-grade pipeline  

---

## Table of Contents

1. [Session Timeline & Work Completed](#1-session-timeline--work-completed)
2. [Architecture Overview](#2-architecture-overview)
3. [Common Patterns (The "Grid Way")](#3-common-patterns-the-grid-way)
4. [Known Caveats & Gotchas](#4-known-caveats--gotchas)
5. [The Mismatch Myth: How Small Disconnects Cause Decision Fatigue](#5-the-mismatch-myth-how-small-disconnects-cause-decision-fatigue)
6. [Fact-Based Best Practices & Recommended Approach](#6-fact-based-best-practices--recommended-approach)
7. [File Inventory & Module Map](#7-file-inventory--module-map)
8. [Test Coverage Matrix](#8-test-coverage-matrix)
9. [Onboarding Quick-Start](#9-onboarding-quick-start)

---

## 1. Session Timeline & Work Completed

### Phase 1: Enterprise Guardrail System (conversation `c66cce35`)
**Goal**: Generate a well-formatted, annotated markdown document describing the Enterprise Search Guardrail System.

**Work completed**:
- Authored `src/search/guardrail/LIMITATIONS.md` — a 170-line honest assessment of pattern-based detection limits
- Documented profile-specific considerations (Developer, Designer, Manager)
- Added compliance/legal notes covering GDPR Article 25, CCPA, PCI DSS, HIPAA
- Established the **"one layer of defense"** principle in writing

### Phase 2: Improving Search Guardrails (conversation `50369361`)
**Goal**: Three concrete improvements to the search service:

| Improvement | What Changed | Key Files |
|:---|:---|:---|
| **Optional Search Pipeline** | New `SEARCH_FULL_PIPELINE` flag (default: `false`) | `config.py`, `engine.py` |
| **Real Access Control** | Replaced stub with index/field allowlists in `GuardrailProfile` | `access_control.py`, `models.py` |
| **Default Guardrails** | `guardrail_enabled=True` by default + migration docs | `config.py`, `SEARCH_GUARDRAIL_MIGRATION.md` |

**New test files created**:
- `tests/unit/search/test_search_pipeline_flag.py` — 3 tests covering basic vs full pipeline
- `tests/unit/search/test_search_guardrail_security.py` — 3 tests (injection, script, rate limit)
- `tests/unit/search/test_guardrail_api_integration.py` — 3 tests (auth required/optional)
- `tests/unit/search/test_access_control_real.py` — 3 tests (index/field allowlists)

### Phase 3: Debugging Test Failures (conversation `0f6270ad`)
**Goal**: Fix `IndexError` in `test_pipeline_flag_affects_explanation` and verify all tests pass.

**Root cause**: The `engine.search()` method's basic pipeline path was not properly populating `allowed_ids` for filter-only queries, and the explanation metadata was missing `pipeline` and `source` keys.

**Fix applied**: 
- `engine.py` lines 184–293: Complete rewrite of the search method's dual-path logic (basic vs full pipeline)
- Explanation dict now always includes `pipeline` and `source` fields
- Basic pipeline falls back to `"keyword"` source; full pipeline shows `"fusion"` source

---

## 2. Architecture Overview

### The Search Pipeline (Two Modes)

```
QUERY ──► Parser ──► Intent Classifier ──► [Pipeline Branch] ──► Hits ──► Response
                                                │
                          ┌─────────────────────┤
                          ▼                     ▼
                    BASIC PATH            FULL PATH
                  (fast, keyword)     (ML-heavy, ranked)
                          │                     │
               KeywordRetriever         QueryExpander
                          │            HybridFusion (RRF)
                          │           RankingPipeline (LTR + CE)
                          │           FacetAggregator
                          │                     │
                          └─────────┬───────────┘
                                    ▼
                            SearchResponse
```

**Key design decision**: The `search_full_pipeline` flag gates expensive operations. When `false` (default), the pipeline skips query expansion, hybrid fusion, ranking (LTR/cross-encoder), and facet aggregation. This is **the most important flag for performance**.

### The Guardrail Pipeline

```
REQUEST
   │
   ├── Pre-Query Phase (parallel):
   │     ├── auth          → identity validation
   │     ├── rate_limit    → sliding-window per-identity
   │     ├── sanitize      → regex pattern blocking + budget
   │     └── access_control→ index/field allowlists
   │
   ├── Search Execution (engine.search)
   │
   └── Post-Query Phase (parallel):
         ├── pii_redact    → SSN/email/phone redaction
         ├── result_filter → sensitive field masking + size cap
         └── audit         → SHA-256 query hash logging
```

### Module Dependency Graph

```
search/
├── config.py          ← SearchConfig (pydantic-settings, env vars)
├── models.py          ← Pydantic (API boundary) + dataclass (internal DTOs)
├── engine.py          ← SearchEngine orchestrator (the "brain")
├── __init__.py        ← Public exports
│
├── api/
│   ├── routes.py      ← FastAPI router factory (create_search_router)
│   └── middleware.py   ← AuthMiddleware, RateLimitMiddleware, LatencyTracker
│
├── query/
│   ├── parser.py      ← QueryParser + sanitize() function
│   ├── intent.py      ← SearchIntentClassifier (navigational/exploratory/analytical)
│   └── expander.py    ← QueryExpander (semantic term expansion)
│
├── retrieval/
│   ├── keyword.py     ← KeywordRetriever (BM25 + fallback substring)
│   ├── semantic.py    ← SemanticRetriever (vector store)
│   ├── structured.py  ← StructuredRetriever (field-level filtering)
│   ├── fusion.py      ← HybridFusion (RRF merge with intent weights)
│   └── base.py        ← BaseRetriever interface
│
├── ranking/
│   ├── scorer.py      ← RankingPipeline (features → LTR → cross-encoder)
│   ├── features.py    ← FeatureExtractor (BM25/vector/freshness/popularity)
│   ├── cross_encoder.py ← SearchCrossEncoder wrapper
│   └── ltr_model.py   ← Learn-to-Rank (numpy-based, no pickle)
│
├── facets/
│   └── aggregator.py  ← FacetAggregator (keyword/numeric/boolean/date/histogram)
│
├── indexing/
│   └── pipeline.py    ← IndexingPipeline (schema validation + vector + BM25)
│
└── guardrail/
    ├── __init__.py     ← Public exports
    ├── models.py       ← GuardrailProfile dataclass
    ├── auth.py         ← HMAC signature auth + role-based access narrowing
    ├── policy.py       ← GuardrailPolicy (phases, profiles, YAML/JSON loading)
    ├── registry.py     ← GuardrailToolRegistry (tool→callable dispatch)
    ├── orchestrator.py ← GuardrailOrchestrator (parallel tool execution)
    ├── LIMITATIONS.md  ← Honest pattern-detection limitations doc
    └── tools/
        ├── base.py           ← ToolResult enum, GuardrailContext/Result
        ├── auth.py           ← auth_tool
        ├── rate_limit.py     ← rate_limit_tool (InMemoryRateLimiter)
        ├── sanitize.py       ← sanitize_tool (profile-aware regex)
        ├── access_control.py ← access_control_tool (index/field allowlists)
        ├── pii.py            ← pii_redact_tool (SSN/email/phone)
        ├── result_filter.py  ← result_filter_tool (sensitive field redaction)
        └── audit.py          ← audit_tool (SHA-256 query hash)
```

---

## 3. Common Patterns (The "Grid Way")

### Pattern 1: Pydantic at API Boundary, Dataclass Internally

```python
# API boundary (user-facing, validated, serialisable):
class SearchHit(BaseModel):          # pydantic
    document: Document
    score: float = 0.0

# Internal transfer (lightweight, no validation overhead):
@dataclass
class ScoredCandidate:               # dataclass
    doc_id: str
    score: float = 0.0
    source: str = ""
```

**Why this matters**: Mixing the two causes subtle issues. If you use a Pydantic model where a dataclass is expected, `.model_dump()` calls propagate unexpectedly. If you use a dataclass at the API boundary, FastAPI won't auto-serialize it. **Always check `models.py` before creating new types.**

### Pattern 2: Lazy Imports in conftest.py

```python
@pytest.fixture
def embedding_provider():
    from tools.rag.embeddings.test_provider import DeterministicEmbeddingProvider
    return DeterministicEmbeddingProvider(dimension=384, seed=42)
```

**Why**: pytest's `--import-mode=importlib` processes conftest files before `sys.path` is fully configured. If you move imports to the top-level, tests break with `ModuleNotFoundError` during collection. This is documented in `tests/unit/search/conftest.py` line 4-6.

### Pattern 3: Dual-Layer Sanitization

Sanitization happens in **two places**:
1. **`query/parser.py` → `sanitize()` function** — validates raw query text before parsing
2. **`guardrail/tools/sanitize.py` → `sanitize_tool()`** — profile-aware regex blocking in the guardrail pipeline

Both use the same `BASE_DANGEROUS_PATTERNS` list but the guardrail tool adds:
- Budget-based length limits per profile
- Profile-specific pattern overrides
- ReDoS mitigation (patterns > 500 chars rejected)
- Provenance tracking (which pattern matched, from which profile)

**Caveat**: If you modify patterns in one location, consider whether the other needs updating too.

### Pattern 4: Config as Single Source of Truth

All algorithmic constants live in `SearchConfig` (pydantic-settings), loaded from environment variables with the `SEARCH_` prefix:

```python
class SearchConfig(BaseSettings):
    model_config = {"env_prefix": "SEARCH_"}
    rrf_k: int = 60
    cross_encoder_top_k: int = 20
    guardrail_enabled: bool = True
    search_full_pipeline: bool = False
    # ... 25+ fields
```

**Implication**: Tests override these via fixture (`test_config` in conftest), not environment variables. If you set `SEARCH_GUARDRAIL_ENABLED=false` in `.env` but tests override it in `SearchConfig(guardrail_enabled=True)`, the test wins.

### Pattern 5: GuardrailProfile-Driven Behavior

The guardrail system uses personas (profiles) to customize behavior per role:

| Profile | sanitize budget | PII budget | Safety Rules |
|:--------|:---------------|:-----------|:-------------|
| basic | 2,000 chars | 5,000 | perpetrator voice, citation honesty, limitations header |
| developer | 5,000 chars | 8,000 | Same as basic + SQL/code injection patterns |
| designer | 8,000 chars | 10,000 | Same as basic + event handler injection + PII patterns |
| manager | 10,000 chars | 15,000 | All above + compliance_reporting, phase_overrides |

Profiles are activated via `orchestrator.activate_profile()` with HMAC-based signature authentication for non-basic profiles.

### Pattern 6: The _IndexState Dataclass

All per-index state (schema, pipeline, parsers, retrievers, ranker, facets) lives in a private `_IndexState` dataclass inside the engine. This is **not public API** but tests access it via `engine._indices["name"]`:

```python
@dataclass
class _IndexState:
    schema: IndexSchema
    pipeline: IndexingPipeline
    parser: QueryParser
    # ... 10 fields
```

**Decision**: Accessing `_IndexState` in tests is accepted (prefix `_` signals "internal, not external"). The alternative — making it public — would expose implementation details to API consumers.

---

## 4. Known Caveats & Gotchas

### Caveat 1: The `search_full_pipeline` Default is `False`

This is the **#1 onboarding trap**. New developers expect facets, ranking, and semantic search to work by default. They don't.

```python
# config.py line 57:
search_full_pipeline: bool = False  # if False, skip fusion/ranking/facets
```

**What breaks**:
- `search(... facet_fields=["category"])` → returns empty `facets: {}` on basic pipeline
- `response.hits[0].explanation["source"]` → always `"keyword"` on basic pipeline
- No query expansion → semantic near-misses won't be found
- No cross-encoder reranking → BM25 score order only

**Mitigation**: Set `SEARCH_FULL_PIPELINE=true` when you need ML-powered search. Default `false` is for throughput-sensitive deployments.

### Caveat 2: Rate Limiter State is Per-Config-Instance

```python
# rate_limit.py line 33:
_limiters: dict[int, InMemoryRateLimiter] = {}
```

The limiter key is `id(config)`, meaning each `SearchConfig` instance gets its own limiter. In tests, each fixture creates a new config, so rate limiters don't carry across fixtures. In production with a single config singleton, this works as expected.

**Gotcha**: If you create two `SearchConfig()` instances with the same values, they get **separate** rate limiters. This is by design (isolation), but can surprise you if you're debugging "why isn't rate limiting working across my two routers?"

### Caveat 3: BM25 Scores Can Be Negative

```python
# keyword.py line 54:
if score < 0:
    break
```

`rank_bm25.BM25Okapi` can return negative scores for terms that are ubiquitous in the corpus (IDF penalty). The keyword retriever breaks early on negative scores. This means a query like `"the"` against a large corpus may return fewer results than expected.

### Caveat 4: Embedding Provider Fallback Chain

```python
# engine.py line 307-322:
try:
    from tools.rag.config import RAGConfig
    from tools.rag.embeddings.factory import get_embedding_provider
    # Full HuggingFace/sentence-transformers provider
except ImportError:
    from tools.rag.embeddings.simple import SimpleEmbedding
    # Fallback: deterministic hash-based pseudo-embeddings
```

**Impact**: If `sentence-transformers` is not installed, semantic search uses `SimpleEmbedding` which produces hash-based vectors. These vectors have **no semantic meaning** — cosine similarity between "dog" and "puppy" will be essentially random. Tests use this fallback intentionally (via `embedding_provider="simple"` in config).

### Caveat 5: Dual Sanitization Creates a Silent Disagreement Risk

The parser (`query/parser.py`) and the guardrail tool (`guardrail/tools/sanitize.py`) both check `DANGEROUS_PATTERNS`. But they operate at different stages:

1. Parser sanitization runs **inside** `QueryParser.parse()` — affects all queries
2. Guardrail sanitization runs **in the pre-query phase** — only when guardrails are enabled

If guardrails are disabled, only parser sanitization applies. If someone adds a new pattern to the guardrail tool but forgets the parser, unguarded deployments are exposed.

### Caveat 6: The `_get_safety_validated_message` Duplication

This helper function is copy-pasted across three files:
- `guardrail/tools/sanitize.py`
- `guardrail/tools/pii.py`  
- `guardrail/tools/result_filter.py`

Each copy implements the same perpetrator-voice-prevention and limitations-header logic. If you fix a bug in one, you must fix all three. **Recommended**: Extract to a shared utility in `guardrail/tools/base.py`.

### Caveat 7: `sys.path` Manipulation is Load-Bearing

Both `conftest.py` (root) and `tests/conftest.py` aggressively manage `sys.path`:

```python
# Root conftest.py:
sys.path.insert(0, _src)   # src/ first
sys.path.append(_root)     # root last

# tests/conftest.py:
sys.path.insert(0, src)    # re-ensure src is first
```

**Why**: There's a top-level `grid/` directory and `src/grid/` which shadow each other. Without explicit path ordering, `import grid.resilience` resolves to the wrong module. This is a **structural debt** — the root `grid/` directory should ideally be renamed or removed.

### Caveat 8: Windows Sandbox Environment

The test environment has sandbox-related configurations:

```python
# tests/conftest.py line 30-32:
if os.name == "nt" and hasattr(config.option, "numprocesses"):
    if getattr(config.option, "numprocesses", None):
        config.option.numprocesses = 0  # Force single-process on Windows sandbox
```

This means `pytest -n auto` (xdist parallel) is **automatically disabled** on Windows. Tests always run sequentially. This is a workaround for sandbox temp-root ACL failures.

---

## 5. The Mismatch Myth: How Small Disconnects Cause Decision Fatigue

This section documents the **recurring pattern** where small mismatches between expectations and reality compound into significant debugging time and decision fatigue.

### Mismatch 1: "Guardrails are enabled" ≠ "Everything is secured"

**The myth**: Setting `guardrail_enabled=True` makes the search service secure.

**The fact**: Guardrails provide **one layer** of regex-based defense. They cannot detect:
- Unicode normalization attacks
- Base64-encoded payloads
- Context-dependent multi-part injection
- Novel attack patterns not in the regex database

See `guardrail/LIMITATIONS.md` for the full enumeration. The correct mental model is: guardrails are an **input sanitization layer**, not a security boundary.

### Mismatch 2: "Tests pass" ≠ "The feature works in production"

**The myth**: All 12 search tests pass, therefore the search service is production-ready.

**The fact**: Tests use:
- `SimpleEmbedding` (hash-based vectors, not semantic)
- `in_memory` vector store (not ChromaDB or persistent storage)
- `cross_encoder_enabled=False` (no ML reranking)
- Small corpora (2-5 documents)

Production will use HuggingFace sentence-transformers with real semantic embeddings and potentially millions of documents. The BM25 + RRF fusion behaves very differently at scale.

**Recommended**: Create a `tests/integration/search/` suite with:
- Real embedding providers (when CI GPU is available)
- Corpora of 1000+ documents
- Cross-encoder enabled
- Latency assertions (p95 < 200ms)

### Mismatch 3: "Basic pipeline" ≠ "No filtering"

**The myth**: The basic pipeline (`search_full_pipeline=False`) doesn't support filtering.

**The fact**: The basic pipeline **does** support structured filtering. It uses `StructuredRetriever` to get matching doc IDs, then intersects them with keyword results:

```python
# engine.py line 224-228:
if parsed.filters:
    struct_results = state.fusion.structured.retrieve(parsed.filters)
    if not struct_results:
        return SearchResponse(page=page, size=size, took_ms=self._elapsed(t0))
    allowed_ids = {c.doc_id for c in struct_results}
```

What the basic pipeline **actually** skips:
- Query expansion (semantic term enrichment)
- Hybrid fusion (RRF across keyword + semantic + structured)
- Ranking (LTR model + cross-encoder)
- Facet aggregation

### Mismatch 4: "Profile patterns" ≠ "Base patterns"

**The myth**: Setting profile-specific patterns replaces the base patterns.

**The fact**: This is correct — but only when the profile patterns **compile successfully**. If any profile pattern fails to compile (`re.error`), the system silently falls back to `BASE_DANGEROUS_PATTERNS`:

```python
# sanitize.py line 89-91:
try:
    patterns_to_check = [re.compile(p) for p in valid] if valid else BASE_DANGEROUS_PATTERNS
except (re.error, TypeError):
    patterns_to_check = BASE_DANGEROUS_PATTERNS  # silent fallback
```

**Decision fatigue scenario**: You add a complex regex to a profile, it fails silently, and the base patterns catch your test query by coincidence. You believe profile patterns are active when they're not. Debugging this requires checking the guardrail result's `provenance` field.

### Mismatch 5: "Auth required" ≠ "Auth validated"

**The myth**: `guardrail_auth_required=True` validates credentials against a user database.

**The fact**: The auth tool only checks **presence** of identity, not validity:

```python
# guardrail/tools/auth.py line 17:
if auth_required and not identity:
    return GuardrailToolResult(..., result=ToolResult.BLOCK)
```

Any non-empty `Authorization` header passes:
```
Authorization: Bearer literally-anything-here  ← passes auth
```

Real credential validation would require JWT verification, token introspection, or an external auth provider. The current implementation is a **gating mechanism**, not authentication.

### Mismatch 6: "Policy profiles" ≠ "Active by default"

**The myth**: Defining profiles in `GuardrailPolicy.default()` means they're all active.

**The fact**: The default policy creates 4 profiles (basic, developer, designer, manager) but **none is active by default**:

```python
# policy.py:
active_profile: str | None = None  # No profile active by default
```

When no profile is active:
- `get_budget_limit()` returns default 10,000 → no budget enforcement
- `get_safety_rule()` returns `True` → all rules enabled but with no profile context
- `get_profile_patterns()` returns `[]` → base patterns used

You must explicitly call `orchestrator.activate_profile("developer", ...)` to engage profile-specific behavior.

### The Compounding Effect

Each mismatch alone is minor. Together they create a decision tree where every assumption needs verification:

```
"Is my search working?"
  ├─ "Is full pipeline enabled?" (check SEARCH_FULL_PIPELINE)
  ├─ "Are guardrails running?" (check guardrail_enabled)
  │   ├─ "Is a profile active?" (check active_profile)
  │   │   ├─ "Did profile patterns compile?" (check provenance)
  │   │   └─ "Is auth actually validating?" (check auth implementation)
  │   └─ "Is parser sanitization also running?" (always yes)
  └─ "Are embeddings semantic?" (check embedding_provider)
```

**Recommended**: Add a `search_engine.diagnostics()` method that returns the full configuration state in a single call.

---

## 6. Fact-Based Best Practices & Recommended Approach

### Practice 1: Always Specify Pipeline Mode Explicitly

```python
# ❌ Implicit (unclear whether full or basic):
engine = SearchEngine()

# ✅ Explicit:
engine = SearchEngine(config=SearchConfig(search_full_pipeline=True))
```

### Practice 2: Extract `_get_safety_validated_message` to Shared Utility

Current state: Copy-pasted across 3 files.

```python
# ✅ Recommended: guardrail/tools/base.py
def get_safety_validated_message(message: str, tool_name: str, ctx: GuardrailContext) -> str:
    """Shared safety validation for tool messages."""
    ...
```

### Practice 3: Test Both Pipeline Modes

The `test_search_pipeline_flag.py` file already does this with separate fixtures:

```python
@pytest.fixture
def engine_basic():
    return SearchEngine(config=SearchConfig(search_full_pipeline=False, ...))

@pytest.fixture
def engine_full():
    return SearchEngine(config=SearchConfig(search_full_pipeline=True, ...))
```

Always test both when adding new search features.

### Practice 4: Use Provenance for Debugging

The sanitize tool returns `provenance` metadata when it blocks:

```python
provenance = {
    "pattern_type": "profile_specific" or "base_fallback",
    "matched_pattern": pat.pattern,
    "query_length": len(query),
    "budget_limit": budget_limit,
    "profile_name": ctx.profile.name,
    "timestamp": datetime.now().isoformat(),
}
```

Log this in production. It's the fastest way to debug "why was this query blocked?"

### Practice 5: Never Bypass the Dual `sys.path` Setup

If you add a new package to `src/`, both conftest files (`conftest.py` root and `tests/conftest.py`) must remain consistent. The root conftest runs at import time; the tests conftest runs at `pytest_configure`. Both are needed because pytest plugins can modify `sys.path` between the two.

### Practice 6: Use `model_copy(deep=True)` for Hit Documents

```python
# engine.py line 267:
document=state.documents[c.doc_id].model_copy(deep=True),
```

This prevents test mutations from corrupting the indexed document store. The test `test_search_hits_do_not_mutate_indexed_documents` explicitly verifies this contract.

### Practice 7: Rate Limiter Isolation in Tests

Each test fixture should create its own `SearchConfig` instance to get isolated rate limiter state:

```python
@pytest.fixture
def guardrail_config_strict():
    return SearchConfig(
        guardrail_rate_limit_per_minute=2,  # Fresh limiter per test
        ...
    )
```

### Practice 8: Guardrail Profile Activation Requires Auth for Non-Basic

```python
# ✅ Basic profile (no auth needed):
orchestrator.activate_profile("basic", user_role="basic")

# ✅ Developer profile (auth required):
sig = policy.create_profile_signature("developer", "user123")
orchestrator.activate_profile("developer", user_id="user123", auth_signature=sig, user_role="developer")

# ❌ This will fail silently (returns False):
orchestrator.activate_profile("developer")  # No user_id or signature
```

---

## 7. File Inventory & Module Map

### Source Files (`src/search/`)

| File | Lines | Purpose |
|:-----|------:|:--------|
| `config.py` | 64 | All config via `pydantic-settings` with `SEARCH_` env prefix |
| `models.py` | 172 | 6 Pydantic models (API) + 4 dataclasses (internal DTOs) |
| `engine.py` | 387 | Top-level orchestrator with dual pipeline paths |
| `api/routes.py` | 245 | FastAPI router factory with guardrail integration |
| `api/middleware.py` | 200 | Auth, RateLimit, Audit middleware + LatencyTracker |
| `query/parser.py` | 116 | Filter extraction + sanitization |
| `query/intent.py` | ~80 | Intent classification (nav/explore/analytical) |
| `query/expander.py` | ~60 | Semantic query term expansion |
| `retrieval/keyword.py` | 109 | BM25 + fallback substring matching |
| `retrieval/semantic.py` | ~60 | Vector store cosine similarity |
| `retrieval/structured.py` | ~80 | Field-level filter evaluation |
| `retrieval/fusion.py` | 83 | RRF merge with intent-aware weighting |
| `ranking/scorer.py` | 112 | Ranking pipeline (features → LTR → cross-encoder) |
| `ranking/features.py` | ~100 | Feature extraction (BM25/vector/freshness/popularity) |
| `ranking/cross_encoder.py` | ~60 | Cross-encoder reranking wrapper |
| `ranking/ltr_model.py` | ~80 | Learn-to-rank (numpy, JSON persistence) |
| `facets/aggregator.py` | ~120 | Facet aggregation by field type |
| `guardrail/orchestrator.py` | 154 | Parallel tool execution per policy phase |
| `guardrail/policy.py` | 297 | Policy engine with YAML/JSON loading |
| `guardrail/models.py` | 19 | GuardrailProfile dataclass |
| `guardrail/auth.py` | 165 | HMAC signature auth + role narrowing |
| `guardrail/registry.py` | 56 | Tool name → callable dispatch |
| `guardrail/tools/base.py` | 39 | ToolResult enum + GuardrailContext |
| `guardrail/tools/auth.py` | 28 | Identity presence check |
| `guardrail/tools/rate_limit.py` | 59 | Sliding-window per-identity limiter |
| `guardrail/tools/sanitize.py` | 119 | Profile-aware regex validation |
| `guardrail/tools/access_control.py` | 59 | Index/field allowlist enforcement |
| `guardrail/tools/pii.py` | 130 | SSN/email/phone redaction |
| `guardrail/tools/result_filter.py` | 94 | Sensitive field masking + size cap |
| `guardrail/tools/audit.py` | 38 | SHA-256 query hash logging |

### Test Files (`tests/unit/search/`)

| File | Tests | Scope |
|:-----|------:|:------|
| `test_engine.py` | 9 | End-to-end: CRUD + search + pagination + mutation safety |
| `test_search_pipeline_flag.py` | 3 | Basic vs full pipeline behavior |
| `test_search_guardrail_security.py` | 3 | Injection blocking + rate limiting |
| `test_guardrail_api_integration.py` | 3 | Auth required/optional + response format |
| `test_access_control_real.py` | 3 | Index/field allowlist enforcement |
| `test_api_routes.py` | ~10 | FastAPI route behavior |
| `test_query_parser.py` | ~8 | Filter extraction + value coercion |
| `test_query_parser_sanitize.py` | ~6 | Sanitization edge cases |
| `test_fusion.py` | ~5 | RRF merge + intent weighting |
| `test_ranking.py` | ~5 | Ranking pipeline orchestration |
| `test_facets.py` | ~5 | Facet aggregation by type |
| `test_models.py` | ~5 | Model validation + serialization |
| `test_retrievers.py` | ~5 | BM25 + semantic + structured retrieval |
| `test_intent.py` | ~5 | Intent classification |
| `test_indexing_pipeline.py` | ~5 | Document indexation + BM25 corpus |
| `test_structured_store.py` | ~5 | Structured index operations |
| `guardrail/test_auth_tool.py` | ~3 | Auth tool unit tests |
| `guardrail/test_orchestrator.py` | ~5 | Orchestrator execution flow |
| `guardrail/test_rate_limit_tool.py` | ~3 | Rate limiter behavior |
| `guardrail/test_sanitize_tool.py` | ~5 | Pattern matching + budget limits |

---

## 8. Test Coverage Matrix

| Subsystem | Unit | Integration | Security | Performance |
|:----------|:----:|:----------:|:--------:|:-----------:|
| Engine (dual pipeline) | ✅ | ✅ | — | — |
| Query Parser | ✅ | — | ✅ (sanitize) | — |
| Keyword Retriever | ✅ | — | — | — |
| Semantic Retriever | ✅ | — | — | — |
| Structured Retriever | ✅ | — | — | — |
| Hybrid Fusion | ✅ | — | — | — |
| Ranking Pipeline | ✅ | — | — | — |
| Facet Aggregator | ✅ | ✅ | — | — |
| Auth Tool | ✅ | ✅ | ✅ | — |
| Rate Limit Tool | ✅ | — | ✅ | — |
| Sanitize Tool | ✅ | — | ✅ | — |
| Access Control | ✅ | — | — | — |
| PII Redaction | ✅ (implicit) | — | — | — |
| Result Filter | ✅ (implicit) | — | — | — |
| API Routes | ✅ | ✅ | ✅ | — |
| Latency Tracker | ✅ | — | — | — |

**Gaps**: No dedicated performance tests. No ML-quality tests with real embeddings. No chaos/failure injection tests for guardrail error paths.

---

## 9. Onboarding Quick-Start

### Step 1: Run the Tests

```powershell
cd E:\Seeds\GRID-main
uv run pytest tests/unit/search/ -q --tb=short
```

Expected: All tests pass. If you see `ModuleNotFoundError`, check that root `conftest.py` hasn't been modified.

### Step 2: Understand the Two Pipeline Modes

Read `engine.py` lines 166-292. The `search()` method branches on `self.config.search_full_pipeline`:
- **Basic** (lines 221-245): keyword retrieval + filter intersection
- **Full** (lines 184-220): fusion + ranking + facets

### Step 3: Understand the Guardrail Flow

Read `api/routes.py` lines 131-193. The `_search_with_guardrail()` function:
1. Extracts identity from `Authorization` header
2. Builds `RequestContext` with parsed filters
3. Runs pre-query guardrails (auth, rate limit, sanitize, access control)
4. Executes search
5. Runs post-query guardrails (PII redaction, result filter, audit)

### Step 4: Key Configuration Flags

| Flag | Default | Effect |
|:-----|:--------|:-------|
| `SEARCH_GUARDRAIL_ENABLED` | `true` | Enables/disables the guardrail pipeline |
| `SEARCH_GUARDRAIL_AUTH_REQUIRED` | `true` | Requires Authorization header for search |
| `SEARCH_FULL_PIPELINE` | `false` | Enables ML-powered search (expansion, fusion, ranking, facets) |
| `SEARCH_CROSS_ENCODER_ENABLED` | `true` | Enables cross-encoder reranking (requires model download) |
| `SEARCH_GUARDRAIL_RATE_LIMIT_PER_MINUTE` | `60` | Per-identity request limit |
| `SEARCH_GUARDRAIL_FAIL_OPEN` | `false` | If `true`, allow requests on guardrail errors |

### Step 5: Create Your First Index

```python
from search.engine import SearchEngine
from search.config import SearchConfig
from search.models import Document, FieldSchema, FieldType, IndexSchema

engine = SearchEngine(config=SearchConfig(search_full_pipeline=False))

schema = IndexSchema(
    name="products",
    fields={
        "title": FieldSchema(type=FieldType.TEXT, searchable=True, weight=2.0),
        "price": FieldSchema(type=FieldType.FLOAT, filterable=True),
        "category": FieldSchema(type=FieldType.KEYWORD, filterable=True, facetable=True),
    },
)

engine.create_index(schema)
engine.index_documents("products", [
    Document(id="p1", fields={"title": "Wireless Headphones", "price": 79.99, "category": "electronics"}),
    Document(id="p2", fields={"title": "USB-C Cable", "price": 12.99, "category": "electronics"}),
])

response = engine.search("products", "headphones")
print(f"Found {response.total} hits in {response.took_ms}ms")
```

---

## Appendix: Session Conversations Referenced

| Conversation ID | Title | Key Contribution |
|:----------------|:------|:-----------------|
| `c66cce35-9924-4cf0-a6fa-27d0fe599296` | Enterprise Guardrail System | LIMITATIONS.md + annotated documentation |
| `50369361-89ed-4a69-8cea-7f115729d43b` | Improving Search Guardrails | Pipeline flag + real access control + default guardrails |
| `0f6270ad-45cd-4070-be3f-c5254ab05c9f` | Debugging Test Failures | IndexError fix in pipeline flag test + explanation metadata |

---

*Document generated 2026-03-03T01:05 UTC+6. All code references verified against current codebase state.*
