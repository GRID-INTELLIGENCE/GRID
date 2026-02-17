"""Unit test configuration.

Ensures src/ is at the beginning of sys.path to prevent shadowing
of the grid package by the root-level grid/ directory.
"""

import os
import sys

# Ensure src is at the very beginning of sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")

# Remove any existing src entries and re-add at position 0
sys.path = [p for p in sys.path if p != SRC_DIR]
sys.path.insert(0, SRC_DIR)
