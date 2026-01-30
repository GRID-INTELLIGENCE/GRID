"""
I/O Gateway Module for GRID Event-Driven Architecture.

Provides input gateways and output handlers for the event-driven
processing pipeline, supporting multiple input sources and output
destinations with unified event-based communication.

Key Components:
- InputGateway: Abstract base for input sources
- CLIGateway: Command-line interface input handling
- APIGateway: REST/HTTP API input handling
- FileWatcherGateway: File system change detection
- WebSocketGateway: WebSocket message handling
- OutputHandler: Response formatting and delivery
- ResponseFormatter: Output format conversion

Features:
- Unified event emission for all input types
- Correlation ID tracking across I/O boundaries
- Multiple output format support (JSON, Table, Text)
- Async and sync I/O operations
- Error handling and recovery

Example:
    >>> from grid.io import CLIGateway, OutputHandler
    >>> from grid.events import get_event_bus
    >>>
    >>> bus = get_event_bus()
    >>> cli = CLIGateway(bus)
    >>> output = OutputHandler(bus)
    >>>
    >>> cli.handle_input("analyze", {"text": "Hello world"})
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "GRID Team"

from .gateways import (
    APIGateway,
    CLIGateway,
    FileWatcherGateway,
    InputGateway,
    WebSocketGateway,
)
from .outputs import (
    OutputFormat,
    OutputHandler,
    ResponseFormatter,
)

__all__ = [
    # Input gateways
    "InputGateway",
    "CLIGateway",
    "APIGateway",
    "FileWatcherGateway",
    "WebSocketGateway",
    # Output handling
    "OutputHandler",
    "ResponseFormatter",
    "OutputFormat",
]
