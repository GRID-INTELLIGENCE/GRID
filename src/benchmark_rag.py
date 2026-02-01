#!/usr/bin/env python3
"""Benchmark script to measure RAG quality."""

import asyncio
import sys

# Add src to path
sys.path.insert(0, "src")

from tools.rag.config import RAGConfig
from tools.rag.rag_engine import RAGEngine


async def benchmark() -> None:
    config = RAGConfig.from_env()
    engine = RAGEngine(config=config)

    queries = [
        "How is the project indexed for RAG?",
        "What models are used for embeddings?",
        "Explain the purpose of the MultiModelOrchestrator.",
    ]

    print(f"{'Query':<50} | {'Relevance':<10} | {'Sources':<8}")
    print("-" * 75)

    for q in queries:
        result = await engine.query(q, top_k=5)
        metrics = result.get("evaluation_metrics", {})
        relevance = metrics.get("context_relevance_avg", 0.0)
        num_sources = len(result.get("sources", []))

        print(f"{q[:50]:<50} | {relevance:10.4f} | {num_sources:<8}")


if __name__ == "__main__":
    asyncio.run(benchmark())
