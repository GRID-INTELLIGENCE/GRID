"""
Privacy Worker - Background processor for PII detection requests.

Consumes from Redis Stream: privacy-stream
Performs async PII detection/masking and writes results to result-stream or updates audit log.
"""

import asyncio
import json
import signal
import time
from typing import Any

from safety.observability.logging_setup import get_logger, set_trace_context
from safety.observability.metrics import (
    WORKER_JOBS_PROCESSED,
    WORKER_QUEUE_DEPTH,
)
from safety.privacy.core.engine import get_privacy_engine
from safety.privacy.core.presets import PrivacyPreset
from safety.workers.worker_utils import (
    check_redis_health,
    get_redis,
)

logger = get_logger("privacy.worker")

# Configuration
STREAM_NAME = "privacy-stream"
CONSUMER_GROUP = "privacy-workers"
_CONSUMER_NAME = f"privacy-worker-{int(time.time())}"
_BATCH_SIZE = 10
_BLOCK_MS = 2000  # 2 seconds


class PrivacyWorker:
    """Consumes privacy check jobs from Redis Streams."""

    def __init__(self):
        self.running = False
        self.redis = None

    async def start(self):
        """Start the worker loop."""
        self.running = True
        self.redis = await get_redis()

        # Ensure consumer group exists
        try:
            await self.redis.xgroup_create(STREAM_NAME, CONSUMER_GROUP, mkstream=True)
            logger.info("consumer_group_created", group=CONSUMER_GROUP)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error("consumer_group_error", error=str(e))

        logger.info("privacy_worker_started", consumer=_CONSUMER_NAME)

        while self.running:
            try:
                # Update queue depth metric
                depth = await self.redis.xlen(STREAM_NAME)
                WORKER_QUEUE_DEPTH.set(depth)

                # Fetch messages
                messages = await self.redis.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=_CONSUMER_NAME,
                    streams={STREAM_NAME: ">"},
                    count=_BATCH_SIZE,
                    block=_BLOCK_MS,
                )

                if not messages:
                    continue

                for _, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        await self._process_message(message_id, fields)

            except Exception as e:
                logger.error("worker_loop_error", error=str(e))
                await asyncio.sleep(1)

    async def _process_message(self, message_id: bytes, fields: dict[bytes, bytes]):
        """Process a single message."""
        if self.redis is None:
            logger.error("redis_not_connected", message_id=message_id)
            return
        try:
            # Decode fields
            data = {k.decode(): v.decode() for k, v in fields.items()}

            request_id = data.get("request_id")
            text = data.get("text", "")
            context_id = data.get("context_id")
            action = data.get("action", "detect")  # detect | mask

            set_trace_context(request_id=request_id)

            # Get privacy engine (Singular or Plural based on context_id)
            engine = get_privacy_engine(
                collaborative=bool(context_id),
                context_id=context_id,
                preset=PrivacyPreset.BALANCED,
            )

            # Process
            start_time = time.time()
            if action == "mask":
                result = await engine.process(text, context_id=context_id)
                output = result.to_dict()
            else:
                detections = await engine.detect(text, context_id=context_id)
                output = {"detections": detections}

            duration = time.time() - start_time

            # Log completion
            logger.info(
                "privacy_job_completed",
                request_id=request_id,
                duration=duration,
                action=action
            )
            WORKER_JOBS_PROCESSED.labels(result="success").inc()

            # For now, we assume this is just background scanning.
            # In a real system, we might push results to a 'results-stream'
            # or update a db status.

            # Acknowledge (redis already checked at start of method)
            await self.redis.xack(STREAM_NAME, CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error("message_processing_failed", error=str(e), message_id=message_id)
            WORKER_JOBS_PROCESSED.labels(result="error").inc()
            # Don't ack so it can be retried or moved to DLQ

    async def stop(self):
        """Stop the worker."""
        self.running = False
        if self.redis:
            await self.redis.close()
        logger.info("privacy_worker_stopped")


async def main():
    """Entry point."""
    worker = PrivacyWorker()

    def handle_signal():
        asyncio.create_task(worker.stop())

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
