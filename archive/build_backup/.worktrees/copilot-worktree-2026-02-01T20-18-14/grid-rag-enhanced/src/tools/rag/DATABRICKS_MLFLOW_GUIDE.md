# GRID RAG with Databricks and MLflow

This guide covers using GRID's RAG system with Databricks vector storage, MLflow tracking, and HuggingFace embeddings.

## Environment Variables

### Databricks Configuration

```bash
# Required for Databricks vector store
export DATABRICKS_HOST=https://dbc-9747ff30-23c5.cloud.databricks.com
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xxxxx
export DATABRICKS_TOKEN=dapi_REDACTED_REPLACE_WITH_YOUR_TOKEN

# Optional: schema and table names
export RAG_DATABRICKS_SCHEMA=default
export RAG_DATABRICKS_CHUNK_TABLE=rag_chunks
export RAG_DATABRICKS_DOCUMENT_TABLE=rag_documents
```

### MLflow Configuration

```bash
# Required for MLflow autologging
export MLFLOW_TRACKING_URI=databricks
export MLFLOW_REGISTRY_URI=databricks-uc
export MLFLOW_EXPERIMENT_ID=4189423223916324
```

### RAG Configuration

```bash
# Vector store provider (chromadb, databricks, in_memory)
export RAG_VECTOR_STORE_PROVIDER=databricks

# Embedding provider (huggingface, ollama, simple)
export RAG_EMBEDDING_PROVIDER=huggingface

# Embedding model (HuggingFace model ID or Ollama model name)
export RAG_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# LLM configuration
export RAG_LLM_MODEL_LOCAL=ministral-3:3b
export RAG_LLM_MODE=local

# Chunking configuration
export RAG_CHUNK_SIZE=1000
export RAG_CHUNK_OVERLAP=100

# Retrieval configuration
export RAG_TOP_K=10
export RAG_SIMILARITY_THRESHOLD=0.0

# Ollama configuration (if using Ollama)
export OLLAMA_BASE_URL=http://localhost:11434
```

## HuggingFace Embedding Models

### Recommended Models

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `BAAI/bge-small-en-v1.5` | 384 | Fast | Good | General purpose, fast indexing |
| `BAAI/bge-base-en-v1.5` | 768 | Medium | Very Good | Balanced speed/quality |
| `BAAI/bge-large-en-v1.5` | 1024 | Slower | Excellent | High-quality retrieval |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast | Good | Lightweight, multilingual |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Medium | Very Good | English-focused, high quality |

### Installation

```bash
pip install sentence-transformers
```

### Optional Faster Backends

#### ONNX Runtime (Faster CPU Inference)

```bash
pip install onnxruntime
pip install sentence-transformers[onnx]
```

#### CUDA (GPU Acceleration)

```bash
pip install sentence-transformers[cuda]
```

#### Optimum (Better Performance)

```bash
pip install optimum[onnxruntime]
```

## Usage Examples

### Index with Databricks Vector Store

```bash
python -m tools.rag.cli index e:/grid --rebuild
```

### Query with Databricks Vector Store

```bash
python -m tools.rag.cli query "What is the GRID RAG system?"
```

### On-Demand Query-Time Indexing

```bash
python -m tools.rag.cli ondemand "Where is RAG implemented?" \
    --docs e:/grid/docs \
    --repo e:/grid \
    --depth 1 \
    --top-k 6
```

### Using HuggingFace Embeddings

```bash
export RAG_EMBEDDING_PROVIDER=huggingface
export RAG_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
python -m tools.rag.cli index e:/grid --rebuild
```

### Using Ollama Embeddings

```bash
export RAG_EMBEDDING_PROVIDER=ollama
export RAG_EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
python -m tools.rag.cli index e:/grid --rebuild
```

## Vector Store Providers

### ChromaDB (Default)

```bash
export RAG_VECTOR_STORE_PROVIDER=chromadb
export RAG_VECTOR_STORE_PATH=.rag_db
```

### Databricks

```bash
export RAG_VECTOR_STORE_PROVIDER=databricks
export RAG_DATABRICKS_SCHEMA=default
```

### In-Memory (Ephemeral)

```bash
export RAG_VECTOR_STORE_PROVIDER=in_memory
```

## MLflow Tracking

When MLflow is configured, the RAG engine automatically logs:

- **Indexing operations**: repo path, chunk size, embedding model, provider
- **Query operations**: query text, top_k, embedding model, LLM model, temperature
- **Retrieval metrics**: num_retrieved, avg_distance, min_distance, max_distance
- **Answer metrics**: answer_length, generation_time_seconds

### Viewing Traces in MLflow UI

1. Navigate to your Databricks workspace
2. Go to Experiments
3. Select the experiment specified by `MLFLOW_EXPERIMENT_ID`
4. View traces under the "Traces" tab

## Performance Tuning

### Batch Embedding

The indexer automatically uses batch embeddings for HuggingFace providers (batch_size=32 by default). To adjust:

```python
# In tools/rag/indexer.py, modify batch_size
batch_size = 64  # Increase for faster indexing (more memory)
```

### Chunk Size

Larger chunks reduce the number of embeddings but may reduce retrieval precision:

```bash
export RAG_CHUNK_SIZE=2000  # Larger chunks
export RAG_CHUNK_OVERLAP=200
```

### Top-K Retrieval

Adjust the number of documents retrieved:

```bash
export RAG_TOP_K=20  # More context, slower generation
```

## Troubleshooting

### Databricks Connection Issues

```bash
# Test connection
python -c "from application.mothership.db.databricks_connector import validate_databricks_connection; print(validate_databricks_connection())"
```

### MLflow Not Logging

```bash
# Verify MLflow configuration
python -c "import os; print('MLFLOW_TRACKING_URI:', os.getenv('MLFLOW_TRACKING_URI')); print('MLFLOW_EXPERIMENT_ID:', os.getenv('MLFLOW_EXPERIMENT_ID'))"
```

### Ollama Not Running

```bash
# Start Ollama
ollama serve

# Pull required models
ollama pull nomic-embed-text-v2-moe:latest
ollama pull ministral-3:3b
```

### HuggingFace Model Download Issues

```bash
# Set HuggingFace cache directory
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache
```

## Advanced Features

### Hybrid Search (BM25 + Vector)

```bash
export RAG_USE_HYBRID=true
python -m tools.rag.cli query "query text"
```

### Reranking

```bash
export RAG_USE_RERANKER=true
export RAG_RERANKER_TOP_K=20
python -m tools.rag.cli query "query text"
```

### Query Caching

```bash
export RAG_CACHE_ENABLED=true
export RAG_CACHE_SIZE=100
export RAG_CACHE_TTL=3600
```

## API Usage

```python
from tools.rag import RAGEngine, RAGConfig

# Initialize with Databricks
config = RAGConfig.from_env()
config.vector_store_provider = "databricks"
config.embedding_provider = "huggingface"
config.embedding_model = "BAAI/bge-small-en-v1.5"

engine = RAGEngine(config=config)

# Index
engine.index("e:/grid", rebuild=True)

# Query
result = engine.query("What is GRID?")
print(result["answer"])
print(result["sources"])
```

## On-Demand RAG with Hooks

```python
from tools.rag.on_demand_engine import OnDemandRAGEngine, RAGHooks
from tools.rag.model_router import ModelRoutingDecision

def on_route(query: str, routing: ModelRoutingDecision):
    print(f"Routing: {routing.reason}")

hooks = RAGHooks(on_route=on_route)

engine = OnDemandRAGEngine(
    docs_root="e:/grid/docs",
    repo_root="e:/grid",
    hooks=hooks,
)

result = engine.query(
    query_text="Explain the RAG architecture",
    depth=1,
    top_k=6,
)
print(result["answer"])
print(result["routing"])
```
