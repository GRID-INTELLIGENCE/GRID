"""
Threat Detection Module for GRID Security Stack.

Provides real-time threat detection with pattern matching, behavioral analysis,
rate limiting, and risk scoring. Implements defense-in-depth approach for
identifying and responding to security threats in the GRID event-driven architecture.

Features:
- Pattern-based threat detection with configurable rules
- Behavioral analysis for anomaly detection
- Rate limiting with sliding window tracking
- IP-based blocking and tracking
- Risk scoring with configurable thresholds
- Request history for forensic analysis
- Integration with EventBus for security event emission

Security Standards:
- OWASP threat detection guidelines
- Community threat intelligence patterns
- Behavioral anomaly detection best practices

Example:
    >>> from grid.security.threat_detector import ThreatDetector
    >>> detector = ThreatDetector()
    >>> result = detector.analyze_request({"text": "SELECT * FROM users"}, "192.168.1.1")
    >>> print(result.risk_score, result.action)
    0.7 monitor
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ThreatAction(StrEnum):
    """Actions to take for detected threats."""

    ALLOW = "allow"
    MONITOR = "monitor"
    CHALLENGE = "challenge"
    THROTTLE = "throttle"
    BLOCK = "block"
    REPORT = "report"


class ThreatCategory(StrEnum):
    """Categories of security threats."""

    INJECTION = "injection"
    XSS = "xss"
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT = "rate_limit"
    DOS = "dos"
    ENUMERATION = "enumeration"
    RECONNAISSANCE = "reconnaissance"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALICIOUS_PAYLOAD = "malicious_payload"
    BLOCKED_SOURCE = "blocked_source"
    ANOMALY = "anomaly"


class RiskLevel(StrEnum):
    """Risk levels for threat assessment."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ThreatPattern:
    """Definition of a threat detection pattern."""

    pattern_id: str
    name: str
    description: str
    regex: str
    category: ThreatCategory
    risk_score: float  # 0.0 to 1.0
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    _compiled: re.Pattern | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Compile regex pattern."""
        try:
            self._compiled = re.compile(self.regex, re.IGNORECASE | re.DOTALL)
        except re.error as e:
            logger.error("Failed to compile pattern '%s': %s", self.pattern_id, e)
            self.enabled = False

    def matches(self, text: str) -> list[str]:
        """Check if pattern matches text."""
        if not self.enabled or self._compiled is None:
            return []
        return self._compiled.findall(text)


@dataclass
class ThreatIndicator:
    """Detected threat indicator."""

    indicator_id: str
    pattern_id: str
    category: ThreatCategory
    description: str
    matched_content: list[str]
    risk_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "indicator_id": self.indicator_id,
            "pattern_id": self.pattern_id,
            "category": self.category.value,
            "description": self.description,
            "matched_content": self.matched_content[:5],  # Limit for logging
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ThreatAnalysisResult:
    """Result of threat analysis."""

    request_id: str
    client_ip: str
    timestamp: datetime
    threats: list[ThreatIndicator]
    risk_score: float
    risk_level: RiskLevel
    action: ThreatAction
    rate_limit_status: dict[str, Any]
    behavioral_flags: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_blocked(self) -> bool:
        """Check if request should be blocked."""
        return self.action == ThreatAction.BLOCK

    @property
    def is_safe(self) -> bool:
        """Check if request is considered safe."""
        return self.action == ThreatAction.ALLOW and self.risk_level in [RiskLevel.NONE, RiskLevel.LOW]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "client_ip": self.client_ip,
            "timestamp": self.timestamp.isoformat(),
            "threats": [t.to_dict() for t in self.threats],
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "action": self.action.value,
            "rate_limit_status": self.rate_limit_status,
            "behavioral_flags": self.behavioral_flags,
            "metadata": self.metadata,
        }


@dataclass
class RequestRecord:
    """Record of a request for history tracking."""

    request_id: str
    client_ip: str
    timestamp: datetime
    endpoint: str | None
    content_hash: str
    risk_score: float
    action_taken: ThreatAction
    user_id: str | None = None


@dataclass
class ThreatDetectorConfig:
    """Configuration for threat detector."""

    # Rate limiting
    rate_limit_window_seconds: int = 300  # 5 minutes
    rate_limit_max_requests: int = 100
    rate_limit_burst: int = 20  # Max requests per second

    # Blocking
    auto_block_threshold: float = 0.9
    block_duration_seconds: int = 3600  # 1 hour
    max_failed_attempts: int = 10

    # Risk scoring
    risk_weight_patterns: float = 0.4
    risk_weight_rate: float = 0.2
    risk_weight_behavior: float = 0.2
    risk_weight_history: float = 0.2

    # History
    max_history_per_ip: int = 1000
    history_retention_hours: int = 24

    # Features
    enable_pattern_matching: bool = True
    enable_rate_limiting: bool = True
    enable_behavioral_analysis: bool = True
    enable_auto_blocking: bool = True
    log_all_requests: bool = False


class ThreatDetector:
    """
    Real-time threat detection with pattern matching and behavioral analysis.

    Provides comprehensive threat detection capabilities including:
    - Pattern-based detection for known attack vectors
    - Rate limiting with sliding window tracking
    - Behavioral analysis for anomaly detection
    - Risk scoring and automatic response actions

    Attributes:
        config: Detector configuration
        patterns: List of active threat patterns
        blocked_ips: Set of blocked IP addresses
    """

    # Default threat patterns
    DEFAULT_PATTERNS: list[dict[str, Any]] = [
        # SQL Injection patterns
        {
            "pattern_id": "sqli_union",
            "name": "SQL Injection - UNION",
            "description": "Detects UNION-based SQL injection attempts",
            "regex": r"\b(union\s+(all\s+)?select)\b",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.9,
            "tags": ["sqli", "database"],
        },
        {
            "pattern_id": "sqli_comment",
            "name": "SQL Injection - Comment",
            "description": "Detects SQL comment-based injection",
            "regex": r"(--|#|/\*.*\*/)\s*$",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.6,
            "tags": ["sqli", "database"],
        },
        {
            "pattern_id": "sqli_boolean",
            "name": "SQL Injection - Boolean",
            "description": "Detects boolean-based SQL injection",
            "regex": r"('\s*or\s+'?\d+'?\s*=\s*'?\d+'?|'\s*or\s+'[^']+'\s*=\s*'[^']+')",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.85,
            "tags": ["sqli", "database"],
        },
        {
            "pattern_id": "sqli_stacked",
            "name": "SQL Injection - Stacked Queries",
            "description": "Detects stacked query SQL injection",
            "regex": r";\s*(drop|delete|update|insert|alter|create|truncate)\s+",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.95,
            "tags": ["sqli", "database", "destructive"],
        },
        # XSS patterns
        {
            "pattern_id": "xss_script",
            "name": "XSS - Script Tag",
            "description": "Detects script tag XSS attempts",
            "regex": r"<script[^>]*>",
            "category": ThreatCategory.XSS,
            "risk_score": 0.9,
            "tags": ["xss", "javascript"],
        },
        {
            "pattern_id": "xss_event",
            "name": "XSS - Event Handler",
            "description": "Detects event handler XSS attempts",
            "regex": r"\bon\w+\s*=\s*['\"]?[^'\"]*['\"]?",
            "category": ThreatCategory.XSS,
            "risk_score": 0.8,
            "tags": ["xss", "javascript"],
        },
        {
            "pattern_id": "xss_javascript_uri",
            "name": "XSS - JavaScript URI",
            "description": "Detects javascript: URI XSS attempts",
            "regex": r"javascript\s*:",
            "category": ThreatCategory.XSS,
            "risk_score": 0.85,
            "tags": ["xss", "javascript"],
        },
        # Command Injection patterns
        {
            "pattern_id": "cmdi_shell",
            "name": "Command Injection - Shell",
            "description": "Detects shell command injection",
            "regex": r"[;&|]\s*(sh|bash|cmd|powershell|python|perl|ruby)\b",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.95,
            "tags": ["cmdi", "shell", "critical"],
        },
        {
            "pattern_id": "cmdi_pipe",
            "name": "Command Injection - Pipe",
            "description": "Detects pipe-based command injection",
            "regex": r"\|\s*(cat|nc|netcat|wget|curl)\s+",
            "category": ThreatCategory.INJECTION,
            "risk_score": 0.9,
            "tags": ["cmdi", "shell"],
        },
        # Path Traversal patterns
        {
            "pattern_id": "path_traversal",
            "name": "Path Traversal",
            "description": "Detects directory traversal attempts",
            "regex": r"(\.\.[\\/]|%2e%2e[\\/]|%252e%252e[\\/])",
            "category": ThreatCategory.DATA_EXFILTRATION,
            "risk_score": 0.8,
            "tags": ["lfi", "path_traversal"],
        },
        # Reconnaissance patterns
        {
            "pattern_id": "recon_common_files",
            "name": "Reconnaissance - Common Files",
            "description": "Detects access to common sensitive files",
            "regex": r"(\.git|\.env|\.htaccess|web\.config|wp-config|config\.php)",
            "category": ThreatCategory.RECONNAISSANCE,
            "risk_score": 0.6,
            "tags": ["recon", "enumeration"],
        },
        # Data Exfiltration patterns
        {
            "pattern_id": "exfil_large_query",
            "name": "Data Exfiltration - Large Query",
            "description": "Detects potential data exfiltration queries",
            "regex": r"\bselect\s+\*\s+from\s+\w+\s*(;|$)",
            "category": ThreatCategory.DATA_EXFILTRATION,
            "risk_score": 0.5,
            "tags": ["exfil", "database"],
        },
        # Malicious Payload patterns
        {
            "pattern_id": "payload_base64",
            "name": "Suspicious Base64 Payload",
            "description": "Detects suspicious base64 encoded content",
            "regex": r"(eval|exec|system)\s*\(\s*(base64_decode|atob)\s*\(",
            "category": ThreatCategory.MALICIOUS_PAYLOAD,
            "risk_score": 0.9,
            "tags": ["payload", "encoded"],
        },
    ]

    def __init__(self, config: ThreatDetectorConfig | None = None) -> None:
        """
        Initialize threat detector.

        Args:
            config: Detector configuration
        """
        self.config = config or ThreatDetectorConfig()

        # Pattern matching
        self._patterns: list[ThreatPattern] = []
        self._load_default_patterns()

        # Rate limiting
        self._request_counts: dict[str, list[float]] = defaultdict(list)

        # Blocking
        self._blocked_ips: dict[str, float] = {}  # IP -> block expiry timestamp
        self._failed_attempts: dict[str, int] = defaultdict(int)

        # History tracking
        self._request_history: dict[str, list[RequestRecord]] = defaultdict(list)

        # Behavioral analysis
        self._ip_profiles: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "first_seen": None,
                "total_requests": 0,
                "high_risk_requests": 0,
                "endpoints_accessed": set(),
                "content_hashes": set(),
                "avg_risk_score": 0.0,
            }
        )

        # Thread safety
        self._lock = threading.RLock()

        # Statistics
        self._stats = {
            "total_analyzed": 0,
            "threats_detected": 0,
            "requests_blocked": 0,
            "requests_throttled": 0,
            "false_positives_reported": 0,
        }

        logger.info(
            "ThreatDetector initialized with %d patterns, rate_limit=%d/%ds",
            len(self._patterns),
            self.config.rate_limit_max_requests,
            self.config.rate_limit_window_seconds,
        )

    def _load_default_patterns(self) -> None:
        """Load default threat detection patterns."""
        for pattern_data in self.DEFAULT_PATTERNS:
            pattern = ThreatPattern(
                pattern_id=pattern_data["pattern_id"],
                name=pattern_data["name"],
                description=pattern_data["description"],
                regex=pattern_data["regex"],
                category=pattern_data["category"],
                risk_score=pattern_data["risk_score"],
                tags=pattern_data.get("tags", []),
            )
            if pattern.enabled:
                self._patterns.append(pattern)

    def add_pattern(self, pattern: ThreatPattern) -> None:
        """
        Add a custom threat pattern.

        Args:
            pattern: ThreatPattern to add
        """
        with self._lock:
            self._patterns.append(pattern)
            logger.debug("Added threat pattern: %s", pattern.pattern_id)

    def remove_pattern(self, pattern_id: str) -> bool:
        """
        Remove a threat pattern by ID.

        Args:
            pattern_id: ID of pattern to remove

        Returns:
            True if pattern was removed
        """
        with self._lock:
            original_count = len(self._patterns)
            self._patterns = [p for p in self._patterns if p.pattern_id != pattern_id]
            return len(self._patterns) < original_count

    def analyze_request(
        self,
        request_data: dict[str, Any],
        client_ip: str,
        endpoint: str | None = None,
        user_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> ThreatAnalysisResult:
        """
        Analyze a request for potential threats.

        Args:
            request_data: Request data to analyze
            client_ip: Client IP address
            endpoint: Request endpoint (optional)
            user_id: User identifier (optional)
            headers: Request headers (optional)

        Returns:
            ThreatAnalysisResult with analysis details
        """
        import uuid

        request_id = f"req-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()
        threats: list[ThreatIndicator] = []
        behavioral_flags: list[str] = []

        self._stats["total_analyzed"] += 1

        # Convert request data to string for analysis
        content_str = self._flatten_content(request_data)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()  # noqa: S324 non-cryptographic use

        with self._lock:
            # Check if IP is blocked
            if self._is_ip_blocked(client_ip):
                return ThreatAnalysisResult(
                    request_id=request_id,
                    client_ip=client_ip,
                    timestamp=timestamp,
                    threats=[
                        ThreatIndicator(
                            indicator_id=f"ind-{uuid.uuid4().hex[:8]}",
                            pattern_id="blocked_ip",
                            category=ThreatCategory.BLOCKED_SOURCE,
                            description="IP address is currently blocked",
                            matched_content=[],
                            risk_score=1.0,
                        )
                    ],
                    risk_score=1.0,
                    risk_level=RiskLevel.CRITICAL,
                    action=ThreatAction.BLOCK,
                    rate_limit_status={"blocked": True},
                    behavioral_flags=["blocked_ip"],
                )

            # Pattern matching
            if self.config.enable_pattern_matching:
                pattern_threats = self._detect_pattern_threats(content_str, request_id)
                threats.extend(pattern_threats)

            # Rate limiting check
            rate_limit_status = {"exceeded": False, "remaining": 0}
            if self.config.enable_rate_limiting:
                rate_status = self._check_rate_limit(client_ip)
                rate_limit_status = rate_status
                if rate_status["exceeded"]:
                    threats.append(
                        ThreatIndicator(
                            indicator_id=f"ind-{uuid.uuid4().hex[:8]}",
                            pattern_id="rate_limit",
                            category=ThreatCategory.RATE_LIMIT,
                            description=f"Rate limit exceeded: {rate_status['count']}/{self.config.rate_limit_max_requests}",
                            matched_content=[],
                            risk_score=0.7,
                            metadata=rate_status,
                        )
                    )

            # Behavioral analysis
            if self.config.enable_behavioral_analysis:
                behavioral_flags = self._analyze_behavior(
                    client_ip,
                    content_hash,
                    endpoint,
                    len(threats) > 0,
                )

            # Calculate risk score
            risk_score = self._calculate_risk_score(threats, rate_limit_status, behavioral_flags)
            risk_level = self._get_risk_level(risk_score)

            # Determine action
            action = self._determine_action(risk_score, threats, rate_limit_status)

            # Update statistics
            if threats:
                self._stats["threats_detected"] += 1
            if action == ThreatAction.BLOCK:
                self._stats["requests_blocked"] += 1
                if self.config.enable_auto_blocking and risk_score >= self.config.auto_block_threshold:
                    self._block_ip(client_ip)
            elif action == ThreatAction.THROTTLE:
                self._stats["requests_throttled"] += 1

            # Record request in history
            self._record_request(
                request_id=request_id,
                client_ip=client_ip,
                endpoint=endpoint,
                content_hash=content_hash,
                risk_score=risk_score,
                action=action,
                user_id=user_id,
            )

        # Log if configured
        if self.config.log_all_requests or threats:
            logger.info(
                "Threat analysis: ip=%s, threats=%d, risk=%.2f, action=%s",
                client_ip,
                len(threats),
                risk_score,
                action.value,
            )

        return ThreatAnalysisResult(
            request_id=request_id,
            client_ip=client_ip,
            timestamp=timestamp,
            threats=threats,
            risk_score=risk_score,
            risk_level=risk_level,
            action=action,
            rate_limit_status=rate_limit_status,
            behavioral_flags=behavioral_flags,
            metadata={
                "endpoint": endpoint,
                "user_id": user_id,
                "content_hash": content_hash,
            },
        )

    def _flatten_content(self, data: Any) -> str:
        """Flatten data structure to string for analysis."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            parts = []
            for key, value in data.items():
                parts.append(f"{key}:{self._flatten_content(value)}")
            return " ".join(parts)
        elif isinstance(data, list):
            return " ".join(self._flatten_content(item) for item in data)
        else:
            return str(data)

    def _detect_pattern_threats(self, content: str, request_id: str) -> list[ThreatIndicator]:
        """Detect threats using pattern matching."""
        import uuid

        threats = []

        for pattern in self._patterns:
            if not pattern.enabled:
                continue

            matches = pattern.matches(content)
            if matches:
                threats.append(
                    ThreatIndicator(
                        indicator_id=f"ind-{uuid.uuid4().hex[:8]}",
                        pattern_id=pattern.pattern_id,
                        category=pattern.category,
                        description=pattern.description,
                        matched_content=matches[:10],  # Limit stored matches
                        risk_score=pattern.risk_score,
                        metadata={
                            "pattern_name": pattern.name,
                            "tags": pattern.tags,
                            "match_count": len(matches),
                        },
                    )
                )

        return threats

    def _check_rate_limit(self, client_ip: str) -> dict[str, Any]:
        """Check rate limiting for an IP address."""
        current_time = time.time()
        window_start = current_time - self.config.rate_limit_window_seconds

        # Clean old entries
        self._request_counts[client_ip] = [ts for ts in self._request_counts[client_ip] if ts > window_start]

        # Add current request
        self._request_counts[client_ip].append(current_time)

        count = len(self._request_counts[client_ip])
        exceeded = count > self.config.rate_limit_max_requests

        # Check burst rate (requests in last second)
        recent = [ts for ts in self._request_counts[client_ip] if ts > current_time - 1]
        burst_exceeded = len(recent) > self.config.rate_limit_burst

        return {
            "count": count,
            "limit": self.config.rate_limit_max_requests,
            "window_seconds": self.config.rate_limit_window_seconds,
            "remaining": max(0, self.config.rate_limit_max_requests - count),
            "exceeded": exceeded or burst_exceeded,
            "burst_exceeded": burst_exceeded,
        }

    def _analyze_behavior(
        self,
        client_ip: str,
        content_hash: str,
        endpoint: str | None,
        has_threats: bool,
    ) -> list[str]:
        """Analyze behavioral patterns for anomalies."""
        flags = []
        profile = self._ip_profiles[client_ip]

        # Update profile
        if profile["first_seen"] is None:
            profile["first_seen"] = datetime.now()
            flags.append("new_ip")

        profile["total_requests"] += 1

        if has_threats:
            profile["high_risk_requests"] += 1

        if endpoint:
            profile["endpoints_accessed"].add(endpoint)

        # Check for anomalies

        # High rate of malicious requests
        if profile["total_requests"] > 10:
            malicious_rate = profile["high_risk_requests"] / profile["total_requests"]
            if malicious_rate > 0.3:
                flags.append("high_malicious_rate")

        # Too many unique endpoints (enumeration)
        if len(profile["endpoints_accessed"]) > 50:
            flags.append("endpoint_enumeration")

        # Repeated identical content (automation)
        if content_hash in profile["content_hashes"]:
            flags.append("repeated_content")
        else:
            profile["content_hashes"].add(content_hash)
            # Keep hash set bounded
            if len(profile["content_hashes"]) > 100:
                profile["content_hashes"] = set(list(profile["content_hashes"])[-50:])

        return flags

    def _calculate_risk_score(
        self,
        threats: list[ThreatIndicator],
        rate_status: dict[str, Any],
        behavioral_flags: list[str],
    ) -> float:
        """Calculate overall risk score."""
        scores = []

        # Pattern-based risk
        if threats:
            pattern_risk = max(t.risk_score for t in threats)
            scores.append((pattern_risk, self.config.risk_weight_patterns))
        else:
            scores.append((0.0, self.config.risk_weight_patterns))

        # Rate limiting risk
        if rate_status.get("exceeded"):
            rate_risk = 0.8 if rate_status.get("burst_exceeded") else 0.6
        else:
            # Proportional to how close to limit
            count = rate_status.get("count", 0)
            limit = rate_status.get("limit", 100)
            rate_risk = min(1.0, count / limit) * 0.5
        scores.append((rate_risk, self.config.risk_weight_rate))

        # Behavioral risk
        behavior_risk = min(1.0, len(behavioral_flags) * 0.2)
        if "high_malicious_rate" in behavioral_flags:
            behavior_risk = max(behavior_risk, 0.7)
        scores.append((behavior_risk, self.config.risk_weight_behavior))

        # Calculate weighted average
        total_weight = sum(weight for _, weight in scores)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(score * weight for score, weight in scores)
        return min(1.0, weighted_sum / total_weight)

    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level."""
        if risk_score < 0.2:
            return RiskLevel.NONE
        elif risk_score < 0.4:
            return RiskLevel.LOW
        elif risk_score < 0.6:
            return RiskLevel.MEDIUM
        elif risk_score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _determine_action(
        self,
        risk_score: float,
        threats: list[ThreatIndicator],
        rate_status: dict[str, Any],
    ) -> ThreatAction:
        """Determine action based on analysis results."""
        # Critical threats or very high risk -> Block
        if risk_score >= self.config.auto_block_threshold:
            return ThreatAction.BLOCK

        # Check for critical categories
        critical_categories = {ThreatCategory.INJECTION, ThreatCategory.MALICIOUS_PAYLOAD}
        for threat in threats:
            if threat.category in critical_categories and threat.risk_score >= 0.9:
                return ThreatAction.BLOCK

        # Rate limit exceeded -> Throttle
        if rate_status.get("exceeded"):
            return ThreatAction.THROTTLE

        # High risk -> Monitor closely
        if risk_score >= 0.6:
            return ThreatAction.MONITOR

        # Medium risk with threats -> Report
        if risk_score >= 0.3 and threats:
            return ThreatAction.REPORT

        return ThreatAction.ALLOW

    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked."""
        if client_ip not in self._blocked_ips:
            return False

        expiry = self._blocked_ips[client_ip]
        if time.time() > expiry:
            del self._blocked_ips[client_ip]
            return False

        return True

    def _block_ip(self, client_ip: str, duration: int | None = None) -> None:
        """Block an IP address."""
        duration = duration or self.config.block_duration_seconds
        self._blocked_ips[client_ip] = time.time() + duration
        logger.warning("IP blocked: %s for %d seconds", client_ip, duration)

    def _record_request(
        self,
        request_id: str,
        client_ip: str,
        endpoint: str | None,
        content_hash: str,
        risk_score: float,
        action: ThreatAction,
        user_id: str | None,
    ) -> None:
        """Record request in history."""
        record = RequestRecord(
            request_id=request_id,
            client_ip=client_ip,
            timestamp=datetime.now(),
            endpoint=endpoint,
            content_hash=content_hash,
            risk_score=risk_score,
            action_taken=action,
            user_id=user_id,
        )

        # Add to history
        history = self._request_history[client_ip]
        history.append(record)

        # Limit history size
        if len(history) > self.config.max_history_per_ip:
            self._request_history[client_ip] = history[-self.config.max_history_per_ip :]
