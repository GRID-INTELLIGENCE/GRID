"""
Distributed Worker Pool using Redis Streams for "Exactly-Once" task processing.
Enables competing consumers across multiple K8s replicas.
"""

import asyncio
import json
import logging
import socket
from collections.abc import Callable
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DistributedWorkerPool:
    def __init__(
        self,
        redis_url: str = "redis://redis:6379/0",
        stream_name: str = "grid:tasks",
        group_name: str = "grid:worker_group",
    ):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = f"worker:{socket.gethostname()}"
        self.redis: redis.Redis | None = None
        self._running = False

    async def connect(self):
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        logger.info(f"Connected to Redis Stream: {self.stream_name} as {self.consumer_name}")

    async def submit_task(self, task_type: str, payload: dict[str, Any]):
        """Submit a task to the distributed stream."""
        if not self.redis:
            await self.connect()

        data = {"type": task_type, "payload": json.dumps(payload), "submitted_by": self.consumer_name}
        task_id = await self.redis.xadd(self.stream_name, data)
        logger.debug(f"Task {task_id} submitted to stream")
        return task_id

    async def start_worker(self, handler: Callable[[str, dict[str, Any]], Any]):
        """Start consuming tasks from the stream."""
        self._running = True
        logger.info(f"Worker {self.consumer_name} starting...")

        if not self.redis:
            await self.connect()

        while self._running:
            try:
                # Read new messages from group
                # '>' means only new messages that haven't been delivered to other consumers
                messages = await self.redis.xreadgroup(
                    self.group_name, self.consumer_name, {self.stream_name: ">"}, count=1, block=5000
                )

                if not messages:
                    continue

                for _stream, msgs in messages:
                    for msg_id, data in msgs:
                        task_type = data["type"]
                        payload = json.loads(data["payload"])

                        logger.info(f"Processing task {msg_id} (Type: {task_type})")

                        try:
                            await handler(task_type, payload)
                            # Acknowledge successful processing
                            await self.redis.xack(self.stream_name, self.group_name, msg_id)
                        except Exception as e:
                            logger.error(f"Error processing task {msg_id}: {e}")
                            # In a real system, you might implement retry logic or DLQ here

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)

    async def stop(self):
        self._running = False
        if self.redis:
            await self.redis.close()
