# RAG Indexing Strategic Plan

**Version**: 1.0
**Date**: 2026-01-07
**Status**: Planning Phase
**Owner**: GRID RAG Team

---

## Executive Summary

This document outlines a comprehensive strategic plan for evolving the GRID RAG (Retrieval-Augmented Generation) indexing system. The plan focuses on **production readiness**, **scalability**, **performance optimization**, and **intelligent content curation** to support the GRID project's knowledge management and retrieval capabilities.

### Current State
- ✅ **Functional RAG system** with local-only operation
- ✅ **Incremental indexing** via `FileTracker` (hash-based change detection)
- ✅ **Hybrid search** (semantic + keyword) with reranking
- ✅ **Query caching** for performance optimization
- ✅ **Nomic Embed Text V2 MOE** for high-quality embeddings
- ✅ **ChromaDB** persistent vector store
- ⚠️ **Manual curation** via `important_files.json` and manifests
- ⚠️ **Limited automation** for index maintenance
- ⚠️ **No multi-collection support** for domain-specific indexes

### Vision
Transform RAG indexing from a **manual batch process** into an **intelligent, automated knowledge management system** with:
- **Automatic content discovery** and curation
- **Domain-aware multi-collection indexing** (code, docs, configs, etc.)
- **Real-time incremental updates** triggered by file changes
- **Quality-based filtering** to keep index signal-high
- **Monitoring and observability** for index health
- **Production-grade scalability** for large codebases (>10K files)

---

## Table of Contents

1. [Architecture Enhancements](#1-architecture-enhancements)
2. [Performance Optimization](#2-performance-optimization)
3. [Content Curation & Intelligence](#3-content-curation--intelligence)
4. [Operational Workflows](#4-operational-workflows)
5. [Monitoring & Observability](#5-monitoring--observability)
6. [Production Readiness](#6-production-readiness)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Success Metrics](#8-success-metrics)

---

## 1. Architecture Enhancements

### 1.1 Multi-Collection Architecture

**Objective**: Support domain-specific indexes for improved retrieval accuracy.

#### Design
```
.rag_db/
├── collections/
│   ├── code/              # Python, JavaScript, Rust, etc.
│   ├── docs/              # Markdown, RST documentation
│   ├── config/            # JSON, YAML, TOML configs
│   ├── schemas/           # Data schemas and types
│   ├── tests/             # Test files and fixtures
│   └── default/           # Fallback collection
├── trackers/
│   ├── code_tracker.json
│   ├── docs_tracker.json
│   └── ...
└── metadata/
    ├── collection_registry.json
    └── index_metadata.json
```

#### Implementation Tasks
- [ ] Create `CollectionManager` class to manage multiple vector stores
- [ ] Update `RAGConfig` to support collection-specific settings
- [ ] Implement automatic collection routing based on file type
- [ ] Add CLI commands: `index --collection <name>`, `query --collection <name>`
- [ ] Support cross-collection queries with result aggregation

#### Benefits
- **Better precision**: Domain-specific retrieval reduces noise
- **Independent scaling**: Index different content types at different rates
- **Specialized chunking**: Different chunk sizes for code vs. docs
- **Query optimization**: Target specific domains for faster results

---

### 1.2 Smart Chunking Strategies

**Objective**: Adaptive chunking based on content type and structure.

#### Current State
- Fixed chunk size (800 chars) with overlap (100 chars)
- Basic text splitting on `\n\n` separator

#### Proposed Strategies

##### Code Chunking
```python
class CodeChunker:
    """AST-aware chunking for source code."""

    def chunk_by_function(self, code: str, language: str):
        """Chunk by function/class boundaries."""
        # Use tree-sitter or AST parsing

    def chunk_by_import_groups(self, code: str):
        """Keep imports together, separate logic."""
```

##### Documentation Chunking
```python
class DocChunker:
    """Markdown-aware chunking."""

    def chunk_by_section(self, markdown: str):
        """Chunk by headers (##, ###, etc.)."""

    def preserve_code_blocks(self, markdown: str):
        """Keep code examples intact."""
```

##### Configuration Chunking
```python
class ConfigChunker:
    """Structured data chunking."""

    def chunk_by_top_level_keys(self, json_data: dict):
        """Chunk large configs by top-level sections."""
```

#### Implementation Tasks
- [ ] Create `chunking/` module with specialized chunkers
- [ ] Integrate tree-sitter for code parsing (Python, JS, Rust)
- [ ] Add markdown-aware chunking with header preservation
- [ ] Implement JSON/YAML structural chunking
- [ ] Update `indexer.py` to route by file type

#### Benefits
- **Semantic coherence**: Chunks align with logical code/doc units
- **Better retrieval**: More meaningful context boundaries
- **Improved embeddings**: Embeddings capture complete thoughts
- **Reduced fragmentation**: Fewer partial/incomplete chunks

---

### 1.3 Enhanced File Tracking

**Objective**: More granular change detection and tracking.

#### Enhancements
```python
@dataclass
class FileState:
    """Enhanced file state tracking."""
    path: str
    file_hash: str
    indexed_at: str
    file_size: int
    chunk_count: int

    # NEW FIELDS
    collection: str                    # Which collection this belongs to
    chunking_strategy: str             # How it was chunked
    embedding_model: str               # Which model was used
    quality_score: float               # Computed quality metric
    last_accessed: str                 # Query access tracking
    error_count: int = 0               # Indexing failure tracking
    metadata: dict = field(default_factory=dict)  # Extensible metadata
```

#### Features
- **Version tracking**: Detect when chunking/embedding changes require re-indexing
- **Access patterns**: Track which files are frequently accessed in queries
- **Quality metrics**: Score file content quality to deprioritize low-signal files
- **Error resilience**: Track and skip files that consistently fail indexing

---

### 1.4 Parallel Indexing Pipeline

**Objective**: Speed up indexing with concurrent processing.

#### Current State
- Serial processing of files
- `max_concurrent_embeddings=4` (limited parallelism)

#### Proposed Architecture
```python
class ParallelIndexer:
    """Multi-stage parallel indexing pipeline."""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

    async def index_batch(self, files: List[Path]):
        """
        Stage 1: File reading (I/O bound) - high parallelism
        Stage 2: Chunking (CPU bound) - moderate parallelism
        Stage 3: Embedding (network/GPU bound) - controlled parallelism
        Stage 4: Storage (I/O bound) - batched writes
        """
        # Parallel file reading
        contents = await self._read_files_parallel(files)

        # Parallel chunking
        chunks = await self._chunk_parallel(contents)

        # Batched embedding with rate limiting
        embeddings = await self._embed_batched(chunks)

        # Batched writes to vector store
        await self._store_batched(embeddings)
```

#### Implementation Tasks
- [ ] Implement async file I/O with `aiofiles`
- [ ] Create worker pool for CPU-bound chunking
- [ ] Add rate limiting for embedding API calls
- [ ] Implement batched vector store writes
- [ ] Add progress reporting and error handling

#### Performance Targets
- **Current**: ~2-5 minutes for 50 files
- **Target**: < 1 minute for 50 files, < 10 minutes for 500 files

---

## 2. Performance Optimization

### 2.1 Query Performance

#### Current Metrics (Reference)
| Operation | Time | Notes |
|-----------|------|-------|
| Cached query | < 100ms | LRU cache hit |
| Uncached semantic query | 500ms-2s | Embedding + search |
| Uncached keyword query | 50-200ms | No embedding |
| Hybrid query | 500ms-2s | Semantic + keyword + rerank |

#### Optimization Strategies

##### 1. Embedding Cache
```python
class EmbeddingCache:
    """Cache query embeddings for repeated queries."""

    def __init__(self, max_size: int = 1000):
        self.cache = LRUCache(max_size)

    def get_or_embed(self, text: str) -> List[float]:
        """Return cached embedding or compute new."""
        cache_key = hashlib.sha256(text.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        embedding = self.embed_provider.embed(text)
        self.cache[cache_key] = embedding
        return embedding
```

##### 2. Index Warm-up
```python
class IndexWarmer:
    """Pre-load frequently accessed collections."""

    async def warm_up(self, collection_name: str):
        """Load collection metadata into memory."""
        # Pre-fetch frequently accessed vectors
        # Load collection statistics
        # Initialize connection pools
```

##### 3. Result Streaming
```python
async def query_stream(query: str, top_k: int = 10):
    """Stream results as they become available."""
    async for chunk in retriever.stream(query, top_k):
        yield chunk  # Return early results
```

#### Implementation Tasks
- [ ] Implement embedding-level cache (separate from query cache)
- [ ] Add index warm-up on startup for default collection
- [ ] Implement streaming query results for large result sets
- [ ] Profile and optimize vector similarity search
- [ ] Add query batching for multiple simultaneous queries

---

### 2.2 Indexing Performance

#### Optimization Strategies

##### 1. Incremental Batch Updates
```python
class IncrementalBatcher:
    """Batch incremental updates efficiently."""

    def __init__(self, batch_size: int = 100, batch_timeout: float = 5.0):
        self.pending = []
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

    async def add_file(self, file_path: Path):
        """Add file to pending batch."""
        self.pending.append(file_path)

        if len(self.pending) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """Process pending batch."""
        if not self.pending:
            return

        await self.index_batch(self.pending)
        self.pending = []
```

##### 2. Delta Indexing
```python
class DeltaIndexer:
    """Only re-index changed chunks within a file."""

    def compute_chunk_diff(self, old_chunks: List[str], new_chunks: List[str]):
        """Compute diff between chunk sets."""
        # Use edit distance or hash-based diffing
        # Only re-embed changed chunks
```

##### 3. Smart Scheduling
```python
class IndexScheduler:
    """Schedule indexing during low-activity periods."""

    def should_index_now(self) -> bool:
        """Check if system is idle enough for indexing."""
        # Check CPU usage, memory, disk I/O
        # Avoid indexing during active development
```

#### Implementation Tasks
- [ ] Implement batching for incremental updates
- [ ] Add chunk-level diffing for large files
- [ ] Create scheduler for background indexing
- [ ] Optimize delete operations (bulk delete)
- [ ] Add indexing queue with priority levels

---

### 2.3 Storage Optimization

#### Strategies

##### 1. Compression
```python
# Store embeddings in compressed format
import numpy as np

def compress_embedding(embedding: List[float]) -> bytes:
    """Compress embedding vector."""
    arr = np.array(embedding, dtype=np.float16)  # Half precision
    return arr.tobytes()
```

##### 2. Pruning
```python
class IndexPruner:
    """Remove low-quality or unused chunks."""

    def prune_by_access(self, min_access_count: int = 1, days: int = 90):
        """Remove chunks not accessed in N days."""

    def prune_by_quality(self, min_quality_score: float = 0.3):
        """Remove low-quality chunks."""
```

##### 3. Sharding
```python
class ShardedVectorStore:
    """Shard large collections across multiple ChromaDB instances."""

    def __init__(self, num_shards: int = 4):
        self.shards = [ChromaDB(f"shard_{i}") for i in range(num_shards)]

    def get_shard(self, doc_id: str) -> ChromaDB:
        """Route document to shard by hash."""
        shard_idx = hash(doc_id) % len(self.shards)
        return self.shards[shard_idx]
```

#### Implementation Tasks
- [ ] Add embedding compression option
- [ ] Implement periodic index pruning
- [ ] Add shard support for large collections (>100K chunks)
- [ ] Implement index compaction command
- [ ] Add disk usage monitoring and alerts

---

## 3. Content Curation & Intelligence

### 3.1 Automatic Content Discovery

**Objective**: Intelligently discover and prioritize content for indexing.

#### Discovery Rules
```python
class ContentDiscoverer:
    """Discover high-value content for indexing."""

    def __init__(self):
        self.rules = [
            GitActivityRule(),      # Recently modified files
            ImportanceRule(),       # Files imported frequently
            DocumentationRule(),    # README, docs/, etc.
            EntryPointRule(),       # main.py, __init__.py, etc.
            ConfigurationRule(),    # Core config files
        ]

    def discover(self, repo_path: Path) -> List[Path]:
        """Apply rules to find high-value files."""
        candidates = {}

        for rule in self.rules:
            scored_files = rule.score_files(repo_path)
            for file, score in scored_files.items():
                candidates[file] = candidates.get(file, 0) + score

        # Return top-scored files
        return sorted(candidates, key=candidates.get, reverse=True)
```

#### Discovery Rules

##### 1. Git Activity Rule
- Prioritize recently modified files (last 30 days)
- Weight by commit frequency
- Boost files with multiple contributors

##### 2. Importance Rule
- Parse import statements to build dependency graph
- Prioritize files with high fan-in (imported by many)
- Boost "core" modules (grid/, application/, tools/)

##### 3. Documentation Rule
- Always index README files
- Prioritize docs/ directory
- Include inline docstrings from important modules

##### 4. Entry Point Rule
- Index main.py, __init__.py, cli.py
- Include API endpoint definitions
- Boost files with `if __name__ == "__main__"`

##### 5. Test Coverage Rule
- Include test files for well-tested modules
- Use as signal for code quality

#### Implementation Tasks
- [ ] Implement `ContentDiscoverer` with pluggable rules
- [ ] Add Git log parsing for activity analysis
- [ ] Build static analysis for import graph
- [ ] Create scoring algorithm with rule weights
- [ ] Add CLI command: `rag discover --show-scores`

---

### 3.2 Quality Filtering

**Objective**: Filter out low-quality content that pollutes the index.

#### Quality Metrics
```python
class QualityScorer:
    """Score content quality for indexing decisions."""

    def score_file(self, file_path: Path, content: str) -> float:
        """Compute quality score (0.0 - 1.0)."""
        score = 0.0

        # Penalize generated files
        if self._is_generated(content):
            score -= 0.5

        # Penalize lock files, minified code
        if self._is_machine_readable(file_path):
            score -= 0.3

        # Boost documentation
        if self._has_good_docs(content):
            score += 0.3

        # Boost well-structured code
        if self._is_well_structured(content):
            score += 0.2

        return max(0.0, min(1.0, score))
```

#### Quality Signals

| Signal | Weight | Detection |
|--------|--------|-----------|
| Auto-generated file | -0.5 | Header comments, .lock files |
| Minified code | -0.4 | Long lines, low readability |
| Test fixtures | -0.2 | Large JSON/data dumps |
| Good documentation | +0.3 | Docstrings, comments, README |
| Clean structure | +0.2 | Low complexity, readable |
| Recent activity | +0.1 | Git commits in last 30 days |

#### Filters
- **Exclude**: node_modules, venv, .git, __pycache__, *.pyc
- **Exclude**: package-lock.json, uv.lock, *.min.js
- **Conditionally exclude**: Large binary files (>1MB), large logs
- **Include**: All docs/, schema files, core source

#### Implementation Tasks
- [ ] Implement quality scoring system
- [ ] Add heuristics for generated file detection
- [ ] Create configurable quality threshold
- [ ] Add `--quality-threshold` flag to indexing
- [ ] Report quality scores in index stats

---

### 3.3 Semantic Deduplication

**Objective**: Avoid indexing duplicate or near-duplicate content.

#### Strategy
```python
class SemanticDeduplicator:
    """Detect and remove semantic duplicates."""

    def find_duplicates(self, chunks: List[str], threshold: float = 0.95):
        """Find chunks with >95% similarity."""
        embeddings = [self.embed(c) for c in chunks]

        duplicates = []
        for i, emb_i in enumerate(embeddings):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity(emb_i, embeddings[j])
                if similarity >= threshold:
                    duplicates.append((i, j, similarity))

        return duplicates
```

#### Use Cases
- Remove boilerplate code chunks (license headers, imports)
- Avoid indexing copy-pasted documentation
- Detect versioned duplicates (old backups, archived files)

#### Implementation Tasks
- [ ] Implement similarity-based deduplication
- [ ] Add deduplication pass before embedding
- [ ] Make threshold configurable
- [ ] Report deduplicated count in stats

---

## 4. Operational Workflows

### 4.1 Indexing Modes

#### 1. Full Rebuild
```bash
# Rebuild entire index from scratch
python -m tools.rag.cli index . --rebuild --curate

# Rebuild specific collection
python -m tools.rag.cli index . --rebuild --collection docs
```

**Use Cases**:
- Major codebase restructuring
- Embedding model upgrade
- Index corruption recovery

**Duration**: 5-15 minutes for medium repos (500-1000 files)

---

#### 2. Incremental Update
```bash
# Update changed files only
python -m tools.rag.cli index . --incremental

# Update specific file
python -m tools.rag.cli index README.md --incremental
```

**Use Cases**:
- Daily/hourly updates
- Single file modifications
- Continuous integration

**Duration**: 15-60 seconds for small changes (5-20 files)

---

#### 3. Smart Discovery
```bash
# Discover and index important files automatically
python -m tools.rag.cli index . --discover --limit 100

# Show discovery scores without indexing
python -m tools.rag.cli discover --show-scores
```

**Use Cases**:
- Initial index creation
- Periodic quality refresh
- New project onboarding

**Duration**: 2-5 minutes for discovery + indexing top 100 files

---

#### 4. Watch Mode (Future)
```bash
# Continuously watch for file changes and auto-index
python -m tools.rag.cli watch . --delay 60
```

**Use Cases**:
- Development mode
- Real-time knowledge updates
- Long-running services

---

### 4.2 Maintenance Operations

#### Index Health Check
```bash
# Check index health and show recommendations
python -m tools.rag.cli health-check

# Output:
# ✅ Index version: 1.0
# ✅ Collections: 5 (code, docs, config, schemas, tests)
# ✅ Total chunks: 4,523
# ⚠️  Quality: 78% (22% low-quality chunks detected)
# ⚠️  Duplicates: 45 near-duplicates found
# 💡 Recommendation: Run 'rag optimize' to improve quality
```

#### Index Optimization
```bash
# Run all optimization passes
python -m tools.rag.cli optimize

# Includes:
# - Prune low-quality chunks
# - Remove duplicates
# - Compact storage
# - Update statistics
```

#### Cache Management
```bash
# Clear query cache
python -m tools.rag.cli clear-cache

# Clear old cache entries (>30 days)
python -m tools.rag.cli clear-cache --older-than 30

# View cache statistics
python -m tools.rag.cli cache-stats
```

#### Backup & Restore
```bash
# Backup index
python -m tools.rag.cli backup --output .rag_backup_2026_01_07.tar.gz

# Restore from backup
python -m tools.rag.cli restore --input .rag_backup_2026_01_07.tar.gz
```

---

### 4.3 CI/CD Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/rag-index.yml
name: Update RAG Index

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'grid/**'
      - 'application/**'

  schedule:
    # Daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  update-index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Pull Ollama models
        run: |
          ollama pull nomic-embed-text-v2-moe:latest

      - name: Update RAG index
        run: |
          python -m tools.rag.cli index . --incremental

      - name: Upload index artifact
        uses: actions/upload-artifact@v3
        with:
          name: rag-index
          path: .rag_db/
```

---

## 5. Monitoring & Observability

### 5.1 Metrics Collection

#### Index Metrics
```python
@dataclass
class IndexMetrics:
    """Metrics for RAG index health."""

    # Size metrics
    total_collections: int
    total_chunks: int
    total_files: int
    disk_usage_mb: float

    # Quality metrics
    avg_quality_score: float
    low_quality_chunks: int
    duplicate_chunks: int

    # Performance metrics
    avg_indexing_time_sec: float
    avg_query_time_ms: float
    cache_hit_rate: float

    # Activity metrics
    queries_last_24h: int
    indexes_last_24h: int
    errors_last_24h: int

    # Freshness metrics
    last_indexed_at: str
    oldest_chunk_age_days: int
    files_pending_index: int
```

#### Logging
```python
# Structured logging for observability
import structlog

logger = structlog.get_logger()

logger.info(
    "index.completed",
    collection="docs",
    files_indexed=45,
    chunks_created=523,
    duration_sec=32.5,
    quality_score=0.85
)
```

---

### 5.2 Dashboards (Future)

#### Proposed Metrics Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ RAG Index Health Dashboard                              │
├─────────────────────────────────────────────────────────┤
│ Collections: 5        Chunks: 4,523     Files: 287      │
│ Disk Usage: 234 MB    Quality: 82%     Duplicates: 23   │
├─────────────────────────────────────────────────────────┤
│ Activity (Last 24h)                                      │
│ Queries: 156 (↑12%)   Cache Hit Rate: 67%              │
│ Indexes: 23           Avg Query Time: 450ms            │
│ Errors: 2             Last Index: 2 hours ago          │
├─────────────────────────────────────────────────────────┤
│ Top Queries (Last 7 days)                               │
│ 1. "GRID architecture"                       45 queries │
│ 2. "RAG implementation"                      32 queries │
│ 3. "Docker deployment"                       28 queries │
├─────────────────────────────────────────────────────────┤
│ Alerts                                                   │
│ ⚠️  Quality score dropped below 80% (current: 78%)      │
│ 💡 45 duplicate chunks detected - run optimization      │
└─────────────────────────────────────────────────────────┘
```

---

### 5.3 Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Disk usage > 1GB | Warning | Notify, suggest pruning |
| Quality score < 70% | Warning | Suggest optimization |
| Query time > 5s | Critical | Investigate performance |
| Indexing errors > 10/day | Critical | Check logs |
| Index age > 7 days | Info | Suggest refresh |

---

## 6. Production Readiness

### 6.1 Reliability

#### Error Handling
```python
class RobustIndexer:
    """Indexer with comprehensive error handling."""

    async def index_file(self, file_path: Path):
        """Index single file with retries and fallbacks."""
        try:
            content = await self.read_file(file_path)
            chunks = await self.chunk_content(content)
            embeddings = await self.embed_with_retry(chunks)
            await self.store_with_transaction(embeddings)

        except EmbeddingError as e:
            logger.error("embedding.failed", file=file_path, error=str(e))
            # Fallback to keyword-only indexing
            await self.index_keywords_only(file_path, content)

        except StorageError as e:
            logger.error("storage.failed", file=file_path, error=str(e))
            # Queue for retry
            await self.retry_queue.add(file_path)

        except Exception as e:
            logger.exception("index.unexpected_error", file=file_path)
            # Track in error metrics
            self.metrics.record_error(file_path, e)
```

#### Retry Logic
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(TransientError)
)
async def embed_with_retry(self, text: str):
    """Embed with exponential backoff retry."""
    return await self.embedding_provider.embed(text)
```

---

### 6.2 Scalability Limits

#### Current Architecture

| Component | Limit | Mitigation |
|-----------|-------|------------|
| ChromaDB | 100K chunks/collection | Sharding, pruning |
| Embedding API | 100 req/min (Ollama) | Batching, caching |
| Disk Space | 1GB default budget | Compression, cleanup |
| Memory | Loads full collection | Lazy loading, paging |

#### Scaling Strategies

**For Medium Repos (1K-5K files)**:
- Single ChromaDB instance
- Multi-collection architecture
- Periodic pruning
- **Expected usage**: 500MB, 50K chunks

**For Large Repos (5K-20K files)**:
- Sharded collections
- Aggressive quality filtering
- Distributed embedding workers
- **Expected usage**: 2-5GB, 200K chunks

**For Enterprise (>20K files)**:
- External vector DB (Pinecone, Weaviate)
- Distributed indexing pipeline
- Dedicated embedding service
- **Expected usage**: 10GB+, 1M+ chunks

---

### 6.3 Security & Privacy

#### Local-Only Guarantee
- ✅ All embeddings via local Ollama
- ✅ All storage in local ChromaDB
- ✅ No cloud API calls by default
- ✅ Optional telemetry (opt-in only)

#### Access Control
```python
class SecureRAGEngine:
    """RAG engine with access control."""

    def __init__(self, allowed_paths: List[Path]):
        self.allowed_paths = allowed_paths

    def query(self, query: str, user_id: str):
        """Query with user-level access control."""
        # Check user permissions
        # Filter results by allowed paths
        # Audit log query access
```

#### Sensitive Data Filtering
```python
class SensitiveDataFilter:
    """Filter sensitive data before indexing."""

    PATTERNS = [
        r'(?i)(api[_-]?key|secret|password)\s*[:=]\s*["\']?[\w-]+',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
    ]

    def sanitize(self, content: str) -> str:
        """Remove sensitive patterns."""
        for pattern in self.PATTERNS:
            content = re.sub(pattern, '[REDACTED]', content)
        return content
```

---

## 7. Implementation Roadmap

### Phase 1: Foundations (Weeks 1-2)
**Goal**: Production-ready core with monitoring

- [x] ✅ Current: Incremental indexing working
- [x] ✅ Current: Query caching implemented
- [x] ✅ Current: Hybrid search available
- [ ] **NEW**: Add structured logging
- [ ] **NEW**: Implement metrics collection
- [ ] **NEW**: Create health-check command
- [ ] **NEW**: Add comprehensive error handling
- [ ] **NEW**: Write operational runbook

**Deliverables**:
- Robust indexer with retries
- Metrics dashboard (CLI)
- Health monitoring
- Documentation updates

---

### Phase 2: Intelligence (Weeks 3-4)
**Goal**: Smart curation and quality filtering

- [ ] Implement `ContentDiscoverer` with rule engine
- [ ] Add quality scoring system
- [ ] Create semantic deduplication
- [ ] Build automatic discovery mode
- [ ] Add `discover` CLI command

**Deliverables**:
- Auto-curation system
- Quality-based filtering
- Discovery mode for new repos
- Updated quickstart guide

---

### Phase 3: Scalability (Weeks 5-6)
**Goal**: Multi-collection architecture and performance

- [ ] Implement `CollectionManager`
- [ ] Add smart chunking strategies
- [ ] Build parallel indexing pipeline
- [ ] Create sharding support
- [ ] Optimize storage compression

**Deliverables**:
- Multi-collection support
- 5x indexing speed improvement
- Domain-specific chunking
- Scalability testing (10K files)

---

### Phase 4: Automation (Weeks 7-8)
**Goal**: Automated workflows and CI/CD

- [ ] Implement watch mode
- [ ] Create GitHub Actions workflow
- [ ] Add scheduled optimization
- [ ] Build backup/restore system
- [ ] Write CI/CD integration guide

**Deliverables**:
- Automated indexing pipeline
- CI/CD templates
- Backup strategy
- Production deployment guide

---

### Phase 5: Advanced Features (Future)
**Goal**: Enterprise-grade capabilities

- [ ] Add access control system
- [ ] Implement sensitive data filtering
- [ ] Create web dashboard
- [ ] Build distributed indexing
- [ ] Add external vector DB support

**Deliverables**:
- Security enhancements
- Web-based monitoring
- Multi-node indexing
- Enterprise deployment options

---

## 8. Success Metrics

### Performance KPIs

| Metric | Current | Target (Phase 1) | Target (Phase 3) |
|--------|---------|------------------|------------------|
| Index build time (100 files) | 2-5 min | 1-2 min | < 1 min |
| Incremental update (10 files) | 30-60 sec | 15-30 sec | < 15 sec |
| Query latency (uncached) | 500ms-2s | 300ms-1s | < 300ms |
| Cache hit rate | ~40% | 60% | 75% |
| Index quality score | Unknown | 75% | 85% |

### Operational KPIs

| Metric | Target |
|--------|--------|
| Indexing success rate | > 99% |
| Query success rate | > 99.9% |
| Uptime (for watch mode) | > 99% |
| Mean time to recovery | < 5 min |
| Error rate | < 1% |

### Quality KPIs

| Metric | Target |
|--------|--------|
| Retrieval precision@5 | > 80% |
| Retrieval recall@10 | > 70% |
| Duplicate chunk rate | < 5% |
| Low-quality chunk rate | < 20% |
| User satisfaction | > 4/5 |

---

## Appendix A: Configuration Reference

### Environment Variables

```bash
# Core Configuration
export RAG_EMBEDDING_MODEL="nomic-embed-text-v2-moe:latest"
export RAG_LLM_MODEL_LOCAL="ministral-3:3b"
export RAG_VECTOR_STORE_PATH=".rag_db"

# Performance Tuning
export RAG_CHUNK_SIZE=800
export RAG_CHUNK_OVERLAP=100
export RAG_MAX_CONCURRENT_EMBEDDINGS=8
export RAG_EMBEDDING_BATCH_SIZE=50

# Quality Settings
export RAG_QUALITY_THRESHOLD=0.5
export RAG_ENABLE_DEDUPLICATION=true
export RAG_DEDUP_THRESHOLD=0.95

# Caching
export RAG_CACHE_ENABLED=true
export RAG_CACHE_SIZE=200
export RAG_CACHE_TTL=7200

# Monitoring
export RAG_ENABLE_METRICS=true
export RAG_LOG_LEVEL=INFO
export RAG_METRICS_PORT=9090

# Advanced
export RAG_USE_HYBRID=true
export RAG_USE_RERANKER=true
export RAG_ENABLE_COMPRESSION=true
```

---

## Appendix B: Troubleshooting Guide

### Common Issues

#### Issue: Slow indexing performance
**Symptoms**: Indexing takes >10 minutes for small repos

**Solutions**:
1. Check Ollama is running: `ollama list`
2. Verify embedding model loaded: `ollama pull nomic-embed-text-v2-moe:latest`
3. Increase concurrency: `export RAG_MAX_CONCURRENT_EMBEDDINGS=8`
4. Use curated indexing: `--curate` flag
5. Enable compression: `export RAG_ENABLE_COMPRESSION=true`

---

#### Issue: Low quality results
**Symptoms**: Queries return irrelevant or low-quality chunks

**Solutions**:
1. Rebuild index: `--rebuild --curate`
2. Enable quality filtering: `export RAG_QUALITY_THRESHOLD=0.7`
3. Use hybrid search: `--hybrid --rerank`
4. Run optimization: `rag optimize`
5. Check index stats: `rag stats --detail`

---

#### Issue: Disk space exhaustion
**Symptoms**: `.rag_db` directory grows to >1GB

**Solutions**:
1. Run pruning: `rag optimize --prune`
2. Clear old cache: `rag clear-cache --older-than 30`
3. Enable compression: `export RAG_ENABLE_COMPRESSION=true`
4. Reduce chunk size: `export RAG_CHUNK_SIZE=500`
5. Use quality filtering: Higher threshold excludes more files

---

## Appendix C: API Reference

### Core Classes

```python
# RAG Engine
from tools.rag import RAGEngine, RAGConfig

config = RAGConfig.from_env()
engine = RAGEngine(config)

# Indexing
engine.index("/path/to/repo", rebuild=False, curate=True)

# Querying
result = engine.query("question", top_k=5, use_hybrid=True)

# Stats
stats = engine.get_stats()
```

### CLI Commands

```bash
# Indexing
rag index <path> [--rebuild] [--curate] [--incremental] [--collection NAME]

# Querying
rag query <query> [--top-k N] [--hybrid] [--rerank] [--collection NAME]

# Maintenance
rag stats [--detail]
rag health-check
rag optimize [--prune] [--dedupe]
rag clear-cache [--older-than DAYS]

# Discovery
rag discover [--show-scores] [--limit N]

# Advanced
rag backup --output FILE
rag restore --input FILE
rag watch <path> [--delay SECONDS]
```

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-07 | Initial plan | GRID RAG Team |

---

**Next Review**: 2026-02-07
**Status**: Ready for implementation
**Approval**: Pending user sign-off
