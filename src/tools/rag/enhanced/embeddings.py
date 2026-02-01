"""
Enhanced RAG with improved embedding model and retrieval
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

from .enrichment import RAGMetadataEnricher

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for enhanced retrieval"""

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 10
    similarity_threshold: float = 0.7
    rerank_top_k: int = 5
    enable_hybrid_search: bool = True
    enable_semantic_chunking: bool = True
    enable_kg_enrichment: bool = True


@dataclass
class ChunkMetadata:
    """Metadata for text chunks"""

    chunk_index: int
    total_chunks: int
    source_document: str
    chunk_type: str  # paragraph, code, list, etc.
    semantic_density: float
    technical_terms_count: int
    position_ratio: float


class EnhancedRAG:
    """Enhanced RAG with better embeddings and retrieval"""

    def __init__(self, config: RetrievalConfig, db_path: str = ".rag_db"):
        self.config = config
        self.model = SentenceTransformer(config.model_name)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("documents")
        self.logger = logging.getLogger(f"{__name__}.EnhancedRAG")
        self.enricher = RAGMetadataEnricher() if config.enable_kg_enrichment else None

    def enhanced_chunking(self, text: str) -> list[tuple[str, ChunkMetadata]]:
        """Improved text chunking with semantic awareness"""
        chunks = []

        if self.config.enable_semantic_chunking:
            chunks = self._semantic_chunking(text)
        else:
            chunks = self._paragraph_chunking(text)

        # Add metadata to each chunk
        chunk_data = []
        for i, (chunk_text, chunk_type) in enumerate(chunks):
            metadata = ChunkMetadata(
                chunk_index=i,
                total_chunks=len(chunks),
                source_document="",  # Will be set during indexing
                chunk_type=chunk_type,
                semantic_density=self._calculate_semantic_density(chunk_text),
                technical_terms_count=self._count_technical_terms(chunk_text),
                position_ratio=i / len(chunks) if chunks else 0,
            )
            chunk_data.append((chunk_text, metadata))

        return chunk_data

    def _semantic_chunking(self, text: str) -> list[tuple[str, str]]:
        """Chunk text based on semantic boundaries"""
        chunks = []

        # Split by major sections
        sections = re.split(r"\n#{1,3}\s+", text)

        for section in sections:
            if not section.strip():
                continue

            # Further split by paragraphs within sections
            paragraphs = section.split("\n\n")

            current_chunk = ""
            current_type = "paragraph"

            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue

                # Detect paragraph type
                if "```" in paragraph:
                    chunk_type = "code"
                elif paragraph.strip().startswith(("- ", "* ", "1. ", "2. ")):
                    chunk_type = "list"
                else:
                    chunk_type = "paragraph"

                # If type changes or chunk too large, save current chunk
                if (current_chunk and chunk_type != current_type) or (
                    len(current_chunk) + len(paragraph) > self.config.chunk_size
                ):
                    if current_chunk.strip():
                        chunks.append((current_chunk.strip(), current_type))

                    current_chunk = paragraph + "\n\n"
                    current_type = chunk_type
                else:
                    current_chunk += paragraph + "\n\n"

            # Add remaining chunk
            if current_chunk.strip():
                chunks.append((current_chunk.strip(), current_type))

        return chunks

    def _paragraph_chunking(self, text: str) -> list[tuple[str, str]]:
        """Simple paragraph-based chunking"""
        paragraphs = text.split("\n\n")
        chunks = []

        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < self.config.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append((current_chunk.strip(), "paragraph"))

                # Handle very long paragraphs
                if len(paragraph) > self.config.chunk_size:
                    words = paragraph.split()
                    for i in range(0, len(words), self.config.chunk_size // 10):
                        chunk_words = words[i : i + self.config.chunk_size // 10]
                        chunks.append((" ".join(chunk_words), "paragraph"))
                else:
                    current_chunk = paragraph + "\n\n"

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append((current_chunk.strip(), "paragraph"))

        return chunks

    def _calculate_semantic_density(self, text: str) -> float:
        """Calculate semantic density of text"""
        if not text.strip():
            return 0.0

        # Count meaningful words (non-stopwords)
        words = text.lower().split()
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]

        # Count unique concepts
        unique_words = set(meaningful_words)

        # Density = unique meaningful words / total words
        density = len(unique_words) / len(words) if words else 0.0

        return min(density, 1.0)

    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""
        # Look for patterns that indicate technical content
        patterns = [
            r"\b[A-Z]{2,}\b",  # Acronyms
            r"\b\w+_\w+\b",  # Snake_case
            r"\b\w+\(\)",  # Function calls
            r"\b\w+\.\w+",  # Dotted notation
            r"\b\w+\[\]",  # Array access
        ]

        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            count += len(matches)

        return count

    def embed_with_metadata(self, chunks: list[tuple[str, ChunkMetadata]]) -> list[np.ndarray]:
        """Create embeddings with rich metadata"""
        chunk_texts = [chunk[0] for chunk in chunks]
        chunk_metadata = [chunk[1] for chunk in chunks]

        # Get base embeddings
        base_embeddings = self.model.encode(chunk_texts, convert_to_numpy=True)

        # Create enhanced embeddings with metadata features
        enhanced_embeddings = []

        for i, (base_embedding, metadata) in enumerate(zip(base_embeddings, chunk_metadata, strict=False)):
            # Extract semantic features from metadata
            semantic_features = np.array(
                [
                    metadata.semantic_density,
                    metadata.technical_terms_count / 10.0,  # Normalize
                    metadata.position_ratio,
                    1.0 if metadata.chunk_type == "code" else 0.0,
                    1.0 if metadata.chunk_type == "list" else 0.0,
                    len(chunk_texts[i]) / 1000.0,  # Text length normalized
                ]
            )

            # Combine base embedding with semantic features
            # Pad semantic features to match base embedding dimension if needed
            if len(semantic_features) < base_embedding.shape[0]:
                padding = np.zeros(base_embedding.shape[0] - len(semantic_features))
                semantic_features = np.concatenate([semantic_features, padding])
            else:
                semantic_features = semantic_features[: base_embedding.shape[0]]

            # Weighted combination
            enhanced_embedding = 0.9 * base_embedding + 0.1 * semantic_features
            enhanced_embeddings.append(enhanced_embedding)

        return enhanced_embeddings

    def hybrid_search(self, query: str, top_k: int = None) -> list[dict]:
        """Hybrid search combining semantic and keyword matching"""
        if top_k is None:
            top_k = self.config.top_k

        # Semantic search
        query_embedding = self.model.encode([query])[0]
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k * 2,  # Get more for hybrid combination
        )

        # Keyword search
        keyword_results = self._keyword_search(query, top_k * 2)

        # Combine results
        combined_results = self._combine_search_results(semantic_results, keyword_results, query)

        # Filter by threshold and return top results
        filtered_results = [r for r in combined_results if r["combined_score"] >= self.config.similarity_threshold]

        return filtered_results[: self.config.rerank_top_k]

    def _keyword_search(self, query: str, top_k: int) -> list[dict]:
        """Simple keyword-based search"""
        query_words = set(query.lower().split())

        # Get all documents
        all_docs = self.collection.get()
        keyword_scores = []

        for i, doc in enumerate(all_docs["documents"]):
            if not doc:
                continue

            doc_words = set(doc.lower().split())

            # Calculate keyword relevance
            overlap = len(query_words.intersection(doc_words))
            jaccard = overlap / len(query_words.union(doc_words)) if query_words.union(doc_words) else 0

            # Boost for exact phrase matches
            phrase_boost = 1.0
            if query.lower() in doc.lower():
                phrase_boost = 1.5

            keyword_scores.append(
                {
                    "id": all_docs["ids"][i],
                    "document": doc,
                    "metadata": all_docs["metadatas"][i],
                    "keyword_score": jaccard * phrase_boost,
                }
            )

        # Sort by keyword score and return top_k
        keyword_scores.sort(key=lambda x: x["keyword_score"], reverse=True)
        return keyword_scores[:top_k]

    def _combine_search_results(self, semantic_results: dict, keyword_results: list[dict], query: str) -> list[dict]:
        """Combine semantic and keyword search results"""
        combined_results = []

        # Create lookup for keyword results
        keyword_lookup = {r["id"]: r for r in keyword_results}

        # Process semantic results
        semantic_ids = semantic_results["ids"][0] if semantic_results["ids"] else []
        semantic_distances = semantic_results["distances"][0] if semantic_results["distances"] else []
        semantic_docs = semantic_results["documents"][0] if semantic_results["documents"] else []
        semantic_metas = semantic_results["metadatas"][0] if semantic_results["metadatas"] else []

        for i, doc_id in enumerate(semantic_ids):
            # Convert distance to similarity
            semantic_score = 1 - semantic_distances[i]

            # Get keyword score if available
            keyword_result = keyword_lookup.get(doc_id)
            keyword_score = keyword_result["keyword_score"] if keyword_result else 0.0

            # Calculate combined score (weighted average)
            combined_score = 0.7 * semantic_score + 0.3 * keyword_score

            # Apply reranking based on query relevance
            rerank_boost = self._calculate_rerank_boost(semantic_docs[i], query, semantic_metas[i])

            final_score = combined_score * rerank_boost

            combined_results.append(
                {
                    "id": doc_id,
                    "document": semantic_docs[i],
                    "metadata": semantic_metas[i],
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "combined_score": final_score,
                    "rerank_boost": rerank_boost,
                }
            )

        # Add keyword-only results that weren't in semantic results
        for keyword_result in keyword_results:
            if keyword_result["id"] not in semantic_ids:
                combined_results.append(
                    {
                        "id": keyword_result["id"],
                        "document": keyword_result["document"],
                        "metadata": keyword_result["metadata"],
                        "semantic_score": 0.0,
                        "keyword_score": keyword_result["keyword_score"],
                        "combined_score": keyword_result["keyword_score"] * 0.5,  # Downweight keyword-only
                        "rerank_boost": 1.0,
                    }
                )

        # Sort by final score
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined_results

    def _calculate_rerank_boost(self, document: str, query: str, metadata: dict) -> float:
        """Calculate reranking boost based on various factors"""
        boost = 1.0

        # Boost for exact query matches
        if query.lower() in document.lower():
            boost *= 1.2

        # Boost for code chunks in technical queries
        if metadata.get("chunk_type") == "code" and any(
            term in query.lower() for term in ["function", "code", "implement", "example"]
        ):
            boost *= 1.1

        # Boost for high semantic density
        semantic_density = metadata.get("semantic_density", 0.0)
        if semantic_density > 0.7:
            boost *= 1.05

        # Boost for recent documents (if timestamp available)
        if "indexed_at" in metadata:
            try:
                indexed_date = datetime.fromisoformat(metadata["indexed_at"])
                days_old = (datetime.now() - indexed_date).days
                if days_old < 7:
                    boost *= 1.05
            except (ValueError, KeyError, TypeError):
                pass

        return boost

    def index_document(self, text: str, metadata: dict) -> list[str]:
        """Index document with enhanced processing"""
        # Generate chunks with metadata
        chunk_data = self.enhanced_chunking(text)

        # Create embeddings
        embeddings = self.embed_with_metadata(chunk_data)

        # Index chunks
        ids = []
        for i, ((chunk_text, chunk_metadata), embedding) in enumerate(zip(chunk_data, embeddings, strict=False)):
            doc_id = f"{metadata.get('doc_id', 'doc')}_{i}"

            # Combine document metadata with chunk metadata
            chunk_dict_metadata = chunk_metadata.__dict__

            # Apply KG enrichment if enabled
            if self.enricher:
                chunk_dict_metadata = self.enricher.enrich_metadata(chunk_text, chunk_dict_metadata)

            combined_metadata = {
                **metadata,
                **chunk_dict_metadata,
                "indexed_at": datetime.now().isoformat(),
                "chunk_preview": chunk_text[:200],  # Preview for search results
            }

            self.collection.add(
                ids=[doc_id], documents=[chunk_text], embeddings=[embedding.tolist()], metadatas=[combined_metadata]
            )

            ids.append(doc_id)

        self.logger.info(f"Indexed document {metadata.get('doc_id', 'unknown')} with {len(ids)} chunks")
        return ids

    def get_retrieval_stats(self) -> dict[str, Any]:
        """Get statistics about the retrieval system"""
        try:
            collection_info = self.collection.get()

            stats = {
                "total_documents": len(set(collection_info["metadatas"] or [])),
                "total_chunks": len(collection_info["ids"] or []),
                "chunk_types": {},
                "avg_semantic_density": 0.0,
                "index_timestamp": datetime.now().isoformat(),
            }

            # Analyze chunk types and semantic density
            if collection_info["metadatas"]:
                semantic_densities = []
                for meta in collection_info["metadatas"]:
                    chunk_type = meta.get("chunk_type", "unknown")
                    stats["chunk_types"][chunk_type] = stats["chunk_types"].get(chunk_type, 0) + 1

                    density = meta.get("semantic_density", 0.0)
                    if density > 0:
                        semantic_densities.append(density)

                if semantic_densities:
                    stats["avg_semantic_density"] = sum(semantic_densities) / len(semantic_densities)

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get retrieval stats: {e}")
            return {"error": str(e)}

    def search_with_context(self, query: str, max_context_length: int = 2000) -> dict[str, Any]:
        """Search with contextual information"""
        results = self.hybrid_search(query)

        # Build context from top results
        context_chunks = []
        context_length = 0

        for result in results:
            chunk = result["document"]
            if context_length + len(chunk) <= max_context_length:
                context_chunks.append(chunk)
                context_length += len(chunk)
            else:
                # Add partial chunk if space allows
                remaining_space = max_context_length - context_length
                if remaining_space > 100:  # Only add if meaningful space remains
                    context_chunks.append(chunk[:remaining_space] + "...")
                break

        context = "\n\n".join(context_chunks)

        return {
            "query": query,
            "context": context,
            "results": results,
            "context_length": len(context),
            "sources_used": len(
                [r for r in results if r["id"] in [res["id"] for res in results[: len(context_chunks)]]]
            ),
        }
