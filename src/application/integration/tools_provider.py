"""
Application Layer Tools Provider

FastAPI dependency provider for tools integration with graceful degradation.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, status

logger = logging.getLogger(__name__)


class ToolsProvider:
    """
    FastAPI dependency provider for tools services.

    Provides dependency injection for tools with graceful degradation
    when tools are unavailable.
    """

    def __init__(self) -> None:
        """Initialize tools provider."""
        self._tools_integration: Any | None = None

    def _get_integration(self) -> Any:
        """Lazy load tools integration."""
        if self._tools_integration is None:
            try:
                from tools.integration import get_tools_integration

                self._tools_integration = get_tools_integration()
            except ImportError:
                logger.warning("Tools integration not available")
                return None
        return self._tools_integration

    def get_rag_engine(self, required: bool = False) -> Any:
        """
        Get RAG engine as FastAPI dependency.

        Args:
            required: If True, raise HTTPException if unavailable

        Returns:
            RAGEngine instance or None

        Raises:
            HTTPException: If required=True and RAG is unavailable
        """
        integration = self._get_integration()
        if integration is None:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="RAG system is not available",
                )
            return None

        engine = integration.get_rag_engine()
        if engine is None and required:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG system is not available",
            )
        return engine

    def get_agent_processor(self, required: bool = False, knowledge_base_path: str | None = None) -> Any:
        """
        Get agent processor as FastAPI dependency.

        Args:
            required: If True, raise HTTPException if unavailable
            knowledge_base_path: Optional path to knowledge base

        Returns:
            ProcessingUnit instance or None

        Raises:
            HTTPException: If required=True and agent processor is unavailable
        """
        integration = self._get_integration()
        if integration is None:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Agent processor is not available",
                )
            return None

        processor = integration.get_agent_processor(knowledge_base_path=knowledge_base_path)
        if processor is None and required:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent processor is not available",
            )
        return processor

    def check_health(self) -> dict[str, Any]:
        """
        Check health status of all tools.

        Returns:
            Dictionary with tool availability status
        """
        integration = self._get_integration()
        if integration is None:
            return {
                "tools_integration": False,
                "rag": False,
                "agent_prompts": False,
                "eq": False,
            }

        status = integration.get_availability_status()
        return {
            "tools_integration": True,
            **status,
        }


# Global instance (singleton pattern)
_tools_provider_instance: ToolsProvider | None = None


def get_tools_provider() -> ToolsProvider:
    """
    Get the global ToolsProvider instance (singleton).

    Returns:
        ToolsProvider instance
    """
    global _tools_provider_instance
    if _tools_provider_instance is None:
        _tools_provider_instance = ToolsProvider()
    return _tools_provider_instance


def get_tools_integration() -> Any:
    """
    Get tools integration instance for direct use.

    Returns:
        ToolsIntegration instance or None
    """
    provider = get_tools_provider()
    return provider._get_integration()


# FastAPI dependency functions
def get_rag_engine_dependency(required: bool = False) -> Any:
    """
    FastAPI dependency for RAG engine.

    Args:
        required: If True, raise HTTPException if unavailable

    Returns:
        Dependency function
    """

    def _get_rag_engine() -> Any:
        provider = get_tools_provider()
        return provider.get_rag_engine(required=required)

    return Depends(_get_rag_engine)


def get_agent_processor_dependency(
    required: bool = False,
    knowledge_base_path: str | None = None,
) -> Any:
    """
    FastAPI dependency for agent processor.

    Args:
        required: If True, raise HTTPException if unavailable
        knowledge_base_path: Optional path to knowledge base

    Returns:
        Dependency function
    """

    def _get_agent_processor() -> Any:
        provider = get_tools_provider()
        return provider.get_agent_processor(
            required=required,
            knowledge_base_path=knowledge_base_path,
        )

    return Depends(_get_agent_processor)


__all__ = [
    "ToolsProvider",
    "get_tools_provider",
    "get_tools_integration",
    "get_rag_engine_dependency",
    "get_agent_processor_dependency",
]
