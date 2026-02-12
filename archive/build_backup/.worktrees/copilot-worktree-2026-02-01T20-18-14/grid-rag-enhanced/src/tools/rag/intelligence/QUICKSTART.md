# Phase 3: Intelligent RAG - Quick Start Guide

**Ready to see the reasoning layer in action?** Follow these steps!

---

## Prerequisites

1. **Python 3.11+** installed
2. **Ollama** running locally (`ollama serve`)
3. **Dependencies** installed:
   ```bash
   pip install sentence-transformers transformers torch chromadb
   ```

---

## Step 1: Index Your Repository (2 minutes)

```bash
# Index the GRID project itself
cd grid
python -m tools.rag.cli index . --rebuild

# Or index a specific directory
python -m tools.rag.cli index ./docs
```

**Expected output:**
```
Indexing repository at: . (mode: rebuild)
✓ RAG engine ready
Processing files: 100%|████████████| 150/150 [00:45<00:00]
✓ Indexed 150 files, 1,234 chunks
```

---

## Step 2: Try Your First Intelligent Query (30 seconds)

```bash
python -m tools.rag.cli intelligent-query "What is the GRID architecture?"
```

**You'll see:**
- 📝 **Answer** with full explanation
- 🟢 **Confidence score** (e.g., 88%)
- 📚 **Citations** with file paths and line numbers
- **No reasoning shown yet** (add `--show-reasoning` for that)

---

## Step 3: Enable Reasoning Visualization (1 minute)

```bash
python -m tools.rag.cli intelligent-query "What is the GRID architecture?" \
    --show-reasoning \
    --show-metrics
```

**Now you'll see the full pipeline:**

```
🧠 Intelligent RAG Query: What is the GRID architecture?
════════════════════════════════════════════════════════════════════

📝 ANSWER
────────────────────────────────────────────────────────────────────
GRID is a Python-based framework for exploring complex systems through
geometric resonance patterns. The architecture follows a layered approach
with core, API, database, CLI, and services layers.

🟢 Confidence: 88%

📚 SOURCES
────────────────────────────────────────────────────────────────────
1. [docs/README.md:1]
2. [docs/ARCHITECTURE.md:10]
3. [grid/core/engine.py:32]

🧠 REASONING CHAIN
────────────────────────────────────────────────────────────────────

Total steps: 4
Is confident: True
Has gaps: False

👁️ Step 1: [OBSERVATION] (confidence: 90%)
   I found 5 highly relevant evidence pieces from 3 source files.
   → Supported by 5 evidence piece(s)

🧠 Step 2: [INFERENCE] (confidence: 90%)
   Based on the definition in docs/README.md, I can establish the core concept.
   → Supported by 1 evidence piece(s)

🔗 Step 3: [SYNTHESIS] (confidence: 85%)
   Synthesizing information from 3 sources (README.md, ARCHITECTURE.md, engine.py).
   The information appears consistent.
   → Supported by 3 evidence piece(s)

💡 Step 4: [CONCLUSION] (confidence: 88%)
   Conclusion: Based on 5 pieces of evidence, I can answer the query.
   → Supported by 5 evidence piece(s)

📊 PIPELINE METRICS
────────────────────────────────────────────────────────────────────

⏱️  Timing:
  • understanding        : 0.045s
  • retrieval            : 0.312s
  • extraction           : 0.089s
  • reasoning            : 0.023s
  • synthesis            : 0.156s
  • total                : 0.625s

🔄 Pipeline:
  • intent               : definition
  • intent_confidence    : 92%
  • chunks_retrieved     : 6
  • evidence_extracted   : 8
  • strong_evidence      : 5
  • reasoning_steps      : 4
  • final_confidence     : 88%

✨ Quality:
  • contradictions       : False
  • knowledge_gaps       : False
  • evidence_coverage    : 88%
```

**Amazing, right?** The system shows its complete thought process!

---

## Step 4: Compare Standard vs Intelligent RAG (2 minutes)

```bash
python -m tools.rag.intelligence.test_phase3 --compare
```

**You'll see side-by-side comparison:**
- **Standard RAG:** Simple concatenation of chunks
- **Intelligent RAG:** Structured reasoning with evidence

**Spoiler:** Intelligent RAG wins on clarity, confidence, and citations!

---

## Step 5: Run the Test Suite (5 minutes)

```bash
python -m tools.rag.intelligence.test_phase3 --suite
```

**This runs 4 test queries:**
1. Definition query (What is GRID?)
2. Implementation query (How does X work?)
3. Location query (Where is Y defined?)
4. List query (What are the patterns?)

**You'll get a summary:**
```
TEST SUITE SUMMARY
════════════════════════════════════════════════════════════════════

Tests Passed: 4/4
Average Confidence: 85%

Results:
  ✓ Test 1: (88%)
  ✓ Test 2: (82%)
  ✓ Test 3: (79%)
  ✓ Test 4: (91%)
```

---

## Common Queries to Try

### Architecture Questions
```bash
python -m tools.rag.cli intelligent-query "What is the GRID architecture strategy?"
python -m tools.rag.cli intelligent-query "How does the layered architecture work?"
```

### Implementation Questions
```bash
python -m tools.rag.cli intelligent-query "How does RAGEngine handle retrieval?"
python -m tools.rag.cli intelligent-query "Show me the embedding provider implementation"
```

### Location Questions
```bash
python -m tools.rag.cli intelligent-query "Where is the cognitive layer defined?"
python -m tools.rag.cli intelligent-query "Find the LLM provider code"
```

### Comparison Questions
```bash
python -m tools.rag.cli intelligent-query "What's the difference between hybrid and vector search?"
```

---

## Understanding the Output

### Confidence Levels
- 🟢 **70-100%:** High confidence, strong evidence
- 🟡 **50-69%:** Medium confidence, moderate evidence
- 🔴 **0-49%:** Low confidence, weak or contradictory evidence

### Reasoning Step Types
- 👁️ **OBSERVATION:** What evidence was found
- 🧠 **INFERENCE:** What we deduce from evidence
- 🔗 **SYNTHESIS:** Combining multiple sources
- ✓ **VALIDATION:** Checking consistency
- 💡 **CONCLUSION:** Final answer
- ❓ **UNCERTAINTY:** Knowledge gaps acknowledged

### Citations Format
- `[file.py:123]` - Source file with starting line number
- `[docs/README.md]` - Source file (no line number available)

---

## Python API Usage

### Basic Query
```python
from tools.rag.rag_engine import RAGEngine
from tools.rag.config import RAGConfig

config = RAGConfig.from_env()
config.use_intelligent_rag = True
engine = RAGEngine(config=config)

result = await engine.intelligent_query("What is GRID?")
print(result["answer"])
```

### With Reasoning
```python
result = await engine.intelligent_query(
    query_text="What is GRID?",
    include_reasoning=True,
    include_metrics=True
)

# Access reasoning chain
for step in result["reasoning"]["steps"]:
    print(f"{step['step']}. {step['type']}: {step['content']}")

# Access metrics
print(result["metrics"]["timing"]["total"])
```

### Synchronous Version
```python
result = engine.intelligent_query_sync(
    query_text="What is GRID?",
    include_reasoning=True
)
```

---

## Configuration

### Enable/Disable Intelligent RAG

**Environment Variable:**
```bash
export RAG_USE_INTELLIGENT_RAG=true  # Enable
export RAG_USE_INTELLIGENT_RAG=false # Disable (fallback to standard RAG)
```

**Python Code:**
```python
config = RAGConfig.from_env()
config.use_intelligent_rag = True  # Enable
```

### Adjust Performance

**Speed up queries (sacrifice some accuracy):**
```bash
export RAG_USE_RERANKER=false        # Skip cross-encoder reranking
export RAG_MULTI_HOP_ENABLED=false   # Skip multi-hop expansion
```

**Increase accuracy (slower):**
```bash
export RAG_USE_RERANKER=true
export RAG_MULTI_HOP_ENABLED=true
export RAG_MULTI_HOP_MAX_DEPTH=3
export RAG_RERANKER_TOP_K=30         # Rerank more candidates
```

---

## Troubleshooting

### "No documents in the knowledge base"
**Fix:** Index first!
```bash
python -m tools.rag.cli index .
```

### "Intelligent RAG orchestrator not initialized"
**Fix:** Enable it in config
```bash
export RAG_USE_INTELLIGENT_RAG=true
```

### Slow performance
**Fix:** Reduce reranking candidates
```bash
export RAG_RERANKER_TOP_K=10  # Default is 20
export RAG_TOP_K=5             # Default is 10
```

### Low confidence scores
**Causes:**
- Query phrasing doesn't match codebase terminology
- Missing content in knowledge base
- Insufficient indexed documents

**Fixes:**
- Rephrase query to match project terms
- Index more comprehensive documentation
- Use `--show-reasoning` to see which evidence is weak

---

## What Next?

### Learn More
- Read `README_PHASE3.md` for full documentation
- Check `PHASE3_COMPLETE.md` for architecture details
- Review code examples in each module's `__main__` block

### Experiment
- Try edge cases (questions the system can't answer)
- Test with your own codebase
- Compare confidence scores across different query types

### Integrate
- Add intelligent queries to your CLI tools
- Build a web interface using the API
- Create custom reasoning step types

---

## Key Takeaways

✅ **Transparent:** See every reasoning step  
✅ **Trustworthy:** Every claim has citations  
✅ **Confident:** Know when the system is uncertain  
✅ **Fast:** ~0.5-1.5s per query  
✅ **Local:** No external APIs, full privacy  

---

**You're ready to explore intelligent RAG!** 🚀

```bash
# Start exploring!
python -m tools.rag.cli intelligent-query "your question here" --show-reasoning
```

**Questions?** Check `README_PHASE3.md` or run:
```bash
python -m tools.rag.cli intelligent-query --help
```

---

**Happy Reasoning!** 🧠✨
