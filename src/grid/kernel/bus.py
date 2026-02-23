"""Message broker with retry tracking and dead-letter queue."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class RetryRecord:
    """Track retry attempts for a message."""

    def __init__(self, message_id: str, max_retries: int = 3) -> None:
        self.message_id = message_id
        self.attempts = 0
        self.max_retries = max_retries
        self.last_error: str | None = None

    def can_retry(self) -> bool:
        return self.attempts <= self.max_retries

    def record_attempt(self, error: str) -> None:
        self.attempts += 1
        self.last_error = error


class DeadLetterQueue:
    """Dead letter queue for messages that exceeded retry limits."""

    def __init__(self) -> None:
        self.messages: dict[str, dict[str, Any]] = {}

    def put(self, message_id: str, message: Any, error: str) -> None:
        """Add a message to the DLQ."""
        self.messages[message_id] = {
            "message": message,
            "error": error,
            "timestamp": datetime.now(),
        }

    def get_all(self) -> list[dict[str, Any]]:
        """Get all DLQ messages."""
        return list(self.messages.values())


class MessageBroker:
    """Message broker with retry tracking and dead-letter queue support."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.retry_records: dict[str, RetryRecord] = {}
        self.dlq = DeadLetterQueue()

    def handle_message_failure(self, message_id: str, message: Any, error: str) -> bool:
        """Handle a message failure. Returns True if the message should be retried."""
        if message_id not in self.retry_records:
            self.retry_records[message_id] = RetryRecord(message_id, self.max_retries)

        record = self.retry_records[message_id]
        record.record_attempt(error)

        if record.can_retry():
            return True

        # Max retries exceeded — move to DLQ
        self.dlq.put(message_id, message, f"Max retries exceeded: {error}")
        return False
