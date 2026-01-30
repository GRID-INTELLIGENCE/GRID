"""
GRID Secrets Package

Command-line interface for managing local encrypted secrets.

Usage:
    python -m grid.secrets set MY_KEY "my-value"
    python -m grid.secrets get MY_KEY
    python -m grid.secrets list
    python -m grid.secrets delete MY_KEY
"""

# This package is just a wrapper for the main module
from .__main__ import main

__all__ = ["main"]
