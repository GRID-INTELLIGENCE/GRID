"""
AI Safety Distribution Bridge
==============================
Distributes AI Safety features from wellness_studio across E:/ projects.

Goals:
- Recover memory and IO load
- Centralize safety validation
- Enable async processing
"""
import importlib.util
import logging
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from . import Event, EventDomain, EventResponse, get_event_bus, init_event_bus
from .audit import AuditEventType, get_audit_logger
from .cross_project_validator import get_policy_validator
from .safety_router import SafetyDecision, SafetyReport, get_safety_router

logger = logging.getLogger(__name__)


class SafetySource(Enum):
    """Source of safety validation"""
    WELLNESS_STUDIO = "wellness_studio"
    UNIFIED_FABRIC = "unified_fabric"
    HYBRID = "hybrid"


@dataclass
class SafetyBridgeConfig:
    """Configuration for safety bridge"""
    source: SafetySource = SafetySource.UNIFIED_FABRIC
    wellness_studio_path: str = "C:/Users/irfan/CascadeProjects/windsurf-project-2/wellness_studio"
    enable_async: bool = True
    enable_audit: bool = True
    enable_events: bool = True
    cache_safety_results: bool = True
    cache_ttl_sec: float = 30.0


@dataclass
class SafetyContext:
    """Context for safety validation"""
    project: str
    domain: str
    user_id: str
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AISafetyBridge:
    r"""
    Bridge for distributing AI Safety across E:\ projects.
    
    Connects wellness_studio safety features to:
    - E:\grid - GRID cognitive routers
    - E:\coinbase - Coinbase portfolio/trading
    - Other E:\ projects
    
    Features:
    - Async non-blocking validation
    - Event-driven safety alerts
    - Memory-efficient caching
    - Unified audit trail
    """

    def __init__(self, config: SafetyBridgeConfig | None = None):
        self.config = config or SafetyBridgeConfig()
        self._safety_router = get_safety_router()
        self._audit_logger = get_audit_logger()
        self._event_bus = get_event_bus()
        self._policy_validator = get_policy_validator()
        self._cache: dict[str, tuple[SafetyReport, float]] = {}
        self._wellness_safety: Any | None = None
        self._initialized = False

    async def initialize(self):
        """Initialize the safety bridge"""
        if self._initialized:
            return

        # Initialize event bus if event mode enabled
        if self.config.enable_events:
            await init_event_bus()
            self._subscribe_to_events()

        # Try to import wellness_studio safety modules if hybrid mode
        if self.config.source in [SafetySource.WELLNESS_STUDIO, SafetySource.HYBRID]:
            await self._load_wellness_safety()

        self._initialized = True
        logger.info(f"AISafetyBridge initialized with source: {self.config.source.value}")

    async def validate(
        self,
        content: str,
        context: SafetyContext
    ) -> SafetyReport:
        """
        Validate content with safety checks.
        
        Args:
            content: Content to validate
            context: Safety context with project/domain info
            
        Returns:
            SafetyReport with decision
        """
        # Check cache first
        cache_key = self._make_cache_key(content, context)
        if self.config.cache_safety_results:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        # Perform validation
        report = await self._validate_internal(content, context)

        # Cache result
        if self.config.cache_safety_results:
            self._cache[cache_key] = (report, datetime.now(UTC).timestamp())

        # Log to audit
        if self.config.enable_audit:
            await self._audit_validation(report, context)

        # Broadcast event if violations
        if self.config.enable_events and report.violations:
            await self._broadcast_safety_event(report, context)

        return report

    async def validate_grid_request(
        self,
        request: dict[str, Any],
        user_id: str = "system"
    ) -> SafetyReport:
        """Validate a GRID router request"""
        content = str(request.get("content", request.get("query", request)))
        context = SafetyContext(
            project="grid",
            domain="grid",
            user_id=user_id,
            metadata={"request_type": request.get("type", "unknown")}
        )
        return await self.validate(content, context)

    def _build_context_from_payload(self, payload: dict[str, Any]) -> SafetyContext:
        context_payload = payload.get("context") if isinstance(payload, dict) else {}
        if not isinstance(context_payload, dict):
            context_payload = {}
        return SafetyContext(
            project=context_payload.get("project", payload.get("project", "unknown")),
            domain=context_payload.get("domain", payload.get("domain", "unknown")),
            user_id=context_payload.get("user_id", payload.get("user_id", "system")),
            request_id=context_payload.get("request_id"),
            correlation_id=context_payload.get("correlation_id"),
            metadata=context_payload.get("metadata", {}),
        )

    async def validate_coinbase_action(
        self,
        action: dict[str, Any],
        user_id: str = "system"
    ) -> SafetyReport:
        """Validate a Coinbase portfolio action"""
        content = str(action)
        context = SafetyContext(
            project="coinbase",
            domain="coinbase",
            user_id=user_id,
            metadata={"action_type": action.get("type", "unknown")}
        )
        return await self.validate(content, context)

    async def validate_revenue_event(
        self,
        event: dict[str, Any],
        user_id: str = "system"
    ) -> SafetyReport:
        """Validate a revenue pipeline event"""
        content = str(event)
        context = SafetyContext(
            project="coinbase",
            domain="revenue",
            user_id=user_id,
            metadata=event
        )
        return await self.validate(content, context)

    def create_async_hook(
        self,
        on_block: Callable[[SafetyReport], Awaitable[Any]] | None = None,
        on_warn: Callable[[SafetyReport], Awaitable[Any]] | None = None
    ) -> Callable:
        """
        Create an async hook for GRID routers.
        
        Returns decorator that wraps router handlers with safety.
        """
        async def safety_hook(
            handler: Callable[..., Awaitable[Any]]
        ) -> Callable[..., Awaitable[Any]]:
            async def wrapped(*args, **kwargs):
                # Extract request from args
                request = kwargs.get("request") or (args[0] if args else {})
                user_id = kwargs.get("user_id", "system")

                # Validate
                report = await self.validate_grid_request(
                    request if isinstance(request, dict) else {"content": str(request)},
                    user_id
                )

                # Handle based on decision
                if report.should_block:
                    if on_block:
                        return await on_block(report)
                    raise SafetyBlockedException(report)

                if report.decision == SafetyDecision.WARN and on_warn:
                    await on_warn(report)

                # Proceed with original handler
                return await handler(*args, **kwargs)

            return wrapped
        return safety_hook

    async def _validate_internal(
        self,
        content: str,
        context: SafetyContext
    ) -> SafetyReport:
        """Internal validation logic"""
        if self.config.source == SafetySource.WELLNESS_STUDIO:
            return await self._validate_with_wellness(content, context)
        elif self.config.source == SafetySource.HYBRID:
            # Run both and merge
            unified = await self._safety_router.validate(
                content, context.domain, context.user_id
            )
            wellness = await self._validate_with_wellness(content, context)
            return self._merge_reports(unified, wellness)
        else:
            return await self._safety_router.validate(
                content, context.domain, context.user_id
            )

    async def _validate_with_wellness(
        self,
        content: str,
        context: SafetyContext
    ) -> SafetyReport:
        """Validate using wellness_studio safety"""
        if not self._wellness_safety:
            # Fallback to unified fabric
            return await self._safety_router.validate(
                content, context.domain, context.user_id
            )

        # Use loaded wellness_studio module
        try:
            result = self._wellness_safety.validate_content(content)
            return self._convert_wellness_result(result)
        except Exception as e:
            logger.warning(f"Wellness safety failed, using fallback: {e}")
            return await self._safety_router.validate(
                content, context.domain, context.user_id
            )

    async def _load_wellness_safety(self):
        """Load wellness_studio safety modules"""
        try:
            safety_path = Path(self.config.wellness_studio_path) / "src/wellness_studio/security"

            # Add to path if not present
            if str(safety_path.parent) not in sys.path:
                sys.path.insert(0, str(safety_path.parent))

            # Try to import ai_safety module
            spec = importlib.util.spec_from_file_location(
                "ai_safety",
                safety_path / "ai_safety.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._wellness_safety = module
                logger.info("Loaded wellness_studio AI safety module")
        except Exception as e:
            logger.warning(f"Could not load wellness_studio safety: {e}")

    def _convert_wellness_result(self, result: Any) -> SafetyReport:
        """Convert wellness_studio result to SafetyReport"""
        # Adapt based on wellness_studio's return format
        from .safety_router import SafetyDecision, SafetyReport, ThreatLevel

        if hasattr(result, 'is_safe') and not result.is_safe:
            return SafetyReport(
                decision=SafetyDecision.BLOCK,
                threat_level=ThreatLevel.HIGH,
                violations=[]
            )
        return SafetyReport(
            decision=SafetyDecision.ALLOW,
            threat_level=ThreatLevel.NONE
        )

    def _merge_reports(
        self,
        unified: SafetyReport,
        wellness: SafetyReport
    ) -> SafetyReport:
        """Merge two safety reports (most restrictive wins)"""
        from .safety_router import ThreatLevel

        # Use more restrictive decision
        if wellness.should_block or unified.should_block:
            merged_decision = SafetyDecision.BLOCK
        elif wellness.decision == SafetyDecision.ESCALATE or unified.decision == SafetyDecision.ESCALATE:
            merged_decision = SafetyDecision.ESCALATE
        elif wellness.decision == SafetyDecision.WARN or unified.decision == SafetyDecision.WARN:
            merged_decision = SafetyDecision.WARN
        else:
            merged_decision = SafetyDecision.ALLOW

        # Merge violations
        merged_violations = unified.violations + wellness.violations

        # Use higher threat level
        threat_order = [ThreatLevel.NONE, ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        unified_idx = threat_order.index(unified.threat_level) if unified.threat_level in threat_order else 0
        wellness_idx = threat_order.index(wellness.threat_level) if wellness.threat_level in threat_order else 0
        merged_threat = threat_order[max(unified_idx, wellness_idx)]

        return SafetyReport(
            decision=merged_decision,
            threat_level=merged_threat,
            violations=merged_violations
        )

    def _make_cache_key(self, content: str, context: SafetyContext) -> str:
        """Create cache key for content"""
        return f"{context.project}:{context.domain}:{hash(content)}"

    def _get_cached(self, key: str) -> SafetyReport | None:
        """Get cached result if not expired"""
        if key not in self._cache:
            return None

        report, timestamp = self._cache[key]
        if datetime.now(UTC).timestamp() - timestamp > self.config.cache_ttl_sec:
            del self._cache[key]
            return None

        return report

    async def _audit_validation(
        self,
        report: SafetyReport,
        context: SafetyContext
    ):
        """Log validation to audit trail"""
        await self._audit_logger.log(
            event_type=AuditEventType.SAFETY_CHECK,
            project_id=context.project,
            domain=context.domain,
            action="safety_validation",
            status=report.decision.value,
            user_id=context.user_id,
            correlation_id=context.correlation_id,
            details={
                "threat_level": report.threat_level.value,
                "violation_count": len(report.violations)
            }
        )

    async def _broadcast_safety_event(
        self,
        report: SafetyReport,
        context: SafetyContext
    ):
        """Broadcast safety event to subscribers"""
        payload = {
            "project": context.project,
            "domain": context.domain,
            "decision": report.decision.value,
            "threat_level": report.threat_level.value,
            "violation_count": len(report.violations),
        }
        primary = Event(
            event_type="safety.violation_detected",
            payload=payload,
            source_domain=EventDomain.SAFETY.value,
            target_domains=["all"],
        )
        legacy = Event(
            event_type=f"safety.distributed.{report.threat_level.value}",
            payload=payload,
            source_domain=EventDomain.SAFETY.value,
            target_domains=["all"],
        )
        await self._event_bus.publish(primary)
        await self._event_bus.publish(legacy)

    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        async def handle_grid_request(event: Event):
            if event.event_type == "grid.request":
                await self.validate_grid_request(event.payload)

        async def handle_coinbase_action(event: Event):
            if event.event_type == "coinbase.action":
                await self.validate_coinbase_action(event.payload)

        async def handle_validation_request(event: Event) -> EventResponse | None:
            payload = event.payload or {}
            policy_result = self._policy_validator.validate_payload(payload)
            if not policy_result.allowed:
                violation_event = Event(
                    event_type="safety.violation_detected",
                    payload={
                        "violation_type": "policy_violation",
                        "severity": policy_result.severity,
                        "reason": policy_result.reason,
                        "details": payload,
                    },
                    source_domain=EventDomain.SAFETY.value,
                    target_domains=["all"],
                )
                await self._event_bus.publish(violation_event)
                if self.config.enable_audit:
                    await self._audit_logger.log(
                        event_type=AuditEventType.SAFETY_VIOLATION,
                        project_id="unified_fabric",
                        domain="safety",
                        action="policy_violation",
                        status="blocked",
                        details={"reason": policy_result.reason, "payload": payload},
                    )
                return EventResponse(success=False, error=policy_result.reason, event_id=event.event_id)

            context = self._build_context_from_payload(payload)
            content = str(payload.get("content", payload))
            report = await self.validate(content, context)
            result_event = Event(
                event_type="safety.validation_completed",
                payload={
                    "decision": report.decision.value,
                    "threat_level": report.threat_level.value,
                    "violation_count": len(report.violations),
                    "request_id": context.request_id,
                    "correlation_id": context.correlation_id,
                },
                source_domain=EventDomain.SAFETY.value,
                target_domains=event.target_domains,
            )
            await self._event_bus.publish(result_event)
            return EventResponse(success=report.is_safe, data=result_event.payload, event_id=event.event_id)

        async def handle_audit_replication(event: Event) -> EventResponse | None:
            payload = event.payload or {}
            await self._audit_logger.log(
                event_type=AuditEventType.SYSTEM_EVENT,
                project_id=payload.get("project_id", "external"),
                domain=payload.get("domain", "safety"),
                action="audit_replication",
                status="received",
                details=payload,
            )
            return EventResponse(success=True, data={"status": "replicated"}, event_id=event.event_id)

        self._event_bus.subscribe("grid.*", handle_grid_request, domain="grid")
        self._event_bus.subscribe("coinbase.*", handle_coinbase_action, domain="coinbase")
        self._event_bus.subscribe("safety.validation_required", handle_validation_request, domain="safety")
        self._event_bus.subscribe("safety.audit_replication", handle_audit_replication, domain="safety")

    def clear_cache(self):
        """Clear safety cache to recover memory"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached safety results")

    def get_stats(self) -> dict[str, Any]:
        """Get bridge statistics"""
        return {
            "source": self.config.source.value,
            "cached_results": len(self._cache),
            "async_enabled": self.config.enable_async,
            "audit_enabled": self.config.enable_audit,
            "events_enabled": self.config.enable_events
        }


class SafetyBlockedException(Exception):
    """Exception raised when safety blocks a request"""
    def __init__(self, report: SafetyReport):
        self.report = report
        super().__init__(f"Request blocked: {report.threat_level.value}")


# Singleton instance
_safety_bridge: AISafetyBridge | None = None


def get_safety_bridge() -> AISafetyBridge:
    """Get the singleton safety bridge instance"""
    global _safety_bridge
    if _safety_bridge is None:
        _safety_bridge = AISafetyBridge()
    return _safety_bridge


async def init_safety_bridge(config: SafetyBridgeConfig | None = None) -> AISafetyBridge:
    """Initialize and return the safety bridge"""
    global _safety_bridge
    if _safety_bridge is None:
        _safety_bridge = AISafetyBridge(config)
    await _safety_bridge.initialize()
    return _safety_bridge
