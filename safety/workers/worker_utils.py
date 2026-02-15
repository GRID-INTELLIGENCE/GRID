"""
Utility functions for the inference worker.

Provides Redis Streams helpers, health checks, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
from typing import Any

import redis.asyncio as aioredis

from safety.observability.logging_setup import get_logger
from safety.observability.metrics import REDIS_HEALTHY, WORKER_QUEUE_DEPTH

logger = get_logger("workers.utils")

_redis: aioredis.Redis | None = None
_shutdown_event = asyncio.Event()

INFERENCE_STREAM = "inference-stream"
RESPONSE_STREAM = "response-stream"
AUDIT_STREAM = "audit-stream"
CONSUMER_GROUP = "safety-workers"


async def get_redis() -> aioredis.Redis:
    """Get the shared async Redis client."""
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis = aioredis.from_url(url, decode_responses=True)
    return _redis


async def ensure_consumer_group() -> None:
    """Create the consumer group if it doesn't exist."""
    client = await get_redis()
    try:
        await client.xgroup_create(INFERENCE_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info("consumer_group_created", group=CONSUMER_GROUP)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info("consumer_group_exists", group=CONSUMER_GROUP)
        else:
            raise


async def enqueue_request(
    request_id: str,
    user_id: str,
    input_text: str,
    trust_tier: str,
    trace_id: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Enqueue a request to the inference stream.

    Returns the Redis stream message ID.
    Raises RuntimeError if Redis is unreachable (fail closed).
    """
    try:
        client = await get_redis()
        msg_id = await client.xadd(
            INFERENCE_STREAM,
            {
                "request_id": request_id,
                "user_id": user_id,
                "input": input_text,
                "trust_tier": trust_tier,
                "trace_id": trace_id,
                "metadata": json.dumps(metadata or {}),
            },
        )
        logger.info(
            "request_enqueued",
            request_id=request_id,
            stream_id=msg_id,
        )
        REDIS_HEALTHY.set(1)
        return msg_id
    except Exception as exc:
        REDIS_HEALTHY.set(0)
        logger.error("enqueue_failed", request_id=request_id, error=str(exc))
        raise RuntimeError(f"Failed to enqueue request: {exc}") from exc


async def publish_response(request_id: str, response: str, status: str = "completed") -> None:
    """Publish a response to the response stream."""
    try:
        client = await get_redis()
        await client.xadd(
            RESPONSE_STREAM,
            {
                "request_id": request_id,
                "response": response,
                "status": status,
            },
        )
    except Exception as exc:
        logger.error("response_publish_failed", request_id=request_id, error=str(exc))
        raise


async def write_audit_event(
    event: str,
    request_id: str,
    user_id: str,
    reason: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Write an event to the audit stream."""
    try:
        client = await get_redis()
        await client.xadd(
            AUDIT_STREAM,
            {
                "event": event,
                "request_id": request_id,
                "user_id": user_id,
                "reason": reason,
                "payload": json.dumps(payload or {}),
            },
        )
    except Exception as exc:
        logger.error("audit_event_failed", event=event, error=str(exc))  # type: ignore[reportArgumentType]


async def get_queue_depth() -> int:
    """Get the current depth of the inference stream."""
    try:
        client = await get_redis()
        info = await client.xinfo_stream(INFERENCE_STREAM)
        depth = info.get("length", 0)
        WORKER_QUEUE_DEPTH.set(depth)
        return depth
    except Exception:
        return -1


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        client = await get_redis()
        await client.ping()  # type: ignore[reportAwaitableReturnType]
        REDIS_HEALTHY.set(1)
        return True
    except Exception as exc:
        logger.error("redis_health_check_failed", error=str(exc))  # type: ignore[reportArgumentType]
        REDIS_HEALTHY.set(0)
        return False


def setup_shutdown_handler() -> None:
    """Register signal handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown_event.set)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for all signals
            signal.signal(sig, lambda s, f: _shutdown_event.set())


def is_shutting_down() -> bool:
    """Check if shutdown has been requested."""
    return _shutdown_event.is_set()


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
