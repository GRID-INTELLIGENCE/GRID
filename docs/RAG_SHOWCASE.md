# GRID RAG System Implementation

## Overview
This implementation provides a robust Retrieval Augmented Generation (RAG) system for GRID, designed to enhance context-awareness and reduce agent-user alignment issues.

## Core Components

### 1. Vector Store (`tools/rag/`)
- `store_base.py`: Abstract base class defining the vector store interface
- `store.py`: Concrete implementation with in-memory storage and persistence
- Features:
  - Document storage and retrieval
  - Sparse vector embeddings
  - NDJSON import/export
  - LLM integration
  - Pickle-based persistence

### 2. LLM Integration (`tests/test_rag.py`)
- Primary LLM: Nemotron (via Ollama)
- Embedding Model: nomic-embed-text
- Fallback: Word frequency embeddings
- Features:
  - Local model execution
  - Error handling with fallbacks
  - Structured prompt formatting

## Usage Instructions

### Prerequisites
```bash
# Install Ollama (requires WSL2 on Windows)
curl https://ollama.ai/install.sh | sh

# Pull required models
ollama pull nomic-embed-text
ollama pull nemo
```

### Basic Usage
```python
from tools.rag.store import VectorStore
from tests.test_rag import OllamaEmbedding, NemotronLLM

# Initialize
embedder = OllamaEmbedding()
llm = NemotronLLM()
store = VectorStore()

# Add documents
store.add(
    ids=["doc1"],
    docs=["Document content"],
    embeddings=[embedder.embed("Document content")],
    metadatas=[{"source": "example"}]
)

# Query
answer = store.query_with_llm("Your question", llm)
```

### Running Tests & Demo
```bash
# Run tests
python -m pytest tests/test_rag.py -v

# Interactive demo
python tests/test_rag.py
```

## Implementation Details

### Vector Store Interface
```python
class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, ids, docs, embeddings, metadatas): ...
    @abstractmethod
    def query(self, query_emb, k=5): ...
    @abstractmethod
    def save(self, path): ...
    @abstractmethod
    def load(self, path): ...
    def to_ndjson(self): ...
    def from_ndjson(data): ...
    def query_with_llm(self, query, llm, k=5): ...
```

### Key Features
1. **Document Storage**
   - In-memory vector store
   - Sparse embedding representation
   - Metadata support
   - Persistence options

2. **Retrieval**
   - Cosine similarity search
   - Top-k retrieval
   - LLM-enhanced responses
   - Configurable context window

3. **Data Exchange**
   - NDJSON format support
   - Pickle persistence
   - Structured metadata

4. **LLM Integration**
   - Local model execution via Ollama
   - Fallback mechanisms
   - Structured prompting
   - Error handling

## Development Context

### Initial Problem Space
- Agent-user alignment issues in IDE
- Context preservation challenges
- Trust gap mitigation
- Need for local, dependency-minimal solution

### Solution Approach
1. Implement base abstractions
2. Add concrete implementations
3. Integrate modern LLM capabilities
4. Provide comprehensive testing
5. Enable interactive demonstration

### Environmental Considerations
- Windows compatibility (via WSL2)
- File system constraints
- Local model execution
- Minimal dependencies

## Verification Status

```json
{
  "implementation": {
    "status": "completed",
    "components": [
      "vector_store",
      "llm_integration",
      "data_exchange",
      "testing"
    ],
    "files_implemented": [
      "tools/rag/store_base.py",
      "tools/rag/store.py",
      "tests/test_rag.py"
    ]
  },
  "testing": {
    "unit_tests": "completed",
    "integration_tests": "completed",
    "interactive_demo": "completed"
  }
}
```

## Future Enhancements
- Background indexing for real-time updates
- Additional embedding models
- Distributed vector storage
- Enhanced caching layer
- Knowledge graph integration

## References
- Original implementation: `tools/rag/`
- Tests and demos: `tests/test_rag.py`
- Documentation: This file
