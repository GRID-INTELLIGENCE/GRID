"""Indexing pipeline: validates documents, generates embeddings, populates stores."""

from __future__ import annotations

import logging
import re
from typing import Any

from ..config import SearchConfig
from ..models import Document, FieldType, IndexSchema
from .structured_store import StructuredFieldIndex

logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"\b\w+\b")


class _FallbackBM25:
    def __init__(self, corpus: list[list[str]]) -> None:
        self._corpus = [set(tokens) for tokens in corpus]

    def get_scores(self, tokens: list[str]) -> list[float]:
        query_terms = set(tokens)
        if not query_terms:
            return [0.0] * len(self._corpus)
        scores: list[float] = []
        for doc_terms in self._corpus:
            exact_matches = len(query_terms & doc_terms)
            substring_matches = sum(0.5 for term in query_terms if any(term in doc_term for doc_term in doc_terms))
            scores.append(float(exact_matches * 2 + substring_matches))
        return scores


class IndexingPipeline:
    """Orchestrates document ingestion into vector, keyword, and structured stores."""

    def __init__(
        self,
        schema: IndexSchema,
        vector_store: Any,
        embedding_provider: Any,
        config: SearchConfig | None = None,
    ) -> None:
        self.schema = schema
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.config = config or SearchConfig()

        self.structured_index = StructuredFieldIndex(schema)
        self._bm25_corpus: list[list[str]] = []
        self._bm25_doc_ids: list[str] = []
        self._bm25_texts: list[str] = []
        self._bm25_instance: Any = None

    def index_batch(self, documents: list[Document]) -> int:
        """Index a batch of documents. Returns the count successfully indexed."""
        ids: list[str] = []
        texts: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []

        for doc in documents:
            self._validate(doc)

            search_text = self.build_search_text(doc)
            if not search_text.strip():
                logger.warning("Document %s has no searchable text, skipping", doc.id)
                continue

            embedding = self.embedding_provider.embed(search_text)
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

            ids.append(doc.id)
            texts.append(search_text)
            embeddings.append(embedding)
            metadatas.append(doc.fields)

            self.structured_index.add(doc.id, doc.fields)

            tokens = TOKEN_PATTERN.findall(search_text.lower())
            self._bm25_corpus.append(tokens)
            self._bm25_doc_ids.append(doc.id)
            self._bm25_texts.append(search_text)

        if ids:
            self.vector_store.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            self._rebuild_bm25()

        return len(ids)

    def remove(self, doc_id: str) -> None:
        self.structured_index.remove(doc_id)
        self.vector_store.delete(ids=[doc_id])

        if doc_id in self._bm25_doc_ids:
            idx = self._bm25_doc_ids.index(doc_id)
            self._bm25_doc_ids.pop(idx)
            self._bm25_corpus.pop(idx)
            self._bm25_texts.pop(idx)
            self._rebuild_bm25()

    @property
    def bm25(self) -> Any:
        return self._bm25_instance

    @property
    def bm25_doc_ids(self) -> list[str]:
        return self._bm25_doc_ids

    @property
    def bm25_texts(self) -> list[str]:
        return self._bm25_texts

    def doc_count(self) -> int:
        return self.structured_index.doc_count()

    def build_search_text(self, doc: Document) -> str:
        """Concatenate searchable fields weighted by their schema weight."""
        parts: list[str] = []
        for field_name, field_schema in self.schema.fields.items():
            if not field_schema.searchable:
                continue
            value = doc.fields.get(field_name)
            if value is None:
                continue
            text = str(value)
            repeat = max(1, int(field_schema.weight))
            parts.extend([text] * repeat)
        return " ".join(parts)

    def _validate(self, doc: Document) -> None:
        for field_name, field_schema in self.schema.fields.items():
            if field_name not in doc.fields:
                continue
            value = doc.fields[field_name]
            if field_schema.type == FieldType.INTEGER and not isinstance(value, int):
                try:
                    doc.fields[field_name] = int(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Field '{field_name}' expects integer, got {type(value).__name__}") from exc
            elif field_schema.type == FieldType.FLOAT and not isinstance(value, (int, float)):
                try:
                    doc.fields[field_name] = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Field '{field_name}' expects float, got {type(value).__name__}") from exc

    def _rebuild_bm25(self) -> None:
        if not self._bm25_corpus:
            self._bm25_instance = None
            return
        try:
            from rank_bm25 import BM25Okapi

            self._bm25_instance = BM25Okapi(self._bm25_corpus)
        except ImportError:
            logger.warning("rank_bm25 not installed; using fallback keyword scorer")
            self._bm25_instance = _FallbackBM25(self._bm25_corpus)
