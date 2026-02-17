"""
Application Integration Package

Provides integration between application layer and other GRID domains.
"""

from .tools_provider import ToolsProvider, get_tools_integration

__all__ = ["get_tools_integration", "ToolsProvider"]
