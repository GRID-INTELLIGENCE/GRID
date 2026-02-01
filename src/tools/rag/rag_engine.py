"""Unified RAG engine orchestrating embedding, retrieval, and generation."""

import logging
import time
from typing import Any

from .config import ModelMode, RAGConfig

logger = logging.getLogger(__name__)
from .embeddings.factory import get_embedding_provider
from .indexer import index_repository
from .llm.factory import get_llm_provider
from .mlflow_tracking import log_answer_metrics, log_retrieval_metrics, track_indexing, track_query
from .vector_store.base import BaseVectorStore

# Optional ChromaDB dependency
try:
    from .vector_store.chromadb_store import ChromaDBVectorStore
except ImportError:
    ChromaDBVectorStore = None  # type: ignore[misc,assignment]

# Optional Databricks dependency
try:
    from .vector_store.databricks_store import DatabricksVectorStore
except ImportError:
    DatabricksVectorStore = None  # type: ignore[misc,assignment]


class RAGEngine:
    """Unified RAG engine for querying project knowledge base.

    Orchestrates embedding, retrieval, and generation with proper local-only operation.
    """

    def __init__(self, config: RAGConfig | None = None) -> None:
        """Initialize RAG engine.

        Args:
            config: RAG configuration (default: from environment)
        """
        from .utils import check_ollama_connection, find_embedding_model, find_llm_model

        if config is None:
            config = RAGConfig.from_env()

        # Ensure local-only operation
        config.ensure_local_only()

        # Check Ollama connection (required for LLM, even if embedding is HF)
        is_ollama_needed = config.embedding_provider == "ollama" or config.llm_mode == ModelMode.LOCAL

        if is_ollama_needed:
            if not check_ollama_connection(config.ollama_base_url):
                if config.embedding_provider == "ollama":
                    raise RuntimeError(
                        f"Ollama is not running or not accessible at {config.ollama_base_url}.\n"
                        f"Please start Ollama for embeddings and LLM: ollama serve"
                    )
                else:
                    print(f"Warning: Ollama not accessible at {config.ollama_base_url}. Local LLM will fail.")
        elif config.llm_mode == ModelMode.COPILOT:
            print("Using GitHub Copilot SDK - no Ollama required")

        # Try to find available models for Ollama provider
        if config.embedding_provider == "ollama":
            try:
                available_embedding_model = find_embedding_model(
                    preferred=config.embedding_model, base_url=config.ollama_base_url
                )
                if available_embedding_model and available_embedding_model != config.embedding_model:
                    print(
                        f"Info: Using available Ollama model '{available_embedding_model}' instead of '{config.embedding_model}'"
                    )
                    config.embedding_model = available_embedding_model
            except Exception:
                pass

        if config.llm_mode == ModelMode.LOCAL:
            try:
                available_llm_model = find_llm_model(preferred=config.llm_model_local, base_url=config.ollama_base_url)
                if available_llm_model and available_llm_model != config.llm_model_local:
                    print(
                        f"Info: Using available Ollama LLM '{available_llm_model}' instead of '{config.llm_model_local}'"
                    )
                    config.llm_model_local = available_llm_model
            except Exception:
                pass

        self.config = config

        # Initialize components
        self.embedding_provider = get_embedding_provider(config=config)
        self.llm_provider = get_llm_provider(config=config)
        self.vector_store: BaseVectorStore | None = None

        # Select vector store using new registry pattern
        from .vector_store.registry import VectorStoreRegistry

        provider = config.vector_store_provider.lower()

        try:
            if provider == "databricks":
                self.vector_store = VectorStoreRegistry.create(
                    provider,
                    chunk_table=config.databricks_chunk_table,
                    document_table=config.databricks_document_table,
                    schema=config.databricks_schema,
                )
            elif provider == "chromadb":
                self.vector_store = VectorStoreRegistry.create(
                    provider,
                    collection_name=config.collection_name,
                    persist_directory=config.vector_store_path,
                )
            elif provider == "pinecone":
                # Pinecone configuration from environment or config
                import os

                api_key = os.getenv("PINECONE_API_KEY")
                index_name = os.getenv("PINECONE_INDEX_NAME", config.collection_name)

                self.vector_store = VectorStoreRegistry.create(
                    provider,
                    api_key=api_key,
                    index_name=index_name,
                    dimension=768,  # nomic-embed-text dimension
                    metric="cosine",
                    cloud="aws",
                    region="us-east-1",
                )
            elif provider == "in_memory":
                self.vector_store = VectorStoreRegistry.create(provider)
            else:
                available = ", ".join(VectorStoreRegistry.list_backends())
                raise ValueError(f"Unknown vector_store_provider: {provider}. Options: {available}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

        # Initialize query cache if enabled
        self._cache = None
        if config.cache_enabled:
            from .cache import QueryCache

            self._cache = QueryCache(
                max_size=config.cache_size, ttl_seconds=config.cache_ttl, collection_name=config.collection_name
            )

        # Initialize hybrid retriever if enabled
        self._hybrid_retriever = None
        if config.use_hybrid:
            from .retrieval.hybrid_retriever import create_hybrid_retriever

            self._hybrid_retriever = create_hybrid_retriever(
                vector_store=self.vector_store, embedding_provider=self.embedding_provider, config=config
            )

        # Initialize reranker if enabled
        self._reranker = None
        if config.use_reranker:
            if config.reranker_type == "cross_encoder":
                from .retrieval.cross_encoder_reranker import create_cross_encoder_reranker

                self._reranker = create_cross_encoder_reranker(config=config)
            else:
                from .retrieval.reranker import create_reranker

                self._reranker = create_reranker(config=config)

        # Initialize evaluator
        from .evaluation import RAGEvaluator

        self._evaluator = RAGEvaluator(embedding_provider=self.embedding_provider)

        # Initialize intelligent orchestrator for Phase 3 reasoning
        self._intelligent_orchestrator = None
        if config.use_intelligent_rag:
            from .intelligence.intelligent_orchestrator import create_intelligent_orchestrator
            from .intelligence.retrieval_orchestrator import create_retrieval_orchestrator

            retrieval_orch = create_retrieval_orchestrator(engine=self)
            self._intelligent_orchestrator = create_intelligent_orchestrator(
                retrieval_orchestrator=retrieval_orch,
                llm_provider=self.llm_provider,
                enable_all_features=True,
            )
            logger.info("Intelligent RAG orchestrator enabled with full reasoning pipeline.")

    def index(
        self,
        repo_path: str,
        rebuild: bool = False,
        exclude_dirs: list[str] | None = None,
        include_patterns: list[str] | None = None,
        files: list[str] | None = None,
        quality_threshold: float = 0.0,
        quiet: bool = False,
    ) -> None:
        """Index a repository with dimension validation."""
        if not rebuild and self.vector_store and self.vector_store.count() > 0:
            expected_dim = getattr(self.vector_store, "get_dimension", lambda: 0)()
            if expected_dim > 0:
                actual_dim = len(self.embedding_provider.embed("test"))
                if expected_dim != actual_dim:
                    print(f"⚠️  Dimension mismatch: Index={expected_dim}D, Model={actual_dim}D. Rebuilding...")
                    rebuild = True

        """Index a repository.

        Args:
            repo_path: Path to repository
            rebuild: Whether to rebuild index
            exclude_dirs: Optional directories to exclude
            include_patterns: Optional file patterns to include
            files: Optional explicit list of files to index
            quality_threshold: Minimum quality score for files (0.0-1.0)
        """
        with track_indexing(
            repo_path=repo_path,
            chunk_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap,
            embedding_model=self.config.embedding_model,
            embedding_provider=self.config.embedding_provider,
        ):
            # Use the refactored indexer
            index_repository(
                repo_path=repo_path,
                store_path=None,  # We use vector store directly
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
                rebuild=rebuild,
                embedding_provider=self.embedding_provider,
                exclude_dirs=exclude_dirs,
                include_patterns=include_patterns,
                vector_store=self.vector_store,
                files=files,
                quality_threshold=quality_threshold,
                quiet=quiet,
            )

    async def query(
        self, query_text: str, top_k: int | None = None, temperature: float = 0.7, include_sources: bool = True
    ) -> dict[str, Any]:
        """Query the RAG system (async).

        Args:
            query_text: Query text
            top_k: Number of documents to retrieve (default: from config)
            temperature: LLM temperature
            include_sources: Whether to include source documents

        Returns:
            Dictionary with 'answer', 'sources', 'context', optionally 'cached'
        """
        top_k = top_k or self.config.top_k
        llm_model: str = (
            self.config.llm_model_local if self.config.llm_mode.value == "local" else self.config.llm_model_cloud
        ) or "default"

        with track_query(
            query_text=query_text,
            top_k=top_k,
            embedding_model=self.config.embedding_model,
            llm_model=llm_model,
            temperature=temperature,
        ):
            # Use hybrid retriever if enabled, otherwise standard vector search
            if self._hybrid_retriever is not None:
                # Assuming hybrid retriever search is or will be async
                if hasattr(self._hybrid_retriever, "async_search"):
                    results = await self._hybrid_retriever.async_search(query=query_text, top_k=top_k)
                else:
                    results = self._hybrid_retriever.search(query=query_text, top_k=top_k)
            else:
                # Generate query embedding using async method
                query_embedding = await self.embedding_provider.async_embed(query_text)

                # Retrieve relevant documents
                if self.vector_store is None:
                    return {"answer": "Error: Vector store is not available.", "sources": [], "context": ""}

                # Check if vector store query is async
                async_query_fn = getattr(self.vector_store, "async_query", None)
                if async_query_fn is not None and callable(async_query_fn):
                    results = await async_query_fn(query_embedding=query_embedding, n_results=top_k)  # type: ignore[misc]
                else:
                    results = self.vector_store.query(query_embedding=query_embedding, n_results=top_k)

            if not results["documents"]:
                return {"answer": "No relevant documents found in the knowledge base.", "sources": [], "context": ""}

            # Rerank if enabled (after initial retrieval)
            if self._reranker is not None:
                reranked_indices = await self._reranker.async_rerank(
                    query=query_text, documents=results["documents"], top_k=top_k
                )

                # Reorder results based on reranker scores
                new_ids = []
                new_docs = []
                new_metas = []
                new_dists = []

                for idx, score in reranked_indices:
                    new_ids.append(results["ids"][idx])
                    new_docs.append(results["documents"][idx])
                    new_metas.append(results["metadatas"][idx])
                    # Convert 0-10 score to a distance-like value (0.0 is best)
                    new_dists.append(1.0 - (score / 10.0))

                results = {"ids": new_ids, "documents": new_docs, "metadatas": new_metas, "distances": new_dists}

            # Extract source IDs and chunk count for cache key
            source_ids = results.get("ids", [])
            chunk_count = self.vector_store.count() if self.vector_store else 0

            # Check cache if enabled
            if self._cache is not None:
                cached_result = self._cache.get(
                    query=query_text, top_k=top_k, source_ids=source_ids, chunk_count=chunk_count
                )
                if cached_result is not None:
                    # Return cached response (sources may be stale but context hash should prevent this)
                    cached_result["context"] = "" if not include_sources else cached_result.get("context", "")
                    return cached_result

            # Build context from retrieved documents
            context_parts = []
            sources = []

            for i, (doc, metadata, distance) in enumerate(
                zip(results["documents"], results["metadatas"], results["distances"], strict=False)
            ):
                source_info = {"index": i + 1, "distance": distance, "metadata": metadata}
                sources.append(source_info)

                context_parts.append(f"[{i + 1}] {doc}")

            context = "\n\n".join(context_parts)

            # Evaluate retrieval quality
            eval_metrics = self._evaluator.evaluate_retrieval(query=query_text, retrieved_docs=results["documents"])

            # Log retrieval metrics
            if results["distances"]:
                log_retrieval_metrics(
                    num_retrieved=len(results["documents"]),
                    avg_distance=sum(results["distances"]) / len(results["distances"]),
                    min_distance=min(results["distances"]),
                    max_distance=max(results["distances"]),
                )

            # Generate answer using LLM
            prompt = f"""Based on the following context from the project knowledge base, please answer the query.

Context:
{context}

Query: {query_text}

Answer:"""

            start_time = time.time()
            answer = await self.llm_provider.async_generate(prompt=prompt, temperature=temperature)
            generation_time = time.time() - start_time

            # Log answer metrics
            log_answer_metrics(answer_length=len(answer), generation_time_seconds=generation_time)

            result = {
                "answer": answer,
                "context": context if include_sources else "",
                "cached": False,
                "evaluation_metrics": eval_metrics,
            }

            if include_sources:
                result["sources"] = sources

            # Cache the result if enabled
            if self._cache is not None:
                self._cache.set(
                    query=query_text,
                    top_k=top_k,
                    source_ids=source_ids,
                    chunk_count=chunk_count,
                    answer=answer,
                    sources=sources,
                )

            return result

    def add_documents(
        self, documents: list[str], ids: list[str] | None = None, metadatas: list[dict[str, Any]] | None = None
    ) -> None:
        """Add documents directly to the vector store.

        Args:
            documents: List of document texts
            ids: Optional document IDs
            metadatas: Optional metadata for each document
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = self.embedding_provider.embed_batch(documents)

        # Add to vector store
        if self.vector_store:
            self.vector_store.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            raise RuntimeError("Cannot add documents: Vector store not available.")

    async def intelligent_query(
        self,
        query_text: str,
        top_k: int | None = None,
        temperature: float = 0.3,
        include_reasoning: bool = False,
        include_metrics: bool = False,
    ) -> dict[str, Any]:
        """Query using the intelligent RAG pipeline with reasoning layer.

        This method uses the Phase 3 intelligent orchestrator which provides:
        - Query understanding (intent classification + entity extraction)
        - Multi-stage retrieval (hybrid + multi-hop + reranking)
        - Evidence extraction (structured facts with provenance)
        - Chain-of-thought reasoning (transparent reasoning steps)
        - Response synthesis (polished answer with citations)

        Args:
            query_text: Query text
            top_k: Number of documents to retrieve (default: from config)
            temperature: LLM temperature for synthesis
            include_reasoning: Whether to include reasoning chain in response
            include_metrics: Whether to include pipeline metrics

        Returns:
            Dictionary with 'answer', 'sources', 'citations', 'confidence',
            and optionally 'reasoning' and 'metrics'
        """
        if not self._intelligent_orchestrator:
            raise RuntimeError(
                "Intelligent RAG orchestrator not initialized. "
                "Set use_intelligent_rag=True in RAGConfig or use the standard query() method."
            )

        top_k = top_k or self.config.top_k

        return await self._intelligent_orchestrator.query(
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            include_reasoning=include_reasoning,
            include_metrics=include_metrics,
        )

    def intelligent_query_sync(
        self,
        query_text: str,
        top_k: int | None = None,
        temperature: float = 0.3,
        include_reasoning: bool = False,
        include_metrics: bool = False,
    ) -> dict[str, Any]:
        """Synchronous version of intelligent_query.

        Args:
            query_text: Query text
            top_k: Number of documents to retrieve (default: from config)
            temperature: LLM temperature for synthesis
            include_reasoning: Whether to include reasoning chain in response
            include_metrics: Whether to include pipeline metrics

        Returns:
            Dictionary with 'answer', 'sources', 'citations', 'confidence',
            and optionally 'reasoning' and 'metrics'
        """
        if not self._intelligent_orchestrator:
            raise RuntimeError(
                "Intelligent RAG orchestrator not initialized. "
                "Set use_intelligent_rag=True in RAGConfig or use the standard query() method."
            )

        return self._intelligent_orchestrator.query_sync(
            query_text=query_text,
            top_k=top_k or self.config.top_k,
            temperature=temperature,
            include_reasoning=include_reasoning,
            include_metrics=include_metrics,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the knowledge base.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "document_count": self.vector_store.count() if self.vector_store else 0,
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
            "llm_model": (
                self.config.llm_model_local if self.config.llm_mode.value == "local" else self.config.llm_model_cloud
            ),
        }

        # Add intelligent RAG stats if enabled
        if self._intelligent_orchestrator:
            stats["intelligent_rag"] = self._intelligent_orchestrator.get_stats()

        return stats
