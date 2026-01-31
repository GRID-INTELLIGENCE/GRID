"""
Vector Embedding Engine
=======================

Handles generation and management of vector embeddings for document chunks.
Supports OpenAI embeddings with batch processing and caching.
"""

import asyncio
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import numpy as np
from openai import OpenAI

from ..core.config import KnowledgeBaseConfig
from ..core.database import KnowledgeBaseDB

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    embedding: list[float]
    token_count: int
    model: str
    processing_time: float


class EmbeddingEngine:
    """Vector embedding engine for document chunks."""

    def __init__(self, config: KnowledgeBaseConfig, db: KnowledgeBaseDB):
        self.config = config
        self.db = db

        # Initialize OpenAI client
        self.client = OpenAI(api_key=config.embeddings.api_key)

        # Initialize cache
        self.embedding_cache: dict[str, list[float]] = {}

        # Thread pool for batch processing
        self.executor = ThreadPoolExecutor(max_workers=4)

    def generate_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text."""
        start_time = time.time()

        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            cached_embedding = self.embedding_cache[text_hash]
            return EmbeddingResult(
                text=text,
                embedding=cached_embedding,
                token_count=len(text.split()),
                model=self.config.embeddings.model,
                processing_time=time.time() - start_time
            )

        try:
            # Call OpenAI API using new client
            response = self.client.embeddings.create(
                model=self.config.embeddings.model,
                input=text,
                user="knowledge-base"
            )

            embedding = response.data[0].embedding
            token_count = response.usage.total_tokens

            # Cache the result
            self.embedding_cache[text_hash] = embedding

            processing_time = time.time() - start_time

            logger.debug(f"Generated embedding for text ({len(text)} chars) in {processing_time:.2f}s")

            return EmbeddingResult(
                text=text,
                embedding=embedding,
                token_count=token_count,
                model=self.config.embeddings.model,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def generate_embeddings_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts in batch."""
        if not texts:
            return []

        start_time = time.time()
        results = []

        # Process in batches to respect API limits
        batch_size = self.config.embeddings.batch_size

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            # Check cache for this batch
            uncached_texts = []
            uncached_indices = []

            for j, text in enumerate(batch_texts):
                text_hash = hashlib.md5(text.encode()).hexdigest()
                if text_hash in self.embedding_cache:
                    cached_embedding = self.embedding_cache[text_hash]
                    results.append(EmbeddingResult(
                        text=text,
                        embedding=cached_embedding,
                        token_count=len(text.split()),
                        model=self.config.embeddings.model,
                        processing_time=0.0  # Cached, no API call
                    ))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(j)

            # Generate embeddings for uncached texts
            if uncached_texts:
                try:
                    response = self.client.embeddings.create(
                        model=self.config.embeddings.model,
                        input=uncached_texts,
                        user="knowledge-base"
                    )

                    for j, data in enumerate(response.data):
                        original_index = uncached_indices[j]
                        text = uncached_texts[j]
                        embedding = data.embedding

                        # Cache the result
                        text_hash = hashlib.md5(text.encode()).hexdigest()
                        self.embedding_cache[text_hash] = embedding

                        results.append(EmbeddingResult(
                            text=text,
                            embedding=embedding,
                            token_count=len(text.split()),
                            model=self.config.embeddings.model,
                            processing_time=time.time() - start_time
                        ))

                except Exception as e:
                    logger.error(f"Batch embedding generation failed: {e}")
                    # Add failed results
                    for text in uncached_texts:
                        results.append(EmbeddingResult(
                            text=text,
                            embedding=[],
                            token_count=0,
                            model=self.config.embeddings.model,
                            processing_time=time.time() - start_time
                        ))

        total_time = time.time() - start_time
        logger.info(f"Generated embeddings for {len(texts)} texts in {total_time:.2f}s")

        return results

    async def generate_embeddings_async(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.generate_embeddings_batch,
            texts
        )

    def update_chunk_embeddings(self, limit: int = 100) -> int:
        """Update embeddings for chunks that don't have them."""
        updated_count = 0

        with self.db.session() as cursor:
            # Get chunks without embeddings
            cursor.execute("""
                SELECT id, content FROM kb_chunks
                WHERE embedding IS NULL OR embedding = '' OR embedding = '[]'
                LIMIT ?
            """, (limit,))

            chunks = cursor.fetchall()

            if not chunks:
                logger.info("No chunks need embedding updates")
                return 0

            # Extract texts for embedding
            chunk_data = []
            for row in chunks:
                chunk_data.append({
                    'id': row[0],
                    'content': row[1]
                })

            # Generate embeddings
            texts = [chunk['content'] for chunk in chunk_data]
            results = self.generate_embeddings_batch(texts)

            # Update chunks with embeddings
            for chunk, result in zip(chunk_data, results):
                if result.embedding:
                    cursor.execute("""
                        UPDATE kb_chunks
                        SET embedding = ?
                        WHERE id = ?
                    """, (json.dumps(result.embedding), chunk['id']))
                    updated_count += 1

        logger.info(f"Updated embeddings for {updated_count} chunks")
        return updated_count

    def search_similar(self, query: str, limit: int = 10,
                      threshold: float = 0.7) -> list[tuple[str, float, dict[str, Any]]]:
        """Find chunks similar to query using embeddings."""
        # Generate embedding for query
        query_result = self.generate_embedding(query)
        query_embedding = np.array(query_result.embedding)

        similar_chunks = []

        with self.db.session() as cursor:
            # Get all chunks with embeddings (simplified - in production use vector DB)
            cursor.execute("""
                SELECT id, content, embedding, extra_metadata
                FROM kb_chunks
                WHERE embedding IS NOT NULL AND embedding != ''
            """)

            rows = cursor.fetchall()

            for row in rows:
                chunk_id, content, embedding_str, metadata_str = row

                # Parse embedding and metadata
                embedding = json.loads(embedding_str) if embedding_str else []
                metadata = json.loads(metadata_str) if metadata_str else {}

                if embedding:
                    chunk_embedding = np.array(embedding)

                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                    )

                    if similarity >= threshold:
                        similar_chunks.append((
                            content,
                            float(similarity),
                            {
                                "chunk_id": chunk_id,
                                "metadata": metadata
                            }
                        ))

        # Sort by similarity and return top results
        similar_chunks.sort(key=lambda x: x[1], reverse=True)
        return similar_chunks[:limit]

    def get_embedding_stats(self) -> dict[str, Any]:
        """Get embedding statistics."""
        total_chunks = self.db.get_chunk_count()

        with self.db.session() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM kb_chunks
                WHERE embedding IS NOT NULL AND embedding != ''
            """)
            embedded_chunks = cursor.fetchone()[0]

        return {
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
            "embedding_coverage": embedded_chunks / total_chunks if total_chunks > 0 else 0,
            "cache_size": len(self.embedding_cache),
            "model": self.config.embeddings.model,
            "dimensions": self.config.embeddings.dimensions
        }

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")

    def preload_common_embeddings(self, common_texts: list[str]) -> None:
        """Preload embeddings for commonly used texts."""
        if not common_texts:
            return

        logger.info(f"Preloading embeddings for {len(common_texts)} common texts")

        # Generate embeddings for common texts
        results = self.generate_embeddings_batch(common_texts)

        # Cache them
        for text, result in zip(common_texts, results):
            if result.embedding:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self.embedding_cache[text_hash] = result.embedding

        logger.info("Common text embeddings preloaded")
