# GRID RAG System

Unified Retrieval-Augmented Generation (RAG) system for GRID. Supports **local-only operation** (Ollama + ChromaDB) by default and **external API providers** (OpenAI, Anthropic, OpenAI-compatible endpoints) when configured.

## Features

- **Local-first default**: Ollama for embeddings and LLM, ChromaDB for vector storage
- **External API support**: Optional OpenAI, Anthropic, or any OpenAI-compatible endpoint (e.g. LiteLLM)
- **Nomic Embed Text**: Local embeddings via Ollama; optional OpenAI embeddings
- **ChromaDB Storage**: Persistent vector store (can be used with external embed/LLM)
- **Easy Querying**: Simple API for indexing and querying your project

## Setup

### Prerequisites

1. **Install Ollama**: [https://ollama.ai](https://ollama.ai)
2. **Pull Required Models**:
   ```bash
   ollama pull nomic-embed-text-v2-moe:latest
   ollama pull ministral-3:3b
   ollama pull gpt-oss-safeguard  # Optional
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install chromadb httpx numpy
   ```

   Optional: Install Ollama Python package for better integration:
   ```bash
   pip install ollama
   ```

## Usage

### Command Line Interface

#### Index a Repository

```bash
python -m tools.rag.cli index /path/to/repository
```

Rebuild index:
```bash
python -m tools.rag.cli index /path/to/repository --rebuild
```

#### Query the Knowledge Base

```bash
python -m tools.rag.cli query "How does the grid system work?"
```

With custom parameters:
```bash
python -m tools.rag.cli query "Your question" --top-k 10 --temperature 0.5
```

#### View Statistics

```bash
python -m tools.rag.cli stats
```

### Python API

```python
from tools.rag import RAGEngine, RAGConfig

# Create configuration (defaults to local-only)
config = RAGConfig.from_env()

# Initialize engine
engine = RAGEngine(config=config)

# Index a repository
engine.index("/path/to/repository", rebuild=False)

# Query
result = engine.query("How does the cognitive layer work?")
print(result["answer"])
print(f"Sources: {result['sources']}")

# Get statistics
stats = engine.get_stats()
print(f"Documents: {stats['document_count']}")
```

## Configuration

Configuration can be set via environment variables.

### Local-only (default)

```bash
# Embedding model
export RAG_EMBEDDING_MODEL="nomic-embed-text-v2-moe:latest"
export RAG_EMBEDDING_MODE="local"  # local or cloud
export RAG_EMBEDDING_PROVIDER="ollama"

# LLM model
export RAG_LLM_MODEL_LOCAL="ministral-3:3b"  # or gpt-oss-safeguard
export RAG_LLM_MODE="local"  # local, cloud, copilot, or external

# Vector store (unchanged when using external APIs)
export RAG_VECTOR_STORE_PATH=".rag_db"
export RAG_COLLECTION_NAME="grid_knowledge_base"

# Ollama
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Using external API providers

To use OpenAI, Anthropic, or an OpenAI-compatible endpoint for the LLM and/or embeddings:

```bash
# Use external LLM (OpenAI)
export RAG_LLM_MODE="external"
export RAG_LLM_PROVIDER="openai"   # or anthropic, openai_compatible
export RAG_LLM_MODEL="gpt-4o-mini" # or OPENAI_MODEL
export OPENAI_API_KEY="sk-..."

# Optional: proxy or custom endpoint (e.g. LiteLLM)
export OPENAI_BASE_URL="https://your-proxy.com/v1"
# or for openai_compatible only: RAG_LLM_API_BASE

# Use external embeddings (OpenAI)
export RAG_EMBEDDING_PROVIDER="openai"
export RAG_EMBEDDING_MODEL="text-embedding-3-small"
export OPENAI_API_KEY="sk-..."

# Anthropic (when RAG_LLM_PROVIDER=anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
```

Vector store can remain ChromaDB; only the embedding and LLM backends switch to external APIs.

### Other options

```bash
# Chunking
export RAG_CHUNK_SIZE="800"
export RAG_CHUNK_OVERLAP="100"

# Retrieval
export RAG_TOP_K="10"
export RAG_SIMILARITY_THRESHOLD="0.0"
```

## Architecture

### Components

1. **Embedding Provider** (`embeddings/`)
   - Ollama (default): nomic-embed-text via Ollama
   - OpenAI: `RAG_EMBEDDING_PROVIDER=openai` with `OPENAI_API_KEY`
   - Returns dense vectors (not sparse dicts)

2. **LLM Provider** (`llm/`)
   - `OllamaLocalLLM` / `OllamaCloudLLM`: Local or cloud Ollama
   - `OpenAILLM`: OpenAI API (or OpenAI-compatible via base_url)
   - `AnthropicLLM`: Anthropic Claude API
   - `OpenAICompatibleLLM`: LiteLLM or any OpenAI-compatible chat completions endpoint

3. **Vector Store** (`vector_store/`)
   - `ChromaDBVectorStore`: ChromaDB-based persistent storage

4. **RAG Engine** (`rag_engine.py`)
   - Orchestrates embedding, retrieval, and generation
   - Ensures local-only operation

### Data Flow

```
Repository Files
    ↓
Indexer (chunks documents)
    ↓
Embedding Provider (nomic-embed-text-v2)
    ↓
ChromaDB Vector Store (persistent)
    ↓
Query → Embedding → Retrieval → LLM → Answer
```

## Local-first default

The RAG system defaults to local operation:

- **Embeddings**: Local Ollama (`nomic-embed-text`) unless `RAG_EMBEDDING_PROVIDER=openai`
- **LLM**: Local Ollama unless `RAG_LLM_MODE=external` and `RAG_LLM_PROVIDER` (openai, anthropic, openai_compatible)
- **Storage**: ChromaDB stores data locally in `.rag_db/` (used for both local and external backends)

To use external APIs, set the env vars in "Using external API providers" above. The main RAG stack lives under `src/tools/rag`; the `knowledge_base/` package is a separate, OpenAI-only subsystem.

## Best Practices

1. **Index Regularly**: Rebuild index when codebase changes significantly
2. **Chunk Size**: Adjust `chunk_size` based on your document types (500 is good for code)
3. **Top-K**: Use 3-5 for most queries, increase for complex questions
4. **Temperature**: Lower (0.3-0.5) for factual queries, higher (0.7-0.9) for creative tasks

## Troubleshooting

### "Model not found" errors

Make sure you've pulled the required models:
```bash
ollama pull nomic-embed-text-v2-moe:latest
ollama pull ministral
```

### Ollama connection errors

Ensure Ollama is running:
```bash
ollama serve
```

Or check if it's running on a different port:
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Low-quality results

1. Rebuild the index: `--rebuild` flag
2. Increase `top_k` for more context
3. Adjust chunk size/overlap for better document segmentation

## Migration from Old RAG System

The new RAG system is not backward compatible with the old sparse dict implementation. To migrate:

1. Rebuild your index using the new system
2. Update code to use `RAGEngine` instead of direct `VectorStore` access
3. Embeddings are now dense vectors (lists), not sparse dicts

## Future Enhancements

- HuggingFace integration (planned)
- Hybrid search (semantic + keyword)
- Reranking for better relevance
- Incremental indexing
