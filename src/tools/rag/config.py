"""Configuration for RAG system."""

import dataclasses
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

# Load .env file if present, but respect GRID_QUIET mode which may have set env vars
# that shouldn't be overridden (e.g., USE_DATABRICKS=false for quiet CLI operation)
_quiet_mode = os.environ.get("GRID_QUIET", "").lower() in ("1", "true", "yes")

if not _quiet_mode:
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped,import-not-found]

        load_dotenv(override=True)
    except ImportError:
        pass  # dotenv not installed, rely on system env vars


class ModelMode(StrEnum):
    """Model execution mode."""

    AUTO = "auto"  # Use fallback chain from config/ollama-models.json (cloud-first, local fallback)
    LOCAL = "local"  # Use local Ollama models
    CLOUD = "cloud"  # Use cloud Ollama models
    COPILOT = "copilot"  # Use GitHub Copilot SDK
    EXTERNAL = "external"  # Use external API providers (OpenAI, Anthropic, etc.)


@dataclass
class RAGConfig:
    """Configuration for RAG system."""

    # Embedding configuration
    embedding_model: str = "nomic-embed-text-v2-moe:latest"
    embedding_mode: ModelMode = ModelMode.LOCAL
    embedding_provider: str = "ollama"  # Use Ollama for nomic-embed-text

    # LLM configuration
    llm_model_local: str = "ministral-3:3b"  # Default local model (RAM-safe)
    llm_model_cloud: str | None = None  # Cloud model if using cloud mode
    llm_model_copilot: str = "gpt-4o"  # Default Copilot model
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

    # External API provider configuration
    openai_api_key: str | None = None  # OpenAI API key
    openai_base_url: str | None = None  # Optional: proxy or custom endpoint (e.g. LiteLLM)
    openai_model: str = "gpt-4o-mini"  # Default OpenAI model
    anthropic_api_key: str | None = None  # Anthropic API key
    anthropic_model: str = "claude-3-5-sonnet-20241022"  # Default Anthropic model
    gemini_api_key: str | None = None  # Google Gemini API key
    gemini_model: str = "gemini-1.5-flash"  # Default Gemini model
    mistral_api_key: str | None = None  # Mistral AI API key
    mistral_model: str = "mistral-large-latest"  # Default Mistral model
    external_provider: str = "mistral"  # Default external provider: openai, anthropic, gemini, mistral, openai_compatible
    llm_api_base: str | None = None  # For openai_compatible: base URL for chat completions

    # Chunking configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100

    # Retrieval configuration
    top_k: int = 10
    similarity_threshold: float = 0.0
    max_context_length: int = 4000  # Max total character length for retrieved context (RAG_MAX_CONTEXT_LENGTH)

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
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text-v2-moe:latest"),
            embedding_mode=ModelMode(os.getenv("RAG_EMBEDDING_MODE", "local")),
            embedding_provider=os.getenv("RAG_EMBEDDING_PROVIDER", "ollama"),
            llm_model_local=os.getenv("RAG_LLM_MODEL_LOCAL", "ministral-3:3b"),
            llm_model_cloud=os.getenv("RAG_LLM_MODEL_CLOUD", None),
            llm_model_copilot=os.getenv("RAG_LLM_MODEL_COPILOT", "gpt-4o"),
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
            # External API provider config
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("RAG_LLM_OPENAI_BASE"),
            openai_model=os.getenv("RAG_LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            mistral_model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            external_provider=os.getenv("RAG_LLM_PROVIDER", os.getenv("RAG_EXTERNAL_PROVIDER", "mistral")),
            llm_api_base=os.getenv("OPENAI_BASE_URL") or os.getenv("RAG_LLM_API_BASE"),
            # Chunking config
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
            # Retrieval config
            top_k=int(os.getenv("RAG_TOP_K", "10")),
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.0")),
            max_context_length=int(os.getenv("RAG_MAX_CONTEXT_LENGTH", "4000")),
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
        """Enforce local-only operation — no external API calls.

        Raises:
            ValueError: If config is set to use external providers.
        """
        if self.llm_mode == ModelMode.EXTERNAL:
            raise ValueError(
                f"Local-only mode required, but llm_mode={self.llm_mode}. "
                "Set RAG_LLM_MODE=local or remove the ensure_local_only() call."
            )
        if self.embedding_provider not in ("ollama", "huggingface", "simple"):
            raise ValueError(
                f"Local-only mode requires a local embedding provider, "
                f"but embedding_provider={self.embedding_provider}. "
                "Set RAG_EMBEDDING_PROVIDER=ollama (or huggingface/simple)."
            )

    @classmethod
    def from_dict(cls, overrides: dict[str, Any] | None = None) -> "RAGConfig":
        """Create configuration from a dict of runtime overrides.

        Falls back to env vars for any field not specified. This enables
        per-session hotloading without requiring MCP server restarts.

        Usage:
            config = RAGConfig.from_dict({
                "embedding_model": "nomic-embed-text-v2-moe:latest",
                "llm_model_local": "ministral-3:latest",
                "vector_store_path": "/custom/path",
            })
        """
        if not overrides:
            return cls.from_env()

        base = cls.from_env()
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in overrides.items() if k in valid_fields}

        # Convert string enums
        if "embedding_mode" in filtered and isinstance(filtered["embedding_mode"], str):
            filtered["embedding_mode"] = ModelMode(filtered["embedding_mode"])
        if "llm_mode" in filtered and isinstance(filtered["llm_mode"], str):
            filtered["llm_mode"] = ModelMode(filtered["llm_mode"])

        # Convert string booleans
        for bool_field in (
            "cache_enabled",
            "use_hybrid",
            "use_reranker",
            "conversation_enabled",
            "include_conversation_history",
            "multi_hop_enabled",
            "use_intelligent_rag",
        ):
            if bool_field in filtered and isinstance(filtered[bool_field], str):
                filtered[bool_field] = filtered[bool_field].lower() in ("true", "1", "yes")

        # Convert string integers
        for int_field in (
            "chunk_size",
            "chunk_overlap",
            "top_k",
            "max_context_length",
            "cache_size",
            "cache_ttl",
            "reranker_top_k",
            "max_concurrent_embeddings",
            "embedding_batch_size",
            "conversation_memory_size",
            "conversation_context_window",
            "multi_hop_max_depth",
        ):
            if int_field in filtered and isinstance(filtered[int_field], str):
                filtered[int_field] = int(filtered[int_field])

        # Convert string floats
        for float_field in ("similarity_threshold",):
            if float_field in filtered and isinstance(filtered[float_field], str):
                filtered[float_field] = float(filtered[float_field])

        return dataclasses.replace(base, **filtered)
