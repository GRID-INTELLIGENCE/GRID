# Skills + RAG Quickstart

This guide covers the "skills" runner (`grid skills ...`) and the local-first RAG CLI (`tools.rag.cli`) with vector-augmented intelligence capabilities.

## Recent Enhancements

- ✨ **Vector-Augmented Intelligence**: Semantic search with embedding models
- 🔍 **Hybrid Search**: Combine keyword and semantic search for better results
- 📊 **Query Caching**: Faster repeated queries with intelligent caching
- 🔄 **Incremental Indexing**: Update index without full rebuilds
- ⚡ **Performance Optimizations**: Improved retrieval speed and accuracy
- 🚀 **Automated Skill Discovery**: Zero-config registration for new skills in `src/grid/skills`
- 🛡️ **Intelligent Monitoring**: Execution tracking and regression detection via `PerformanceGuard`

## Prerequisites

- Run commands from the repo root: `e:\grid`
- Python venv recommended:

```powershell
.\venv\Scripts\python.exe -m pip install -e .
```

- LLM-backed modes require local Ollama.
  - Heuristic modes work without Ollama.

## Skills

### List skills

```powershell
.\venv\Scripts\python.exe -m grid skills list
```

### Run a skill

- Preferred: `--args-json` with JSON
- Also supported: PowerShell/JS-style object literal (identifier keys + single-quoted strings)

```powershell
.\venv\Scripts\python.exe -m grid skills run <skill_id> --args-json "{text:'hello', use_llm:false}"
```

### Common skills

#### `transform.schema_map`

Maps freeform text into a target schema.

```powershell
# Default GRID schema
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'...', target_schema:'default', output_format:'json', use_llm:false}"

# Context Engineering schema (heuristic-first)
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'Context Engineering Service: ... Retrieval logic: Primary Recall, Contextual Recall, Contradiction Flagging. Next: integrate thought_signature with StepBloom IF-THEN.', target_schema:'context_engineering', output_format:'json', use_llm:false}"

# Resonance schema
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'The Resonance Framework: 1) ... Mystique Activation: Purpose: ... How it works: ... Examples: ...', target_schema:'resonance', output_format:'json', use_llm:false}"

# Knowledgebase schema (Shield/Sword)
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'Shield ... Sword ... scope ... feedback ...', target_schema:'knowledgebase', output_format:'markdown', use_llm:false}"

# Sensory schema (inline supported)
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'Sight Element: Light Essence: Clarity Modes: - Focusing - Refracting', target_schema:'sensory', output_format:'json', use_llm:false}"
```

#### `context.refine`

Refines text for clarity (heuristic mode removes pronouns aggressively; `use_llm:true` is higher quality).

```powershell
.\venv\Scripts\python.exe -m grid skills run context.refine --args-json "{text:'I think we should do it because it is important and it will help us.', use_llm:false}"
```

#### `compress.articulate`

Compresses a concept into a character budget.

```powershell
.\venv\Scripts\python.exe -m grid skills run compress.articulate --args-json "{text:'StepBloom validates steps before proceeding; use IF-THEN checkpoints.', max_chars:80, use_llm:false}"
```

#### `cross_reference.explain`

Cross-domain explanation with an explicit map/compass structure.

```powershell
.\venv\Scripts\python.exe -m grid skills run cross_reference.explain --args-json "{concept:'StepBloom', source_domain:'execution frameworks', target_domain:'software delivery', use_llm:false}"
```

#### `youtube.transcript_analyze`

Local-first transcript analysis. Provide transcript text or a file.

```powershell
.\venv\Scripts\python.exe -m grid skills run youtube.transcript_analyze --args-json "{transcript:'...', top_n:5, use_rag:false}"
```

## RAG

### Vector-Augmented Intelligence Features

#### Embedding Models

GRID RAG uses **Nomic Embed Text v2 MOE** for high-quality semantic embeddings:

```powershell
# Verify embedding model is available
.\venv\Scripts\python.exe -c "from tools.rag.embeddings import get_embedding_model; print(get_embedding_model())"
```

**Supported Models**:
- `nomic-embed-text-v2-moe:latest` (default, best quality)
- `nomic-embed-text` (faster, lower memory)
- `all-minilm` (fallback)

#### Hybrid Search (Beta)

Combine keyword and semantic search for optimal results:

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli query "pattern recognition" --hybrid --rerank
```

**Options**:
- `--hybrid`: Enable hybrid search (keyword + semantic)
- `--rerank`: Apply reranking for improved relevance
- `--alpha 0.7`: Control semantic vs keyword balance (0=keyword only, 1=semantic only)

#### Query Caching

Automatic caching of query results for faster repeated searches:

```powershell
# Cache enabled by default, stored in .rag_db/cache/
.\venv\Scripts\python.exe -m tools.rag.cli query "GRID architecture" --use-cache

# Clear cache
.\venv\Scripts\python.exe -m tools.rag.cli clear-cache
```

### Build a curated index (recommended)

Curated indexing builds a small high-signal index seeded by `important_files.json` + key entry points.

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli index . --rebuild --curate
```

**Performance**: Indexes ~50-100 files in 2-5 minutes with semantic embeddings.

### Incremental indexing (fast updates)

Update the index without full rebuild:

```powershell
# Index only changed files since last update
.\venv\Scripts\python.exe -m tools.rag.cli index . --incremental

# Index specific file
.\venv\Scripts\python.exe -m tools.rag.cli index docs/ARCHITECTURE.md --incremental
```

**When to use**:
- ✅ Small documentation updates
- ✅ Adding a few new files
- ❌ Major structural changes (use `--rebuild` instead)

### Build from a manifest

Manifest file can be newline-delimited paths (relative to repo root) or a JSON list.

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli index . --rebuild --manifest .\my_manifest.txt
```

### Query via RAG CLI

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli query "What is the GRID system?"
```

### Query via skill

```powershell
.\venv\Scripts\python.exe -m grid skills run rag.query_knowledge --args-json "{query:'What is the GRID system?'}"
```

## Performance Optimization

### Improving Search Quality

1. **Use hybrid search** for better precision/recall balance
2. **Enable reranking** for queries requiring high accuracy
3. **Curate your index** - smaller, high-quality index > large noisy index
4. **Verify embeddings** - ensure `nomic-embed-text-v2-moe:latest` is used

### Reducing Latency

```powershell
# Enable query caching (default)
.\venv\Scripts\python.exe -m tools.rag.cli query "..." --use-cache

# Reduce results for faster queries
.\venv\Scripts\python.exe -m tools.rag.cli query "..." --top-k 3

# Use incremental indexing instead of full rebuilds
.\venv\Scripts\python.exe -m tools.rag.cli index . --incremental
```

### Memory Management

**Cache cleanup**:
```powershell
# Clear old cache entries (older than 30 days)
.\venv\Scripts\python.exe -m tools.rag.cli clear-cache --older-than 30

# View cache statistics
.\venv\Scripts\python.exe -m tools.rag.cli cache-stats
```

**Index optimization**:
```powershell
# Compact index (removes deleted documents)
.\venv\Scripts\python.exe -m tools.rag.cli optimize-index
```

---

## Troubleshooting

### Common Issues

#### Embedding model fallback

**Symptom**: Warnings about falling back to `all-minilm`

**Solution**:
```powershell
# Pull the recommended embedding model

# Or if using local Ollama
ollama pull nomic-embed-text-v2-moe:latest
```

#### Slow indexing

**Symptom**: Indexing takes > 10 minutes for small repos

**Solutions**:
1. Use `--curate` instead of indexing everything
2. Check Ollama is running and responsive
3. Verify embedding model is loaded: `ollama list`
4. Consider using faster embedding model (trade-off: lower quality)

#### Empty search results

**Symptom**: Queries return no results despite indexed content

**Solutions**:
1. Verify index exists: check `.rag_db/` directory
2. Rebuild index: `tools.rag.cli index . --rebuild --curate`
3. Try hybrid search: add `--hybrid` flag
4. Check query matches indexed content

- **PowerShell quoting**
  - Use double-quotes around the whole `--args-json` string.
  - Prefer single quotes inside the object literal: `{text:'...'}.

- **RAG requires local Ollama + index**
  - If Ollama is not running, LLM-backed RAG queries will fail.
  - If the index is empty, run `tools.rag.cli index` first.

### Performance Benchmarks (Reference)

| Operation | Time | Notes |
|-----------|------|-------|
| Curated index (50 files) | 2-5 min | Using nomic-embed-text-v2-moe |
| Incremental update (5 files) | 15-30 sec | Existing index |
| Query (cached) | < 100ms | Subsequent identical queries |
| Query (uncached, hybrid) | 500ms-2s | Includes embedding + search |
| Query (uncached, keyword) | 50-200ms | No embedding required |

**System**: WSL2, Python 3.13, Ollama local, ChromaDB
