"""
DRT (Don't Repeat Themselves) Middleware for focused monitoring.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class BehavioralSignature:
    """Represents a behavioral signature for pattern matching."""

    def __init__(
        self,
        path_pattern: str,
        method: str,
        headers: tuple[str, ...],
        body_pattern: str | None = None,
        query_pattern: str | None = None,
    ):
        self.path_pattern = path_pattern
        self.method = method
        self.headers = headers
        self.body_pattern = body_pattern
        self.query_pattern = query_pattern
        self.timestamp = datetime.now(UTC)
        self.request_count = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "method": self.method,
            "headers": self.headers,
            "body_pattern": self.body_pattern,
            "query_pattern": self.query_pattern,
            "timestamp": self.timestamp.isoformat(),
            "request_count": self.request_count,
        }


class ComprehensiveDRTMiddleware(BaseHTTPMiddleware):
    """Middleware for DRT - Don't Repeat Themselves focused monitoring."""

    def __init__(
        self,
        app: Any,
        enabled: bool = True,
        similarity_threshold: float = 0.85,
        retention_hours: int = 96,
        websocket_overhead: bool = True,
        auto_escalate: bool = True,
        escalation_timeout_minutes: int = 60,
        rate_limit_multiplier: float = 0.5,
        sampling_rate: float = 1.0,
        alert_on_escalation: bool = True,
        db_session: Any | None = None,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.similarity_threshold = similarity_threshold
        self.retention_hours = retention_hours
        self.websocket_overhead = websocket_overhead
        self.auto_escalate = auto_escalate
        self.escalation_timeout_minutes = escalation_timeout_minutes
        self.rate_limit_multiplier = rate_limit_multiplier
        self.sampling_rate = sampling_rate
        self.alert_on_escalation = alert_on_escalation

        # Database session and repositories (lazy-loaded)
        self._db_session = db_session
        self._sig_repo = None
        self._attack_repo = None
        self._violation_repo = None
        self._escalated_repo = None
        self._config_repo = None

        # In-memory caches for performance
        self.ESCALATED_ENDPOINTS: dict[str, datetime] = {}
        self.behavioral_history: list[BehavioralSignature] = []
        self.attack_vectors: list[BehavioralSignature] = []
        self._attack_vector_ids: dict[str, str] = {}  # signature_id -> attack_vector_id
        self._cleanup_task: asyncio.Task | None = None

        # Initialize from database
        self._initialized = False

    def _ensure_db_components(self) -> None:
        """Lazy-load database components when needed."""
        if self._db_session is None:
            try:
                from ..db.engine import get_db_session

                self._db_session = get_db_session()
            except ImportError:
                # Database not available (e.g., during testing)
                return

        if self._sig_repo is None:
            try:
                from ..repositories.drt import (
                    DRTAttackVectorRepository,
                    DRTBehavioralSignatureRepository,
                    DRTConfigurationRepository,
                    DRTEscalatedEndpointRepository,
                    DRTViolationRepository,
                )

                self._sig_repo = DRTBehavioralSignatureRepository(self._db_session)
                self._attack_repo = DRTAttackVectorRepository(self._db_session)
                self._violation_repo = DRTViolationRepository(self._db_session)
                self._escalated_repo = DRTEscalatedEndpointRepository(self._db_session)
                self._config_repo = DRTConfigurationRepository(self._db_session)
            except ImportError:
                # Repositories not available (e.g., during testing)
                pass

    async def initialize(self) -> None:
        """Initialize middleware by loading data from database."""
        if self._initialized:
            return

        self._ensure_db_components()

        if self._attack_repo is None:
            # Database not available, skip initialization
            self._initialized = True
            return

        try:
            # Load attack vectors
            attack_data = await self._attack_repo.get_all(active_only=True)
            self.attack_vectors = [sig for _, sig, _ in attack_data]
            self._attack_vector_ids = {str(id(sig)): attack_id for attack_id, sig, _ in attack_data}

            # Load recent behavioral history
            self.behavioral_history = await self._sig_repo.get_recent(hours=self.retention_hours)

            # Load escalated endpoints
            escalated_data = await self._escalated_repo.get_active()
            self.ESCALATED_ENDPOINTS = {path: expires for path, expires, _ in escalated_data}

            # Load configuration
            config = await self._config_repo.get_config_dict()
            # Update settings from database if different
            self.enabled = config.get("enabled", self.enabled)
            self.similarity_threshold = config.get("similarity_threshold", self.similarity_threshold)
            self.retention_hours = config.get("retention_hours", self.retention_hours)
            self.websocket_overhead = config.get("websocket_overhead", self.websocket_overhead)
            self.auto_escalate = config.get("auto_escalate", self.auto_escalate)
            self.escalation_timeout_minutes = config.get("escalation_timeout_minutes", self.escalation_timeout_minutes)
            self.rate_limit_multiplier = config.get("rate_limit_multiplier", self.rate_limit_multiplier)
            self.sampling_rate = config.get("sampling_rate", self.sampling_rate)
            self.alert_on_escalation = config.get("alert_on_escalation", self.alert_on_escalation)

            self._initialized = True
            logger.info(
                f"DRT middleware initialized with {len(self.attack_vectors)} attack vectors and {len(self.behavioral_history)} signatures"
            )

        except Exception as e:
            logger.error(f"Failed to initialize DRT middleware from database: {e}")
            # Continue with empty state - better than crashing

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Ensure initialization
        await self.initialize()

        # Track processing start time for metrics
        start_time = time.time()

        signature = self._build_signature(request)
        similarity, matched_vector = self._check_similarity(signature)

        if similarity >= self.similarity_threshold and matched_vector:
            logger.warning(
                f"DRT: Behavioral similarity detected ({similarity:.2f}) with attack vector for {request.url.path}"
            )

            if self.auto_escalate:
                self._escalate_endpoint(request.url.path)

                if request.url.path in self.ESCALATED_ENDPOINTS:
                    await asyncio.sleep(0.1 * self.rate_limit_multiplier)

            if self.websocket_overhead:
                self._apply_websocket_overhead(request)

            # Record violation to database and metrics
            processing_time = time.time() - start_time
            await self._record_violation(signature, matched_vector, similarity, request, processing_time)

        response = await call_next(request)
        self._record_behavior(signature)

        return response

    def _build_signature(self, request: Request) -> BehavioralSignature:
        header_keys = tuple(
            sorted(
                [
                    k
                    for k in request.headers.keys()
                    if k.lower() not in {"authorization", "cookie", "x-api-key", "x-request-id"}
                ]
            )
        )

        return BehavioralSignature(
            path_pattern=self._normalize_path(request.url.path),
            method=request.method,
            headers=header_keys,
            body_pattern=self._extract_body_pattern(request),
            query_pattern=self._normalize_query(request.url.query) if request.url.query else None,
        )

    def _normalize_path(self, path: str) -> str:
        import re

        normalized = re.sub(r"/[a-f0-9-]{36}", "/{UUID}", path)
        normalized = re.sub(r"/\d+", "/{ID}", normalized)
        return normalized

    def _normalize_query(self, query: str) -> str:
        import urllib.parse

        params = urllib.parse.parse_qs(query)
        return "&".join(sorted(params.keys()))

    def _extract_body_pattern(self, request: Request) -> str | None:
        """Extract a pattern from the request body for behavioral analysis."""
        if request.method not in {"POST", "PUT", "PATCH"}:
            return None

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                # Note: In a real implementation, we'd need to read the request body
                # This is a simplified version for demonstration
                # In FastAPI, request.body() is available but may be consumed
                # This would need to be handled carefully to avoid interfering with normal request processing
                return None  # Placeholder for now

            except Exception as e:
                logger.debug(f"Error extracting body pattern: {e}")
                return None

        return None

    def _check_similarity(self, signature: BehavioralSignature) -> tuple[float, BehavioralSignature | None]:
        max_similarity = 0.0
        matched_vector = None

        for vector in self.attack_vectors:
            similarity = self._calculate_similarity(signature, vector)
            if similarity > max_similarity:
                max_similarity = similarity
                matched_vector = vector

        return max_similarity, matched_vector

    def _calculate_similarity(self, sig1: BehavioralSignature, sig2: BehavioralSignature) -> float:
        if sig1.method != sig2.method or sig1.path_pattern != sig2.path_pattern:
            return 0.0

        headers1 = set(sig1.headers)
        headers2 = set(sig2.headers)

        if not headers1 and not headers2:
            header_similarity = 1.0
        elif not headers1 or not headers2:
            header_similarity = 0.0
        else:
            intersection = len(headers1 & headers2)
            union = len(headers1 | headers2)
            header_similarity = intersection / union if union > 0 else 0.0

        return header_similarity

    def _escalate_endpoint(self, path: str) -> None:
        expires_at = datetime.now(UTC) + timedelta(minutes=self.escalation_timeout_minutes)
        self.ESCALATED_ENDPOINTS[path] = expires_at

        if self.alert_on_escalation:
            logger.warning(f"DRT: Endpoint escalated: {path} (timeout: {self.escalation_timeout_minutes} minutes)")

        # Record escalation metrics (local import to avoid circular dependency)
        from .drt_metrics import record_drt_escalation

        record_drt_escalation(path=path, similarity_score=0.0, duration_minutes=self.escalation_timeout_minutes)

        # Persist escalation (fire and forget)
        try:
            asyncio.create_task(self._persist_escalation(path, expires_at))
        except RuntimeError:
            pass  # No running event loop (e.g. unit tests)

    def _apply_websocket_overhead(self, request: Request) -> None:
        """Apply WebSocket overhead to suspicious endpoints."""
        if request.url.path in self.ESCALATED_ENDPOINTS:
            # Add a unique token to the response that must be included in subsequent requests
            token = secrets.token_urlsafe(16)
            request.state.drt_websocket_token = token
            request.state.drt_websocket_timestamp = int(time.time())

            # This token would need to be validated in subsequent WebSocket messages
            logger.debug(f"Applied WebSocket overhead token to {request.url.path}")

    async def _record_violation(
        self,
        signature: BehavioralSignature,
        matched_vector: BehavioralSignature,
        similarity: float,
        request: Request,
        processing_time: float,
    ) -> None:
        """Record a violation to the database."""
        self._ensure_db_components()

        if self._violation_repo is None:
            # Database not available, skip recording
            return

        try:
            # Get attack vector ID and severity
            attack_vector_id = None
            severity = "medium"  # default

            for vector_id, vector_sig in self._attack_vector_ids.items():
                if self._calculate_similarity(signature, vector_sig) >= self.similarity_threshold:
                    attack_vector_id = vector_id
                    # Try to get severity from attack vectors
                    for attack_sig, attack_severity in zip(self.attack_vectors, ["medium"] * len(self.attack_vectors), strict=False):
                        if attack_sig == vector_sig:
                            severity = attack_severity
                            break
                    break

            if attack_vector_id:
                # Extract request metadata
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")

                await self._violation_repo.record(
                    signature=signature,
                    attack_vector_id=attack_vector_id,
                    similarity_score=similarity,
                    request_path=request.url.path,
                    request_method=request.method,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    was_blocked=False,  # Currently we only escalate, not block
                    action_taken="escalate",
                    meta={
                        "headers": dict(request.headers),
                        "query_params": str(request.url.query),
                        "escalated_endpoint": request.url.path in self.ESCALATED_ENDPOINTS,
                        "processing_time_ms": processing_time * 1000,
                    },
                )

                # Record metrics
                try:
                    from .drt_metrics import record_drt_violation

                    record_drt_violation(
                        similarity_score=similarity,
                        attack_vector_severity=severity,
                        request_path=request.url.path,
                        request_method=request.method,
                        was_blocked=False,
                        processing_time=processing_time,
                    )
                except ImportError:
                    pass  # Metrics not available
        except Exception as e:
            logger.error(f"Failed to record DRT violation to database: {e}")
            # Don't crash the middleware for persistence failures

    def _record_behavior(self, signature: BehavioralSignature) -> None:
        """Record behavioral signature."""
        # Add to in-memory cache
        self.behavioral_history.append(signature)

        # Persist to database (fire and forget for performance)
        try:
            asyncio.create_task(self._persist_behavior(signature))
        except RuntimeError:
            pass  # No running event loop (e.g. unit tests)

    async def _persist_behavior(self, signature: BehavioralSignature) -> None:
        """Persist behavioral signature to database."""
        try:
            await self._sig_repo.save(signature, retention_hours=self.retention_hours)
        except Exception as e:
            logger.error(f"Failed to persist behavioral signature: {e}")

    async def _persist_escalation(self, path: str, expires_at: datetime) -> None:
        """Persist escalated endpoint to database."""
        try:
            await self._escalated_repo.save(
                path=path,
                expires_at=expires_at,
                escalation_reason="behavioral_similarity",
                similarity_score=0.0,  # Will be updated when we have the actual score
                attack_vector_id=None,  # Will be updated when we match against specific vectors
            )
        except Exception as e:
            logger.error(f"Failed to persist escalated endpoint: {e}")

    def _cleanup_old_entries(self) -> None:
        cutoff = datetime.now(UTC) - timedelta(hours=self.retention_hours)
        self.behavioral_history = [b for b in self.behavioral_history if b.timestamp >= cutoff]

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up old entries."""
        while True:
            try:
                # Clean up old behavioral history in memory
                self._cleanup_old_entries()

                # Clean up old behavioral history in database
                await self._sig_repo.cleanup_old(retention_hours=self.retention_hours)

                # Clean up expired escalated endpoints in database
                await self._escalated_repo.cleanup_expired()

                # Clean up expired escalated endpoints in memory
                now = datetime.now(UTC)
                expired = [path for path, expiry in self.ESCALATED_ENDPOINTS.items() if expiry <= now]
                for path in expired:
                    del self.ESCALATED_ENDPOINTS[path]
                    logger.info(f"DRT: Auto-deescalated endpoint: {path}")

                # Sleep for 1 hour before next cleanup
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error during DRT cleanup: {e}", exc_info=True)
                await asyncio.sleep(60)  # Shorter delay on error

    async def _start_cleanup_task(self) -> None:
        """Start the background cleanup task if not already running."""
        if self.enabled and (self._cleanup_task is None or self._cleanup_task.done()):
            try:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.info("Started DRT periodic cleanup task")
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    # If no event loop is running, we'll start the task when the app starts
                    logger.debug("No running event loop, cleanup task will be started on app startup")
                else:
                    raise

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped DRT periodic cleanup task")

    def add_attack_vector(self, signature: BehavioralSignature) -> None:
        self.attack_vectors.append(signature)
        logger.info(f"DRT: Added attack vector: {signature.path_pattern}")

        # Record metrics
        from .drt_metrics import get_drt_metrics_collector

        collector = get_drt_metrics_collector()
        collector.record_attack_vector("medium")  # Default severity

        # Persist to database (fire and forget)
        try:
            asyncio.create_task(self._persist_attack_vector(signature))
        except RuntimeError:
            pass  # No running event loop (e.g. unit tests)

    async def _persist_attack_vector(self, signature: BehavioralSignature) -> None:
        """Persist attack vector to database."""
        try:
            attack_vector_id = await self._attack_repo.save(
                signature=signature,
                severity="medium",  # Default severity
                description=f"Added via middleware: {signature.path_pattern}",
            )
            # Cache the ID for future violation recording
            self._attack_vector_ids[str(id(signature))] = attack_vector_id
        except Exception as e:
            logger.error(f"Failed to persist attack vector: {e}")

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "similarity_threshold": self.similarity_threshold,
            "retention_hours": self.retention_hours,
            "auto_escalate": self.auto_escalate,
            "escalated_endpoints": len(self.ESCALATED_ENDPOINTS),
            "behavioral_history_count": len(self.behavioral_history),
            "attack_vectors_count": len(self.attack_vectors),
        }
