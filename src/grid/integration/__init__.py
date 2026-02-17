"""
Grid Domain Integration Package

Bridges between grid/ domain and other GRID domains (tools, application, etc.)
"""

from .domain_gateway import (
    DomainCategory,
    DomainGateway,
    IntelligenceRequest,
    IntelligenceResponse,
    OrchestrationCommand,
    OrchestrationResult,
    get_gateway,
    get_intelligence,
    get_orchestration,
)
from .tools_bridge import ToolsBridge, get_tools_bridge

__all__ = [
    # Tools Bridge
    "get_tools_bridge",
    "ToolsBridge",
    # Domain Gateway (DDD ACL)
    "DomainGateway",
    "get_gateway",
    "get_intelligence",
    "get_orchestration",
    # DTOs
    "IntelligenceRequest",
    "IntelligenceResponse",
    "OrchestrationCommand",
    "OrchestrationResult",
    "DomainCategory",
]
