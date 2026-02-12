"""
Input Gateway Implementations for GRID Event-Driven I/O Architecture.

Provides input gateway implementations that convert various input sources
into standardized events for the processing pipeline.

Gateways:
- CLIGateway: Command-line interface input handling
- APIGateway: REST/HTTP API request handling
- FileWatcherGateway: File system change detection
- WebSocketGateway: WebSocket message handling

Each gateway emits events to the EventBus with consistent structure,
enabling unified processing regardless of input source.

Example:
    >>> from grid.events import get_event_bus
    >>> from grid.io.gateways import CLIGateway
    >>>
    >>> bus = get_event_bus()
    >>> cli = CLIGateway(bus)
    >>> cli.handle_input("analyze", {"text": "Hello world"})
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from grid.events.core import Event, EventBus, EventPriority
from grid.events.types import EventType

logger = logging.getLogger(__name__)


class InputSource(str, Enum):
    """Enumeration of input sources."""

    CLI = "cli"
    API = "api"
    FILE = "file"
    WEBSOCKET = "websocket"
    INTERNAL = "internal"


@dataclass
class InputContext:
    """Context information for input handling."""

    source: InputSource
    session_id: str | None = None
    user_id: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate request ID if not provided."""
        if self.request_id is None:
            self.request_id = f"req-{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source.value,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class InputGateway(ABC):
    """
    Abstract base class for input gateways.

    Provides common functionality for all input sources including
    event emission, validation, and context tracking.
    """

    def __init__(
        self,
        event_bus: EventBus,
        source: InputSource,
        validate_input: bool = True,
    ) -> None:
        """
        Initialize input gateway.

        Args:
            event_bus: EventBus for emitting events
            source: Input source type
            validate_input: Whether to validate input before processing
        """
        self.event_bus = event_bus
        self.source = source
        self.validate_input = validate_input

        # Statistics
        self._stats = {
            "inputs_received": 0,
            "inputs_processed": 0,
            "inputs_rejected": 0,
            "errors": 0,
        }

        logger.debug("InputGateway initialized: %s", source.value)

    @abstractmethod
    def handle_input(self, *args: Any, **kwargs: Any) -> str | None:
        """
        Handle incoming input and emit events.

        Returns:
            Correlation ID for tracking
        """
        pass

    def _emit_input_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        context: InputContext | None = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: str | None = None,
    ) -> str:
        """
        Emit an input event to the event bus.

        Args:
            event_type: Type of event to emit
            data: Event data payload
            context: Input context
            priority: Event priority
            correlation_id: Optional correlation ID

        Returns:
            Correlation ID
        """
        if context is None:
            context = InputContext(source=self.source)

        event = Event(
            type=event_type.value,
            data={
                **data,
                "input_context": context.to_dict(),
            },
            source=f"{self.source.value}_gateway",
            correlation_id=correlation_id,
            priority=priority,
            metadata={
                "request_id": context.request_id,
                "session_id": context.session_id,
            },
        )

        self.event_bus.emit(event)
        self._stats["inputs_processed"] += 1

        return event.correlation_id or ""

    def get_stats(self) -> dict[str, Any]:
        """Get gateway statistics."""
        return {
            "source": self.source.value,
            **self._stats,
        }


class CLIGateway(InputGateway):
    """
    Command-line interface input gateway.

    Handles CLI commands and arguments, converting them to events
    for the processing pipeline.
    """

    # Supported CLI commands
    VALID_COMMANDS = {
        "analyze",
        "process",
        "serve",
        "skills",
        "health",
        "version",
        "config",
        "help",
    }

    def __init__(
        self,
        event_bus: EventBus,
        validate_commands: bool = True,
    ) -> None:
        """
        Initialize CLI gateway.

        Args:
            event_bus: EventBus for emitting events
            validate_commands: Whether to validate command names
        """
        super().__init__(event_bus, InputSource.CLI)
        self.validate_commands = validate_commands

    def handle_input(
        self,
        command: str,
        args: dict[str, Any] | None = None,
        context: InputContext | None = None,
    ) -> str | None:
        """
        Handle CLI command input.

        Args:
            command: CLI command name
            args: Command arguments
            context: Optional input context

        Returns:
            Correlation ID for tracking
        """
        self._stats["inputs_received"] += 1
        args = args or {}

        # Validate command if enabled
        if self.validate_commands and command not in self.VALID_COMMANDS:
            self._stats["inputs_rejected"] += 1
            logger.warning("Invalid CLI command rejected: %s", command)
            return None

        # Create context if not provided
        if context is None:
            context = InputContext(
                source=InputSource.CLI,
                metadata={"command": command},
            )

        # Emit CLI input event
        correlation_id = self._emit_input_event(
            event_type=EventType.CLI_INPUT,
            data={
                "command": command,
                "args": args,
            },
            context=context,
        )

        # Emit command-specific event
        self._emit_input_event(
            event_type=EventType.CLI_COMMAND,
            data={
                "command": command,
                "args": args,
            },
            context=context,
            correlation_id=correlation_id,
        )

        logger.debug("CLI input processed: %s (correlation=%s)", command, correlation_id)
        return correlation_id

    def parse_args(self, raw_args: list[str]) -> dict[str, Any]:
        """
        Parse raw CLI arguments into a dictionary.

        Args:
            raw_args: Raw argument strings

        Returns:
            Parsed arguments dictionary
        """
        parsed: dict[str, Any] = {}
        current_key: str | None = None
        positional_index = 0

        for arg in raw_args:
            if arg.startswith("--"):
                # Long option
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    parsed[key.replace("-", "_")] = self._parse_value(value)
                else:
                    current_key = arg[2:].replace("-", "_")
                    parsed[current_key] = True  # Flag
            elif arg.startswith("-"):
                # Short option
                current_key = arg[1:]
                parsed[current_key] = True  # Flag
            elif current_key:
                # Value for previous option
                parsed[current_key] = self._parse_value(arg)
                current_key = None
            else:
                # Positional argument
                parsed[f"arg_{positional_index}"] = arg
                positional_index += 1

        return parsed

    def _parse_value(self, value: str) -> Any:
        """Parse a string value to appropriate type."""
        # Try numeric types
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Boolean values
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False

        # Return as string
        return value


class APIGateway(InputGateway):
    """
    REST/HTTP API input gateway.

    Handles API requests, converting them to events for processing.
    Supports request validation, rate limiting context, and authentication context.
    """

    def __init__(
        self,
        event_bus: EventBus,
        validate_endpoints: bool = True,
        valid_endpoints: set[str] | None = None,
    ) -> None:
        """
        Initialize API gateway.

        Args:
            event_bus: EventBus for emitting events
            validate_endpoints: Whether to validate endpoint paths
            valid_endpoints: Set of valid endpoint paths
        """
        super().__init__(event_bus, InputSource.API)
        self.validate_endpoints = validate_endpoints
        self.valid_endpoints = valid_endpoints or {
            "/api/v1/analyze",
            "/api/v1/process",
            "/api/v1/skills",
            "/api/v1/health",
            "/api/v1/entities",
        }

    def handle_input(
        self,
        request: dict[str, Any],
        context: InputContext | None = None,
    ) -> str | None:
        """
        Handle API request input.

        Args:
            request: API request data containing:
                - endpoint: Request endpoint path
                - method: HTTP method
                - body: Request body
                - headers: Request headers
                - query_params: Query parameters
            context: Optional input context

        Returns:
            Correlation ID for tracking
        """
        self._stats["inputs_received"] += 1

        endpoint = request.get("endpoint", "/")
        method = request.get("method", "GET").upper()

        # Validate endpoint if enabled
        if self.validate_endpoints:
            # Normalize endpoint for validation
            normalized = endpoint.rstrip("/")
            if normalized not in self.valid_endpoints:
                self._stats["inputs_rejected"] += 1
                logger.warning("Invalid API endpoint rejected: %s", endpoint)
                return None

        # Create context if not provided
        if context is None:
            headers = request.get("headers", {})
            context = InputContext(
                source=InputSource.API,
                client_ip=request.get("client_ip"),
                user_agent=headers.get("User-Agent"),
                session_id=headers.get("X-Session-ID"),
                user_id=request.get("user_id"),
                metadata={
                    "endpoint": endpoint,
                    "method": method,
                },
            )

        # Emit API input event
        correlation_id = self._emit_input_event(
            event_type=EventType.API_INPUT,
            data={
                "endpoint": endpoint,
                "method": method,
                "body": request.get("body", {}),
                "query_params": request.get("query_params", {}),
                "headers": self._sanitize_headers(request.get("headers", {})),
            },
            context=context,
        )

        # Emit request event
        self._emit_input_event(
            event_type=EventType.API_REQUEST,
            data={
                "endpoint": endpoint,
                "method": method,
                "body": request.get("body", {}),
            },
            context=context,
            correlation_id=correlation_id,
        )

        logger.debug(
            "API input processed: %s %s (correlation=%s)",
            method,
            endpoint,
            correlation_id,
        )
        return correlation_id

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Remove sensitive headers from logging."""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        }

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized


class FileWatcherGateway(InputGateway):
    """
    File system change detection gateway.

    Watches directories for file changes and emits events for
    created, modified, and deleted files.
    """

    def __init__(
        self,
        event_bus: EventBus,
        watch_directories: list[str | Path] | None = None,
        file_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize file watcher gateway.

        Args:
            event_bus: EventBus for emitting events
            watch_directories: Directories to watch
            file_patterns: File patterns to include (e.g., ["*.py", "*.json"])
            ignore_patterns: Patterns to ignore
        """
        super().__init__(event_bus, InputSource.FILE)
        self.watch_directories = [Path(d) for d in (watch_directories or [])]
        self.file_patterns = file_patterns or ["*"]
        self.ignore_patterns = ignore_patterns or ["__pycache__", ".git", "*.pyc"]

        # Track file states for change detection
        self._file_states: dict[str, str] = {}
        self._watching = False

    def handle_input(
        self,
        file_path: str | Path,
        content: str | None = None,
        change_type: str = "modified",
        context: InputContext | None = None,
    ) -> str | None:
        """
        Handle file input event.

        Args:
            file_path: Path to the file
            content: File content (read if not provided)
            change_type: Type of change (created, modified, deleted)
            context: Optional input context

        Returns:
            Correlation ID for tracking
        """
        self._stats["inputs_received"] += 1

        file_path = Path(file_path)

        # Check if file should be ignored
        if self._should_ignore(file_path):
            self._stats["inputs_rejected"] += 1
            return None

        # Read content if not provided and file exists
        if content is None and file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error("Failed to read file %s: %s", file_path, e)
                content = ""

        # Create context if not provided
        if context is None:
            context = InputContext(
                source=InputSource.FILE,
                metadata={
                    "file_path": str(file_path),
                    "change_type": change_type,
                    "file_extension": file_path.suffix,
                },
            )

        # Select event type based on change type
        event_type_map = {
            "created": EventType.FILE_CREATED,
            "modified": EventType.FILE_CHANGED,
            "deleted": EventType.FILE_DELETED,
        }
        event_type = event_type_map.get(change_type, EventType.FILE_INPUT)

        # Emit file input event
        correlation_id = self._emit_input_event(
            event_type=EventType.FILE_INPUT,
            data={
                "file_path": str(file_path),
                "content": content,
                "change_type": change_type,
                "file_size": len(content) if content else 0,
                "file_extension": file_path.suffix,
            },
            context=context,
        )

        # Emit change-specific event
        self._emit_input_event(
            event_type=event_type,
            data={
                "file_path": str(file_path),
                "change_type": change_type,
            },
            context=context,
            correlation_id=correlation_id,
        )

        logger.debug(
            "File input processed: %s (%s, correlation=%s)",
            file_path,
            change_type,
            correlation_id,
        )
        return correlation_id

    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)

        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True

        return False

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute hash of file content for change detection."""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def scan_directory(self, directory: str | Path) -> list[str]:
        """
        Scan directory and emit events for all files.

        Args:
            directory: Directory to scan

        Returns:
            List of correlation IDs
        """
        directory = Path(directory)
        correlation_ids = []

        if not directory.exists():
            logger.warning("Directory does not exist: %s", directory)
            return correlation_ids

        for pattern in self.file_patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file() and not self._should_ignore(file_path):
                    cid = self.handle_input(file_path, change_type="created")
                    if cid:
                        correlation_ids.append(cid)

        return correlation_ids


class WebSocketGateway(InputGateway):
    """
    WebSocket message handling gateway.

    Handles WebSocket connections and messages, converting them
    to events for processing.
    """

    def __init__(
        self,
        event_bus: EventBus,
        max_message_size: int = 65536,
    ) -> None:
        """
        Initialize WebSocket gateway.

        Args:
            event_bus: EventBus for emitting events
            max_message_size: Maximum message size in bytes
        """
        super().__init__(event_bus, InputSource.WEBSOCKET)
        self.max_message_size = max_message_size

        # Connection tracking
        self._connections: dict[str, dict[str, Any]] = {}

    def handle_input(
        self,
        message: str | dict[str, Any],
        connection_id: str,
        message_type: str = "message",
        context: InputContext | None = None,
    ) -> str | None:
        """
        Handle WebSocket message input.

        Args:
            message: Message content (string or dict)
            connection_id: WebSocket connection ID
            message_type: Type of message (message, connect, disconnect)
            context: Optional input context

        Returns:
            Correlation ID for tracking
        """
        self._stats["inputs_received"] += 1

        # Validate message size
        message_str = str(message) if isinstance(message, dict) else message
        if len(message_str) > self.max_message_size:
            self._stats["inputs_rejected"] += 1
            logger.warning(
                "WebSocket message too large: %d > %d",
                len(message_str),
                self.max_message_size,
            )
            return None

        # Create context if not provided
        if context is None:
            conn_info = self._connections.get(connection_id, {})
            context = InputContext(
                source=InputSource.WEBSOCKET,
                session_id=connection_id,
                user_id=conn_info.get("user_id"),
                client_ip=conn_info.get("client_ip"),
                metadata={
                    "connection_id": connection_id,
                    "message_type": message_type,
                },
            )

        # Handle connection events
        if message_type == "connect":
            return self._handle_connect(connection_id, message, context)
        elif message_type == "disconnect":
            return self._handle_disconnect(connection_id, context)

        # Emit WebSocket input event
        correlation_id = self._emit_input_event(
            event_type=EventType.WEBSOCKET_INPUT,
            data={
                "message": message,
                "connection_id": connection_id,
                "message_type": message_type,
            },
            context=context,
        )

        # Emit message event
        self._emit_input_event(
            event_type=EventType.WEBSOCKET_MESSAGE,
            data={
                "message": message,
                "connection_id": connection_id,
            },
            context=context,
            correlation_id=correlation_id,
        )

        logger.debug(
            "WebSocket message processed: connection=%s (correlation=%s)",
            connection_id,
            correlation_id,
        )
        return correlation_id

    def _handle_connect(
        self,
        connection_id: str,
        connection_info: str | dict[str, Any],
        context: InputContext,
    ) -> str:
        """Handle WebSocket connection."""
        self._connections[connection_id] = connection_info if isinstance(connection_info, dict) else {}

        correlation_id = self._emit_input_event(
            event_type=EventType.WEBSOCKET_CONNECTED,
            data={
                "connection_id": connection_id,
                "connection_info": connection_info,
            },
            context=context,
        )

        logger.info("WebSocket connected: %s", connection_id)
        return correlation_id

    def _handle_disconnect(
        self,
        connection_id: str,
        context: InputContext,
    ) -> str:
        """Handle WebSocket disconnection."""
        self._connections.pop(connection_id, None)

        correlation_id = self._emit_input_event(
            event_type=EventType.WEBSOCKET_DISCONNECTED,
            data={
                "connection_id": connection_id,
            },
            context=context,
        )

        logger.info("WebSocket disconnected: %s", connection_id)
        return correlation_id

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

    def broadcast(self, message: str | dict[str, Any]) -> list[str]:
        """
        Broadcast message to all connections (emits events).

        Args:
            message: Message to broadcast

        Returns:
            List of correlation IDs
        """
        correlation_ids = []

        for connection_id in self._connections:
            cid = self.handle_input(message, connection_id)
            if cid:
                correlation_ids.append(cid)

        return correlation_ids
