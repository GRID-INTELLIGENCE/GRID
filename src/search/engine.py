"""SearchEngine: top-level orchestrator wiring all layers of the search pipeline."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .config import SearchConfig
from .facets.aggregator import FacetAggregator
from .indexing.pipeline import IndexingPipeline
from .models import (
    Document,
    FacetResult,
    IndexSchema,
    SearchHit,
    SearchResponse,
)
from .query.expander import QueryExpander
from .query.intent import SearchIntentClassifier
from .query.parser import QueryParser
from .ranking.scorer import RankingPipeline
from .retrieval.fusion import HybridFusion
from .retrieval.keyword import KeywordRetriever
from .retrieval.semantic import SemanticRetriever
from .retrieval.structured import StructuredRetriever

logger = logging.getLogger(__name__)


@dataclass
class _IndexState:
    """Internal state for a single search index."""

    schema: IndexSchema
    pipeline: IndexingPipeline
    parser: QueryParser
    intent_classifier: SearchIntentClassifier
    expander: QueryExpander
    fusion: HybridFusion
    ranking: RankingPipeline
    facet_aggregator: FacetAggregator
    keyword_retriever: KeywordRetriever
    documents: dict[str, Document] = field(default_factory=dict)
    doc_texts: dict[str, str] = field(default_factory=dict)


class SearchEngine:
    """Orchestrates the full search pipeline.

    Lifecycle:
      1. ``create_index(schema)`` -- register an index with typed fields
      2. ``index_documents(name, docs)`` -- ingest structured records
      3. ``search(name, query, ...)`` -- parse -> understand -> retrieve -> rank -> facet -> respond
      4. ``delete_index(name)`` -- tear down
    """

    def __init__(self, config: SearchConfig | None = None) -> None:
        self.config = config or SearchConfig()
        self._indices: dict[str, _IndexState] = {}
        self._embedding_provider: Any = None

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def create_index(self, schema: IndexSchema) -> None:
        if schema.name in self._indices:
            raise ValueError(f"Index '{schema.name}' already exists")

        emb = self._get_embedding_provider()
        vector_store = self._create_vector_store(schema.name)

        pipeline = IndexingPipeline(schema, vector_store, emb, self.config)
        parser = QueryParser(schema)
        intent_classifier = SearchIntentClassifier(
            emb,
            similarity_threshold=self.config.intent_similarity_threshold,
            analytical_threshold=self.config.intent_analytical_threshold,
        )
        expander = QueryExpander(
            emb,
            similarity_threshold=self.config.expansion_similarity_threshold,
            max_expansions=self.config.expansion_max_terms,
        )
        keyword_retriever = KeywordRetriever()

        structured_retriever = StructuredRetriever(pipeline.structured_index)
        semantic_retriever = SemanticRetriever(vector_store, emb)

        fusion = HybridFusion(
            structured_retriever,
            semantic_retriever,
            keyword_retriever,
            rrf_k=self.config.rrf_k,
        )
        ranking = RankingPipeline(schema, self.config)
        facet_aggregator = FacetAggregator(
            schema,
            pipeline.structured_index,
            default_max_values=self.config.facet_max_values,
            default_histogram_buckets=self.config.facet_histogram_buckets,
        )

        self._indices[schema.name] = _IndexState(
            schema=schema,
            pipeline=pipeline,
            parser=parser,
            intent_classifier=intent_classifier,
            expander=expander,
            fusion=fusion,
            ranking=ranking,
            facet_aggregator=facet_aggregator,
            keyword_retriever=keyword_retriever,
        )
        logger.info("Created index '%s' with %d fields", schema.name, len(schema.fields))

    def index_documents(self, index_name: str, documents: list[Document]) -> int:
        state = self._get_index(index_name)
        count = state.pipeline.index_batch(documents)

        for doc in documents:
            state.documents[doc.id] = doc
            state.doc_texts[doc.id] = state.pipeline.build_search_text(doc)

        state.keyword_retriever.update(state.pipeline.bm25, state.pipeline.bm25_doc_ids, state.pipeline.bm25_texts)
        return count

    def delete_index(self, index_name: str) -> None:
        if index_name not in self._indices:
            raise KeyError(f"Index '{index_name}' not found")
        del self._indices[index_name]
        logger.info("Deleted index '%s'", index_name)

    def list_indices(self) -> list[str]:
        return list(self._indices.keys())

    def get_index_stats(self, index_name: str) -> dict[str, Any]:
        state = self._get_index(index_name)
        return {
            "index_name": index_name,
            "doc_count": state.pipeline.doc_count(),
            "field_count": len(state.schema.fields),
            "fields": {
                name: {
                    "type": fs.type.value,
                    "searchable": fs.searchable,
                    "filterable": fs.filterable,
                    "facetable": fs.facetable,
                }
                for name, fs in state.schema.fields.items()
            },
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        index_name: str,
        query: str,
        facet_fields: list[str] | None = None,
        page: int = 1,
        size: int | None = None,
    ) -> SearchResponse:
        t0 = time.perf_counter()
        state = self._get_index(index_name)
        size = size or self.config.default_page_size

        parsed = state.parser.parse(query, page=page, size=size, facet_fields=facet_fields)

        intent_result = state.intent_classifier.classify(parsed)
        parsed.intent = intent_result.intent
        parsed.intent_confidence = intent_result.confidence

        if self.config.search_full_pipeline:
            parsed.expanded_terms = state.expander.expand(parsed.text)
        else:
            parsed.expanded_terms = []

        if self.config.search_full_pipeline:
            n_retrieve = max(size * self.config.retrieval_multiplier, self.config.default_retrieval_size)
            candidates = state.fusion.fuse(parsed, n_results=n_retrieve)
        else:
            # Basic path: keyword retrieval honoring filters
            allowed_ids = None
            if parsed.filters:
                struct_results = state.fusion.structured.retrieve(parsed.filters)
                if not struct_results:
                    return SearchResponse(page=page, size=size, took_ms=self._elapsed(t0))
                allowed_ids = {c.doc_id for c in struct_results}
            
            # For basic path, we get enough for the current page
            candidates = state.keyword_retriever.retrieve(
                parsed.text, 
                n_results=page * size, 
                allowed_ids=allowed_ids
            )

        if not candidates:
            return SearchResponse(page=page, size=size, took_ms=self._elapsed(t0))

        if self.config.search_full_pipeline:
            bm25_scores: dict[str, float] = {}
            vector_scores: dict[str, float] = {}

            ranked = state.ranking.rank(
                parsed,
                candidates,
                state.documents,
                state.doc_texts,
                bm25_scores,
                vector_scores,
            )
        else:
            ranked = candidates

        start = (page - 1) * size
        page_candidates = ranked[start : start + size]

        hits = [
            SearchHit(
                document=state.documents[c.doc_id],
                score=c.score,
                explanation={
                    "source": c.source or ("keyword" if not self.config.search_full_pipeline else "unknown"),
                    "intent": intent_result.intent.value,
                    "intent_confidence": intent_result.confidence,
                    "pipeline": "full" if self.config.search_full_pipeline else "basic",
                },
            )
            for c in page_candidates
            if c.doc_id in state.documents
        ]

        facets: dict[str, FacetResult] = {}
        if self.config.search_full_pipeline and facet_fields:
            result_ids = {c.doc_id for c in ranked}
            facets = state.facet_aggregator.aggregate(result_ids, facet_fields)

        return SearchResponse(
            hits=hits,
            facets=facets,
            total=len(ranked),
            page=page,
            size=size,
            took_ms=self._elapsed(t0),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_index(self, name: str) -> _IndexState:
        if name not in self._indices:
            raise KeyError(f"Index '{name}' not found")
        return self._indices[name]

    def _get_embedding_provider(self) -> Any:
        if self._embedding_provider is not None:
            return self._embedding_provider

        try:
            from tools.rag.config import RAGConfig
            from tools.rag.embeddings.factory import get_embedding_provider

            rag_config = RAGConfig.from_env()
            rag_config.embedding_provider = self.config.embedding_provider
            rag_config.embedding_model = self.config.embedding_model
            self._embedding_provider = get_embedding_provider(
                self.config.embedding_provider,
                rag_config,
            )
        except ImportError:
            from tools.rag.embeddings.simple import SimpleEmbedding

            logger.warning("RAG embedding factory unavailable; using SimpleEmbedding fallback")
            self._embedding_provider = SimpleEmbedding()

        return self._embedding_provider

    def _create_vector_store(self, index_name: str) -> Any:
        backend = self.config.vector_store_backend
        if backend == "chromadb":
            try:
                from tools.rag.vector_store.chromadb_store import ChromaDBStore

                return ChromaDBStore(collection_name=f"search_{index_name}")
            except ImportError:
                logger.warning("chromadb not available, falling back to in-memory store")

        from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore

        return InMemoryDenseStore()

    @staticmethod
    def _elapsed(t0: float) -> float:
        return round((time.perf_counter() - t0) * 1000, 2)
