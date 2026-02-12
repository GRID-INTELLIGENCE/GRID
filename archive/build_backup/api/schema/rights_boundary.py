"""Rights-Preserving Boundary Schema for GRID Sovereign API.

This module defines the core data models for:
- Human rights guardrails
- Boundary enforcement policies
- Request/response patterns with rights validation
- Audit trails for accountability
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class RiskLevel(str, Enum):
    """Risk classification levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    VIOLATION = "violation"


class HumanRightCategory(str, Enum):
    """Universal human rights categories based on UDHR."""
    RIGHT_TO_LIFE = "right_to_life"  # Article 3
    FREEDOM_FROM_TORTURE = "freedom_from_torture"  # Article 5
    RIGHT_TO_PRIVACY = "right_to_privacy"  # Article 12
    FREEDOM_OF_EXPRESSION = "freedom_of_expression"  # Article 19
    FREEDOM_FROM_DISCRIMINATION = "freedom_from_discrimination"  # Article 2
    RIGHT_TO_WORK = "right_to_work"  # Article 23
    RIGHT_TO_HEALTH = "right_to_health"  # Article 25
    RIGHT_TO_EDUCATION = "right_to_education"  # Article 26
    FREEDOM_OF_THOUGHT = "freedom_of_thought"  # Article 18
    RIGHT_TO_ASYLUM = "right_to_asylum"  # Article 14
    RIGHT_TO_NATIONALITY = "right_to_nationality"  # Article 15
    RIGHT_TO_MARRIAGE = "right_to_marriage"  # Article 16
    RIGHT_TO_PROPERTY = "right_to_property"  # Article 17
    RIGHT_TO_POLITICAL_PARTICIPATION = "right_to_political_participation"  # Article 21


class RequestType(str, Enum):
    """Types of API requests for rights analysis."""
    DATA_ANALYSIS = "data_analysis"
    CONTENT_GENERATION = "content_generation"
    USER_TRACKING = "user_tracking"
    AUTOMATED_DECISION = "automated_decision"
    RESEARCH_QUERY = "research_query"
    EXTERNAL_API_CALL = "external_api_call"
    FILE_PROCESSING = "file_processing"
    REAL_TIME_STREAMING = "real_time_streaming"


class BoundaryAction(str, Enum):
    """Actions boundary system can take."""
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"  # Hold for review
    ANONYMIZE = "anonymize"  # Strip PII and allow
    LOG_ONLY = "log_only"  # Allow but log extensively
    RATE_LIMIT = "rate_limit"  # Slow down


class HumanRightsImpact(BaseModel):
    """Assessment of human rights impact for a request."""
    rights_categories: list[HumanRightCategory] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NONE
    affected_populations: list[str] = Field(default_factory=list)
    potential_harms: list[str] = Field(default_factory=list)
    mitigation_required: bool = False
    requires_human_review: bool = False
    review_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "rights_categories": ["right_to_privacy", "freedom_from_discrimination"],
                "risk_level": "high",
                "affected_populations": ["vulnerable_groups", "children"],
                "potential_harms": ["privacy_breach", "biased_outcomes"],
                "mitigation_required": True,
                "requires_human_review": True,
                "review_reason": "Potential discrimination in automated decision"
            }
        }


class RightsPreservingRequest(BaseModel):
    """Base request model with human rights validation."""
    request_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_type: RequestType
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    
    # Rights analysis
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    declared_purpose: Optional[str] = None
    data_subjects: list[str] = Field(default_factory=list)  # Who's data is involved
    
    # Consent tracking
    consent_obtained: bool = False
    consent_type: Optional[str] = None  # explicit, implicit, legitimate_interest
    consent_timestamp: Optional[datetime] = None
    
    @validator("content")
    def validate_content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure content is not just whitespace."""
        if v is not None and not v.strip():
            return None
        return v


class BoundaryDecision(BaseModel):
    """Decision made by the boundary enforcement system."""
    decision_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Decision
    action: BoundaryAction
    action_reason: str
    human_rights_impact: HumanRightsImpact
    
    # Justification
    policy_rules_triggered: list[str] = Field(default_factory=list)
    rights_categories_protected: list[HumanRightCategory] = Field(default_factory=list)
    override_used: bool = False
    override_justification: Optional[str] = None
    
    # Next steps
    requires_follow_up: bool = False
    follow_up_action: Optional[str] = None
    retention_period_days: int = 90  # How long to keep audit trail


class AuditLogEntry(BaseModel):
    """Immutable audit log entry for accountability."""
    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    correlation_id: str
    
    # What happened
    event_type: str  # request_received, rights_check, boundary_decision, etc.
    event_data: dict[str, Any] = Field(default_factory=dict)
    
    # Who did it
    actor_type: str  # user, system, admin, external_service
    actor_id: Optional[str] = None
    
    # Where
    service_name: str
    endpoint: Optional[str] = None
    
    # Integrity
    integrity_hash: Optional[str] = None  # Cryptographic hash for tamper detection
    previous_entry_hash: Optional[str] = None  # Chain for audit trail


class RightsGuardrailPolicy(BaseModel):
    """Policy configuration for human rights guardrails."""
    policy_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    description: str
    
    # Scope
    applies_to_request_types: list[RequestType] = Field(default_factory=list)
    applies_to_rights_categories: list[HumanRightCategory] = Field(default_factory=list)
    
    # Rules
    prohibited_patterns: list[str] = Field(default_factory=list)
    required_consent_types: list[str] = Field(default_factory=list)
    max_risk_level_allowed: RiskLevel = RiskLevel.HIGH
    
    # Actions
    default_action: BoundaryAction = BoundaryAction.DENY
    high_risk_action: BoundaryAction = BoundaryAction.QUARANTINE
    violation_action: BoundaryAction = BoundaryAction.DENY
    
    # Notifications
    alert_channels: list[str] = Field(default_factory=list)
    notify_on_violation: bool = True
    notify_on_high_risk: bool = True


class WebSocketMessage(BaseModel):
    """Real-time WebSocket message schema."""
    message_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str
    
    # Message type
    message_type: str  # request, response, boundary_alert, rights_check, heartbeat
    
    # Payload
    payload: dict[str, Any] = Field(default_factory=dict)
    
    # Rights metadata
    rights_validated: bool = False
    rights_violations: list[str] = Field(default_factory=list)
    requires_acknowledgment: bool = False
    
    # Status
    status: str = "pending"  # pending, processing, completed, blocked, error
    processing_time_ms: Optional[int] = None


class MonitoringMetrics(BaseModel):
    """Real-time monitoring metrics for boundary system."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Request counts
    total_requests: int = 0
    allowed_requests: int = 0
    denied_requests: int = 0
    quarantined_requests: int = 0
    
    # Rights metrics
    rights_violations_detected: int = 0
    human_reviews_triggered: int = 0
    high_risk_requests: int = 0
    
    # Performance
    avg_processing_time_ms: float = 0.0
    p99_processing_time_ms: float = 0.0
    active_websocket_connections: int = 0
    
    # By category
    violations_by_category: dict[str, int] = Field(default_factory=dict)
    requests_by_type: dict[str, int] = Field(default_factory=dict)


class BoundarySchema(BaseModel):
    """Complete boundary enforcement schema."""
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Policies
    guardrail_policies: list[RightsGuardrailPolicy] = Field(default_factory=list)
    
    # Prohibited research domains
    prohibited_domains: list[str] = Field(default_factory=lambda: [
        "surveillance_technology",
        "discriminatory_profiling",
        "autonomous_weapons",
        "forced_behavior_modification",
        "exploitative_data_collection",
        "coercive_psychological_manipulation",
        "non_consensual_biometric_tracking",
        "social_credit_scoring",
        "predictive_policing_without_oversight",
        "algorithmic_discrimination_enforcement"
    ])
    
    # Rights to protect
    protected_rights: list[HumanRightCategory] = Field(default_factory=lambda: list(HumanRightCategory))
    
    # Settings
    real_time_monitoring_enabled: bool = True
    audit_logging_enabled: bool = True
    human_review_required_for_high_risk: bool = True
    auto_deny_on_violation: bool = True
    webhooks_enabled: bool = False


# Schema export
__all__ = [
    "RiskLevel",
    "HumanRightCategory",
    "RequestType",
    "BoundaryAction",
    "HumanRightsImpact",
    "RightsPreservingRequest",
    "BoundaryDecision",
    "AuditLogEntry",
    "RightsGuardrailPolicy",
    "WebSocketMessage",
    "MonitoringMetrics",
    "BoundarySchema",
]
