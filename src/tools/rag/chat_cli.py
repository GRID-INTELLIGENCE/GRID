#!/usr/bin/env python3
"""
Quiet launcher for RAG Chat CLI.

This script sets environment variables BEFORE any imports happen,
ensuring noisy logging from application modules is suppressed.

Usage:
    python -m tools.rag.chat_cli
    python -m tools.rag.chat_cli --model qwen2.5-coder:latest
    python -m tools.rag.chat_cli --query "What is GRID?"
"""

# Set quiet mode and suppress noisy config BEFORE any other imports
import os
import sys

os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"
os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress all logging before imports trigger side effects
import logging
import warnings

logging.basicConfig(level=logging.CRITICAL, force=True)
logging.getLogger().setLevel(logging.CRITICAL)

# Suppress specific noisy loggers
for name in [
    "httpx",
    "sentence_transformers",
    "application",
    "chromadb",
    "transformers",
    "huggingface_hub",
    "urllib3",
    "asyncio",
    "application.mothership",
    "application.mothership.security",
    "application.mothership.security.api_sentinels",
    "application.mothership.main",
    "uvicorn",
    "fastapi",
]:
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Now safe to import and run
if __name__ == "__main__":
    from tools.rag.chat import main

    sys.exit(main())
