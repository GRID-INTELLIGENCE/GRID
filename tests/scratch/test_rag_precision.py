#!/usr/bin/env python3
"""Test RAG precision after rebuild."""

import os

# Use a valid public model that doesn't require authentication
os.environ["RAG_EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"

from tools.rag.config import RAGConfig
from tools.rag.rag_engine import RAGEngine


def test_precision():
    config = RAGConfig.from_env()
    config.ensure_local_only()

    engine = RAGEngine(config)

    # Test queries related to the thoughtmap implementation
    test_queries = [
        "cognitive state capture",
        "pattern recognition",
        "thoughtmap visualization",
        "quantum engine",
        "path visualizer",
    ]

    print("=== RAG Precision Test ===\n")

    for query in test_queries:
        print(f"Query: {query}")
        try:
            query_embedding = engine.embedding_provider.embed(query)
            results = engine.vector_store.query(query_embedding=query_embedding, n_results=3)

            print(f"  Found {len(results['documents'])} documents:")
            for i, doc in enumerate(results["documents"], 1):
                # Show first 100 chars
                snippet = doc[:100].replace("\n", " ")
                print(f"    {i}. {snippet}...")
            print()

        except Exception as e:
            print(f"  Error: {e}\n")

    # Show overall stats
    stats = engine.get_stats()
    print(f"Total indexed documents: {stats['document_count']}")
    print(f"Collection: {stats['collection_name']}")


if __name__ == "__main__":
    test_precision()
