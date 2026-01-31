"""
Unified Fabric - Safety-First Router
=====================================
Central entrypoint for all safety validation across domains.

Key Features:
- Intercepts all requests before processing
- Validates content, rate limits, and audit logging
- Broadcasts safety events to event bus
- AI SAFETY as the governing layer
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional
from enum import Enum

from . import Event, EventDomain, get_event_bus, EventResponse

logger = logging.getLogger(__name__)


class SafetyDecision(Enum):
    """Safety validation decision"""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"


class ThreatLevel(Enum):
    """Threat severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyViolation:
    """Individual safety violation detected"""
    category: str
    severity: ThreatLevel
    confidence: float
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class SafetyReport:
    """Safety validation result"""
    decision: SafetyDecision
    threat_level: ThreatLevel
    violations: list[SafetyViolation] = field(default_factory=list)
    processing_time_ms: float = 0.0
    request_id: str = ""
    domain: str = ""
    
    @property
    def is_safe(self) -> bool:
        return self.decision in [SafetyDecision.ALLOW, SafetyDecision.WARN]
    
    @property
    def should_block(self) -> bool:
        return self.decision == SafetyDecision.BLOCK


class SafetyFirstRouter:
    """
    Central safety router for all cross-system requests.
    
    Implements the "AI SAFETY first" principle by intercepting
    all requests and validating before routing to target systems.
    """
    
    def __init__(self):
        self._content_patterns: dict[str, list[str]] = self._load_patterns()
        self._rate_limits: dict[str, int] = {}  # user_id -> request_count
        self._rate_window_sec = 60
        self._max_requests_per_window = 100
        self._initialized = False
        
    def _load_patterns(self) -> dict[str, list[str]]:
        """Load safety detection patterns"""
        return {
            "harmful": [
                "violence", "attack", "weapon", "kill", "harm"
            ],
            "privacy": [
                "social security", "credit card", "password", "private key"
            ],
            "injection": [
                "ignore previous", "system prompt", "you are now", 
                "disregard instructions", "jailbreak"
            ],
            "medical_risk": [
                "suicide", "self harm", "overdose", "kill myself"
            ]
        }
    
    async def initialize(self):
        """Initialize the safety router"""
        if self._initialized:
            return
        
        # Subscribe to safety events
        bus = get_event_bus()
        bus.subscribe("safety.*", self._handle_safety_event, domain="all")
        
        self._initialized = True
        logger.info("SafetyFirstRouter initialized")
    
    async def validate(
        self,
        content: str,
        domain: str,
        user_id: str = "anonymous",
        context: Optional[dict] = None
    ) -> SafetyReport:
        """
        Validate content before processing.
        
        Args:
            content: Content to validate
            domain: Target domain (safety, grid, coinbase)
            user_id: User identifier for rate limiting
            context: Additional context
            
        Returns:
            SafetyReport with decision and violations
        """
        start_time = time.perf_counter()
        violations: list[SafetyViolation] = []
        
        # Step 1: Rate limit check
        if not self._check_rate_limit(user_id):
            violations.append(SafetyViolation(
                category="rate_limit",
                severity=ThreatLevel.MEDIUM,
                confidence=1.0,
                description=f"Rate limit exceeded for user {user_id[:8]}..."
            ))
        
        # Step 2: Content pattern check
        violations.extend(self._check_patterns(content))
        
        # Step 3: Domain-specific checks
        if domain == EventDomain.COINBASE.value:
            violations.extend(await self._check_financial_safety(content, context))
        
        # Determine decision
        decision, threat_level = self._make_decision(violations)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        report = SafetyReport(
            decision=decision,
            threat_level=threat_level,
            violations=violations,
            processing_time_ms=processing_time,
            domain=domain
        )
        
        # Broadcast safety event if violations found
        if violations:
            await self._broadcast_safety_event(report)
        
        return report
    
    async def validate_portfolio_action(
        self,
        action: dict[str, Any],
        user_id: str
    ) -> SafetyReport:
        """Validate portfolio-related actions"""
        content = str(action)
        return await self.validate(content, EventDomain.COINBASE.value, user_id, action)
    
    async def validate_trading_signal(
        self,
        signal: dict[str, Any],
        user_id: str
    ) -> SafetyReport:
        """Validate trading signal generation"""
        content = str(signal)
        return await self.validate(content, EventDomain.COINBASE.value, user_id, signal)
    
    async def validate_navigation(
        self,
        nav_request: dict[str, Any],
        user_id: str
    ) -> SafetyReport:
        """Validate GRID navigation request"""
        content = str(nav_request)
        return await self.validate(content, EventDomain.GRID.value, user_id, nav_request)
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current = self._rate_limits.get(user_id, 0)
        if current >= self._max_requests_per_window:
            return False
        self._rate_limits[user_id] = current + 1
        return True
    
    def _check_patterns(self, content: str) -> list[SafetyViolation]:
        """Check content against safety patterns"""
        violations = []
        normalized = content.lower()
        
        for category, patterns in self._content_patterns.items():
            for pattern in patterns:
                if pattern in normalized:
                    severity = ThreatLevel.CRITICAL if category in ["injection", "medical_risk"] else ThreatLevel.MEDIUM
                    violations.append(SafetyViolation(
                        category=category,
                        severity=severity,
                        confidence=0.8,
                        description=f"Pattern detected: {pattern}",
                        evidence={"pattern": pattern, "category": category}
                    ))
        
        return violations
    
    async def _check_financial_safety(
        self,
        content: str,
        context: Optional[dict]
    ) -> list[SafetyViolation]:
        """Financial domain-specific safety checks"""
        violations = []
        
        # Check for unrealistic claims
        if context and context.get("expected_return", 0) > 100:
            violations.append(SafetyViolation(
                category="financial_risk",
                severity=ThreatLevel.HIGH,
                confidence=0.9,
                description="Unrealistic return expectation detected"
            ))
        
        return violations
    
    def _make_decision(
        self,
        violations: list[SafetyViolation]
    ) -> tuple[SafetyDecision, ThreatLevel]:
        """Determine safety decision based on violations"""
        if not violations:
            return SafetyDecision.ALLOW, ThreatLevel.NONE
        
        # Check for critical violations
        critical = [v for v in violations if v.severity == ThreatLevel.CRITICAL]
        if critical:
            return SafetyDecision.BLOCK, ThreatLevel.CRITICAL
        
        high = [v for v in violations if v.severity == ThreatLevel.HIGH]
        if len(high) >= 2:
            return SafetyDecision.BLOCK, ThreatLevel.HIGH
        elif high:
            return SafetyDecision.ESCALATE, ThreatLevel.HIGH
        
        medium = [v for v in violations if v.severity == ThreatLevel.MEDIUM]
        if medium:
            return SafetyDecision.WARN, ThreatLevel.MEDIUM
        
        return SafetyDecision.ALLOW, ThreatLevel.LOW
    
    async def _broadcast_safety_event(self, report: SafetyReport):
        """Broadcast safety event to all subscribers"""
        bus = get_event_bus()
        
        event = Event(
            event_type=f"safety.violation.{report.threat_level.value}",
            payload={
                "decision": report.decision.value,
                "threat_level": report.threat_level.value,
                "violation_count": len(report.violations),
                "domain": report.domain
            },
            source_domain=EventDomain.SAFETY.value,
            target_domains=["all"]
        )
        
        await bus.publish(event)
    
    async def _handle_safety_event(self, event: Event) -> Optional[EventResponse]:
        """Handle incoming safety events"""
        logger.info(f"Safety event received: {event.event_type}")
        return None


# Singleton instance
_safety_router: Optional[SafetyFirstRouter] = None


def get_safety_router() -> SafetyFirstRouter:
    """Get the singleton safety router instance"""
    global _safety_router
    if _safety_router is None:
        _safety_router = SafetyFirstRouter()
    return _safety_router


async def init_safety_router() -> SafetyFirstRouter:
    """Initialize and setup the safety router"""
    router = get_safety_router()
    await router.initialize()
    return router
