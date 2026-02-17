"""
Output Handler Module for GRID Event-Driven I/O Architecture.

Provides output handling and response formatting for the event-driven
processing pipeline, supporting multiple output formats and destinations.

Key Components:
- OutputFormat: Enumeration of supported output formats
- ResponseFormatter: Converts results to various formats (JSON, Table, Text)
- OutputHandler: Manages response delivery based on input source

Features:
- Multiple output format support (JSON, Table, Text, Markdown)
- Source-aware response routing
- Response caching for correlation-based retrieval
- Async response delivery
- Error response handling

Example:
    >>> from grid.events import get_event_bus
    >>> from grid.io.outputs import OutputHandler, OutputFormat
    >>>
    >>> bus = get_event_bus()
    >>> handler = OutputHandler(bus)
    >>>
    >>> # Retrieve response after processing
    >>> response = handler.get_response(correlation_id)
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from grid.events.core import Event, EventBus, EventPriority
from grid.events.types import EventType

logger = logging.getLogger(__name__)


class OutputFormat(StrEnum):
    """Supported output formats."""

    JSON = "json"
    TABLE = "table"
    TEXT = "text"
    MARKDOWN = "markdown"
    CSV = "csv"
    HTML = "html"
    RAW = "raw"


class ResponseStatus(StrEnum):
    """Response status values."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"
    TIMEOUT = "timeout"


@dataclass
class FormattedResponse:
    """Formatted response with metadata."""

    correlation_id: str
    status: ResponseStatus
    content: str
    format: OutputFormat
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "status": self.status.value,
            "content": self.content,
            "format": self.format.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class ResponseFormatter:
    """
    Converts processing results to various output formats.

    Supports JSON, Table, Text, Markdown, CSV, and HTML output
    with customizable formatting options.
    """

    def __init__(
        self,
        default_format: OutputFormat = OutputFormat.JSON,
        indent: int = 2,
        table_max_width: int = 120,
    ) -> None:
        """
        Initialize response formatter.

        Args:
            default_format: Default output format
            indent: JSON indentation level
            table_max_width: Maximum width for table columns
        """
        self.default_format = default_format
        self.indent = indent
        self.table_max_width = table_max_width

        # Format handlers
        self._formatters: dict[OutputFormat, Callable[[dict[str, Any]], str]] = {
            OutputFormat.JSON: self._format_json,
            OutputFormat.TABLE: self._format_table,
            OutputFormat.TEXT: self._format_text,
            OutputFormat.MARKDOWN: self._format_markdown,
            OutputFormat.CSV: self._format_csv,
            OutputFormat.HTML: self._format_html,
            OutputFormat.RAW: self._format_raw,
        }

    def format(
        self,
        result: dict[str, Any],
        output_format: OutputFormat | None = None,
    ) -> str:
        """
        Format result in specified format.

        Args:
            result: Processing result dictionary
            output_format: Desired output format (uses default if not specified)

        Returns:
            Formatted string
        """
        fmt = output_format or self.default_format
        formatter = self._formatters.get(fmt, self._format_json)

        try:
            return formatter(result)
        except Exception as e:
            logger.error("Formatting error: %s", e)
            return self._format_json({"error": str(e), "original": result})

    def _format_json(self, result: dict[str, Any]) -> str:
        """Format result as JSON."""
        return json.dumps(result, indent=self.indent, default=str, ensure_ascii=False)

    def _format_table(self, result: dict[str, Any]) -> str:
        """Format result as ASCII table."""
        lines = []

        # Title
        if "title" in result:
            lines.append(f"╔{'═' * (self.table_max_width - 2)}╗")
            title = str(result["title"])[: self.table_max_width - 4]
            lines.append(f"║ {title.center(self.table_max_width - 4)} ║")
            lines.append(f"╠{'═' * (self.table_max_width - 2)}╣")

        # Handle different result structures
        if "entities" in result:
            lines.extend(self._format_entities_table(result["entities"]))
        elif "categories" in result:
            lines.extend(self._format_categories_table(result["categories"]))
        elif "items" in result and isinstance(result["items"], list):
            lines.extend(self._format_list_table(result["items"]))
        else:
            # Generic key-value table
            lines.extend(self._format_dict_table(result))

        # Footer
        if lines and not lines[-1].startswith("╚"):
            lines.append(f"╚{'═' * (self.table_max_width - 2)}╝")

        return "\n".join(lines)

    def _format_entities_table(self, entities: list[dict[str, Any]]) -> list[str]:
        """Format entities as table rows."""
        lines = []

        if not entities:
            lines.append("║ No entities found".ljust(self.table_max_width - 1) + "║")
            return lines

        # Header
        header = "│ Text".ljust(40) + "│ Type".ljust(20) + "│ Confidence │"
        lines.append(header)
        lines.append("├" + "─" * 39 + "┼" + "─" * 19 + "┼" + "─" * 12 + "┤")

        # Rows
        for entity in entities[:20]:  # Limit to 20 entities
            text = str(entity.get("text", ""))[:36]
            etype = str(entity.get("type", ""))[:16]
            conf = entity.get("confidence", 0.0)
            row = f"│ {text.ljust(37)} │ {etype.ljust(17)} │ {conf:10.2%} │"
            lines.append(row)

        if len(entities) > 20:
            lines.append(f"│ ... and {len(entities) - 20} more entities".ljust(73) + "│")

        return lines

    def _format_categories_table(self, categories: list[str]) -> list[str]:
        """Format categories as table rows."""
        lines = []

        if not categories:
            lines.append("║ No categories found".ljust(self.table_max_width - 1) + "║")
            return lines

        for i, category in enumerate(categories, 1):
            row = f"║ {i}. {category}".ljust(self.table_max_width - 1) + "║"
            lines.append(row)

        return lines

    def _format_list_table(self, items: list[Any]) -> list[str]:
        """Format list items as table rows."""
        lines = []

        for i, item in enumerate(items[:50], 1):  # Limit to 50 items
            if isinstance(item, dict):
                text = json.dumps(item, default=str)[: self.table_max_width - 10]
            else:
                text = str(item)[: self.table_max_width - 10]
            row = f"║ {i:3}. {text}".ljust(self.table_max_width - 1) + "║"
            lines.append(row)

        if len(items) > 50:
            lines.append(f"║ ... and {len(items) - 50} more items".ljust(self.table_max_width - 1) + "║")

        return lines

    def _format_dict_table(self, data: dict[str, Any]) -> list[str]:
        """Format dictionary as key-value table."""
        lines = []

        # Calculate column widths
        max_key_len = min(30, max(len(str(k)) for k in data.keys()) if data else 10)
        value_width = self.table_max_width - max_key_len - 7

        for key, value in data.items():
            key_str = str(key)[:max_key_len]
            value_str = str(value)[:value_width]

            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, default=str)[:value_width]

            row = f"║ {key_str.ljust(max_key_len)} │ {value_str.ljust(value_width)} ║"
            lines.append(row)

        return lines

    def _format_text(self, result: dict[str, Any]) -> str:
        """Format result as plain text."""
        lines = []

        # Status
        status = result.get("status", "unknown")
        lines.append(f"Status: {status}")
        lines.append("")

        # Main content
        if "entities" in result:
            lines.append("Entities:")
            for entity in result["entities"]:
                text = entity.get("text", "")
                etype = entity.get("type", "")
                conf = entity.get("confidence", 0.0)
                lines.append(f"  - {text} ({etype}, {conf:.1%})")

        if "categories" in result:
            lines.append("Categories:")
            lines.extend(f"  - {category}" for category in result["categories"])

        if "analysis" in result:
            lines.append("Analysis:")
            analysis = result["analysis"]
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append(f"  {analysis}")

        # Metadata
        if "timestamp" in result:
            lines.append("")
            lines.append(f"Timestamp: {result['timestamp']}")

        return "\n".join(lines)

    def _format_markdown(self, result: dict[str, Any]) -> str:
        """Format result as Markdown."""
        lines = []

        # Title
        title = result.get("title", "Processing Result")
        lines.append(f"# {title}")
        lines.append("")

        # Status badge
        status = result.get("status", "unknown")
        status_emoji = {"success": "✅", "error": "❌", "partial": "⚠️"}.get(status, "ℹ️")
        lines.append(f"**Status:** {status_emoji} {status}")
        lines.append("")

        # Entities table
        if "entities" in result and result["entities"]:
            lines.append("## Entities")
            lines.append("")
            lines.append("| Text | Type | Confidence |")
            lines.append("|------|------|------------|")
            for entity in result["entities"][:20]:
                text = entity.get("text", "").replace("|", "\\|")
                etype = entity.get("type", "")
                conf = entity.get("confidence", 0.0)
                lines.append(f"| {text} | {etype} | {conf:.1%} |")
            lines.append("")

        # Categories
        if "categories" in result and result["categories"]:
            lines.append("## Categories")
            lines.append("")
            lines.extend(f"- {category}" for category in result["categories"])
            lines.append("")

        # Analysis
        if "analysis" in result:
            lines.append("## Analysis")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(result["analysis"], indent=2, default=str))
            lines.append("```")
            lines.append("")

        # Footer
        if "timestamp" in result:
            lines.append("---")
            lines.append(f"*Generated at: {result['timestamp']}*")

        return "\n".join(lines)

    def _format_csv(self, result: dict[str, Any]) -> str:
        """Format result as CSV."""
        lines = []

        # Handle entities
        if "entities" in result and result["entities"]:
            lines.append("text,type,confidence")
            for entity in result["entities"]:
                text = str(entity.get("text", "")).replace(",", ";").replace('"', '""')
                etype = str(entity.get("type", ""))
                conf = entity.get("confidence", 0.0)
                lines.append(f'"{text}",{etype},{conf:.4f}')
            return "\n".join(lines)

        # Handle categories
        if "categories" in result and result["categories"]:
            lines.append("category")
            lines.extend(f'"{category}"' for category in result["categories"])
            return "\n".join(lines)

        # Generic key-value
        lines.append("key,value")
        for key, value in result.items():
            key_str = str(key).replace(",", ";")
            value_str = str(value).replace(",", ";").replace('"', '""')
            lines.append(f'{key_str},"{value_str}"')

        return "\n".join(lines)

    def _format_html(self, result: dict[str, Any]) -> str:
        """Format result as HTML."""
        parts = [
            "<!DOCTYPE html>",
            "<html><head><style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".success { color: green; } .error { color: red; }",
            "</style></head><body>",
        ]

        # Title
        title = result.get("title", "Processing Result")
        parts.append(f"<h1>{title}</h1>")

        # Status
        status = result.get("status", "unknown")
        status_class = status if status in ["success", "error"] else ""
        parts.append(f'<p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>')

        # Entities table
        if "entities" in result and result["entities"]:
            parts.append("<h2>Entities</h2>")
            parts.append("<table><tr><th>Text</th><th>Type</th><th>Confidence</th></tr>")
            for entity in result["entities"][:50]:
                text = str(entity.get("text", "")).replace("<", "&lt;").replace(">", "&gt;")
                etype = entity.get("type", "")
                conf = entity.get("confidence", 0.0)
                parts.append(f"<tr><td>{text}</td><td>{etype}</td><td>{conf:.1%}</td></tr>")
            parts.append("</table>")

        # Categories
        if "categories" in result and result["categories"]:
            parts.append("<h2>Categories</h2><ul>")
            parts.extend(f"<li>{category}</li>" for category in result["categories"])
            parts.append("</ul>")

        parts.append("</body></html>")
        return "\n".join(parts)

    def _format_raw(self, result: dict[str, Any]) -> str:
        """Return raw string representation."""
        return str(result)


class OutputHandler:
    """
    Manages response delivery for the event-driven pipeline.

    Subscribes to processing completion events and routes
    responses to appropriate destinations based on input source.

    Features:
    - Automatic response caching for correlation-based retrieval
    - Source-aware response routing
    - Format conversion on delivery
    - Error response handling
    """

    def __init__(
        self,
        event_bus: EventBus,
        cache_ttl_seconds: int = 300,
        max_cached_responses: int = 1000,
        default_format: OutputFormat = OutputFormat.JSON,
    ) -> None:
        """
        Initialize output handler.

        Args:
            event_bus: EventBus for subscribing to events
            cache_ttl_seconds: Time-to-live for cached responses
            max_cached_responses: Maximum number of responses to cache
            default_format: Default output format
        """
        self.event_bus = event_bus
        self.cache_ttl = cache_ttl_seconds
        self.max_cached = max_cached_responses
        self.default_format = default_format

        # Response formatter
        self.formatter = ResponseFormatter(default_format=default_format)

        # Response cache: correlation_id -> (response, timestamp) using OrderedDict for O(1) FIFO eviction
        self._responses: OrderedDict[str, tuple[FormattedResponse, float]] = OrderedDict()
        self._lock = threading.Lock()

        # Output handlers by source
        self._source_handlers: dict[str, Callable[[FormattedResponse], None]] = {}

        # Statistics
        self._stats = {
            "responses_processed": 0,
            "responses_delivered": 0,
            "errors_handled": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Subscribe to events
        self._setup_subscriptions()

        logger.debug("OutputHandler initialized")

    def _setup_subscriptions(self) -> None:
        """Set up event subscriptions."""
        # Processing completion
        self.event_bus.subscribe(
            EventType.PROCESSING_COMPLETED.value,
            self._handle_processing_complete,
            priority=EventPriority.NORMAL,
        )

        # Processing errors
        self.event_bus.subscribe(
            EventType.PROCESSING_FAILED.value,
            self._handle_processing_error,
            priority=EventPriority.HIGH,
        )

        # Analysis completion
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_complete,
            priority=EventPriority.NORMAL,
        )

        # Entity extraction
        self.event_bus.subscribe(
            EventType.ENTITY_EXTRACTED.value,
            self._handle_entity_extracted,
            priority=EventPriority.LOW,
        )

    def _handle_processing_complete(self, event: Event) -> None:
        """Handle processing completion event."""
        correlation_id = event.correlation_id or ""
        result = event.data.get("result", {})
        input_context = event.data.get("input_context", {})

        # Create formatted response
        output_format = self._get_output_format(input_context)
        formatted_content = self.formatter.format(result, output_format)

        response = FormattedResponse(
            correlation_id=correlation_id,
            status=ResponseStatus.SUCCESS,
            content=formatted_content,
            format=output_format,
            metadata={
                "source": input_context.get("source", "unknown"),
                "request_id": input_context.get("request_id"),
            },
            processing_time_ms=event.metadata.get("processing_time_ms", 0.0),
        )

        # Cache response
        self._cache_response(response)

        # Emit response ready event
        self._emit_response_event(response, EventType.RESPONSE_READY)

        # Deliver to source-specific handler
        self._deliver_response(response, input_context)

        self._stats["responses_processed"] += 1

    def _handle_processing_error(self, event: Event) -> None:
        """Handle processing error event."""
        correlation_id = event.correlation_id or ""
        error = event.data.get("error", "Unknown error")
        input_context = event.data.get("input_context", {})

        # Create error response
        output_format = self._get_output_format(input_context)
        error_result = {
            "status": "error",
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
        formatted_content = self.formatter.format(error_result, output_format)

        response = FormattedResponse(
            correlation_id=correlation_id,
            status=ResponseStatus.ERROR,
            content=formatted_content,
            format=output_format,
            errors=[error],
            metadata={
                "source": input_context.get("source", "unknown"),
            },
        )

        # Cache response
        self._cache_response(response)

        # Emit error response event
        self._emit_response_event(response, EventType.ERROR_RESPONSE)

        # Deliver to source-specific handler
        self._deliver_response(response, input_context)

        self._stats["errors_handled"] += 1

    def _handle_analysis_complete(self, event: Event) -> None:
        """Handle analysis completion event."""
        # Similar to processing complete, but may have analysis-specific formatting
        correlation_id = event.correlation_id or ""
        result = event.data.get("analysis_result", event.data)
        input_context = event.data.get("input_context", {})

        # Wrap in analysis structure
        analysis_result = {
            "status": "success",
            "title": "Analysis Result",
            "analysis": result,
            "timestamp": datetime.now().isoformat(),
        }

        output_format = self._get_output_format(input_context)
        formatted_content = self.formatter.format(analysis_result, output_format)

        response = FormattedResponse(
            correlation_id=correlation_id,
            status=ResponseStatus.SUCCESS,
            content=formatted_content,
            format=output_format,
            metadata={"type": "analysis"},
        )

        self._cache_response(response)
        self._emit_response_event(response, EventType.RESPONSE_READY)

    def _handle_entity_extracted(self, event: Event) -> None:
        """Handle entity extraction event."""
        correlation_id = event.correlation_id or ""
        entities = event.data.get("entities", [])
        input_context = event.data.get("input_context", {})

        # Create entities result
        entity_result = {
            "status": "success",
            "title": "Entity Extraction Result",
            "entities": entities,
            "entity_count": len(entities),
            "timestamp": datetime.now().isoformat(),
        }

        output_format = self._get_output_format(input_context)
        formatted_content = self.formatter.format(entity_result, output_format)

        response = FormattedResponse(
            correlation_id=correlation_id,
            status=ResponseStatus.SUCCESS,
            content=formatted_content,
            format=output_format,
            metadata={"type": "entities", "count": len(entities)},
        )

        self._cache_response(response)

    def _get_output_format(self, input_context: dict[str, Any]) -> OutputFormat:
        """Determine output format from input context."""
        # Check for explicit format in context
        format_str = input_context.get("metadata", {}).get("output_format")
        if format_str:
            try:
                return OutputFormat(format_str.lower())
            except ValueError:
                pass

        # Source-based defaults
        source = input_context.get("source", "")
        source_formats = {
            "cli": OutputFormat.TABLE,
            "api": OutputFormat.JSON,
            "file": OutputFormat.JSON,
            "websocket": OutputFormat.JSON,
        }

        return source_formats.get(source, self.default_format)

    def _cache_response(self, response: FormattedResponse) -> None:
        """Cache response for retrieval."""
        with self._lock:
            # Evict old entries if at capacity
            if len(self._responses) >= self.max_cached:
                self._evict_expired()

            # Cache with timestamp
            self._responses[response.correlation_id] = (response, time.time())

    def _evict_expired(self) -> None:
        """Evict expired cache entries."""
        current_time = time.time()
        expired = [cid for cid, (_, ts) in self._responses.items() if current_time - ts > self.cache_ttl]
        for cid in expired:
            del self._responses[cid]

        # If still over capacity, evict oldest using OrderedDict FIFO (O(1) operation)
        while len(self._responses) > self.max_cached:
            self._responses.popitem(last=False)

    def _emit_response_event(self, response: FormattedResponse, event_type: EventType) -> None:
        """Emit response event."""
        event = Event(
            type=event_type.value,
            data={
                "correlation_id": response.correlation_id,
                "response": response.to_dict(),
            },
            source="output_handler",
            correlation_id=response.correlation_id,
        )
        self.event_bus.emit(event)

    def _deliver_response(
        self,
        response: FormattedResponse,
        input_context: dict[str, Any],
    ) -> None:
        """Deliver response to source-specific handler."""
        source = input_context.get("source", "")

        if source in self._source_handlers:
            try:
                self._source_handlers[source](response)
                self._stats["responses_delivered"] += 1
            except Exception as e:
                logger.error("Response delivery error for %s: %s", source, e)

    def register_source_handler(
        self,
        source: str,
        handler: Callable[[FormattedResponse], None],
    ) -> None:
        """
        Register a handler for a specific input source.

        Args:
            source: Input source name (cli, api, file, websocket)
            handler: Handler function
        """
        self._source_handlers[source] = handler
        logger.debug("Registered output handler for source: %s", source)

    def get_response(
        self,
        correlation_id: str,
        timeout_seconds: float = 30.0,
        poll_interval: float = 0.1,
    ) -> FormattedResponse | None:
        """
        Get response by correlation ID, waiting if necessary.

        Args:
            correlation_id: Correlation ID to look up
            timeout_seconds: Maximum time to wait
            poll_interval: Polling interval

        Returns:
            FormattedResponse or None if not found
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            with self._lock:
                if correlation_id in self._responses:
                    self._stats["cache_hits"] += 1
                    return self._responses[correlation_id][0]

            time.sleep(poll_interval)

        self._stats["cache_misses"] += 1
        return None

    async def get_response_async(
        self,
        correlation_id: str,
        timeout_seconds: float = 30.0,
        poll_interval: float = 0.1,
    ) -> FormattedResponse | None:
        """
        Get response by correlation ID, waiting if necessary (async).

        Args:
            correlation_id: Correlation ID to look up
            timeout_seconds: Maximum time to wait
            poll_interval: Polling interval

        Returns:
            FormattedResponse or None if not found
        """
        loop = asyncio.get_running_loop()
        start_time = loop.time()

        while loop.time() - start_time < timeout_seconds:
            with self._lock:
                if correlation_id in self._responses:
                    self._stats["cache_hits"] += 1
                    return self._responses[correlation_id][0]

            await asyncio.sleep(poll_interval)

        self._stats["cache_misses"] += 1
        return None

    def get_response_nowait(self, correlation_id: str) -> FormattedResponse | None:
        """
        Get response immediately without waiting.

        Args:
            correlation_id: Correlation ID to look up

        Returns:
            FormattedResponse or None if not found
        """
        with self._lock:
            if correlation_id in self._responses:
                self._stats["cache_hits"] += 1
                return self._responses[correlation_id][0]

        self._stats["cache_misses"] += 1
        return None

    def format_result(
        self,
        result: dict[str, Any],
        output_format: OutputFormat | None = None,
    ) -> str:
        """
        Format a result directly.

        Args:
            result: Result dictionary to format
            output_format: Desired output format

        Returns:
            Formatted string
        """
        return self.formatter.format(result, output_format or self.default_format)

    def get_stats(self) -> dict[str, Any]:
        """Get handler statistics."""
        return {
            **self._stats,
            "cached_responses": len(self._responses),
            "registered_handlers": len(self._source_handlers),
        }

    def clear_cache(self) -> None:
        """Clear response cache."""
        with self._lock:
            self._responses.clear()
        logger.debug("Response cache cleared")


# ─────────────────────────────────────────────────────────────
# Factory Functions
# ─────────────────────────────────────────────────────────────

_default_output_handler: OutputHandler | None = None


def get_output_handler(event_bus: EventBus | None = None) -> OutputHandler:
    """
    Get the default output handler instance.

    Args:
        event_bus: Optional EventBus (uses default if not provided)

    Returns:
        Shared OutputHandler instance
    """
    global _default_output_handler

    if _default_output_handler is None:
        from grid.events.core import get_event_bus as get_default_bus

        bus = event_bus or get_default_bus()
        _default_output_handler = OutputHandler(bus)

    return _default_output_handler


def set_output_handler(handler: OutputHandler) -> None:
    """
    Set the default output handler instance.

    Args:
        handler: OutputHandler to use as default
    """
    global _default_output_handler
    _default_output_handler = handler
