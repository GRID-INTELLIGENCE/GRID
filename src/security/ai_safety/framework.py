"""
AI Safety Framework for Wellness Studio
======================================

Comprehensive AI Safety system with content moderation, behavioral analysis,
and threat detection. Designed as the primary safety layer for wellness applications.

Key Features:
- Multi-layer content moderation
- Behavioral pattern analysis
- Real-time threat detection
- Cultural context awareness (Southeast Asia focus)
- Privacy-preserving analysis
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ThreatLevel(StrEnum):
    """Threat severity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(StrEnum):
    """Types of content to analyze."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    METADATA = "metadata"


class SafetyCategory(StrEnum):
    """Safety evaluation categories."""

    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"
    MANIPULATION = "manipulation"
    HARASSMENT = "harassment"
    MISINFORMATION = "misinformation"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    MENTAL_HEALTH_RISK = "mental_health_risk"


@dataclass
class SafetyViolation:
    """Individual safety violation detected."""

    category: SafetyCategory
    severity: ThreatLevel
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SafetyReport:
    """Comprehensive safety evaluation report."""

    overall_score: float  # 0.0 to 1.0, higher is safer
    threat_level: ThreatLevel
    violations: list[SafetyViolation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    content_hash: str = ""

    @property
    def is_safe(self) -> bool:
        return self.threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]

    @property
    def requires_review(self) -> bool:
        return self.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]

    @property
    def should_block(self) -> bool:
        return self.threat_level == ThreatLevel.CRITICAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "threat_level": self.threat_level.value,
            "violations": [v.to_dict() for v in self.violations],
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "content_hash": self.content_hash,
            "is_safe": self.is_safe,
            "requires_review": self.requires_review,
            "should_block": self.should_block,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class ContentModerator:
    """Content moderation engine with multi-layer analysis."""

    def __init__(self):
        # Southeast Asia specific patterns
        self.se_asia_sensitive_terms = self._load_se_asia_patterns()
        self.mental_health_keywords = self._load_mental_health_patterns()
        self.privacy_patterns = self._load_privacy_patterns()
        self.harmful_patterns = self._load_harmful_patterns()
        self.safety_patterns = self._load_safety_patterns()

    def _load_se_asia_patterns(self) -> dict[str, list[str]]:
        """Load Southeast Asia cultural sensitivity patterns."""
        return {
            "religious_sensitive": [
                "mosque",
                "temple",
                "church",
                "buddha",
                "allah",
                "hindu",
                "muslim",
                "christian",
                "buddhist",
                "prayer",
                "worship",
            ],
            "cultural_sensitive": [
                "family honor",
                "face",
                "respect elders",
                "filial piety",
                "arranged marriage",
                "dowry",
                "caste",
            ],
            "political_sensitive": [
                "government",
                "politics",
                "protest",
                "democracy",
                "election",
                "corruption",
                "activism",
            ],
        }

    def _load_mental_health_patterns(self) -> list[str]:
        """Load mental health risk patterns."""
        return [
            "suicide",
            "kill myself",
            "end my life",
            "want to die",
            "self harm",
            "cut myself",
            "depressed",
            "anxiety",
            "panic attack",
            "mental breakdown",
            "can't cope",
        ]

    def _load_privacy_patterns(self) -> list[str]:
        """Load privacy violation patterns."""
        return [
            "social security",
            "credit card",
            "bank account",
            "password",
            "secret",
            "private key",
            "address",
            "phone number",
            "email address",
            "personal data",
        ]

    def _load_harmful_patterns(self) -> list[str]:
        """Load harmful content patterns."""
        return ["violence", "kill", "hurt", "attack", "weapon", "drugs", "illegal", "criminal", "abuse", "hate"]

    def _load_safety_patterns(self) -> dict[str, list[tuple[str, str]]]:
        """Load harmful content detection tokens with confidence tiers."""
        try:
            from .patterns import HARMFUL_PATTERNS
            return HARMFUL_PATTERNS
        except ImportError:
            logger.warning("Safety patterns module not available")
            return {}

    async def analyze_content(
        self, content: str, content_type: ContentType = ContentType.TEXT
    ) -> list[SafetyViolation]:
        """Analyze content for safety violations."""
        violations = []

        # Normalize content
        normalized_content = content.lower()

        # Check for harmful content
        violations.extend(await self._check_harmful_content(normalized_content))

        # Check for privacy violations
        violations.extend(await self._check_privacy_violations(normalized_content))

        # Check for mental health risks
        violations.extend(await self._check_mental_health_risks(normalized_content))

        # Check for cultural sensitivities
        violations.extend(await self._check_cultural_sensitivity(normalized_content))

        # Check for harmful content patterns
        violations.extend(await self._check_safety_patterns(content))

        return violations

    async def _check_harmful_content(self, content: str) -> list[SafetyViolation]:
        """Check for harmful content patterns."""
        violations = []

        for pattern in self.harmful_patterns:
            if pattern in content:
                violations.append(
                    SafetyViolation(
                        category=SafetyCategory.HARMFUL_CONTENT,
                        severity=ThreatLevel.MEDIUM,
                        confidence=0.7,
                        description=f"Potentially harmful content detected: {pattern}",
                        evidence={"pattern": pattern, "context": content[:100]},
                    )
                )

        return violations

    async def _check_privacy_violations(self, content: str) -> list[SafetyViolation]:
        """Check for privacy violations."""
        violations = []

        # Check for PII patterns
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        phone_pattern = r"\b\d{3}-\d{3}-\d{4}\b"

        if re.search(email_pattern, content):
            violations.append(
                SafetyViolation(
                    category=SafetyCategory.PRIVACY_VIOLATION,
                    severity=ThreatLevel.MEDIUM,
                    confidence=0.8,
                    description="Email address detected in content",
                    evidence={"pattern": "email", "matches": re.findall(email_pattern, content)},
                )
            )

        if re.search(phone_pattern, content):
            violations.append(
                SafetyViolation(
                    category=SafetyCategory.PRIVACY_VIOLATION,
                    severity=ThreatLevel.MEDIUM,
                    confidence=0.8,
                    description="Phone number detected in content",
                    evidence={"pattern": "phone", "matches": re.findall(phone_pattern, content)},
                )
            )

        return violations

    async def _check_mental_health_risks(self, content: str) -> list[SafetyViolation]:
        """Check for mental health risk indicators."""
        violations = []

        for keyword in self.mental_health_keywords:
            if keyword in content:
                severity = (
                    ThreatLevel.HIGH if keyword in ["suicide", "kill myself", "end my life"] else ThreatLevel.MEDIUM
                )

                violations.append(
                    SafetyViolation(
                        category=SafetyCategory.MENTAL_HEALTH_RISK,
                        severity=severity,
                        confidence=0.8,
                        description=f"Mental health risk indicator: {keyword}",
                        evidence={"keyword": keyword, "context": content[:200]},
                    )
                )

        return violations

    async def _check_cultural_sensitivity(self, content: str) -> list[SafetyViolation]:
        """Check for cultural sensitivity issues."""
        violations = []

        for category, patterns in self.se_asia_sensitive_terms.items():
            for pattern in patterns:
                if pattern in content:
                    violations.append(
                        SafetyViolation(
                            category=SafetyCategory.CULTURAL_SENSITIVITY,
                            severity=ThreatLevel.LOW,
                            confidence=0.6,
                            description=f"Cultural sensitivity issue in {category}: {pattern}",
                            evidence={"category": category, "pattern": pattern},
                        )
                    )

        return violations

    async def _check_safety_patterns(self, content: str) -> list[SafetyViolation]:
        """Check for harmful content detection tokens."""
        violations = []

        # Severity mapping by category
        _critical = {"nonconsensual_media", "violence", "gendered_violence"}
        _high = {"distress_signals", "platform_exploitation"}

        for category, entries in self.safety_patterns.items():
            for token, confidence in entries:
                if token in content:
                    cat_severity = (
                        ThreatLevel.CRITICAL
                        if category in _critical
                        else ThreatLevel.HIGH
                        if category in _high
                        else ThreatLevel.MEDIUM
                    )
                    # Medium-confidence tokens are capped at MEDIUM severity
                    if confidence == "medium" and cat_severity in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
                        effective_severity = ThreatLevel.MEDIUM
                    else:
                        effective_severity = cat_severity

                    violations.append(
                        SafetyViolation(
                            category=SafetyCategory.HARMFUL_CONTENT,
                            severity=effective_severity,
                            confidence=0.9 if confidence == "high" else 0.5,
                            description=f"Harmful content detected ({category})",
                            evidence={
                                "category": category,
                                "token": token,
                                "confidence_tier": confidence,
                            },
                        )
                    )

        return violations


class BehaviorAnalyzer:
    """Behavioral pattern analysis for anomaly detection."""

    def __init__(self):
        self.user_patterns: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.global_patterns = deque(maxlen=10000)
        self.anomaly_threshold = 2.0  # Standard deviations

    async def analyze_behavior(self, user_id: str, action_data: dict[str, Any]) -> list[SafetyViolation]:
        """Analyze user behavior for anomalies."""
        violations = []

        # Record action
        action_record = {
            "user_id": user_id,
            "timestamp": datetime.now(UTC),
            "action": action_data.get("action", "unknown"),
            "content_length": len(str(action_data.get("content", ""))),
            "metadata": action_data,
        }

        self.user_patterns[user_id].append(action_record)
        self.global_patterns.append(action_record)

        # Check for anomalies
        violations.extend(await self._check_frequency_anomalies(user_id))
        violations.extend(await self._check_content_anomalies(user_id))
        violations.extend(await self._check_time_anomalies(user_id))

        return violations

    async def _check_frequency_anomalies(self, user_id: str) -> list[SafetyViolation]:
        """Check for unusual activity frequency."""
        violations: list[SafetyViolation] = []

        user_actions = self.user_patterns[user_id]
        if len(user_actions) < 10:
            return violations  # Not enough data

        # Calculate action frequency
        recent_actions = [a for a in user_actions if (datetime.now(UTC) - a["timestamp"]).total_seconds() < 60]

        if len(recent_actions) > 30:  # More than 30 actions per minute
            violations.append(
                SafetyViolation(
                    category=SafetyCategory.HARASSMENT,
                    severity=ThreatLevel.MEDIUM,
                    confidence=0.7,
                    description="Unusual activity frequency detected",
                    evidence={"actions_per_minute": len(recent_actions)},
                )
            )

        return violations

    async def _check_content_anomalies(self, user_id: str) -> list[SafetyViolation]:
        """Check for unusual content patterns."""
        violations: list[SafetyViolation] = []

        user_actions = self.user_patterns[user_id]
        if len(user_actions) < 5:
            return violations

        # Check for repetitive content
        recent_content = [a["content_length"] for a in user_actions]
        if len(set(recent_content)) == 1 and len(recent_content) > 5:
            violations.append(
                SafetyViolation(
                    category=SafetyCategory.MANIPULATION,
                    severity=ThreatLevel.LOW,
                    confidence=0.6,
                    description="Repetitive content pattern detected",
                    evidence={"repetitive_count": len(recent_content)},
                )
            )

        return violations

    async def _check_time_anomalies(self, user_id: str) -> list[SafetyViolation]:
        """Check for unusual timing patterns."""
        violations: list[SafetyViolation] = []

        user_actions = self.user_patterns[user_id]
        if len(user_actions) < 10:
            return violations

        # Check for activity at unusual hours (2 AM - 5 AM)
        unusual_hour_actions = [a for a in user_actions if a["timestamp"].hour in [2, 3, 4, 5]]

        if len(unusual_hour_actions) > len(user_actions) * 0.3:  # More than 30% at unusual hours
            violations.append(
                SafetyViolation(
                    category=SafetyCategory.HARASSMENT,
                    severity=ThreatLevel.LOW,
                    confidence=0.5,
                    description="Unusual activity timing pattern",
                    evidence={"unusual_hour_actions": len(unusual_hour_actions)},
                )
            )

        return violations


class ThreatDetector:
    """Real-time threat detection and response system."""

    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.active_threats: dict[str, dict[str, Any]] = {}
        self.threat_history = deque(maxlen=1000)

    def _load_threat_patterns(self) -> dict[str, list[str]]:
        """Load threat detection patterns."""
        return {
            "immediate_threat": ["bomb", "explosion", "attack", "kill", "murder", "violence", "weapon", "gun", "knife"],
            "self_harm": ["suicide", "kill myself", "end it", "overdose", "self harm", "cutting", "jump off"],
            "harassment": ["stalking", "bullying", "threat", "blackmail", "extortion", "intimidation"],
        }

    async def detect_threats(self, content: str, user_id: str) -> list[SafetyViolation]:
        """Detect immediate threats in content."""
        violations = []

        normalized_content = content.lower()

        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if pattern in normalized_content:
                    severity = self._get_threat_severity(threat_type, pattern)

                    violation = SafetyViolation(
                        category=SafetyCategory.HARMFUL_CONTENT,
                        severity=severity,
                        confidence=0.9,
                        description=f"Threat detected: {threat_type} - {pattern}",
                        evidence={"threat_type": threat_type, "pattern": pattern},
                    )

                    violations.append(violation)

                    # Track active threat
                    await self._track_threat(user_id, threat_type, violation)

        return violations

    def _get_threat_severity(self, threat_type: str, pattern: str) -> ThreatLevel:
        """Determine threat severity based on type and pattern."""
        if threat_type == "immediate_threat":
            return ThreatLevel.CRITICAL
        elif threat_type == "self_harm":
            return ThreatLevel.HIGH
        elif threat_type == "harassment":
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    async def _track_threat(self, user_id: str, threat_type: str, violation: SafetyViolation):
        """Track active threat for monitoring."""
        threat_id = f"{user_id}_{threat_type}_{int(time.time())}"

        self.active_threats[threat_id] = {
            "user_id": user_id,
            "threat_type": threat_type,
            "violation": violation,
            "detected_at": datetime.now(UTC),
            "status": "active",
        }

        self.threat_history.append(
            {"threat_id": threat_id, "user_id": user_id, "threat_type": threat_type, "detected_at": datetime.now(UTC)}
        )


class AISafetyFramework:
    """
    Comprehensive AI Safety Framework for wellness applications.

    Integrates content moderation, behavioral analysis, and threat detection
    with cultural context awareness for Southeast Asia markets.
    """

    def __init__(self):
        self.content_moderator = ContentModerator()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.threat_detector = ThreatDetector()
        self._initialized = False

        # Configuration
        self.safety_thresholds = {"safe": 0.8, "warning": 0.6, "danger": 0.4}

    async def initialize(self):
        """Initialize the AI Safety Framework."""
        if self._initialized:
            return

        # Load models and patterns
        logger.info("Initializing AI Safety Framework...")

        self._initialized = True
        logger.info("AI Safety Framework initialized successfully")

    async def evaluate_content(
        self,
        content: str,
        user_id: str = "anonymous",
        content_type: ContentType = ContentType.TEXT,
        context: dict[str, Any] | None = None,
    ) -> SafetyReport:
        """
        Comprehensive safety evaluation of content.

        Args:
            content: Content to evaluate
            user_id: User identifier for behavioral analysis
            content_type: Type of content
            context: Additional context for evaluation

        Returns:
            Comprehensive safety report
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        violations = []

        try:
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Content moderation analysis
            content_violations = await self.content_moderator.analyze_content(content, content_type)
            violations.extend(content_violations)

            # Behavioral analysis
            if user_id != "anonymous":
                action_data = {
                    "action": "content_submission",
                    "content": content,
                    "content_type": content_type.value,
                    "context": context or {},
                }
                behavior_violations = await self.behavior_analyzer.analyze_behavior(user_id, action_data)
                violations.extend(behavior_violations)

            # Threat detection
            threat_violations = await self.threat_detector.detect_threats(content, user_id)
            violations.extend(threat_violations)

            # Calculate overall safety score
            overall_score = self._calculate_safety_score(violations)
            threat_level = self._determine_threat_level(overall_score, violations)

            processing_time = time.time() - start_time

            return SafetyReport(
                overall_score=overall_score,
                threat_level=threat_level,
                violations=violations,
                metadata={"content_type": content_type.value, "user_id": user_id, "context": context or {}},
                processing_time=processing_time,
                content_hash=content_hash,
            )

        except Exception as e:
            logger.error(f"Safety evaluation failed: {e}")
            return SafetyReport(
                overall_score=0.0,
                threat_level=ThreatLevel.HIGH,
                violations=[
                    SafetyViolation(
                        category=SafetyCategory.HARMFUL_CONTENT,
                        severity=ThreatLevel.HIGH,
                        confidence=1.0,
                        description=f"Safety evaluation error: {str(e)}",
                    )
                ],
                processing_time=time.time() - start_time,
                content_hash="",
            )

    def _calculate_safety_score(self, violations: list[SafetyViolation]) -> float:
        """Calculate overall safety score from violations."""
        if not violations:
            return 1.0

        # Weight violations by severity and confidence
        severity_weights = {
            ThreatLevel.NONE: 0.0,
            ThreatLevel.LOW: 0.1,
            ThreatLevel.MEDIUM: 0.3,
            ThreatLevel.HIGH: 0.6,
            ThreatLevel.CRITICAL: 1.0,
        }

        total_weight = 0.0
        for violation in violations:
            weight = severity_weights[violation.severity] * violation.confidence
            total_weight += weight

        # Normalize to 0-1 scale (higher is safer)
        safety_score = max(0.0, 1.0 - total_weight)
        return safety_score

    def _determine_threat_level(self, safety_score: float, violations: list[SafetyViolation]) -> ThreatLevel:
        """Determine overall threat level."""
        # Check for critical violations first
        if any(v.severity == ThreatLevel.CRITICAL for v in violations):
            return ThreatLevel.CRITICAL

        # Check for multiple high-severity violations
        high_severity_count = sum(1 for v in violations if v.severity == ThreatLevel.HIGH)
        if high_severity_count >= 2:
            return ThreatLevel.CRITICAL
        elif high_severity_count >= 1:
            return ThreatLevel.HIGH

        # Use safety score thresholds
        if safety_score >= self.safety_thresholds["safe"]:
            return ThreatLevel.NONE
        elif safety_score >= self.safety_thresholds["warning"]:
            return ThreatLevel.LOW
        elif safety_score >= self.safety_thresholds["danger"]:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.HIGH

    async def get_safety_stats(self) -> dict[str, Any]:
        """Get safety framework statistics."""
        return {
            "initialized": self._initialized,
            "content_moderator": {
                "patterns_loaded": len(self.content_moderator.harmful_patterns),
                "se_asia_patterns": len(self.content_moderator.se_asia_sensitive_terms),
            },
            "behavior_analyzer": {
                "tracked_users": len(self.behavior_analyzer.user_patterns),
                "global_actions": len(self.behavior_analyzer.global_patterns),
            },
            "threat_detector": {
                "active_threats": len(self.threat_detector.active_threats),
                "threat_history": len(self.threat_detector.threat_history),
            },
        }


# Singleton instance
_safety_framework: AISafetyFramework | None = None


def get_ai_safety_framework() -> AISafetyFramework:
    """Get the singleton AISafetyFramework instance."""
    global _safety_framework
    if _safety_framework is None:
        _safety_framework = AISafetyFramework()
    return _safety_framework
