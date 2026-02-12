# Phase 4: Advanced Indexing, Chunking & Embedding Strategy

**Status:** 📋 Planning Phase  
**Target Completion:** Q1 2025  
**Research Base:** arXiv 2024-2025 papers + industry best practices  

---

## Executive Summary

Phase 4 focuses on **next-generation indexing and embedding strategies** based on cutting-edge RAG research. While Phase 3 added reasoning capabilities, Phase 4 improves the **foundation** - ensuring we retrieve the *right* information in the *right* granularity with the *right* context.

### Key Innovations:
1. **Adaptive Chunking** - Context-aware segmentation (semantic, hierarchical, sliding)
2. **Multi-Vector Embeddings** - ColBERT-style late interaction for better precision
3. **Conversational Context** - Multi-turn dialogue memory and query reconstruction
4. **Chain-of-Retrieval** - Dynamic query reformulation (CoRAG pattern)
5. **Hierarchical Indexing** - Document → Section → Chunk → Sentence levels

---

## Research Foundation

### Key Papers (arXiv 2024-2025)

#### 1. **Chunking Strategies**
- **"Is Semantic Chunking Worth the Computational Cost?"** (arXiv:2410.13070)
  - Finding: Semantic chunking doesn't always outperform fixed-size
  - Recommendation: Use **adaptive hybrid** based on content type
  
- **"ChunkRAG: Novel LLM-Chunk Filtering"** (arXiv:2410.19572)
  - Innovation: Chunk-level relevance scoring before generation
  - Result: Reduces hallucinations, improves factual accuracy

- **"MoC: Mixtures of Text Chunking Learners"** (arXiv:2503.09600)
  - Innovation: LLM generates chunking regular expressions
  - Metrics: Boundary Clarity + Chunk Stickiness
  - Pattern: Different chunkers for different content types

- **"Max-Min Semantic Chunking"** (Springer 2025)
  - Method: Max-Min algorithm for semantic coherence
  - Result: 85-90% AMI scores, 56% accuracy improvement

#### 2. **Multi-Vector Embeddings**
- **"Jina-ColBERT-v2"** (arXiv:2408.16672)
  - Innovation: Per-token embeddings with late interaction
  - Benefit: Captures fine-grained semantic nuances
  - Tradeoff: Higher storage (mitigated by compression)

- **"Topo-RAG"** (arXiv:2601.10215)
  - Innovation: Cell-Aware Late Interaction for tables
  - Result: 18.4% improvement on hybrid text-table queries
  - Pattern: Different retrieval for different topologies

#### 3. **Conversational RAG**
- **"DH-RAG: Dynamic Historical Context"** (arXiv:2502.13847, AAAI'25)
  - Innovation: Dynamic Historical Information database
  - Strategies: Historical Query Clustering, Hierarchical Matching, Chain of Thought Tracking
  - Pattern: Both long-term memory + immediate context

- **"CORAL: Multi-turn Conversational RAG Benchmark"** (NAACL 2025)
  - Challenge: Open-domain, knowledge-intensive, free-form, topic shifts
  - Tasks: Passage retrieval, response generation, citation labeling
  - Gap: Academic research is single-turn, industry needs multi-turn

- **"CID-GraphRAG"** (arXiv:2506.19385)
  - Innovation: Intent transition graphs + semantic search
  - Result: 58% improvement in response quality
  - Pattern: Dual-retrieval (intent flow + context semantics)

- **"EvoRAG"** (CIKM 2025)
  - Innovation: Evolving knowledge graph aligned with conversation
  - Benefit: Models explicit relations among turns

#### 4. **Chain-of-Retrieval**
- **"CoRAG: Chain-of-Retrieval Augmented Generation"** (arXiv:2501.14342, NeurIPS 2025)
  - Innovation: o1-like RAG with step-by-step retrieval reasoning
  - Method: Dynamic query reformulation based on evolving state
  - Training: Rejection sampling for intermediate retrieval chains
  - Result: +10 points EM score on multi-hop QA, SOTA on KILT
  - Pattern: Retrieve → Reason → Reformulate → Retrieve again

---

## Architecture Overview

### Current State (Phase 3)
```
Query → Understanding → Retrieval (3-stage) → Evidence → Reasoning → Synthesis
```

### Phase 4 Enhanced Architecture
```
Query/Conversation
    ↓
┌────────────────────────────────────────────────────────┐
│ 1. CONVERSATIONAL CONTEXT MANAGER                      │
│    • Multi-turn dialogue history                       │
│    • Dynamic context window (sliding + summarization)  │
│    • Intent transition tracking                        │
│    • Query reconstruction from history                 │
└────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────┐
│ 2. ADAPTIVE CHUNKING LAYER                             │
│    • Content-type detection (code, prose, table, etc.) │
│    • Chunking strategy selection:                      │
│      - Semantic (prose, documentation)                 │
│      - Fixed-size (code with overlap)                  │
│      - Hierarchical (nested structures)                │
│      - Cell-aware (tables)                             │
│    • Boundary optimization                             │
│    • Chunk quality scoring (Boundary Clarity + Stickiness)│
└────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────┐
│ 3. MULTI-VECTOR EMBEDDING                              │
│    • ColBERT-style token-level embeddings              │
│    • Late interaction scoring                          │
│    • Hierarchical embeddings (doc, section, chunk)     │
│    • Context-aware encoding                            │
└────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────┐
│ 4. CHAIN-OF-RETRIEVAL (CoRAG)                          │
│    • Initial retrieval                                 │
│    • Iterative query reformulation:                    │
│      Step 1: Query → Retrieve → Analyze → Sub-query    │
│      Step 2: Sub-query → Retrieve → Synthesize         │
│      Step N: Final retrieval                           │
│    • Test-time compute scaling                         │
└────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────┐
│ 5. HIERARCHICAL RETRIEVAL                              │
│    • Document-level filtering                          │
│    • Section-level matching                            │
│    • Chunk-level scoring                               │
│    • Sentence-level extraction (evidence)              │
└────────────────────────────────────────────────────────┘
    ↓
Evidence → Reasoning (Phase 3) → Synthesis
```

---

## Component Design

### 1. Conversational Context Manager

**Purpose:** Maintain coherent multi-turn dialogue state

**Components:**
```python
class ConversationalContextManager:
    """
    Manages multi-turn conversation state with dynamic memory.
    
    Based on DH-RAG (AAAI'25) and CORAL benchmark patterns.
    """
    
    def __init__(self):
        self.long_term_memory = DynamicHistoricalDB()
        self.short_term_window = SlidingWindow(max_turns=5)
        self.intent_tracker = IntentTransitionGraph()
        
    def add_turn(self, query: str, response: str, intent: str):
        """Add conversation turn to memory."""
        # Update sliding window
        self.short_term_window.append(query, response)
        
        # Cluster and store in long-term memory
        cluster_id = self.long_term_memory.cluster_query(query)
        self.long_term_memory.store(cluster_id, query, response)
        
        # Track intent transitions
        self.intent_tracker.add_transition(intent)
        
    def reconstruct_query(self, current_query: str) -> str:
        """
        Reconstruct standalone query from conversational context.
        
        Uses:
        - Historical Query Clustering
        - Hierarchical Matching
        - Chain of Thought Tracking
        """
        # Get relevant history
        history = self.long_term_memory.retrieve_relevant(current_query)
        
        # Resolve anaphora and ellipsis
        resolved_query = self._resolve_references(current_query, history)
        
        # Add missing context
        enriched_query = self._enrich_with_context(resolved_query, history)
        
        return enriched_query
        
    def _resolve_references(self, query: str, history: List[Turn]) -> str:
        """Resolve 'it', 'that', 'these', etc."""
        # Pattern matching for pronouns
        # Replace with entities from history
        pass
        
    def _enrich_with_context(self, query: str, history: List[Turn]) -> str:
        """Add implicit context from conversation flow."""
        # If query is continuation, prepend topic
        # Example: "What about X?" → "What about X in context of Y?"
        pass
```

**Key Features:**
- **Sliding Window:** Last 5 turns kept in full detail
- **Summarization Buffer:** Older turns condensed (facts only)
- **Intent Graph:** Tracks conversation flow patterns
- **Query Reconstruction:** Resolves anaphora, adds context

**Memory Strategy:**
```
Turn 1-5:  Full detail (immediate context)
Turn 6-10: Summarized (key facts only)
Turn 11+:  Clustered (retrieve on demand)
```

---

### 2. Adaptive Chunking System

**Purpose:** Optimize chunk boundaries for different content types

**Architecture:**
```python
class AdaptiveChunker:
    """
    Selects optimal chunking strategy based on content type.
    
    Based on MoC (arXiv:2503.09600) and ChunkRAG patterns.
    """
    
    def __init__(self):
        self.strategies = {
            'code': FixedSizeChunker(size=1000, overlap=200),
            'prose': SemanticChunker(method='max-min'),
            'table': CellAwareChunker(),
            'list': StructuredChunker(),
            'mixed': HierarchicalChunker()
        }
        
    def chunk(self, document: Document) -> List[Chunk]:
        """Chunk document with adaptive strategy."""
        # Detect content type
        content_type = self._detect_content_type(document)
        
        # Select chunker
        chunker = self.strategies[content_type]
        
        # Generate chunks
        chunks = chunker.chunk(document)
        
        # Score chunk quality
        scored_chunks = self._score_chunks(chunks)
        
        # Filter low-quality chunks
        return [c for c in scored_chunks if c.quality_score > 0.6]
        
    def _detect_content_type(self, document: Document) -> str:
        """Detect primary content type."""
        # Check for code patterns
        if self._is_code(document):
            return 'code'
        
        # Check for tables
        if self._has_tables(document):
            return 'table' if self._is_mostly_tables(document) else 'mixed'
        
        # Check for lists
        if self._is_list_heavy(document):
            return 'list'
        
        return 'prose'
        
    def _score_chunks(self, chunks: List[Chunk]) -> List[ScoredChunk]:
        """Score chunk quality using dual metrics."""
        scored = []
        for chunk in chunks:
            # Metric 1: Boundary Clarity (how clean are splits?)
            boundary_score = self._calculate_boundary_clarity(chunk)
            
            # Metric 2: Chunk Stickiness (semantic coherence)
            stickiness_score = self._calculate_chunk_stickiness(chunk)
            
            # Combined score
            quality_score = 0.5 * boundary_score + 0.5 * stickiness_score
            
            scored.append(ScoredChunk(chunk, quality_score))
            
        return scored
```

**Chunking Strategies:**

| Content Type | Strategy | Size | Overlap | Rationale |
|--------------|----------|------|---------|-----------|
| **Code** | Fixed-size | 1000 chars | 200 chars | Preserve function boundaries |
| **Prose/Docs** | Semantic (Max-Min) | Variable | Semantic | Topic coherence |
| **Tables** | Cell-aware | Per table | None | Preserve structure |
| **Lists** | Structured | Per section | None | Maintain hierarchy |
| **Mixed** | Hierarchical | Variable | Context | Best of both |

**Quality Metrics:**
- **Boundary Clarity:** Are splits at natural boundaries? (1.0 = perfect, 0.0 = mid-sentence)
- **Chunk Stickiness:** Is content semantically coherent? (cosine similarity of sentences within chunk)

---

### 3. Multi-Vector Embedding Layer

**Purpose:** Capture fine-grained semantic information with token-level embeddings

**Architecture:**
```python
class MultiVectorEmbedder:
    """
    ColBERT-style multi-vector embeddings with late interaction.
    
    Based on Jina-ColBERT-v2 (arXiv:2408.16672).
    """
    
    def __init__(self, model_name: str = "jinaai/jina-colbert-v2"):
        self.model = AutoModel.from_pretrained(model_name)
        self.dim = 128  # Compressed dimension per token
        
    def embed_document(self, text: str) -> TokenEmbeddings:
        """Embed document at token level."""
        # Tokenize
        tokens = self.tokenizer(text, return_tensors="pt")
        
        # Get token embeddings (not just [CLS])
        with torch.no_grad():
            outputs = self.model(**tokens)
            token_embeddings = outputs.last_hidden_state  # [1, seq_len, dim]
        
        # Compress dimension (768 → 128)
        compressed = self.compress(token_embeddings)
        
        return TokenEmbeddings(
            tokens=tokens,
            embeddings=compressed,
            mask=tokens.attention_mask
        )
        
    def late_interaction_score(
        self, 
        query_embeddings: TokenEmbeddings,
        doc_embeddings: TokenEmbeddings
    ) -> float:
        """
        Compute late interaction score (MaxSim).
        
        For each query token, find max similarity with any doc token.
        Sum across all query tokens.
        """
        scores = []
        
        for q_token in query_embeddings:
            # Compute similarity with all doc tokens
            sims = cosine_similarity(q_token, doc_embeddings.all_tokens)
            
            # Take maximum
            max_sim = sims.max()
            scores.append(max_sim)
        
        # Sum and normalize
        return sum(scores) / len(scores)
```

**Benefits over Single-Vector:**
- **Fine-grained matching:** "RAGEngine.query()" matches "query" and "RAGEngine" separately
- **Robustness:** Less sensitive to irrelevant context in chunk
- **Interpretability:** Can see which tokens matched

**Tradeoffs:**
- **Storage:** ~10x more space (mitigated by compression: 768D → 128D per token)
- **Compute:** Slower scoring (but still practical with optimizations)
- **Indexing:** Requires specialized indexes (PLAID, etc.)

**Hybrid Strategy:**
```
Stage 1: Single-vector (fast, broad recall)
Stage 2: Multi-vector (precise, rerank top-k)
```

---

### 4. Chain-of-Retrieval (CoRAG)

**Purpose:** Dynamic query reformulation for complex multi-hop queries

**Architecture:**
```python
class ChainOfRetrievalEngine:
    """
    Implements CoRAG pattern for iterative retrieval reasoning.
    
    Based on CoRAG (arXiv:2501.14342, NeurIPS 2025).
    """
    
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.max_hops = 3
        
    async def retrieve_with_chain(
        self, 
        query: str,
        decoding_strategy: str = "best_of_n"
    ) -> ChainOfRetrievalResult:
        """
        Execute chain-of-retrieval reasoning.
        
        Decoding strategies:
        - greedy: Fast, deterministic
        - best_of_n: Sample N chains, pick best
        - tree_search: Explore multiple paths
        """
        chain = RetrievalChain(initial_query=query)
        
        for hop in range(self.max_hops):
            # Current query (may be reformulated)
            current_query = chain.current_query
            
            # Retrieve
            results = await self.retriever.retrieve(current_query, top_k=5)
            
            # Analyze results
            analysis = await self._analyze_results(results, query)
            
            # Check if we have enough information
            if analysis.is_sufficient:
                chain.finalize(results)
                break
            
            # Generate sub-query for next hop
            sub_query = await self._generate_subquery(
                original_query=query,
                current_results=results,
                analysis=analysis
            )
            
            # Add to chain
            chain.add_hop(
                query=current_query,
                results=results,
                sub_query=sub_query,
                reasoning=analysis.reasoning
            )
            
        return chain.to_result()
        
    async def _analyze_results(self, results, original_query) -> Analysis:
        """Analyze if current results are sufficient."""
        prompt = f"""
        Original question: {original_query}
        Retrieved information: {results}
        
        Is this information sufficient to answer the question?
        If not, what additional information is needed?
        
        Respond with:
        - Sufficient: yes/no
        - Missing: <what's missing>
        - Reasoning: <your thought process>
        """
        
        response = await self.llm.generate(prompt)
        return Analysis.from_llm_response(response)
        
    async def _generate_subquery(
        self, 
        original_query: str,
        current_results: List[Chunk],
        analysis: Analysis
    ) -> str:
        """Generate focused sub-query for next retrieval hop."""
        prompt = f"""
        We're trying to answer: {original_query}
        
        So far we found: {current_results}
        But we're missing: {analysis.missing}
        
        Generate a focused search query to find the missing information.
        Query:
        """
        
        sub_query = await self.llm.generate(prompt)
        return sub_query.strip()
```

**Example Chain:**
```
Original Query: "How does RAGEngine integrate with the cognitive layer?"

Hop 1:
  Query: "How does RAGEngine integrate with the cognitive layer?"
  Retrieved: RAGEngine documentation (general)
  Analysis: Found RAGEngine, but missing cognitive layer details
  Sub-query: "What is the cognitive layer architecture in GRID?"

Hop 2:
  Query: "What is the cognitive layer architecture in GRID?"
  Retrieved: Cognitive layer documentation
  Analysis: Found cognitive layer, but missing integration point
  Sub-query: "How do RAG and cognitive systems connect in GRID?"

Hop 3:
  Query: "How do RAG and cognitive systems connect in GRID?"
  Retrieved: Integration documentation
  Analysis: Sufficient! Found connection points.
  Finalize: All information gathered

Final Answer: Synthesized from all 3 hops
```

**Training (Optional):**
- Use rejection sampling to generate training data
- Positive examples: Chains that lead to correct answers
- Negative examples: Chains that don't help
- Fine-tune LLM to generate better sub-queries

---

### 5. Hierarchical Indexing

**Purpose:** Multi-granularity retrieval (document → section → chunk → sentence)

**Architecture:**
```python
class HierarchicalIndex:
    """
    Multi-level index for coarse-to-fine retrieval.
    
    Levels:
    1. Document (file-level metadata)
    2. Section (headings, classes, functions)
    3. Chunk (semantic segments)
    4. Sentence (fine-grained extraction)
    """
    
    def __init__(self):
        self.document_index = DocumentIndex()  # Fast filtering
        self.section_index = SectionIndex()    # Medium granularity
        self.chunk_index = ChunkIndex()        # Main retrieval
        self.sentence_index = SentenceIndex()  # Evidence extraction
        
    async def hierarchical_retrieve(
        self, 
        query: str,
        top_k: int = 5
    ) -> HierarchicalResults:
        """
        Retrieve at multiple granularities.
        
        Strategy: Funnel from coarse to fine.
        """
        # Level 1: Document filtering (fast, broad)
        relevant_docs = await self.document_index.filter(query, top_k=50)
        
        # Level 2: Section matching (medium)
        relevant_sections = await self.section_index.match(
            query, 
            within_docs=relevant_docs,
            top_k=20
        )
        
        # Level 3: Chunk scoring (main retrieval)
        relevant_chunks = await self.chunk_index.score(
            query,
            within_sections=relevant_sections,
            top_k=top_k
        )
        
        # Level 4: Sentence extraction (evidence)
        evidence_sentences = await self.sentence_index.extract(
            query,
            within_chunks=relevant_chunks,
            top_k=top_k * 3  # More sentences than chunks
        )
        
        return HierarchicalResults(
            documents=relevant_docs[:top_k],
            sections=relevant_sections[:top_k],
            chunks=relevant_chunks,
            sentences=evidence_sentences
        )
```

**Index Structure:**
```
Document Level:
  doc_id: "rag_engine.py"
  metadata: {type: "code", language: "python", lines: 500}
  summary_embedding: [768-dim vector]
  
Section Level:
  section_id: "rag_engine.py::RAGEngine"
  parent_doc: "rag_engine.py"
  metadata: {type: "class", start_line: 32, end_line: 400}
  heading_embedding: [768-dim vector]
  
Chunk Level:
  chunk_id: "chunk_001"
  parent_section: "rag_engine.py::RAGEngine"
  text: "The RAGEngine orchestrates..."
  embedding: [768-dim vector] or [128-dim x tokens]
  
Sentence Level:
  sentence_id: "sent_001"
  parent_chunk: "chunk_001"
  text: "RAGEngine orchestrates embedding, retrieval, and generation."
  embedding: [768-dim vector]
```

**Benefits:**
- **Speed:** Document-level filtering reduces search space
- **Precision:** Fine-grained matching at chunk/sentence level
- **Context:** Can retrieve parent sections for additional context
- **Flexibility:** Can adjust granularity based on query complexity

---

## Implementation Roadmap

### Phase 4.1: Adaptive Chunking (Weeks 1-2)
- [ ] Implement content-type detection
- [ ] Build chunking strategies (semantic, fixed, hierarchical, cell-aware)
- [ ] Add chunk quality scoring (Boundary Clarity + Stickiness)
- [ ] Benchmark: Compare adaptive vs fixed-size on test corpus
- [ ] Integration: Replace current fixed-size chunker in indexer

### Phase 4.2: Multi-Vector Embeddings (Weeks 3-4)
- [ ] Integrate Jina-ColBERT-v2 model
- [ ] Implement late interaction scoring
- [ ] Build specialized index for multi-vector retrieval
- [ ] Benchmark: Compare single-vector vs multi-vector accuracy
- [ ] Hybrid strategy: Use for reranking only (not initial retrieval)

### Phase 4.3: Conversational Context (Weeks 5-6)
- [ ] Build ConversationalContextManager
- [ ] Implement sliding window + summarization buffer
- [ ] Add intent transition tracking
- [ ] Query reconstruction logic
- [ ] Integration: Add conversation_id to query API

### Phase 4.4: Chain-of-Retrieval (Weeks 7-8)
- [ ] Implement ChainOfRetrievalEngine
- [ ] Add query analysis and sub-query generation
- [ ] Multiple decoding strategies (greedy, best-of-n, tree)
- [ ] Benchmark: Test on multi-hop question datasets
- [ ] Optional: Fine-tune LLM for better sub-queries

### Phase 4.5: Hierarchical Indexing (Weeks 9-10)
- [ ] Build HierarchicalIndex with 4 levels
- [ ] Document/section/chunk/sentence indices
- [ ] Implement coarse-to-fine retrieval
- [ ] Benchmark: Compare flat vs hierarchical retrieval
- [ ] Integration: Make hierarchical retrieval opt-in via config

### Phase 4.6: Integration & Testing (Weeks 11-12)
- [ ] Integrate all components into RAGEngine
- [ ] Configuration flags for each feature
- [ ] Comprehensive testing
- [ ] Performance benchmarks
- [ ] Documentation updates

---

## Configuration Design

```python
@dataclass
class Phase4Config:
    """Phase 4 feature flags and settings."""
    
    # Adaptive Chunking
    use_adaptive_chunking: bool = True
    min_chunk_quality: float = 0.6  # Filter low-quality chunks
    
    # Multi-Vector Embeddings
    use_multi_vector: bool = True  # For reranking only
    multi_vector_model: str = "jinaai/jina-colbert-v2"
    late_interaction_top_k: int = 20  # How many to rerank
    
    # Conversational Context
    enable_conversation: bool = True
    sliding_window_size: int = 5  # Last N turns
    summarization_threshold: int = 10  # When to start summarizing
    
    # Chain-of-Retrieval
    enable_corag: bool = False  # Opt-in (expensive)
    corag_max_hops: int = 3
    corag_decoding: str = "greedy"  # greedy | best_of_n | tree
    
    # Hierarchical Indexing
    use_hierarchical: bool = True
    hierarchical_levels: List[str] = field(
        default_factory=lambda: ["document", "section", "chunk"]
    )
```

**Environment Variables:**
```bash
# Adaptive Chunking
export RAG_USE_ADAPTIVE_CHUNKING=true
export RAG_MIN_CHUNK_QUALITY=0.6

# Multi-Vector
export RAG_USE_MULTI_VECTOR=true
export RAG_MULTI_VECTOR_MODEL=jinaai/jina-colbert-v2

# Conversational
export RAG_ENABLE_CONVERSATION=true
export RAG_SLIDING_WINDOW_SIZE=5

# CoRAG
export RAG_ENABLE_CORAG=false  # Expensive!
export RAG_CORAG_MAX_HOPS=3

# Hierarchical
export RAG_USE_HIERARCHICAL=true
```

---

## Benchmarking & Evaluation

### Datasets for Testing
1. **Chunking Quality:**
   - GRID codebase (Python, diverse content types)
   - Technical documentation (mixed prose/code/tables)
   - Metric: Boundary Clarity, Chunk Stickiness

2. **Multi-Vector Retrieval:**
   - MS MARCO (standard IR benchmark)
   - BEIR (out-of-domain retrieval)
   - Metric: nDCG@10, Recall@100

3. **Conversational RAG:**
   - CORAL benchmark (NAACL 2025)
   - MTRAG dataset (multi-turn)
   - Metric: Turn-level accuracy, context retention

4. **Chain-of-Retrieval:**
   - HotpotQA (multi-hop questions)
   - 2WikiMultihopQA
   - Metric: Exact Match, F1 score

5. **Hierarchical Retrieval:**
   - Custom GRID corpus
   - Metric: Retrieval speed, precision@k

### Baseline Comparisons
| Method | Chunking | Embedding | Retrieval | Speed | Accuracy |
|--------|----------|-----------|-----------|-------|----------|
| **Current (Phase 3)** | Fixed-size | Single-vector | 3-stage | 0.6s | 85% |
| **Phase 4 Basic** | Adaptive | Single-vector | 3-stage + Hierarchical | 0.7s | 88% |
| **Phase 4 Full** | Adaptive | Multi-vector | CoRAG + Hierarchical | 1.2s | 92% |

---

## Tradeoffs & Decisions

### What to Include

✅ **Adaptive Chunking** - Low overhead, clear benefits  
✅ **Hierarchical Indexing** - Speed + precision gains  
✅ **Conversational Context** - Essential for real-world use  
✅ **Multi-Vector (for reranking)** - Good accuracy boost  

### What to Make Optional

⚠️ **Chain-of-Retrieval (CoRAG)** - Expensive, opt-in for complex queries  
⚠️ **Multi-Vector (for initial retrieval)** - Storage/speed tradeoff  

### What to Defer

❌ **Full ColBERT Index** - Requires PLAID indexing infrastructure (defer to Phase 5)  
❌ **LLM Fine-tuning for CoRAG** - Training pipeline overhead  
❌ **Knowledge Graph Integration** - CID-GraphRAG is complex (Phase 5+)  

---

## Success Metrics

### Performance Targets
- **Accuracy:** +5-10% over Phase 3 on complex queries
- **Latency:** <1.5s for Phase 4 Full (acceptable for quality gain)
- **Chunking Quality:** >0.75 average quality score
- **Conversation:** >80% query reconstruction accuracy

### Quality Indicators
- Fewer hallucinations (chunk filtering)
- Better multi-hop QA performance (CoRAG)
- Improved conversational coherence
- Higher user satisfaction (subjective)

---

## Dependencies

### New Libraries
```bash
pip install jina-colbert-v2      # Multi-vector embeddings
pip install sentence-transformers # Already installed
pip install transformers          # Already installed
pip install nltk                  # Sentence splitting
pip install spacy                 # Content-type detection
```

### Models
- `jinaai/jina-colbert-v2` (~500MB) - Multi-vector embeddings
- `en_core_web_sm` (spaCy) - Content analysis

### Infrastructure
- ChromaDB: Supports multi-vector (with custom distance function)
- Ollama: Existing, for LLM-based sub-query generation

---

## Documentation Plan

### Files to Create
1. `PHASE4_COMPLETE.md` - Completion summary
2. `README_PHASE4.md` - User guide
3. `QUICKSTART_PHASE4.md` - Getting started
4. `BENCHMARKS_PHASE4.md` - Performance results

### Code Documentation
- Docstrings for all new classes
- Architecture diagrams
- Example usage snippets
- Configuration examples

---

## Risk Assessment

### Technical Risks
1. **Multi-Vector Storage:** 10x storage increase
   - Mitigation: Compression (768D → 128D), selective use
   
2. **CoRAG Latency:** 3x slower for
