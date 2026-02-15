"""
Redis Streams consumer worker for the safety inference pipeline.

Consumes jobs from `inference-stream`, calls the model inside the sandbox,
runs post-check detectors, and either releases the response or escalates.

Run as a standalone process:
    python -m safety.workers.consumer
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import redis.asyncio as aioredis

from safety.detectors.post_check import post_check
from safety.escalation.handler import escalate
from safety.model.client import call_model
from safety.observability.canary import safety_canary
from safety.observability.logging_setup import (
    get_logger,
    set_trace_context,
    setup_logging,
)
from safety.observability.metrics import (
    DETECTION_LATENCY,
    WORKER_JOBS_PROCESSED,
    record_service_info,
)
from safety.observability.risk_score import risk_manager
from safety.workers.worker_utils import (
    CONSUMER_GROUP,
    INFERENCE_STREAM,
    close_redis,
    ensure_consumer_group,
    get_redis,
    is_shutting_down,
    publish_response,
    setup_shutdown_handler,
    write_audit_event,
)

logger = get_logger("workers.consumer")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_CONSUMER_NAME = os.getenv("SAFETY_CONSUMER_NAME", f"worker-{os.getpid()}")
_BATCH_SIZE = int(os.getenv("SAFETY_BATCH_SIZE", "5"))
_BLOCK_MS = int(os.getenv("SAFETY_BLOCK_MS", "5000"))
_MAX_RETRIES = int(os.getenv("SAFETY_MAX_RETRIES", "3"))


# ---------------------------------------------------------------------------
# Message processing
# ---------------------------------------------------------------------------
async def _process_message(msg_id: str, fields: dict[str, str]) -> None:
    """
    Process a single inference request message.

    Steps:
    1. Parse message fields.
    2. Set trace context.
    3. Call model via sandbox.
    4. Run post-check.
    5. Release or escalate.
    """
    request_id = fields.get("request_id", "unknown")
    user_id = fields.get("user_id", "unknown")
    input_text = fields.get("input", "")
    trust_tier = fields.get("trust_tier", "user")
    trace_id = fields.get("trace_id", "")
    metadata = json.loads(fields.get("metadata", "{}"))

    set_trace_context(trace_id=trace_id, request_id=request_id, user_id=user_id)

    logger.info(
        "processing_message",
        msg_id=msg_id,
        request_id=request_id,
        user_id=user_id,
    )

    import time

    try:
        # Combined detection pipeline timing
        start_processing = time.perf_counter()

        # Step 1: Call model via sandboxed client
        result = await call_model(
            prompt=input_text,
            user_id=user_id,
            temperature=metadata.get("temperature", 0.7),
            max_tokens=metadata.get("max_tokens", 4096),
        )

        # Step 2: Run post-check detector with timeout (fail-closed)
        try:
            check_result = await asyncio.wait_for(
                post_check(
                    model_output=result.text,
                    original_input=input_text,
                ),
                timeout=10.0,
            )
        except TimeoutError:
            logger.error("post_check_timeout", request_id=request_id)
            # Fail closed: treat as flagged
            from safety.detectors.post_check import PostCheckResult

            check_result = PostCheckResult(
                flagged=True,
                reason_code="POST_CHECK_TIMEOUT",
                severity="high",
                evidence={"error": "timeout_10s_exceeded"},
            )

        # Observe total latency (model + post-check)
        latency = time.perf_counter() - start_processing
        DETECTION_LATENCY.observe(latency)

        if check_result.flagged:
            # Step 3a: Escalate — do NOT return model output
            logger.warning(
                "output_flagged",
                request_id=request_id,
                reason_code=check_result.reason_code,
                severity=check_result.severity,
            )
            await escalate(
                request_id=request_id,
                user_id=user_id,
                trust_tier=trust_tier,
                reason_code=check_result.reason_code,
                severity=check_result.severity,
                input_text=input_text,
                model_output=result.text,
                detector_scores=check_result.evidence,
                trace_id=trace_id,
            )
            await write_audit_event(
                event="postcheck_flag",
                request_id=request_id,
                user_id=user_id,
                reason=check_result.reason_code,
                payload=check_result.evidence,
            )
            WORKER_JOBS_PROCESSED.labels(result="flagged").inc()
        else:
            # Project GUARDIAN: Adaptive Watermarking
            response_text = result.text
            risk_score = await risk_manager.get_score(user_id)
            if risk_score > 0.2:
                response_text = safety_canary.inject(response_text)
                logger.info("safety_canary_injected", request_id=request_id, risk_score=risk_score)

            # Step 3b: Release response
            await publish_response(
                request_id=request_id,
                response=response_text,
                status="completed",
            )
            WORKER_JOBS_PROCESSED.labels(result="passed").inc()
            logger.info(
                "output_released",
                request_id=request_id,
                tokens_used=result.tokens_used,
                canary_injected=(risk_score > 0.2),
            )

    except Exception as exc:
        logger.error(
            "processing_error",
            request_id=request_id,
            error=str(exc),
        )
        WORKER_JOBS_PROCESSED.labels(result="error").inc()
        await write_audit_event(
            event="processing_error",
            request_id=request_id,
            user_id=user_id,
            reason="PROCESSING_ERROR",
            payload={"error": str(exc)},
        )
        raise  # Re-raise to skip xack (message will be retried)


# ---------------------------------------------------------------------------
# Consumer loop
# ---------------------------------------------------------------------------
async def consume() -> None:
    """
    Main consumer loop. Reads from the inference stream and processes messages.

    Uses Redis consumer groups with manual xack for at-least-once delivery.
    """
    setup_logging()
    record_service_info(version="1.0.0", environment=os.getenv("SAFETY_ENV", "development"))

    client = await get_redis()
    await ensure_consumer_group()

    logger.info(
        "consumer_started",
        consumer=_CONSUMER_NAME,
        group=CONSUMER_GROUP,
        stream=INFERENCE_STREAM,
    )

    while not is_shutting_down():
        try:
            # Read messages from the consumer group
            messages = await client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=_CONSUMER_NAME,
                streams={INFERENCE_STREAM: ">"},
                count=_BATCH_SIZE,
                block=_BLOCK_MS,
            )

            if not messages:
                continue

            for stream_name, stream_messages in messages:
                for msg_id, fields in stream_messages:
                    try:
                        await _process_message(msg_id, fields)
                        # Acknowledge successful processing
                        await client.xack(INFERENCE_STREAM, CONSUMER_GROUP, msg_id)
                    except Exception as exc:
                        logger.error(
                            "message_processing_failed",
                            msg_id=msg_id,
                            error=str(exc),
                        )
                        # Message remains pending; will be retried or
                        # picked up by another consumer via XCLAIM

        except aioredis.ConnectionError as exc:
            logger.error("redis_connection_lost", error=str(exc))
            await asyncio.sleep(5)  # Back off and retry
        except Exception as exc:
            logger.error("consumer_error", error=str(exc))
            await asyncio.sleep(1)

    logger.info("consumer_shutting_down", consumer=_CONSUMER_NAME)
    await close_redis()


# ---------------------------------------------------------------------------
# Pending message recovery (for incident forensics and retry)
# ---------------------------------------------------------------------------
async def replay_pending(
    max_messages: int = 100,
) -> list[dict[str, Any]]:
    """
    Retrieve pending messages that haven't been acknowledged.

    Useful for incident forensics and manual retry.
    """
    client = await get_redis()
    pending = await client.xpending_range(
        INFERENCE_STREAM,
        CONSUMER_GROUP,
        min="-",
        max="+",
        count=max_messages,
    )
    results = []
    for entry in pending:
        msg_id = entry["message_id"]
        msgs = await client.xrange(INFERENCE_STREAM, min=msg_id, max=msg_id)
        if msgs:
            results.append({"msg_id": msg_id, "fields": msgs[0][1], "pending": entry})
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the consumer as a standalone process."""
    setup_shutdown_handler()
    asyncio.run(consume())


if __name__ == "__main__":
    main()
