"""
Tests for Parasite Guard system.

Tests are organized by component:
- test_detectors.py: Tests for C1, C2, C3 detectors
- test_middleware.py: Tests for middleware and ASGI integration
- test_init.py: Test fixtures and utilities

Usage:
    pytest infrastructure/parasite_guard/tests/ -v
    pytest infrastructure/parasite_guard/tests/test_detectors.py::TestWebSocketNoAckDetector -v
"""

from __future__ import annotations

__version__ = "1.0.0"
