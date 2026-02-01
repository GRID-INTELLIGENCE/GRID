#!/usr/bin/env python3
"""
Comprehensive Knowledge Base Test Script
=========================================

Tests document ingestion, search functionality, and LLM generation.
"""
import pytest

pytest.importorskip("openai", reason="openai not installed")

import time

from knowledge_base.core.config import KnowledgeBaseConfig
from knowledge_base.core.database import DocumentData, KnowledgeBaseDB
from knowledge_base.embeddings.engine import EmbeddingEngine
from knowledge_base.embeddings.llm_generator import LLMGenerator
from knowledge_base.ingestion.pipeline import DataIngestionPipeline
from knowledge_base.search.retriever import VectorRetriever


def main():
    print("🚀 Starting comprehensive Knowledge Base test...")

    # Initialize components
    config = KnowledgeBaseConfig.from_env()
    db = KnowledgeBaseDB(config)
    db.connect()

    ingestion_pipeline = DataIngestionPipeline(config, db)
    embedding_engine = EmbeddingEngine(config, db)
    retriever = VectorRetriever(config, db, embedding_engine)
    llm_generator = LLMGenerator(config)

    print("✅ All components initialized")

    # Sample documents to ingest
    sample_docs = [
        {
            "title": "Introduction to Machine Learning",
            "content": """Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or decisions based on those patterns. There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.""",
        },
        {
            "title": "Vector Databases Explained",
            "content": """Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently. They use advanced indexing techniques like HNSW (Hierarchical Navigable Small World) or IVF (Inverted File) to enable fast similarity search. Vector databases are essential for modern AI applications including semantic search, recommendation systems, and computer vision tasks.""",
        },
        {
            "title": "Retrieval Augmented Generation",
            "content": """Retrieval Augmented Generation (RAG) is a technique that combines the strengths of retrieval-based and generation-based approaches in natural language processing. It works by first retrieving relevant documents from a knowledge base, then using those documents as context for a language model to generate more accurate and grounded responses. RAG is particularly effective for question-answering systems and knowledge management applications.""",
        },
        {
            "title": "Knowledge Base Systems",
            "content": """Knowledge base systems are structured repositories of information designed to store, organize, and retrieve knowledge effectively. They typically include features like semantic search, relationship mapping, and automated reasoning. Modern knowledge bases often incorporate AI technologies like natural language processing and machine learning to provide intelligent access to stored information.""",
        },
    ]

    print("📄 Ingesting sample documents...")

    # Ingest documents
    ingestion_results = []
    for i, doc in enumerate(sample_docs, 1):
        print(f'  Processing document {i}: {doc["title"]}')

        # Create document data
        doc_data = DocumentData(
            id=f"sample_doc_{i}",
            title=doc["title"],
            content=doc["content"],
            source_type="sample",
            source_path="",
            file_type="txt",
            metadata={"sample": True, "index": i},
        )

        # Process document
        result = ingestion_pipeline._process_document(doc_data)
        ingestion_results.append(result)

        print(f"    ✅ Created {result.chunks_created} chunks")

    print(
        f"📊 Ingestion complete: {len(ingestion_results)} documents, {sum(r.chunks_created for r in ingestion_results)} total chunks"
    )

    # Update embeddings for the chunks
    print("🧠 Generating embeddings for chunks...")
    updated_chunks = embedding_engine.update_chunk_embeddings(limit=100)
    print(f"✅ Generated embeddings for {updated_chunks} chunks")

    # Test search functionality
    print("🔍 Testing search functionality...")

    test_queries = [
        "What is machine learning?",
        "How do vector databases work?",
        "Explain retrieval augmented generation",
        "What are knowledge base systems?",
    ]

    for query in test_queries:
        print(f'  Query: "{query}"')

        start_time = time.time()
        results = retriever.search(query, limit=3)
        search_time = time.time() - start_time

        print(f"    Found {len(results)} results in {search_time:.3f}s")
        for result in results[:2]:  # Show top 2 results
            print(f"      - {result.document_title}: {result.content[:100]}...")

    # Test LLM generation
    print("🤖 Testing LLM generation...")

    test_question = "What is the difference between machine learning and traditional programming?"
    print(f'  Question: "{test_question}"')

    # Get context for the question
    context_results = retriever.search(test_question, limit=3)

    if context_results:
        generation_request = llm_generator.GenerationRequest(
            query=test_question, context=context_results, max_tokens=200
        )

        start_time = time.time()
        answer = llm_generator.generate_answer(generation_request)
        generation_time = time.time() - start_time

        print(f"    Generated answer in {generation_time:.3f}s")
        print(f"    Answer: {answer.answer[:200]}...")
        print(f'    Confidence: {answer.confidence_score}, Tokens: {answer.token_usage["total_tokens"]}')
    else:
        print("    No context found for generation test")

    # Final statistics
    print("📈 Final Knowledge Base Statistics:")
    print(f"  Documents: {db.get_document_count()}")
    print(f"  Chunks: {db.get_chunk_count()}")
    print(f'  Embedding coverage: {embedding_engine.get_embedding_stats()["embedding_coverage"]:.1%}')

    db.disconnect()
    print("✅ Comprehensive Knowledge Base test completed successfully!")


if __name__ == "__main__":
    main()
