"""
Grid/Circuits Tools Package

A collection of utilities for monitoring, visualization, and research.

Available Tools:
    - rag: Local-first RAG system (ChromaDB + Ollama)
    - agent_prompts: Agent processing and prompt management
    - integration: Unified tools integration interface

Usage:
    python -m tools.rag.cli query "your question"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

# Data Connectors
from .data_connectors import (
    BaseConnectorConfig,
    BaseDataClient,
    ConfigurationError,
    ConnectionError,
    ConnectorError,
    ConnectorHandler,
    ConnectorRegistry,
    ConnectorStatus,
    QueryExecutionError,
    QueryInterface,
    QueryResult,
    connector_registry,
    get_connector,
    register_connector,
)

# Databricks Connector
try:
    from .databricks_connector import (
        DatabricksClient,
        DatabricksConfig,
        DatabricksQuery,
        create_databricks_connector,
        execute_databricks_query,
        test_databricks_connection,
    )

    _databricks_available = True
except ImportError:
    logger.warning("Databricks dependencies not found. Databricks tools will be unavailable.")
    _databricks_available = False

# Lazy imports to avoid dependency issues
__all__ = [
    "ToolsIntegration",
    "get_tools_integration",
    "BaseConnectorConfig",
    "BaseDataClient",
    "QueryInterface",
    "QueryResult",
    "ConnectorRegistry",
    "ConnectorHandler",
    "ConnectorStatus",
    "ConnectorError",
    "ConfigurationError",
    "ConnectionError",
    "QueryExecutionError",
    "connector_registry",
    "get_connector",
    "register_connector",
]

if _databricks_available:
    __all__.extend(
        [
            "DatabricksConfig",
            "DatabricksClient",
            "DatabricksQuery",
            "create_databricks_connector",
            "test_databricks_connection",
            "execute_databricks_query",
        ]
    )


if TYPE_CHECKING:
    from tools.integration import ToolsIntegration, get_tools_integration


def __getattr__(name: str) -> Any:
    """Lazy import mechanism for tools."""
    if name == "ToolsIntegration":
        from tools.integration import ToolsIntegration

        return ToolsIntegration
    elif name == "get_tools_integration":
        from tools.integration import get_tools_integration

        return get_tools_integration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
