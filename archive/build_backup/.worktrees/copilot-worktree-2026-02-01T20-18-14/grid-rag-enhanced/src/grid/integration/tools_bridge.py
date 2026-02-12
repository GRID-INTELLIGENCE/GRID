"""
Grid Domain Tools Bridge

Bridge between grid/ domain and tools/ domain with lazy loading
and fallback mechanisms. Maintains backward compatibility with
existing grid/rag imports while providing unified access to tools.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolsBridge:
    """
    Bridge between grid/ domain and tools/ domain.

    Provides unified access to tools through grid namespace with
    lazy loading and graceful degradation.
    """

    def __init__(self) -> None:
        """Initialize tools bridge."""
        self._tools_integration: Any | None = None
        self._rag_engine_cache: Any | None = None

    def _get_tools_integration(self) -> Any:
        """Lazy load tools integration."""
        if self._tools_integration is None:
            try:
                from tools.integration import get_tools_integration

                self._tools_integration = get_tools_integration()
            except ImportError:
                logger.warning("Tools integration not available")
                return None
        return self._tools_integration

    def get_rag_engine(self, config: Any | None = None) -> Any | None:
        """
        Get RAG engine through tools bridge.

        Args:
            config: Optional RAGConfig override

        Returns:
            RAGEngine instance or None if unavailable
        """
        integration = self._get_tools_integration()
        if integration is None:
            return None

        return integration.get_rag_engine(config=config)

    def get_rag_config(self) -> Any | None:
        """
        Get RAG configuration through tools bridge.

        Returns:
            RAGConfig instance or None if unavailable
        """
        integration = self._get_tools_integration()
        if integration is None:
            return None

        return integration.get_rag_config()

    def is_rag_available(self) -> bool:
        """
        Check if RAG is available through tools bridge.

        Returns:
            True if RAG is available, False otherwise
        """
        integration = self._get_tools_integration()
        if integration is None:
            return False

        return bool(integration.is_available("rag"))

    def get_agent_processor(self, knowledge_base_path: str | None = None) -> Any | None:
        """
        Get agent processor through tools bridge.

        Args:
            knowledge_base_path: Optional path to knowledge base

        Returns:
            ProcessingUnit instance or None if unavailable
        """
        integration = self._get_tools_integration()
        if integration is None:
            return None

        return integration.get_agent_processor(knowledge_base_path=knowledge_base_path)

    def is_agent_processor_available(self) -> bool:
        """
        Check if agent processor is available through tools bridge.

        Returns:
            True if agent processor is available, False otherwise
        """
        integration = self._get_tools_integration()
        if integration is None:
            return False

        return bool(integration.is_available("agent_prompts"))


# Global instance (singleton pattern)
_tools_bridge_instance: ToolsBridge | None = None


def get_tools_bridge() -> ToolsBridge:
    """
    Get the global ToolsBridge instance (singleton).

    Returns:
        ToolsBridge instance
    """
    global _tools_bridge_instance
    if _tools_bridge_instance is None:
        _tools_bridge_instance = ToolsBridge()
    return _tools_bridge_instance


__all__ = ["ToolsBridge", "get_tools_bridge"]
