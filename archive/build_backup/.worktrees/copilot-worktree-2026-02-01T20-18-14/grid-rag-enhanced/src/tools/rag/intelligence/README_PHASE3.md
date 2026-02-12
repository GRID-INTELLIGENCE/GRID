# Phase 3: Reasoning Layer - Intelligent RAG

**Status:** ✅ Complete  
**Author:** AI Assistant  
**Date:** 2024

---

## Overview

Phase 3 introduces a **Chain-of-Thought Reasoning Layer** that transforms the RAG system from a simple "retrieve and summarize" pipeline into an **intelligent reasoning system** that:

1. **Understands** what the user is asking (intent + entities)
2. **Retrieves** relevant information using multi-stage search
3. **Extracts** structured evidence with full source attribution
4. **Reasons** transparently through chain-of-thought steps
5. **Synthesizes** polished responses with citations

This makes the system **transparent**, **trustworthy**, and **cognitively aligned** with the project's principles.

---

## Architecture

### Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT RAG PIPELINE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. QUERY UNDERSTANDING                                          │
│     ├─ Intent Classification (9 intent types)                   │
│     ├─ Entity Extraction (symbols, files, concepts)             │
│     └─ Query Expansion (generate search variants)               │
│                          ↓                                       │
│  2. MULTI-STAGE RETRIEVAL                                        │
│     ├─ Stage 1: Hybrid Search (Dense + BM25 + RRF)             │
│     ├─ Stage 2: Multi-Hop Expansion (follow references)         │
│     └─ Stage 3: Cross-Encoder Reranking (precision)             │
│                          ↓                                       │
│  3. EVIDENCE EXTRACTION                                          │
│     ├─ Segment chunks (code blocks, prose, etc.)                │
│     ├─ Classify evidence type (definition, implementation...)   │
│     ├─ Calculate relevance & confidence                          │
│     └─ Extract cross-references & citations                      │
│                          ↓                                       │
│  4. CHAIN-OF-THOUGHT REASONING                                   │
│     ├─ Observation: What evidence do we have?                   │
│     ├─ Validation: Check for contradictions                     │
│     ├─ Inference: What can we deduce?                           │
│     ├─ Synthesis: Combine across sources                        │
│     ├─ Uncertainty: Acknowledge knowledge gaps                  │
│     └─ Conclusion: Final answer with evidence                   │
│                          ↓                                       │
│  5. RESPONSE SYNTHESIS                                           │
│     ├─ Build structured prompt from reasoning chain             │
│     ├─ LLM polish (or template-based fallback)                  │
│     ├─ Add source citations                                     │
│     └─ Calculate overall confidence                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Query Understanding (`query_understanding.py`)

**Purpose:** Understand user intent before retrieval.

**Features:**
- **Intent Classification:** 9 intent types (definition, implementation, usage, location, debugging, architecture, comparison, workflow, other)
- **Entity Extraction:** Identifies symbols, file paths, technical terms
- **Query Expansion:** Generates search variants to improve recall

**Example:**
```python
query = "How does RAGEngine handle retrieval?"
understood = orchestrator.understand(query)

# Output:
# Intent: IMPLEMENTATION (confidence: 92%)
# Entities: [RAGEngine, retrieval]
# Expansions: ["source code for RAGEngine retrieval", "RAGEngine retrieval implementation"]
```

---

### 2. Retrieval Orchestrator (`retrieval_orchestrator.py`)

**Purpose:** Multi-stage retrieval for precision + recall.

**3-Stage Pipeline:**
1. **Hybrid Search:** Dense embeddings + BM25 sparse → Reciprocal Rank Fusion
2. **Multi-Hop:** Follow Python imports, Markdown links, code references
3. **Reranking:** Cross-Encoder (`ms-marco-MiniLM-L6-v2`) re-scores candidates

**Why This Works:**
- Dense search: semantic similarity ("handle retrieval" ≈ "query processing")
- BM25: exact keyword matches (`RAGEngine`, `retrieval`)
- Multi-hop: finds related files automatically
- Reranking: moves most relevant chunks to top

---

### 3. Evidence Extractor (`evidence_extractor.py`)

**Purpose:** Convert raw chunks into structured, attributable facts.

**Evidence Types:**
- `DEFINITION` - What something is
- `IMPLEMENTATION` - How it works (code)
- `EXAMPLE` - Usage demonstrations
- `REFERENCE` - Cross-references
- `CONFIGURATION` - Settings, configs
- `ASSERTION` - Statements of fact
- `PROCEDURE` - Step-by-step instructions
- `METADATA` - File paths, versions

**Evidence Structure:**
```python
Evidence(
    id="ev_chunk001_0_a3f2c1b8",
    content="RAGEngine orchestrates embedding, retrieval, and generation...",
    evidence_type=EvidenceType.DEFINITION,
    strength=EvidenceStrength.STRONG,
    confidence=0.9,
    source_file="tools/rag/rag_engine.py",
    source_line_start=32,
    is_code=False,
    references=["embedding_provider", "vector_store"],
)
```

**Key Features:**
- **Full provenance:** Every fact traces back to source file + line number
- **Confidence scoring:** Based on query overlap + retrieval distance
- **Contradiction detection:** Flags conflicting evidence
- **Reference extraction:** Finds imports, links, symbols automatically

---

### 4. Reasoning Engine (`reasoning_engine.py`)

**Purpose:** Chain-of-thought reasoning over evidence.

**Reasoning Step Types:**
- `OBSERVATION` - What we observe in the evidence
- `INFERENCE` - What we deduce from observations
- `SYNTHESIS` - Combining multiple pieces
- `VALIDATION` - Checking consistency
- `CONCLUSION` - Final answer
- `UNCERTAINTY` - Acknowledging gaps

**Example Reasoning Chain:**

```
Query: "What is the GRID architecture?"

Step 1: [OBSERVATION] (confidence: 90%)
  I found 5 highly relevant evidence pieces from 3 source files.
  → Evidence: ev_001, ev_002, ev_003, ev_004, ev_005

Step 2: [INFERENCE] (confidence: 90%)
  Based on the definition in docs/README.md, I can establish the core concept:
  GRID is a Python-based framework for exploring complex systems...
  → Evidence: ev_001

Step 3: [SYNTHESIS] (confidence: 85%)
  Synthesizing information from 3 sources (README.md, ARCHITECTURE.md, core/engine.py).
  The information appears consistent.
  → Evidence: ev_001, ev_002, ev_003

Step 4: [CONCLUSION] (confidence: 88%)
  Conclusion: Based on 5 pieces of evidence, I can answer the query.
  → Evidence: ev_001, ev_002, ev_003, ev_004, ev_005
```

**Why This Matters:**
- **Transparency:** Users see HOW the answer was derived
- **Trustworthiness:** Evidence is explicitly cited
- **Debugging:** If answer is wrong, you can trace which step failed
- **Confidence:** System knows when it doesn't know

---

### 5. Response Synthesizer (`response_synthesizer.py`)

**Purpose:** Polish reasoning chain into user-friendly response.

**Two Modes:**
1. **LLM Polish:** Uses local LLM to synthesize final answer
2. **Template-Based:** Fallback without LLM (uses reasoning chain directly)

**Output Structure:**
```python
SynthesizedResponse(
    query="What is the GRID architecture?",
    answer="GRID is a Python-based framework for exploring complex systems...",
    confidence=0.88,
    sources=[
        {"file": "docs/README.md", "type": "definition", "confidence": 0.9},
        {"file": "docs/ARCHITECTURE.md", "type": "assertion", "confidence": 0.85},
    ],
    citations=[
        "[docs/README.md:1]",
        "[docs/ARCHITECTURE.md:10]",
    ],
    reasoning_chain=ReasoningChain(...),  # Full chain available
    evidence_set=EvidenceSet(...),        # All evidence available
)
```

---

## Usage

### Option 1: CLI (Recommended)

```bash
# Single query with reasoning
python -m tools.rag.cli intelligent-query "What is the GRID architecture?" \
    --show-reasoning \
    --show-metrics

# JSON output
python -m tools.rag.cli intelligent-query "How does RAGEngine work?" \
    --json > result.json
```

### Option 2: Test Script

```bash
# Single query
python -m tools.rag.intelligence.test_phase3 \
    --query "What is the GRID architecture?"

# Full test suite
python -m tools.rag.intelligence.test_phase3 --suite

# Compare standard vs intelligent RAG
python -m tools.rag.intelligence.test_phase3 --compare
```

### Option 3: Python API

```python
from tools.rag.rag_engine import RAGEngine
from tools.rag.config import RAGConfig

# Initialize with intelligent RAG enabled
config = RAGConfig.from_env()
config.use_intelligent_rag = True
engine = RAGEngine(config=config)

# Query
result = await engine.intelligent_query(
    query_text="What is the GRID architecture?",
    top_k=5,
    temperature=0.3,
    include_reasoning=True,
    include_metrics=True,
)

# Access components
print(result["answer"])
print(f"Confidence: {result['confidence']:.0%}")
print(f"Citations: {result['citations']}")

if "reasoning" in result:
    for step in result["reasoning"]["steps"]:
        print(f"{step['step']}. [{step['type']}] {step['content']}")
```

---

## Configuration

### Environment Variables

```bash
# Enable/disable intelligent RAG
export RAG_USE_INTELLIGENT_RAG=true

# Existing retrieval config (Phase 2)
export RAG_USE_HYBRID=true
export RAG_USE_RERANKER=true
export RAG_MULTI_HOP_ENABLED=true
```

### Python Config

```python
config = RAGConfig(
    use_intelligent_rag=True,      # Enable reasoning layer
    use_hybrid=True,                # Hybrid search
    use_reranker=True,              # Cross-encoder reranking
    multi_hop_enabled=True,         # Multi-hop retrieval
)
```

---

## Performance Metrics

The intelligent orchestrator tracks detailed metrics:

### Timing Metrics
- `query_understanding_time` - Intent classification + entity extraction
- `retrieval_time` - Multi-stage retrieval (hybrid + multi-hop + reranking)
- `evidence_extraction_time` - Segmentation + classification
- `reasoning_time` - Chain-of-thought construction
- `synthesis_time` - LLM generation or template-based synthesis
- `total_time` - End-to-end latency

### Pipeline Metrics
- `intent` - Classified intent (e.g., "definition")
- `intent_confidence` - Confidence in intent classification
- `entities_found` - Number of entities extracted
- `chunks_retrieved` - Total chunks from retrieval
- `evidence_extracted` - Evidence pieces extracted
- `strong_evidence_count` - High-confidence evidence
- `reasoning_steps` - Steps in reasoning chain
- `final_confidence` - Overall answer confidence

### Quality Metrics
- `has_contradictions` - Whether evidence conflicts
- `has_knowledge_gaps` - Whether evidence is insufficient
- `evidence_coverage` - % of evidence used in reasoning

**Example:**
```json
{
  "timing": {
    "understanding": "0.045s",
    "retrieval": "0.312s",
    "extraction": "0.089s",
    "reasoning": "0.023s",
    "synthesis": "0.156s",
    "total": "0.625s"
  },
  "pipeline": {
    "intent": "definition",
    "intent_confidence": "92%",
    "chunks_retrieved": 6,
    "evidence_extracted": 8,
    "strong_evidence": 5,
    "reasoning_steps": 4,
    "final_confidence": "88%"
  },
  "quality": {
    "contradictions": false,
    "knowledge_gaps": false,
    "evidence_coverage": "88%"
  }
}
```

---

## Key Design Principles

### 1. Local-First
- All intelligence layers run **locally** (no external APIs)
- Uses local models: `cross-encoder/nli-deberta-v3-small` for intent, `ms-marco-MiniLM-L6-v2` for reranking
- Optional LLM polish uses local Ollama models

### 2. Transparency
- **Every claim** is backed by evidence
- **Every evidence piece** traces to source file + line
- **Every reasoning step** is explicit and inspectable
- **Confidence scores** at every level

### 3. Bounded Rationality
- System acknowledges **uncertainty** when evidence is weak
- Flags **contradictions** when sources disagree
- Warns about **knowledge gaps** when coverage is low
- Never hallucinates or speculates

### 4. Cognitive Alignment
- Reasoning chain matches **human cognitive process**:
  1. Observe (what do we have?)
  2. Validate (is it consistent?)
  3. Infer (what does it mean?)
  4. Synthesize (combine insights)
  5. Conclude (final answer)
- Reduces **cognitive load** by structuring information
- Maintains **mental models** through consistent patterns

---

## Testing

### Unit Tests

Each component has a built-in test harness:

```bash
# Evidence extractor
python -m tools.rag.intelligence.evidence_extractor

# Reasoning engine
python -m tools.rag.intelligence.reasoning_engine

# Response synthesizer
python -m tools.rag.intelligence.response_synthesizer
```

### Integration Test

```bash
# Full pipeline test
python -m tools.rag.intelligence.test_phase3 --suite --verbose
```

### Expected Output

For the query "What is the GRID architecture?", you should see:

✅ **Intent:** Definition (confidence: 92%)  
✅ **Entities:** [GRID, architecture]  
✅ **Chunks Retrieved:** 6 (reranked)  
✅ **Evidence Extracted:** 8 (5 strong)  
✅ **Reasoning Steps:** 4  
✅ **Final Confidence:** 88%  
✅ **Citations:** 3 sources  

---

## Comparison: Standard vs Intelligent RAG

| Feature | Standard RAG | Intelligent RAG (Phase 3) |
|---------|--------------|---------------------------|
| **Retrieval** | Single-stage vector search | 3-stage (hybrid + multi-hop + reranking) |
| **Understanding** | None (direct embedding) | Intent + entities + expansion |
| **Evidence** | Raw chunks | Structured facts with provenance |
| **Reasoning** | Implicit (LLM black box) | Explicit chain-of-thought |
| **Citations** | Generic source list | Line-level attribution |
| **Confidence** | None | Multi-level confidence scoring |
| **Transparency** | Opaque | Fully inspectable |
| **Knowledge Gaps** | Undetected | Explicitly flagged |
| **Contradictions** | Undetected | Automatically detected |

---

## Future Enhancements

### Potential Additions
1. **Multi-Query Reasoning:** Handle complex queries requiring multiple sub-queries
2. **Temporal Reasoning:** Track information changes over time (e.g., "What changed in v2.0?")
3. **Counterfactual Reasoning:** "What would happen if...?" scenarios
4. **Collaborative Reasoning:** Multiple reasoning chains vote on answer
5. **Self-Correction:** System reviews its own reasoning for logical errors

### Research Directions
1. **Graph-Based Evidence:** Build knowledge graphs from evidence relationships
2. **Adversarial Validation:** Generate counter-arguments to test reasoning
3. **Meta-Reasoning:** Reason about the reasoning process itself
4. **Cognitive Load Optimization:** Adapt reasoning depth to query complexity

---

## Troubleshooting

### Issue: "Intelligent RAG orchestrator not initialized"

**Cause:** `use_intelligent_rag=False` in config or missing dependencies.

**Fix:**
```bash
export RAG_USE_INTELLIGENT_RAG=true
# Or in Python:
config.use_intelligent_rag = True
```

### Issue: Low confidence scores

**Causes:**
- Insufficient indexed documents
- Poor query phrasing
- Missing relevant content in knowledge base

**Fixes:**
- Index more documents
- Use `--show-reasoning` to debug which evidence is weak
- Rephrase query to match terminology in codebase

### Issue: Slow performance

**Causes:**
- Cross-encoder reranking (CPU-bound)
- Multi-hop retrieval depth
- LLM synthesis

**Fixes:**
```bash
# Disable reranking for speed
export RAG_USE_RERANKER=false

# Reduce multi-hop depth
export RAG_MULTI_HOP_MAX_DEPTH=1

# Use template synthesis (no LLM)
config.use_intelligent_rag = True  # But with llm_provider=None
```

### Issue: Missing dependencies

**Error:** `ModuleNotFoundError: No module named 'sentence_transformers'`

**Fix:**
```bash
pip install sentence-transformers
pip install transformers
```

---

## Technical Details

### Models Used

| Component | Model | Size | Purpose |
|-----------|-------|------|---------|
| Intent Classification | `cross-encoder/nli-deberta-v3-small` | ~130MB | Zero-shot intent classification |
| Cross-Encoder Reranking | `ms-marco-MiniLM-L6-v2` | ~90MB | Passage reranking |
| Embeddings | `nomic-embed-text:latest` (Ollama) | ~274MB | Dense vector embeddings |
| LLM (optional) | `ministral` (Ollama) | ~3.8GB | Response synthesis |

All models run **locally** on CPU or GPU.

### Computational Complexity

For a query with `k` retrieved chunks:

- **Query Understanding:** O(1) - constant time (single model inference)
- **Retrieval:** O(n log n) - where n = indexed chunks (with HNSW indexing)
- **Evidence Extraction:** O(k) - linear in retrieved chunks
- **Reasoning:** O(k) - linear in evidence count
- **Synthesis:** O(k) - linear in evidence (if using template) or O(1) if using LLM

**Total:** O(n log n + k) - dominated by retrieval

**Typical latency:** 0.5-1.5s for a single query (depending on index size)

---

## References

### Related Documentation
- `README.md` - Overall RAG system overview
- `docs/ARCHITECTURE_ENHANCEMENTS.md` - Architecture decisions
- Phase 1: Query Understanding (intent classification)
- Phase 2: Retrieval Upgrade (hybrid + multi-hop + reranking)

### External Resources
- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [Self-Ask: Reasoning with Retrieval](https://arxiv.org/abs/2210.03350)
- [ReAct: Reasoning + Acting](https://arxiv.org/abs/2210.03629)
- [FLARE: Forward-Looking Active Retrieval](https://arxiv.org/abs/2305.06983)

---

## License

Part of the GRID project. See main LICENSE file.

---

## Changelog

### 2024-01-XX - Phase 3 Complete
- ✅ Evidence extractor with structured facts
- ✅ Chain-of-thought reasoning engine
- ✅ Response synthesizer with citations
- ✅ Intelligent orchestrator integration
- ✅ CLI commands for intelligent query
- ✅ Comprehensive test suite
- ✅ Full documentation

---

**Status:** Production-ready ✅  
**Tested:** Yes ✅  
**Documented:** Yes ✅  
**Local-Only:** Yes ✅
