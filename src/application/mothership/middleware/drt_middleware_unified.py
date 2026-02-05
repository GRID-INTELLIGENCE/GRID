"""
Unified DRT (Don't Repeat Themselves) Middleware.
Delegates to core DRTMonitor engine for single source of truth.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Import core DRT engine
from grid.resilience.drt_monitor import DRTMonitor, check_drt_violation

logger = logging.getLogger(__name__)


class UnifiedDRTMiddleware(BaseHTTPMiddleware):
    """Unified DRT middleware that delegates to core DRTMonitor engine."""
    
    def __init__(
        self,
        app: Any,
        # Core DRT settings from SecuritySettings
        enabled: bool = True,
        similarity_threshold: float = 0.85,
        retention_hours: int = 96,
        enforcement_mode: str = "monitor",  # monitor, enforce, disabled
        websocket_monitoring_enabled: bool = True,
        api_movement_logging_enabled: bool = True,
        penalty_points_enabled: bool = True,
        slo_evaluation_interval_seconds: int = 300,
        slo_violation_penalty_base: int = 10,
        report_generation_enabled: bool = True,
        # Middleware-specific settings
        sampling_rate: float = 1.0,
        escalation_timeout_minutes: int = 60,
        rate_limit_multiplier: float = 0.5,
        alert_on_escalation: bool = True,
    ):
        super().__init__(app)
        
        # Store configuration
        self.enabled = enabled
        self.enforcement_mode = enforcement_mode
        self.sampling_rate = sampling_rate
        self.escalation_timeout_minutes = escalation_timeout_minutes
        self.rate_limit_multiplier = rate_limit_multiplier
        self.alert_on_escalation = alert_on_escalation
        self.api_movement_logging_enabled = api_movement_logging_enabled
        self.websocket_monitoring_enabled = websocket_monitoring_enabled
        self.penalty_points_enabled = penalty_points_enabled
        
        # Initialize core DRT monitor with unified settings
        self.drt_monitor = DRTMonitor(
            similarity_threshold=similarity_threshold,
            retention_hours=retention_hours,
        )
        
        # Local middleware state for escalation tracking
        self.escalated_endpoints: dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"Unified DRT middleware initialized: enabled={enabled}, "
            f"threshold={similarity_threshold}, mode={enforcement_mode}"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through unified DRT pipeline."""
        
        if not self.enabled:
            return await call_next(request)
        
        # Apply sampling
        if random.random() > self.sampling_rate:
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        path = request.url.path
        
        # Monitor endpoint through core DRT engine
        monitoring_result = check_drt_violation(
            endpoint=path,
            method=method,
            client_ip=client_ip,
            user_agent=user_agent,
            headers=dict(request.headers)
        )
        
        # Handle escalation based on enforcement mode
        if monitoring_result.get("escalation_applied", False):
            await self._handle_escalation(request, monitoring_result)
        
        # Process request
        response = await call_next(request)
        
        # Add DRT headers to response
        self._add_drt_headers(response, monitoring_result)
        
        # Log API movement if enabled
        if self.api_movement_logging_enabled:
            duration_ms = (time.time() - start_time) * 1000
            self._log_api_movement(request, response, duration_ms, monitoring_result)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _handle_escalation(self, request: Request, monitoring_result: dict[str, Any]) -> None:
        """Handle endpoint escalation based on enforcement mode."""
        
        path = request.url.path
        escalation_config = monitoring_result.get("escalation_config", {})
        
        if self.enforcement_mode == "monitor":
            # Log escalation but don't block
            if self.alert_on_escalation:
                logger.warning(
                    f"DRT [MONITOR]: Endpoint escalated: {path} "
                    f"attack_type={escalation_config.get('attack_type', 'unknown')} "
                    f"similarity={escalation_config.get('similarity_score', 0):.3f}"
                )
        
        elif self.enforcement_mode == "enforce":
            # Apply rate limiting and other enforcement measures
            self.escalated_endpoints[path] = datetime.utcnow() + timedelta(
                minutes=self.escalation_timeout_minutes
            )
            
            if self.alert_on_escalation:
                logger.warning(
                    f"DRT [ENFORCE]: Endpoint escalated: {path} "
                    f"attack_type={escalation_config.get('attack_type', 'unknown')} "
                    f"similarity={escalation_config.get('similarity_score', 0):.3f} "
                    f"timeout={self.escalation_timeout_minutes}min"
                )
            
            # Apply rate limiting delay
            await asyncio.sleep(0.1 * self.rate_limit_multiplier)
        
        # Record escalation in middleware state
        self.escalated_endpoints[path] = datetime.utcnow() + timedelta(
            minutes=self.escalation_timeout_minutes
        )
    
    def _add_drt_headers(self, response: Response, monitoring_result: dict[str, Any]) -> None:
        """Add DRT monitoring headers to response."""
        
        headers = {
            "X-DRT-Monitored": "true",
            "X-DRT-Similar-Attacks": str(monitoring_result.get("similar_attacks_detected", 0)),
            "X-DRT-Escalation-Level": monitoring_result.get("current_escalation_level", "normal"),
        }
        
        if monitoring_result.get("escalation_applied", False):
            escalation_config = monitoring_result.get("escalation_config", {})
            headers.update({
                "X-DRT-Escalated": "true",
                "X-DRT-Attack-Type": escalation_config.get("attack_type", "unknown"),
                "X-DRT-Similarity": f"{escalation_config.get('similarity_score', 0):.3f}",
                "X-DRT-Threat-Level": escalation_config.get("threat_level", "unknown"),
            })
        
        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value
    
    def _log_api_movement(self, request: Request, response: Response, duration_ms: float, monitoring_result: dict[str, Any]) -> None:
        """Log API movement for audit trail."""
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "drt_similar_attacks": monitoring_result.get("similar_attacks_detected", 0),
            "drt_escalation_applied": monitoring_result.get("escalation_applied", False),
            "drt_escalation_level": monitoring_result.get("current_escalation_level", "normal"),
        }
        
        logger.info(f"DRT API Movement: {log_data}")
    
    def get_status(self) -> dict[str, Any]:
        """Get current middleware status."""
        
        # Get status from core DRT monitor
        drt_status = self.drt_monitor.get_system_drt_status()
        
        # Add middleware-specific status
        return {
            "enabled": self.enabled,
            "enforcement_mode": self.enforcement_mode,
            "similarity_threshold": self.drt_monitor.similarity_threshold,
            "retention_hours": self.drt_monitor.retention_hours,
            "auto_escalate": True,  # Always true in unified version
            "escalated_endpoints": len(self.escalated_endpoints),
            "behavioral_history_count": sum(
                len(history) for history in self.drt_monitor.behavioral_history.values()
            ),
            "attack_vectors_count": len(self.drt_monitor.attack_database.attack_vectors),
            "sampling_rate": self.sampling_rate,
            "rate_limit_multiplier": self.rate_limit_multiplier,
            # Core engine status
            "core_total_monitored_endpoints": drt_status["total_monitored_endpoints"],
            "core_escalated_endpoints": drt_status["escalated_endpoints"],
            "core_escalation_rate": drt_status["escalation_rate"],
            "core_known_attack_vectors": drt_status["known_attack_vectors"],
        }
    
    def get_endpoint_summary(self, endpoint: str) -> dict[str, Any]:
        """Get endpoint summary from core DRT monitor."""
        return self.drt_monitor.get_endpoint_behavior_summary(endpoint)
    
    def add_attack_vector(self, endpoint: str, method: str, client_ip: str, user_agent: str, attack_type: str, severity: str) -> None:
        """Add attack vector to core DRT monitor."""
        from grid.resilience.drt_monitor import BehavioralFingerprint
        
        fingerprint = BehavioralFingerprint(endpoint, method, client_ip, user_agent)
        self.drt_monitor.attack_database.add_attack_vector(fingerprint, attack_type, severity)
        logger.info(f"Added attack vector: {method} {endpoint} ({attack_type})")


# Global middleware instance for router access
_unified_drt_middleware: Optional[UnifiedDRTMiddleware] = None


def get_unified_drt_middleware() -> UnifiedDRTMiddleware:
    """Get the global unified DRT middleware instance."""
    global _unified_drt_middleware
    if _unified_drt_middleware is None:
        raise RuntimeError("Unified DRT middleware not initialized")
    return _unified_drt_middleware


def set_unified_drt_middleware(middleware: UnifiedDRTMiddleware) -> None:
    """Set the global unified DRT middleware instance."""
    global _unified_drt_middleware
    _unified_drt_middleware = middleware
