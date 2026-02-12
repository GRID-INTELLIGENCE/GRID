"""Enhanced Boundary Middleware with Human Rights Enforcement.

Integrates:
- Rights-preserving request validation
- WebSocket real-time communication
- Comprehensive audit logging
- Prohibited domain blocking
- Real-time monitoring
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware

from api.schema.rights_boundary import (
    BoundaryAction,
    BoundaryDecision,
    HumanRightsImpact,
    HumanRightCategory,
    RequestType,
    RightsPreservingRequest,
    RiskLevel,
)
from api.monitoring.boundary_logger import RightsPreservingLogger, boundary_logger
from api.websocket.rights_gateway import websocket_manager


class RightsPreservingBoundaryMiddleware(BaseHTTPMiddleware):
    """
    Boundary enforcement middleware with human rights protection.
    
    Execution flow:
    1. Request parsing and rights context extraction
    2. Human rights impact assessment
    3. Prohibited domain checking
    4. Boundary decision (allow/deny/quarantine)
    5. Audit logging
    6. Response with rights metadata
    """

    def __init__(
        self,
        app: Any,
        exclude_paths: list[str] | None = None,
        logger: RightsPreservingLogger | None = None,
    ) -> None:
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/ws",  # WebSocket has its own rights enforcement
        ]
        self.logger = logger or boundary_logger
        
        # Prohibited research domains
        self.prohibited_domains = {
            "surveillance": [
                "mass surveillance", "covert monitoring", "warrantless tracking",
                "spy technology", "surveillance capitalism", "dragnet collection"
            ],
            "discrimination": [
                "racial profiling", "ethnic targeting", "discriminatory ai",
                "biased algorithm", "minority exclusion", "segregation technology"
            ],
            "weapons": [
                "autonomous weapon", "lethal autonomous", "killer robot",
                "weaponized ai", "automated targeting", "drone strike"
            ],
            "manipulation": [
                "behavior modification", "coercive control", "forced nudging",
                "psychological manipulation", "coercive persuasion", "gaslighting"
            ],
            "exploitation": [
                "data harvesting", "predatory collection", "exploitative tracking",
                "privacy violation", "non-consensual data", "surveillance monetization"
            ],
            "biometric_abuse": [
                "non-consensual facial", "biometric surveillance", "emotion tracking",
                "facial recognition tracking", "biometric profiling"
            ],
            "social_control": [
                "social credit", "citizen score", "behavioral scoring",
                "social ranking", "trustworthiness algorithm", "obedience tracking"
            ],
            "policing": [
                "predictive policing", "pre-crime detection", "algorithmic policing",
                "predictive incarceration", "automated criminalization"
            ],
        }
        
        # High-risk patterns requiring human review
        self.high_risk_patterns = [
            "vulnerable population",
            "children data",
            "mental health inference",
            "political manipulation",
            "election interference",
            "health data monetization",
            "addiction optimization",
            "engagement at all costs",
        ]
        
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request through rights-preserving boundary enforcement."""
        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4())[:12])
        
        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)
        
        # Extract request context
        rights_request = await self._extract_request_context(request, correlation_id)
        
        # Log request received
        self.logger.log_request_received(rights_request)
        
        # Perform human rights impact assessment
        impact = await self._assess_human_rights_impact(rights_request)
        
        # Log rights check
        content_preview = rights_request.content[:200] if rights_request.content else None
        self.logger.log_rights_check(
            rights_request.request_id,
            correlation_id,
            impact,
            content_preview,
        )
        
        # Make boundary decision
        decision = self._make_boundary_decision(rights_request, impact)
        
        # Log boundary decision
        self.logger.log_boundary_decision(decision)
        
        # Execute decision
        if decision.action == BoundaryAction.DENY:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_processing_complete(
                rights_request.request_id,
                correlation_id,
                processing_time,
                success=False,
                error="Request denied due to human rights violation",
            )
            return self._create_denial_response(correlation_id, decision, impact)
            
        if decision.action == BoundaryAction.QUARANTINE:
            # Log quarantine and require human review
            await self._notify_quarantine(rights_request, decision)
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_processing_complete(
                rights_request.request_id,
                correlation_id,
                processing_time,
                success=False,
                error="Request quarantined for human review",
            )
            return self._create_quarantine_response(correlation_id, decision)
        
        # Process the request
        try:
            # Add rights metadata to request state
            request.state.rights_metadata = {
                "correlation_id": correlation_id,
                "request_id": rights_request.request_id,
                "rights_validated": True,
                "risk_level": impact.risk_level,
            }
            
            response = await call_next(request)
            
            # Add rights headers to response
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Rights-Validated"] = "true"
            response.headers["X-Risk-Level"] = impact.risk_level
            
            if impact.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                response.headers["X-Rights-Warning"] = "High-risk request - review recommended"
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_processing_complete(
                rights_request.request_id,
                correlation_id,
                processing_time,
                success=True,
            )
            
            return response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log_processing_complete(
                rights_request.request_id,
                correlation_id,
                processing_time,
                success=False,
                error=str(e),
            )
            raise
            
    async def _extract_request_context(
        self,
        request: Request,
        correlation_id: str,
    ) -> RightsPreservingRequest:
        """Extract rights-preserving context from HTTP request."""
        # Get client info
        client_host = request.client.host if request.client else None
        
        # Try to get user ID from auth header
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In real implementation, decode JWT to get user_id
            user_id = "authenticated_user"  # Placeholder
            
        # Determine request type from path
        request_type = self._classify_request_type(request.url.path)
        
        # Try to get content from request body (for POST/PUT)
        content = ""
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                content = body.decode("utf-8", errors="ignore")
                # Reset body for downstream processing
                await request.body()
            except Exception:
                pass
                
        # Get declared purpose from header or query
        declared_purpose = request.headers.get("X-Purpose") or request.query_params.get("purpose")
        
        return RightsPreservingRequest(
            correlation_id=correlation_id,
            request_type=request_type,
            source_ip=client_host,
            user_id=user_id,
            content=content if content else None,
            declared_purpose=declared_purpose,
            consent_obtained=request.headers.get("X-Consent-Given") == "true",
        )
        
    def _classify_request_type(self, path: str) -> RequestType:
        """Classify request type from URL path."""
        path_lower = path.lower()
        
        if "data" in path_lower or "analysis" in path_lower:
            return RequestType.DATA_ANALYSIS
        elif "generate" in path_lower or "content" in path_lower:
            return RequestType.CONTENT_GENERATION
        elif "track" in path_lower or "monitor" in path_lower:
            return RequestType.USER_TRACKING
        elif "decision" in path_lower or "automated" in path_lower:
            return RequestType.AUTOMATED_DECISION
        elif "research" in path_lower or "query" in path_lower:
            return RequestType.RESEARCH_QUERY
        elif "external" in path_lower or "api" in path_lower:
            return RequestType.EXTERNAL_API_CALL
        elif "file" in path_lower or "upload" in path_lower or "download" in path_lower:
            return RequestType.FILE_PROCESSING
        elif "stream" in path_lower or "realtime" in path_lower or "ws" in path_lower:
            return RequestType.REAL_TIME_STREAMING
        else:
            return RequestType.RESEARCH_QUERY
            
    async def _assess_human_rights_impact(
        self,
        request: RightsPreservingRequest,
    ) -> HumanRightsImpact:
        """Assess potential human rights impact of request."""
        impact = HumanRightsImpact(risk_level=RiskLevel.NONE)
        content = (request.content or "").lower()
        purpose = (request.declared_purpose or "").lower()
        combined_text = f"{content} {purpose}"
        
        # Check prohibited domains
        detected_domains = []
        rights_violated = []
        harms = []
        
        for domain, patterns in self.prohibited_domains.items():
            for pattern in patterns:
                if pattern in combined_text:
                    detected_domains.append(domain)
                    harms.append(f"Prohibited: {domain} - {pattern}")
                    
                    # Map to rights categories
                    if domain == "surveillance":
                        rights_violated.append(HumanRightCategory.RIGHT_TO_PRIVACY)
                    elif domain == "discrimination":
                        rights_violated.append(HumanRightCategory.FREEDOM_FROM_DISCRIMINATION)
                    elif domain == "weapons":
                        rights_violated.append(HumanRightCategory.RIGHT_TO_LIFE)
                    elif domain == "manipulation":
                        rights_violated.append(HumanRightCategory.FREEDOM_OF_THOUGHT)
                    elif domain == "exploitation":
                        rights_violated.append(HumanRightCategory.RIGHT_TO_PRIVACY)
                    elif domain == "biometric_abuse":
                        rights_violated.append(HumanRightCategory.RIGHT_TO_PRIVACY)
                    elif domain == "social_control":
                        rights_violated.append(HumanRightCategory.FREEDOM_OF_THOUGHT)
                        rights_violated.append(HumanRightCategory.RIGHT_TO_PRIVACY)
                    elif domain == "policing":
                        rights_violated.append(HumanRightCategory.FREEDOM_FROM_DISCRIMINATION)
                    break
                    
        if detected_domains:
            impact.risk_level = RiskLevel.VIOLATION
            impact.rights_categories = list(set(rights_violated))
            impact.potential_harms = harms
            impact.mitigation_required = True
            impact.requires_human_review = True
            impact.review_reason = (
                f"Prohibited research domains detected: {', '.join(detected_domains)}. "
                f"This request violates human rights principles and cannot be processed."
            )
            impact.affected_populations = self._identify_affected_populations(combined_text)
            return impact
        
        # Check high-risk patterns
        high_risk_found = []
        for pattern in self.high_risk_patterns:
            if pattern in combined_text:
                high_risk_found.append(pattern)
                
        if high_risk_found:
            impact.risk_level = RiskLevel.HIGH
            impact.requires_human_review = True
            impact.review_reason = f"High-risk patterns: {', '.join(high_risk_found)}"
            impact.potential_harms = high_risk_found
            
        # Check for consent issues
        if request.request_type in (
            RequestType.USER_TRACKING,
            RequestType.DATA_ANALYSIS,
        ) and not request.consent_obtained:
            if impact.risk_level == RiskLevel.NONE:
                impact.risk_level = RiskLevel.MEDIUM
            impact.potential_harms.append("Processing without explicit consent")
            
        return impact
        
    def _make_boundary_decision(
        self,
        request: RightsPreservingRequest,
        impact: HumanRightsImpact,
    ) -> BoundaryDecision:
        """Make boundary enforcement decision based on rights impact."""
        decision_id = str(uuid4())[:8]
        
        # Determine action based on risk level
        if impact.risk_level == RiskLevel.VIOLATION:
            action = BoundaryAction.DENY
            action_reason = (
                "Request denied: Violates fundamental human rights. "
                "Prohibited research domains detected."
            )
        elif impact.risk_level == RiskLevel.CRITICAL:
            action = BoundaryAction.QUARANTINE
            action_reason = "Request quarantined: Critical risk level requires human review"
        elif impact.risk_level == RiskLevel.HIGH:
            action = BoundaryAction.ALLOW  # Allow but logged extensively
            action_reason = "Request allowed with high-risk monitoring"
        elif impact.requires_human_review:
            action = BoundaryAction.QUARANTINE
            action_reason = "Request quarantined: Requires human review per policy"
        else:
            action = BoundaryAction.ALLOW
            action_reason = "Request allowed: No rights violations detected"
            
        return BoundaryDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            action=action,
            action_reason=action_reason,
            human_rights_impact=impact,
            policy_rules_triggered=[
                "human_rights_protection",
                "prohibited_domain_blocking",
            ],
            rights_categories_protected=list(set(impact.rights_categories)),
            requires_follow_up=impact.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL),
        )
        
    def _identify_affected_populations(self, text: str) -> list[str]:
        """Identify potentially affected populations from request text."""
        populations = []
        text_lower = text.lower()
        
        population_keywords = {
            "children": ["children", "minors", "underage", "kids", "students"],
            "elderly": ["elderly", "seniors", "aging population"],
            "disabled": ["disabled", "disability", "accessibility"],
            "vulnerable": ["vulnerable", "at-risk", "marginalized"],
            "minorities": ["minorities", "ethnic groups", "indigenous"],
            "refugees": ["refugees", "asylum seekers", "displaced"],
            "low_income": ["low income", "poverty", "economically disadvantaged"],
        }
        
        for population, keywords in population_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    populations.append(population)
                    break
                    
        return populations
        
    def _create_denial_response(
        self,
        correlation_id: str,
        decision: BoundaryDecision,
        impact: HumanRightsImpact,
    ) -> Response:
        """Create HTTP response for denied request."""
        content = {
            "error": "Request denied - Human rights violation detected",
            "correlation_id": correlation_id,
            "decision_id": decision.decision_id,
            "reason": decision.action_reason,
            "rights_impact": {
                "risk_level": impact.risk_level,
                "rights_categories": [r.value for r in impact.rights_categories],
                "potential_harms": impact.potential_harms,
            },
            "message": (
                "This request has been blocked because it violates fundamental human rights principles. "
                "Research or applications that may harm individuals or violate their rights are prohibited. "
                "If you believe this is an error, please contact support with the correlation ID."
            ),
            "contact": "support@grid-sovereign.example",
        }
        
        return Response(
            content=json.dumps(content),
            status_code=403,
            media_type="application/json",
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Rights-Validated": "true",
                "X-Request-Blocked": "true",
                "X-Risk-Level": "violation",
            },
        )
        
    def _create_quarantine_response(
        self,
        correlation_id: str,
        decision: BoundaryDecision,
    ) -> Response:
        """Create HTTP response for quarantined request."""
        content = {
            "status": "quarantined",
            "correlation_id": correlation_id,
            "decision_id": decision.decision_id,
            "reason": decision.action_reason,
            "message": (
                "This request has been quarantined for human review. "
                "It will be processed only after review by authorized personnel. "
                "You will be notified of the decision."
            ),
            "estimated_review_time": "24-48 hours",
        }
        
        return Response(
            content=json.dumps(content),
            status_code=202,
            media_type="application/json",
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Rights-Validated": "true",
                "X-Request-Quarantined": "true",
                "X-Review-Required": "true",
            },
        )
        
    async def _notify_quarantine(
        self,
        request: RightsPreservingRequest,
        decision: BoundaryDecision,
    ) -> None:
        """Notify administrators of quarantined request."""
        # Log extensively
        self.logger.logger.warning(
            f"QUARANTINE ALERT: Request {request.request_id} quarantined. "
            f"Reason: {decision.action_reason}"
        )
        
        # Could also send to webhook, email, slack, etc.
        # Integration point for alerting systems


import json

__all__ = [
    "RightsPreservingBoundaryMiddleware",
]
