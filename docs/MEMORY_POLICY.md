# GRID Memory Policy

> Single source of truth for memory management: TTLs, bounds, eviction rules, and three-tier architecture.

---

## 1. Three-Tier Memory Architecture

GRID follows the human-brain model for memory management:

| Tier | Purpose | Location | Retention | Eviction |
|------|---------|----------|-----------|----------|
| **Working** | Current context window + retrieval | Resonance API, RAG pipeline | Request-scoped | Token/chunk cap enforced |
| **Episodic** | Recent events and interactions | Vector store (events namespace) | Time-based (hours–days) | TTL + LRU when full |
| **Semantic** | Long-term facts and preferences | RAG index, ChromaDB | Long-lived | Manual or policy-based |

### 1.1 Working Memory

**Definition**: The active context window used by the LLM for a single request.

**Location**:
- `src/application/resonance/` — resonance service builds the prompt
- `src/tools/rag/` — retrieval pipeline provides context chunks

**Current Cap**:
- `conversation_context_window: int = 1000` (tokens, RAG config)
- `top_k: int = 10` (max chunks retrieved)

**Env variables**:
- `RAG_CONVERSATION_CONTEXT_WINDOW`
- `RAG_TOP_K`

### 1.2 Episodic Memory

**Definition**: Time-bounded records of recent interactions, events, and session context.

**Location**:
- `src/vection/core/stream_context.py` — session and thread state
- `src/mycelium/core.py` — Spore dataclass for transient data

**Current Implementation**:
- Sessions and threads with TTL
- Thread anchors with staleness tracking

### 1.3 Semantic Memory

**Definition**: Long-lived facts, preferences, and knowledge indexed for retrieval.

**Location**:
- `src/tools/rag/` — ChromaDB vector store
- `knowledge_base/` — source documents

**Current Implementation**:
- Persistent vector index (`grid_knowledge_base` collection)
- Document and chunk tables with retention metadata

---

## 2. TTLs (Time-to-Live)

| Component | TTL | Default | Env Variable | Location |
|-----------|-----|---------|--------------|----------|
| **Session** | 24 hours | `24.0` | — | `StreamContext._session_ttl_seconds` |
| **Thread** | 4 hours | `4.0` | — | `StreamContext._thread_ttl_seconds` |
| **RAG Cache** | 1 hour | `3600` | `RAG_CACHE_TTL` | `RAGConfig.cache_ttl` |
| **Spore** | Optional | `None` | — | `Spore.ttl` (per-instance) |
| **DRT Retention** | Configurable | Per-table | — | DRT migrations (`retention_hours`) |
| **Mothership Rate-Limit** | Per-key | — | — | Rate-limit middleware |

### 2.1 Session TTL

```python
# src/vection/core/stream_context.py
session_ttl_hours: float = 24.0  # Default: 24 hours
```

Sessions older than `session_ttl_hours` are dissolved during cleanup.

### 2.2 Thread TTL

```python
# src/vection/core/stream_context.py
thread_ttl_hours: float = 4.0  # Default: 4 hours
```

Threads idle longer than `thread_ttl_hours` are dissolved during cleanup.

### 2.3 RAG Cache TTL

```python
# src/tools/rag/config.py
cache_ttl: int = 3600  # Default: 1 hour (seconds)
```

Cache entries older than `cache_ttl` are considered stale.

---

## 3. Max Sizes and Bounds

| Component | Max Size | Default | Env Variable | Location |
|-----------|----------|---------|--------------|----------|
| **Sessions** | 1000 concurrent | `1000` | — | `StreamContext._max_sessions` |
| **Threads/Session** | 50 per session | `50` | — | `StreamContext._max_threads_per_session` |
| **RAG Cache** | 100 entries | `100` | `RAG_CACHE_SIZE` | `RAGConfig.cache_size` |
| **Conversation Memory** | 10 turns | `10` | `RAG_CONVERSATION_MEMORY_SIZE` | `RAGConfig.conversation_memory_size` |
| **Top-K Retrieval** | 10 chunks | `10` | `RAG_TOP_K` | `RAGConfig.top_k` |
| **Chunk Size** | 1000 chars | `1000` | `RAG_CHUNK_SIZE` | `RAGConfig.chunk_size` |
| **Embedding Batch** | 20 documents | `20` | `RAG_EMBEDDING_BATCH_SIZE` | `RAGConfig.embedding_batch_size` |
| **Concurrent Embeddings** | 4 parallel | `4` | `RAG_MAX_CONCURRENT_EMBEDDINGS` | `RAGConfig.max_concurrent_embeddings` |
| **Reranker Candidates** | 20 max | `20` | `RAG_RERANKER_TOP_K` | `RAGConfig.reranker_top_k` |
| **Multi-hop Depth** | 2 levels | `2` | `RAG_MULTI_HOP_MAX_DEPTH` | `RAGConfig.multi_hop_max_depth` |

### 3.1 Session Bounds

```python
# src/vection/core/stream_context.py
max_sessions: int = 1000
max_threads_per_session: int = 50
```

When `max_sessions` is reached, oldest session is evicted.

### 3.2 RAG Bounds

```python
# src/tools/rag/config.py
cache_size: int = 100
conversation_memory_size: int = 10
top_k: int = 10
chunk_size: int = 1000
chunk_overlap: int = 100
```

---

## 4. Eviction Rules

### 4.1 Session Eviction

**Trigger**: When `max_sessions` limit is reached.

**Policy**: Evict oldest session by `established_at` timestamp.

**Implementation**:
```python
# src/vection/core/stream_context.py
def _evict_oldest_session(self) -> None:
    oldest_id = min(
        self._sessions.keys(),
        key=lambda sid: self._sessions[sid].established_at,
    )
    self.dissolve_session(oldest_id)
```

### 4.2 Thread Eviction

**Trigger**: When `max_threads_per_session` limit is reached.

**Policy**: Evict oldest thread in session by `created_at` timestamp.

**Implementation**:
```python
# src/vection/core/stream_context.py
def _evict_oldest_thread(self, session_id: str) -> None:
    oldest_id = min(
        threads.keys(),
        key=lambda tid: threads[tid].created_at,
    )
    self.dissolve_thread(session_id, oldest_id)
```

### 4.3 TTL-Based Cleanup

**Trigger**: Periodic cleanup (every 5 minutes) or explicit call.

**Policy**: Dissolve sessions/threads exceeding TTL; prune expired shared signals.

**Implementation**:
```python
# src/vection/core/stream_context.py
async def cleanup(self) -> dict[str, int]:
    # Clean stale sessions (staleness > session_ttl)
    # Clean stale threads (idle_seconds > thread_ttl)
    # Prune expired shared signals
```

### 4.4 RAG Cache Eviction

**Trigger**: Cache lookup or explicit cleanup.

**Policy**: TTL-based expiration (`cache_ttl` seconds).

**Note**: No explicit LRU eviction currently implemented for RAG cache. Gap identified (M2).

### 4.5 Mothership Rate-Limit Eviction

**Trigger**: When `max_store_size` is exceeded.

**Policy**: Evict 10% oldest entries.

**Implementation**:
```python
# src/application/mothership/middleware/__init__.py
def _evict_if_needed(self):
    # Evict 10% when over max_store_size
```

### 4.6 Spore Eviction

**Current State**: TTL-based expiration only via `is_expired()`.

**Gap**: No global Spore store with LRU or max-size eviction (Gap M3).

**Future**: Implement `SporeStore` with:
- `max_entries`
- `evict_policy: "ttl_first" | "lru" | "priority"`
- Use `access_count` and `priority` for eviction order

---

## 5. Chunking Strategy

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `chunk_size` | 1000 chars | Maximum characters per chunk |
| `chunk_overlap` | 100 chars | Overlap between adjacent chunks |

**Location**: `src/tools/rag/config.py`, `src/tools/rag/indexing/semantic_chunker.py`

**Recommendation**: For enterprise use, consider:
- Token-based chunking (512 tokens, 10–20% overlap)
- Recursive splitting for structured documents

---

## 6. Observability

### 6.1 Available Metrics

| Metric | Location | Description |
|--------|----------|-------------|
| `active_sessions` | `StreamContext.get_stats()` | Current session count |
| `total_threads` | `StreamContext.get_stats()` | Total threads across sessions |
| `total_anchors` | `StreamContext.get_stats()` | Total anchors stored |
| `shared_signals` | `StreamContext.get_stats()` | Shared signal count |
| Cache stats | `SimpleCache.get_stats()` | Size, max_size, ttl_seconds |

### 6.2 Gaps (To Implement)

| Metric | Status | Priority |
|--------|--------|----------|
| Cache hit rate | Not exposed | High |
| Eviction count | Not exposed | Medium |
| Working memory token usage | Not exposed | Medium |
| Semantic cache metrics | Not implemented | High (Phase 2) |

---

## 7. Configuration Reference

### 7.1 Environment Variables

```bash
# RAG Memory Settings
RAG_CACHE_ENABLED=true
RAG_CACHE_SIZE=100
RAG_CACHE_TTL=3600
RAG_CONVERSATION_MEMORY_SIZE=10
RAG_CONVERSATION_CONTEXT_WINDOW=1000
RAG_TOP_K=10
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100

# Concurrency
RAG_MAX_CONCURRENT_EMBEDDINGS=4
RAG_EMBEDDING_BATCH_SIZE=20
```

### 7.2 Code Configuration

```python
# src/vection/core/stream_context.py
StreamContext(
    max_sessions=1000,
    max_threads_per_session=50,
    session_ttl_hours=24.0,
    thread_ttl_hours=4.0,
    snapshot_interval_minutes=5.0,
)

# src/tools/rag/config.py
RAGConfig(
    cache_enabled=True,
    cache_size=100,
    cache_ttl=3600,
    conversation_memory_size=10,
    conversation_context_window=1000,
    top_k=10,
    chunk_size=1000,
    chunk_overlap=100,
)
```

---

## 8. Gap Summary

| Gap ID | Description | Severity | Phase |
|--------|-------------|----------|-------|
| M1 | No explicit working/episodic/semantic split in one design | Medium | Phase 1 |
| M2 | No semantic cache layer (cache by embedding similarity) | Medium | Phase 2 |
| M3 | Spore has TTL but no LRU/max-size eviction | Low | Phase 2 (optional) |
| M4 | Episodic vs semantic not distinguished in storage | Low | Phase 2 (optional) |
| M5 | No importance-aware eviction | Low | Phase 3 |
| M6 | Chunking strategy not centralized | Low | Documented above |

---

## 9. Implementation Roadmap

### Phase 1: Document & Cap
- [x] Document MEMORY_POLICY.md (this file)
- [ ] Add working-memory cap in hot path
- [ ] Label three-tier in config and docs

### Phase 2: Cache & Retrieval
- [ ] Implement semantic response cache
- [ ] Wire retrieval to episodic vs semantic
- [ ] Expose cache hit rate and eviction metrics

### Phase 3: Tune & Maintain
- [ ] Tune based on observability
- [ ] Add importance-aware eviction (optional)
- [ ] CI check for policy drift

---

## 10. References

- [MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md](./MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md) — Gap analysis and patterns
- [ROADMAP_MEMORY_AND_SUBAGENT.md](./ROADMAP_MEMORY_AND_SUBAGENT.md) — Implementation phases
- `src/vection/core/stream_context.py` — Session/thread management
- `src/mycelium/core.py` — Spore dataclass
- `src/tools/rag/config.py` — RAG configuration
- `src/application/mothership/middleware/__init__.py` — Rate-limit eviction

---

*Last updated: March 2026*
*Version: 1.0.0 (Phase 0 baseline)*