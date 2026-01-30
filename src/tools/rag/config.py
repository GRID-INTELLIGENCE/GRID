"""Configuration for RAG system."""

import os
from dataclasses import dataclass
from enum import Enum

# Load .env file if present, but respect GRID_QUIET mode which may have set env vars
# that shouldn't be overridden (e.g., USE_DATABRICKS=false for quiet CLI operation)
_quiet_mode = os.environ.get("GRID_QUIET", "").lower() in ("1", "true", "yes")

if not _quiet_mode:
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped,import-not-found]

        load_dotenv(override=True)
    except ImportError:
        pass  # dotenv not installed, rely on system env vars


class ModelMode(str, Enum):
    """Model execution mode."""

    LOCAL = "local"  # Use local Ollama models
    CLOUD = "cloud"  # Use cloud Ollama models


@dataclass
class RAGConfig:
    """Configuration for RAG system."""

    # Embedding configuration
    embedding_model: str = "nomic-embed-text:latest"
    embedding_mode: ModelMode = ModelMode.LOCAL
    embedding_provider: str = "ollama"  # Use Ollama for nomic-embed-text

    # LLM configuration
    llm_model_local: str = "ministral-3:3b"  # Default local model
    llm_model_cloud: str | None = None  # Cloud model if using cloud mode
    llm_mode: ModelMode = ModelMode.LOCAL

    # Vector store configuration
    vector_store_provider: str = "chromadb"  # Options: chromadb, databricks, in_memory
    vector_store_path: str = ".rag_db"
    collection_name: str = "grid_knowledge_base"
    databricks_schema: str = "default"
    databricks_chunk_table: str = "rag_chunks"
    databricks_document_table: str = "rag_documents"
    databricks_manifest_table: str = "rag_file_manifest"

    # Ollama configuration
    ollama_base_url: str = "http://localhost:11434"  # Local Ollama
    ollama_cloud_url: str | None = None  # Cloud Ollama URL if using cloud

    # Chunking configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100

    # Retrieval configuration
    top_k: int = 10
    similarity_threshold: float = 0.0

    # Cache configuration
    cache_enabled: bool = True
    cache_size: int = 100
    cache_ttl: int = 3600  # seconds

    # Hybrid search configuration (enabled by default for better recall)
    use_hybrid: bool = True

    # Reranker configuration (enabled by default for better precision)
    use_reranker: bool = True
    reranker_type: str = "cross_encoder"  # Options: cross_encoder, ollama
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    reranker_top_k: int = 20  # Max candidates to rerank

    # Concurrency configuration
    max_concurrent_embeddings: int = 4
    embedding_batch_size: int = 20

    # Conversational RAG configuration
    conversation_enabled: bool = True
    conversation_memory_size: int = 10
    conversation_context_window: int = 1000
    include_conversation_history: bool = True
    multi_hop_enabled: bool = False
    multi_hop_max_depth: int = 2

    # Intelligent RAG configuration (Phase 3: Reasoning Layer)
    use_intelligent_rag: bool = True  # Enable full reasoning pipeline

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Create configuration from environment variables."""
        return cls(
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text:latest"),
            embedding_mode=ModelMode(os.getenv("RAG_EMBEDDING_MODE", "local")),
            embedding_provider=os.getenv("RAG_EMBEDDING_PROVIDER", "ollama"),
            llm_model_local=os.getenv("RAG_LLM_MODEL_LOCAL", "ministral-3:3b"),
            llm_model_cloud=os.getenv("RAG_LLM_MODEL_CLOUD", None),
            llm_mode=ModelMode(os.getenv("RAG_LLM_MODE", "local")),
            # Vector store config
            vector_store_provider=os.getenv("RAG_VECTOR_STORE_PROVIDER", "chromadb"),
            vector_store_path=os.getenv("RAG_VECTOR_STORE_PATH", ".rag_db"),
            collection_name=os.getenv("RAG_COLLECTION_NAME", "grid_knowledge_base"),
            databricks_schema=os.getenv("RAG_DATABRICKS_SCHEMA", "default"),
            databricks_chunk_table=os.getenv("RAG_DATABRICKS_CHUNK_TABLE", "rag_chunks"),
            databricks_document_table=os.getenv("RAG_DATABRICKS_DOCUMENT_TABLE", "rag_documents"),
            databricks_manifest_table=os.getenv("RAG_DATABRICKS_MANIFEST_TABLE", "rag_file_manifest"),
            # Ollama config
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_cloud_url=os.getenv("OLLAMA_CLOUD_URL"),
            # Chunking config
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
            # Retrieval config
            top_k=int(os.getenv("RAG_TOP_K", "10")),
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.0")),
            # Cache config
            cache_enabled=os.getenv("RAG_CACHE_ENABLED", "true").lower() == "true",
            cache_size=int(os.getenv("RAG_CACHE_SIZE", "100")),
            cache_ttl=int(os.getenv("RAG_CACHE_TTL", "3600")),
            # Hybrid/Reranker config
            use_hybrid=os.getenv("RAG_USE_HYBRID", "true").lower() == "true",
            use_reranker=os.getenv("RAG_USE_RERANKER", "true").lower() == "true",
            reranker_type=os.getenv("RAG_RERANKER_TYPE", "cross_encoder"),
            cross_encoder_model=os.getenv("RAG_CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2"),
            reranker_top_k=int(os.getenv("RAG_RERANKER_TOP_K", "20")),
            # Concurrency config
            max_concurrent_embeddings=int(os.getenv("RAG_MAX_CONCURRENT_EMBEDDINGS", "4")),
            embedding_batch_size=int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "20")),
            # Conversational RAG config
            conversation_enabled=os.getenv("RAG_CONVERSATION_ENABLED", "true").lower() == "true",
            conversation_memory_size=int(os.getenv("RAG_CONVERSATION_MEMORY_SIZE", "10")),
            conversation_context_window=int(os.getenv("RAG_CONVERSATION_CONTEXT_WINDOW", "1000")),
            include_conversation_history=os.getenv("RAG_INCLUDE_CONVERSATION_HISTORY", "true").lower() == "true",
            multi_hop_enabled=os.getenv("RAG_MULTI_HOP_ENABLED", "false").lower() == "true",
            multi_hop_max_depth=int(os.getenv("RAG_MULTI_HOP_MAX_DEPTH", "2")),
            # Intelligent RAG config
            use_intelligent_rag=os.getenv("RAG_USE_INTELLIGENT_RAG", "true").lower() == "true",
        )

    def ensure_local_only(self) -> None:
        """Ensure configuration is set for local-only operation."""
        if self.embedding_mode == ModelMode.CLOUD:
            raise ValueError("Cloud embedding mode not allowed. Set RAG_EMBEDDING_MODE=local or use local mode.")
        if self.llm_mode == ModelMode.CLOUD and not self.ollama_cloud_url:
            raise ValueError(
                "Cloud LLM mode requires OLLAMA_CLOUD_URL to be set. For local-only operation, set RAG_LLM_MODE=local"
            )
