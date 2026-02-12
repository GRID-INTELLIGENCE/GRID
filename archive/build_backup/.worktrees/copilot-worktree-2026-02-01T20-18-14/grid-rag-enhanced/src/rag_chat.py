#!/usr/bin/env python3
"""
Standalone RAG Chat Launcher.

This script sets environment variables BEFORE any package imports happen,
ensuring noisy logging from application modules is suppressed.

Usage:
    python rag_chat.py
    python rag_chat.py --model qwen2.5-coder:latest
    python rag_chat.py --query "What is GRID?"

Or after installing the package:
    rag-chat
    rag-chat --model ministral-3:3b
"""

# =============================================================================
# CRITICAL: Set environment variables BEFORE any imports
# =============================================================================
import os
import sys

# Suppress noisy configs and logging
os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"
os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# =============================================================================
# Configure logging to suppress everything before imports
# =============================================================================
import logging
import warnings

# Set root logger to CRITICAL
logging.basicConfig(level=logging.CRITICAL, force=True)
logging.getLogger().setLevel(logging.CRITICAL)

# Pre-suppress known noisy loggers
_NOISY_LOGGERS = [
    "httpx",
    "sentence_transformers",
    "application",
    "application.mothership",
    "application.mothership.config",
    "application.mothership.security",
    "application.mothership.security.api_sentinels",
    "application.mothership.main",
    "chromadb",
    "transformers",
    "huggingface_hub",
    "urllib3",
    "asyncio",
    "uvicorn",
    "fastapi",
]

for name in _NOISY_LOGGERS:
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.handlers = []

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# =============================================================================
# Now safe to import and run the chat module
# =============================================================================


def main() -> int:
    """Main entry point."""
    # Import here after env is configured
    from tools.rag.chat import main as chat_main

    return chat_main()


if __name__ == "__main__":
    sys.exit(main())
