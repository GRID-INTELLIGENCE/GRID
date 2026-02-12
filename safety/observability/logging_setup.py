"""
Structured logging configuration for the safety enforcement pipeline.

All logs are JSON-structured with mandatory trace_id, request_id, and user_id
correlation fields. Uses structlog for processing and loguru for output.
"""

from __future__ import annotations

import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from loguru import logger as loguru_logger

# ---------------------------------------------------------------------------
# Context variables (set in middleware, propagated everywhere)
# ---------------------------------------------------------------------------
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def set_trace_context(
    trace_id: str | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
) -> str:
    """Set trace context for the current async task. Returns the trace_id."""
    tid = trace_id or str(uuid.uuid4())
    rid = request_id or str(uuid.uuid4())
    _trace_id_var.set(tid)
    _request_id_var.set(rid)
    if user_id:
        _user_id_var.set(user_id)
    return tid


def get_trace_id() -> str:
    return _trace_id_var.get()


def get_request_id() -> str:
    return _request_id_var.get()


def get_user_id() -> str:
    return _user_id_var.get()


# ---------------------------------------------------------------------------
# Structlog processors
# ---------------------------------------------------------------------------
def _add_trace_context(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject trace context into every log event."""
    event_dict.setdefault("trace_id", _trace_id_var.get())
    event_dict.setdefault("request_id", _request_id_var.get())
    event_dict.setdefault("user_id", _user_id_var.get())
    return event_dict


def _add_service_info(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    event_dict["service"] = "safety-enforcement"
    event_dict["environment"] = os.getenv("SAFETY_ENV", "development")
    return event_dict


# ---------------------------------------------------------------------------
# Loguru sink (receives structlog output)
# ---------------------------------------------------------------------------
def _loguru_sink(record: dict[str, Any]) -> None:
    """Forward structlog JSON records to loguru for unified output."""
    level = record.get("level", "info")
    loguru_logger.log(level.upper(), "{event}", **record)


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
_initialized = False


def setup_logging(*, json_output: bool = True, log_level: str = "INFO") -> None:
    """
    Initialize structured logging for the safety pipeline.

    Call once at application startup.
    """
    global _initialized
    if _initialized:
        return

    # Configure loguru
    loguru_logger.remove()  # Remove default handler
    log_format = (
        "<green>{time:YYYY-MM-DDTHH:mm:ss.SSSZ}</green> | "
        "<level>{level: <8}</level> | "
        "{message}"
    )
    if json_output:
        loguru_logger.add(
            sys.stderr,
            format="{message}",
            level=log_level,
            serialize=True,  # JSON output
        )
    else:
        loguru_logger.add(sys.stderr, format=log_format, level=log_level)

    # Also log to a file for persistence
    log_dir = os.getenv("SAFETY_LOG_DIR", "safety/logs")
    os.makedirs(log_dir, exist_ok=True)
    loguru_logger.add(
        os.path.join(log_dir, "safety_{time:YYYY-MM-DD}.jsonl"),
        format="{message}",
        serialize=True,
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        level=log_level,
    )

    # Configure structlog
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_trace_context,
        _add_service_info,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.stdlib.NAME_TO_LEVEL.get(log_level.lower(), 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _initialized = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger, optionally named."""
    if not _initialized:
        setup_logging()
    log = structlog.get_logger()
    if name:
        log = log.bind(component=name)
    return log
