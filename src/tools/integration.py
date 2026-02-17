"""
Tools Domain Integration Layer

Unified interface for integrating tools.rag, tools.agent_prompts, and EQ module
into the GRID architecture. Uses service locator pattern with lazy loading
and graceful degradation.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ToolsIntegration:
    """
    Unified interface for Tools domain integration.

    Provides service locator pattern for tool discovery with lazy loading
    and graceful degradation when tools are unavailable.
    """

    def __init__(self) -> None:
        """Initialize tools integration with lazy loading."""
        self._rag_engine: Any | None = None
        self._rag_config: Any | None = None
        self._agent_processor: Any | None = None
        self._api_clients: dict[str, Any] = {}
        self._availability_cache: dict[str, bool] = {}

    def get_rag_engine(self, config: Any | None = None) -> Any | None:
        """
        Get RAG engine instance with lazy loading.

        Args:
            config: Optional RAGConfig override

        Returns:
            RAGEngine instance or None if unavailable
        """
        if not self.is_available("rag"):
            return None

        if self._rag_engine is None:
            try:
                from tools.rag.config import RAGConfig
                from tools.rag.rag_engine import RAGEngine

                if config is None:
                    config = RAGConfig.from_env()

                self._rag_engine = RAGEngine(config=config)
                logger.info("RAG engine initialized successfully")
            except ImportError as e:
                logger.warning(f"RAG engine not available: {e}")
                self._availability_cache["rag"] = False
                return None
            except Exception as e:
                logger.error(f"Failed to initialize RAG engine: {e}")
                self._availability_cache["rag"] = False
                return None

        return self._rag_engine

    def get_rag_config(self) -> Any | None:
        """
        Get RAG configuration with lazy loading.

        Returns:
            RAGConfig instance or None if unavailable
        """
        if not self.is_available("rag"):
            return None

        if self._rag_config is None:
            try:
                from tools.rag.config import RAGConfig

                self._rag_config = RAGConfig.from_env()
                logger.info("RAG config loaded successfully")
            except ImportError as e:
                logger.warning(f"RAG config not available: {e}")
                self._availability_cache["rag"] = False
                return None
            except Exception as e:
                logger.error(f"Failed to load RAG config: {e}")
                self._availability_cache["rag"] = False
                return None

        return self._rag_config

    def get_agent_processor(
        self,
        knowledge_base_path: str | None = None,
    ) -> Any | None:
        """
        Get agent processing unit with lazy loading.

        Args:
            knowledge_base_path: Optional path to knowledge base

        Returns:
            ProcessingUnit instance or None if unavailable
        """
        if not self.is_available("agent_prompts"):
            return None

        if self._agent_processor is None:
            try:
                from pathlib import Path

                from tools.agent_prompts.processing_unit import ProcessingUnit

                if knowledge_base_path is None:
                    knowledge_base_path = "tools/agent_prompts"

                kb_path = Path(knowledge_base_path)
                if not kb_path.exists():
                    logger.warning(f"Knowledge base path not found: {kb_path}")
                    self._availability_cache["agent_prompts"] = False
                    return None

                self._agent_processor = ProcessingUnit(kb_path)
                logger.info(f"Agent processor initialized from {kb_path}")
            except ImportError as e:
                logger.warning(f"Agent processor not available: {e}")
                self._availability_cache["agent_prompts"] = False
                return None
            except Exception as e:
                logger.error(f"Failed to initialize agent processor: {e}")
                self._availability_cache["agent_prompts"] = False
                return None

        return self._agent_processor

    def get_api_client(self, service: str, config: dict[str, Any] | None = None) -> Any | None:
        """
        Get API client for external service (EQ module).

        Args:
            service: Service name (e.g., 'spotify')
            config: Optional configuration dictionary

        Returns:
            APIClient instance or None if unavailable
        """
        if service in self._api_clients:
            return self._api_clients[service]

        if not self.is_available("eq"):
            return None

        try:
            from EQ import APIClient, APIClientConfig, TokenModel

            # For now, EQ module requires manual configuration
            # This is a factory placeholder - actual usage requires proper token setup
            if config is None:
                config = {}

            # Return a factory function that can create clients when needed
            # Actual client creation requires token, so we defer it
            logger.info(f"API client factory registered for service: {service}")
            return None  # Defer actual client creation until token is available

        except ImportError as e:
            logger.warning(f"EQ module not available for service {service}: {e}")
            self._availability_cache["eq"] = False
            return None
        except Exception as e:
            logger.error(f"Failed to create API client for {service}: {e}")
            return None

    def is_available(self, tool: str) -> bool:
        """
        Check if a tool is available.

        Args:
            tool: Tool name ('rag', 'agent_prompts', 'eq')

        Returns:
            True if tool is available, False otherwise
        """
        if tool in self._availability_cache:
            return self._availability_cache[tool]

        available = False

        if tool == "rag":
            try:
                from tools.rag.rag_engine import RAGEngine  # noqa: F401

                available = True
            except ImportError:
                available = False

        elif tool == "agent_prompts":
            try:
                from tools.agent_prompts.processing_unit import ProcessingUnit  # noqa: F401

                available = True
            except ImportError:
                available = False

        elif tool == "eq":
            try:
                from EQ import APIClient  # noqa: F401

                available = True
            except ImportError:
                available = False

        self._availability_cache[tool] = available
        return available

    def get_availability_status(self) -> dict[str, bool]:
        """
        Get availability status for all tools.

        Returns:
            Dictionary mapping tool names to availability
        """
        tools = ["rag", "agent_prompts", "eq"]
        return {tool: self.is_available(tool) for tool in tools}

    def reset(self) -> None:
        """Reset cached instances and availability cache."""
        self._rag_engine = None
        self._rag_config = None
        self._agent_processor = None
        self._api_clients.clear()
        self._availability_cache.clear()
        logger.info("Tools integration reset")


# Global instance (singleton pattern)
_tools_integration_instance: ToolsIntegration | None = None


def get_tools_integration() -> ToolsIntegration:
    """
    Get the global ToolsIntegration instance (singleton).

    Returns:
        ToolsIntegration instance
    """
    global _tools_integration_instance
    if _tools_integration_instance is None:
        _tools_integration_instance = ToolsIntegration()
    return _tools_integration_instance


__all__ = ["ToolsIntegration", "get_tools_integration"]
