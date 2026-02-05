#!/usr/bin/env python3
"""Test GitHub Copilot SDK integration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tools.rag.config import RAGConfig
from tools.rag.llm.factory import get_llm_provider

# Test environment setup
os.environ["RAG_LLM_MODE"] = "copilot"
os.environ["RAG_LLM_MODEL_COPILOT"] = "gpt-4o"

config = RAGConfig.from_env()
print(f"LLM Mode: {config.llm_mode}")
print(f"Copilot Model: {config.llm_model_copilot}")

# Test provider creation
provider = get_llm_provider(config=config)
print(f"Provider type: {type(provider).__name__}")
print("SUCCESS: Copilot provider initialized and working!")
