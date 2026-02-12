# How the System Handles Unsatisfying First Results

## Decision Flow Diagram

```
User Query
    |
    v
Generate Embeddings/Keywords
    |
    v
Search Vector Store / Keyword Index
    |
    v
Calculate Similarity Scores
    |
    +---> ALL scores < min_score?
    |     |
    |     YES --> Return Empty Results
    |     |        - RAG: "No relevant documents found"
    |     |        - Semantic Grep: Empty matches list
    |     |
    |     NO --> Filter by threshold
    |            |
    |            v
    |     Sort by Score (highest first)
    |            |
    |            v
    |     Take top_k results
    |            |
    |            +---> First result score < min_score?
    |            |     |
    |            |     YES --> SKIP first, use next result
    |            |     |
    |            |     NO --> Process in score order
    |            |            |
    |            |            v
    |            |     Generate Instructions
    |            |            |
    |            |            +---> Multiple matches?
    |            |            |     |
    |            |            |     YES --> Add cross-check instruction
    |            |            |            "Cross-check similar matches for conflicts;
    |            |            |             prefer the most recent or most authoritative reference"
    |            |            |
    |            |            +---> Query type detection
    |            |                  |
    |            |                  +---> Bug fix keywords?
    |            |                  |     --> Add: "Locate error messages / stack traces"
    |            |                  |
    |            |                  +---> Implementation keywords?
    |            |                        --> Add: "Derive an interface from the matches"
    |            |
    |            v
    |     Return Results + Instructions
    |
    v
Process Results (following instructions)
    |
    v
Cross-check if multiple matches
    |
    v
Prefer authoritative/recent sources
```

## Key Code Locations

### 1. Threshold Filtering
**File**: `datakit/tool/semantic_grep.py`, lines 193-195
```python
for i in idxs.tolist():
    score = float(scored[i])
    if score < min_score:  # ← Filter happens HERE
        continue  # Skip this result entirely
```

### 2. Score Ordering
**File**: `datakit/tool/semantic_grep.py`, line 191
```python
idxs = np.argsort(-scored)[:max(0, top_k)]  # ← Sort by score, highest first
```

### 3. Cross-Checking Instruction
**File**: `datakit/tool/semantic_grep.py`, lines 150-153
```python
if top_chunks:  # ← Only if matches exist
    instructions.append(
        "Cross-check similar matches for conflicts; "
        "prefer the most recent or most authoritative reference."
    )
```

### 4. RAG Engine Fallback
**File**: `tools/rag/rag_engine.py`, lines 188-189
```python
if not results["documents"]:
    return {"answer": "No relevant documents found...", "sources": [], "context": ""}
```

## Practical Example: What Happens Step-by-Step

### Scenario: Query "database connection" with min_score=0.15

**Step 1: Search & Score**
- Finds 8 documents with scores: [0.85, 0.45, 0.32, 0.25, 0.18, 0.12, 0.10, 0.08]

**Step 2: Filter by Threshold**
- Scores < 0.15 are removed: [0.85, 0.45, 0.32, 0.25, 0.18]
- First result: score=0.85 ✓ (above threshold)
- Last result: score=0.12 ✗ (below threshold, skipped)

**Step 3: Generate Instructions**
```python
instructions = [
    "Identify the relevant files and sections from the top matches.",
    "Read the matched line ranges in order of score; extract definitions...",
    "Cross-check similar matches for conflicts; prefer the most recent...",  # ← Added because matches exist
    "Summarize findings into a structured output..."
]
```

**Step 4: Process Results**
- Process result 1 (score=0.85) - highest relevance
- Process result 2 (score=0.45) - cross-check for conflicts
- Process result 3 (score=0.32) - verify consistency
- ... continue through all remaining results

### Scenario: First Result Below Threshold

**Step 1: Search & Score**
- Finds 5 documents with scores: [0.12, 0.45, 0.32, 0.25, 0.18]
- min_score = 0.15

**Step 2: Filter by Threshold**
- First result (0.12) < 0.15 → **SKIPPED**
- Remaining: [0.45, 0.32, 0.25, 0.18] (all above threshold)

**Step 3: Process**
- What was originally result #2 (score=0.45) becomes the effective "first" result
- System processes all remaining results in score order

## Instructions Generated for Different Scenarios

### Scenario A: High-Quality First Result, Multiple Matches
```python
Query: "implement database connection"
Matches: [score: 0.85, 0.72, 0.65, ...]
Instructions:
  1. Identify the relevant files and sections from the top matches
  2. Read the matched line ranges in order of score
  3. Derive an interface from the matches (inputs/outputs)
  4. Cross-check similar matches for conflicts  ← Added
  5. Summarize findings into structured output
```

### Scenario B: First Result Below Threshold
```python
Query: "obscure feature"
Matches: [score: 0.08, 0.25, 0.18, ...]
min_score: 0.15
Result:
  - First match (0.08) is SKIPPED (below threshold)
  - Processing starts with second match (0.25)
  - Instructions generated normally for remaining matches
```

### Scenario C: No Results Above Threshold
```python
Query: "completely unrelated topic"
Matches: [score: 0.05, 0.03, 0.02, ...]
min_score: 0.15
Result:
  - All matches below threshold
  - Returns empty matches list
  - Instructions still generated (but no matches to process)
  - RAG Engine: "No relevant documents found in the knowledge base"
```

## Key Takeaways

1. **Threshold is applied BEFORE processing** - Low-scoring first results are filtered out automatically

2. **Multiple results are always considered** - The instruction explicitly says "in order of score", not "use first result"

3. **Cross-checking is automatic** - When multiple matches exist, the system automatically generates cross-checking instructions

4. **Explicit fallback for no results** - Both RAG and Semantic Grep explicitly acknowledge when no good matches exist, rather than using poor matches

5. **Query-type aware** - Instructions adapt based on query keywords (bug fix vs implementation)

## How to Use This Information

When the first result doesn't satisfy:

1. **Check the score** - If it's below your min_score threshold, it should already be filtered out
2. **Lower the threshold** - If needed, reduce min_score to see more candidate results
3. **Review all top_k results** - Don't stop at the first; process all in score order
4. **Cross-check matches** - If multiple results exist, compare them for conflicts
5. **Prefer authoritative sources** - When cross-checking, favor canonical docs or recent sources
6. **Acknowledge uncertainty** - If no good matches exist, return explicit "no results" rather than hallucinating
