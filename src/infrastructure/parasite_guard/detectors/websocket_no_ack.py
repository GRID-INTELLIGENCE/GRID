"""
WebSocket No-Ack Detector.

Detects WebSocket sessions that fail to acknowledge messages within a timeout.
This detector is designed to be used within the WebSocket endpoint or as a specialized wrapper.
"""

import logging
from typing import Any

from fastapi import WebSocket

from ..definitions import ParasiteAction, ParasiteContext, ParasiteRisk
from ..detector import ParasiteDetector

logger = logging.getLogger(__name__)


class WebSocketNoAckDetector(ParasiteDetector):
    """
    Detects messages sent without ACK confirmation.

    This detector tracks the time between 'send' and 'ack' messages.
    If the timeout is exceeded, it flags the session as parasitic.
    """

    def __init__(self, timeout_seconds: float = 3.0, max_retries: int = 2):
        self.timeout = timeout_seconds
        self.max_retries = max_retries

    async def __call__(self, request: Any) -> ParasiteContext | None:
        # NOTE: This detector is intended to be called with a WebSocket object
        # or a value-object representing the session state, not a raw HTTP Request.
        # For HTTP Middleware, this would likely return None as it can't inspect active WS frames.

        # Prototype logic for middleware compliance:
        if isinstance(request, WebSocket):
            # We can't easily peek into the state from here without deep integration.
            # This serves as the placeholder for the architecture.
            return None

        return None

    def check_session(self, session_id: str, last_ack_time: float, current_time: float) -> ParasiteContext | None:
        """
        Check a specific session state (to be called by the application logic).
        """
        if current_time - last_ack_time > self.timeout:
            return ParasiteContext(
                component="websocket",
                rule="no_ack",
                risk=ParasiteRisk.CRITICAL,
                action=ParasiteAction.SANITIZE,
                meta={
                    "session_id": session_id,
                    "last_ack_time": last_ack_time,
                    "timeout_exceeded": current_time - last_ack_time,
                },
            )
        return None
