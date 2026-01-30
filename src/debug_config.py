#!/usr/bin/env python3
"""Debug script to verify RAG config loading."""

import os

from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

print("=== Environment Variables ===")
print(f"RAG_EMBEDDING_MODEL = {os.getenv('RAG_EMBEDDING_MODEL', 'NOT SET')}")
print(f"RAG_EMBEDDING_PROVIDER = {os.getenv('RAG_EMBEDDING_PROVIDER', 'NOT SET')}")
print(f"RAG_USE_HYBRID = {os.getenv('RAG_USE_HYBRID', 'NOT SET')}")
print(f"RAG_USE_RERANKER = {os.getenv('RAG_USE_RERANKER', 'NOT SET')}")

print("\n=== RAGConfig.from_env() ===")
from tools.rag.config import RAGConfig

config = RAGConfig.from_env()
print(f"embedding_model = {config.embedding_model}")
print(f"embedding_provider = {config.embedding_provider}")
print(f"use_hybrid = {config.use_hybrid}")
print(f"use_reranker = {config.use_reranker}")
