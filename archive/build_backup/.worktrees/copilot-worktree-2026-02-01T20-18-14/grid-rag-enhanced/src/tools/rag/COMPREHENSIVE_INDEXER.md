# 🔍 GRID Comprehensive Indexer

**NLP-Optimized • Rich Context • Deep Understanding**

---

## Overview

The Comprehensive Indexer is a sophisticated indexing pipeline designed to enable intelligent RAG responses. It creates embeddings that allow the system to answer complex technical questions with simple, natural language.

### Key Features

- **🎨 Beautiful Rich CLI** - Progress bars, time estimates, live statistics
- **🧠 NLP-Aware Chunking** - Content-type detection, semantic boundaries
- **🔤 High-Quality Embeddings** - MiniLM (fast) or BGE-M3 (quality)
- **📝 Rich Metadata** - Symbols, imports, references, summaries
- **⚡ Fast Throughput** - ~70 chunks/second
- **🔧 Workflow Integration** - Simple function calls for automation

---

## Quick Start

### CLI Usage

```bash
# Index current directory (fastest option)
python -m tools.rag.comprehensive_indexer index .

# Index with high-quality embeddings (BGE-M3)
python -m tools.rag.comprehensive_indexer index . --model BAAI/bge-m3

# Full rebuild with custom database path
python -m tools.rag.comprehensive_indexer index . --rebuild --db-path ./my_index

# Quiet mode (JSON output)
python -m tools.rag.comprehensive_indexer index . --quiet
```

### Python API

```python
from tools.rag.comprehensive_indexer import index_codebase, quick_index, quality_index

# Simple indexing (recommended)
result = index_codebase(".")
print(f"Indexed {result['chunks_created']} chunks in {result['duration_seconds']:.1f}s")

# Quick index (returns True/False)
if quick_index("."):
    print("Ready to query!")

# Quality index with BGE-M3 (best for complex queries)
quality_index(".")

# Check if index exists
from tools.rag.comprehensive_indexer import index_exists, get_index_stats
if index_exists():
    stats = get_index_stats()
    print(f"Index has {stats['chunk_count']} chunks")
```

---

## Embedding Models

| Model | Alias | Dimensions | Speed | Quality | Best For |
|-------|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | `fast`, `auto` | 384 | ⚡⚡⚡ | ★★★☆ | General use, quick indexing |
| `all-MiniLM-L12-v2` | - | 384 | ⚡⚡ | ★★★★ | Better quality, still fast |
| `BGE-M3` | `quality`, `bge` | 1024 | ⚡ | ★★★★★ | Complex queries, multilingual |
| `bge-large-en-v1.5` | - | 1024 | ⚡ | ★★★★★ | English only, high quality |
| `E5-large-v2` | - | 1024 | ⚡ | ★★★★☆ | Retrieval-focused |

### Choosing a Model

- **Daily development**: Use `auto` (MiniLM) - fast, good enough
- **Production indexing**: Use `quality` (BGE-M3) - best results
- **Large codebases**: Use `fast` first, upgrade if needed

---

## NLP-Aware Chunking

The chunker intelligently segments code based on content type:

### Content Type Detection

| Extension | Type | Chunking Strategy |
|-----------|------|-------------------|
| `.py` | Python Code | Class/function boundaries |
| `.js`, `.ts` | JavaScript/TypeScript | Fixed-size with overlap |
| `.md` | Markdown | Header sections |
| `.yaml`, `.json` | Config | Fixed-size |
| `.rst`, `.txt` | Documentation | Paragraph boundaries |

### Python Chunking Example

```
File: rag_engine.py
  ├── Chunk 1: RAGEngine class docstring + __init__
  │   └── Metadata: symbols=[RAGEngine], imports=[chromadb, ...]
  ├── Chunk 2: RAGEngine.query method
  │   └── Metadata: symbols=[query], parent=RAGEngine
  └── Chunk 3: RAGEngine.index method
      └── Metadata: symbols=[index], parent=RAGEngine
```

### Rich Metadata

Each chunk includes:

- **`chunk_id`**: Unique identifier
- **`file_path`**: Source file
- **`content_type`**: python, markdown, config, etc.
- **`start_line`, `end_line`**: Line numbers
- **`summary`**: Brief description of content
- **`symbols`**: Defined classes, functions, variables
- **`imports`**: Dependencies
- **`references`**: Cross-references to other files
- **`parent_section`**: Containing class (for methods)
- **`semantic_density`**: Information density score
- **`code_ratio`**: Code vs comments ratio

---

## Workflow Integration

### Initial Index (Once)

```python
from tools.rag.comprehensive_indexer import index_codebase

# Comprehensive initial index
result = index_codebase(
    path=".",
    model="quality",  # BGE-M3 for best results
    rebuild=True      # Start fresh
)

if result["success"]:
    print(f"✅ Indexed {result['chunks_created']} chunks")
    print(f"⏱️  Took {result['duration_seconds']:.1f}s")
```

### Incremental Updates (Regular)

```python
from tools.rag.comprehensive_indexer import incremental_index

# Update index with changes (no rebuild)
result = incremental_index(path=".")
```

### Integration Pattern

```python
from tools.rag.comprehensive_indexer import index_exists, index_codebase

def ensure_index():
    """Ensure index exists before querying."""
    if not index_exists():
        print("📝 Building initial index...")
        index_codebase(".", model="auto", rebuild=True)
    return True

# Use in your workflow
ensure_index()
# Now safe to query
```

---

## Performance

### Benchmarks

| Codebase Size | Files | Chunks | Time | Throughput |
|---------------|-------|--------|------|------------|
| Small (RAG tools) | 70 | 643 | 9s | 70 chunks/s |
| Medium (GRID src) | 554 | 5,380 | 81s | 67 chunks/s |
| Large (1000+ files) | ~1000 | ~10,000 | ~2.5m | 65 chunks/s |

### Memory Usage

- **MiniLM model**: ~100MB
- **BGE-M3 model**: ~500MB
- **Per chunk overhead**: ~1KB

---

## CLI Output Example

```
╭────────────────────────────────────────────────────────────────────╮
│ 🔍 GRID Comprehensive Indexer                                      │
│ NLP-Optimized • Rich Context • Deep Understanding                  │
╰────────────────────────────────────────────────────────────────────╯
⠧ 📁 Processing files ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 554/565 • 0:01:20 • 0:00:02

╭────────────────────────────────────────────────────────────────────╮
│                   📊 Indexing Complete                             │
│  Metric           Value                                            │
│  Duration         80.6s                                            │
│  Files Processed  554                                              │
│  Files Skipped    11                                               │
│  Total Chunks     5380                                             │
│  Code Chunks      3706                                             │
│  Doc Chunks       585                                              │
│  Throughput       66.7 chunks/s                                    │
│  Embedding Model  sentence-transformers/all-MiniLM-L6-v2           │
│  Embedding Dims   384                                              │
╰────────────────────────────────────────────────────────────────────╯
```

---

## API Reference

### `index_codebase(path, model, rebuild)`

Main indexing function for workflow integration.

**Parameters:**
- `path` (str): Path to codebase (default: ".")
- `model` (str): "auto", "fast", "quality", or full model name
- `rebuild` (bool): Clear existing index first

**Returns:**
```python
{
    "success": True,
    "files_processed": 554,
    "chunks_created": 5380,
    "code_chunks": 3706,
    "doc_chunks": 585,
    "duration_seconds": 80.6,
    "throughput_chunks_per_sec": 66.7,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "db_path": ".rag_db_comprehensive"
}
```

### `quick_index(path)`

Fast indexing with MiniLM model. Returns `True` on success.

### `quality_index(path)`

High-quality indexing with BGE-M3. Returns `True` on success.

### `incremental_index(path, files)`

Add/update specific files without full rebuild.

### `index_exists(db_path)`

Check if an index exists at the given path.

### `get_index_stats(db_path)`

Get statistics about an existing index.

---

## Dependencies

```bash
pip install sentence-transformers rich chromadb
```

Required packages:
- `sentence-transformers` - HuggingFace embedding models
- `rich` - Beautiful CLI progress display
- `chromadb` - Vector database

---

## File Structure

```
tools/rag/
├── comprehensive_indexer.py   # Main indexer module
├── COMPREHENSIVE_INDEXER.md   # This documentation
├── vector_store/
│   └── chromadb_store.py      # Vector storage
└── .rag_db_comprehensive/     # Default index location
```

---

## Troubleshooting

### "Model not found"

```bash
# Model will auto-download on first use
# Or pre-download:
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### "Rich not installed"

```bash
pip install rich
```

### Slow indexing

- Use `--model fast` for quicker indexing
- Check for large binary files being indexed
- Ensure SSD storage for database

### Out of memory

- Use smaller model: `all-MiniLM-L6-v2`
- Reduce batch size in code
- Index in smaller batches

---

## Why This Design?

### The Goal
Enable the RAG system to answer complex technical questions with simple, natural language by deeply understanding the codebase.

### Key Principles

1. **Semantic Boundaries**: Don't split functions/classes mid-definition
2. **Rich Context**: Every chunk knows what file, class, and purpose it serves
3. **High-Quality Embeddings**: MiniLM/BGE-M3 capture semantic meaning
4. **Workflow Integration**: Simple function calls for automation
5. **Beautiful UX**: Rich CLI makes indexing enjoyable

### The Result
- Complex question: "How does RAGEngine integrate with the cognitive layer?"
- Simple answer: "RAGEngine connects to the cognitive layer through..."

---

## Next Steps

After indexing, use the intelligent RAG system:

```bash
# Query the indexed codebase
python -m tools.rag.cli intelligent-query "What is GRID?" --show-reasoning
```

---

**Built with ❤️ for the GRID project**
