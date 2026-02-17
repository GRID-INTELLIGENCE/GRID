"""
Security monitoring and threat detection system for GRID.

Provides real-time security monitoring, anomaly detection, vulnerability scanning,
and security auditing capabilities. Implements enterprise-grade security operations
with automated threat detection and response.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ThreatLevel(StrEnum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(StrEnum):
    """Types of security threats."""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    ANOMALOUS_ACCESS = "anomalous_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_PAYLOAD = "suspicious_payload"
    MALICIOUS_USER_AGENT = "malicious_user_agent"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"


@dataclass
class ThreatAlert:
    """Security threat alert."""

    alert_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    description: str
    source_ip: str
    user_id: str | None
    timestamp: datetime
    request_data: dict[str, Any]
    evidence: dict[str, Any]
    mitigations: list[str]
    false_positive: bool = False
    resolved: bool = False
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["resolved_at"] = self.resolved_at.isoformat() if self.resolved_at else None
        data["threat_type"] = self.threat_type.value
        data["threat_level"] = self.threat_level.value
        return data


@dataclass
class VulnerabilityReport:
    """Vulnerability scan report."""

    scan_id: str
    timestamp: datetime
    scan_path: str
    vulnerabilities: list[dict[str, Any]]
    total_vulnerabilities: int
    severity_counts: dict[str, int]
    scan_duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp.isoformat(),
            "scan_path": self.scan_path,
            "vulnerabilities": self.vulnerabilities,
            "total_vulnerabilities": self.total_vulnerabilities,
            "severity_counts": self.severity_counts,
            "scan_duration_seconds": self.scan_duration_seconds,
        }


@dataclass
class AuditResult:
    """Security audit result."""

    audit_id: str
    timestamp: datetime
    user_context: dict[str, Any]
    permissions_checked: list[str]
    violations: list[dict[str, Any]]
    compliance_score: float
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "user_context": self.user_context,
            "permissions_checked": self.permissions_checked,
            "violations": self.violations,
            "compliance_score": self.compliance_score,
            "recommendations": self.recommendations,
        }


class SecurityMonitor:
    """
    Comprehensive security monitoring and threat detection system.

    Features:
    - Real-time threat detection using multiple analysis engines
    - Vulnerability scanning for code and configurations
    - Security auditing and compliance checking
    - Automated threat response and mitigation
    - Integration with existing security infrastructure
    """

    def __init__(
        self,
        alert_storage_path: Path = Path("./data/security/alerts"),
        max_alerts_retention_days: int = 90,
        enable_real_time_detection: bool = True,
        threat_thresholds: dict[ThreatLevel, int] | None = None,
    ):
        """
        Initialize security monitor.

        Args:
            alert_storage_path: Path to store security alerts
            max_alerts_retention_days: Maximum days to retain alerts
            enable_real_time_detection: Enable real-time threat detection
            threat_thresholds: Thresholds for automatic response
        """
        self.alert_storage_path = alert_storage_path
        self.alert_storage_path.mkdir(parents=True, exist_ok=True)
        self.max_alerts_retention_days = max_alerts_retention_days
        self.enable_real_time_detection = enable_real_time_detection

        # Default threat thresholds
        self.threat_thresholds = threat_thresholds or {
            ThreatLevel.LOW: 10,
            ThreatLevel.MEDIUM: 5,
            ThreatLevel.HIGH: 2,
            ThreatLevel.CRITICAL: 1,
        }

        # In-memory alert tracking
        self._recent_alerts: deque = deque(maxlen=1000)
        self._threat_counts: dict[tuple[str, ThreatType, ThreatLevel], int] = defaultdict(int)
        self._ip_reputation: dict[str, dict[str, Any]] = {}

        # Detection patterns
        self._sql_injection_patterns = self._load_sql_injection_patterns()
        self._xss_patterns = self._load_xss_patterns()
        self._malicious_user_agents = self._load_malicious_user_agents()

        # Rate limiting tracking
        self._rate_tracker: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        logger.info("SecurityMonitor initialized")

    def detect_anomalies(self, request_data: dict[str, Any]) -> list[ThreatAlert]:
        """
        Detect security anomalies in request data.

        Args:
            request_data: Request data to analyze

        Returns:
            List of detected threat alerts
        """
        alerts = []

        # Extract basic request information
        source_ip = request_data.get("client_ip", "unknown")
        user_agent = request_data.get("user_agent", "")
        method = request_data.get("method", "")
        path = request_data.get("path", "")
        query_params = request_data.get("query_params", {})
        request_data.get("headers", {})
        body = request_data.get("body", "")

        # 1. SQL Injection Detection
        sql_alerts = self._detect_sql_injection(source_ip, user_agent, query_params, body, request_data)
        alerts.extend(sql_alerts)

        # 2. XSS Detection
        xss_alerts = self._detect_xss(source_ip, user_agent, query_params, body, request_data)
        alerts.extend(xss_alerts)

        # 3. Malicious User Agent Detection
        ua_alerts = self._detect_malicious_user_agent(source_ip, user_agent, request_data)
        alerts.extend(ua_alerts)

        # 4. Rate Limit Abuse Detection
        rate_alerts = self._detect_rate_limit_abuse(source_ip, user_agent, request_data)
        alerts.extend(rate_alerts)

        # 5. Anomalous Access Patterns
        pattern_alerts = self._detect_anomalous_patterns(source_ip, user_agent, method, path, request_data)
        alerts.extend(pattern_alerts)

        # 6. Suspicious Payload Detection
        payload_alerts = self._detect_suspicious_payload(source_ip, user_agent, body, request_data)
        alerts.extend(payload_alerts)

        # Store alerts and update tracking
        for alert in alerts:
            self._store_alert(alert)
            self._update_threat_tracking(alert)

        return alerts

    def scan_vulnerabilities(self, codebase_path: Path) -> VulnerabilityReport:
        """
        Scan codebase for security vulnerabilities.

        Args:
            codebase_path: Path to codebase to scan

        Returns:
            Vulnerability scan report
        """
        scan_id = f"scan_{int(time.time())}"
        start_time = time.time()

        vulnerabilities = []
        severity_counts: defaultdict[str, int] = defaultdict(int)

        # Scan Python files for common vulnerabilities
        for py_file in codebase_path.rglob("*.py"):
            try:
                file_vulns = self._scan_python_file(py_file)
                vulnerabilities.extend(file_vulns)
            except Exception as e:
                logger.warning(f"Failed to scan {py_file}: {e}")

        # Scan configuration files
        config_files = list(codebase_path.rglob("*.yaml")) + list(codebase_path.rglob("*.yml"))
        for config_file in config_files:
            try:
                file_vulns = self._scan_config_file(config_file)
                vulnerabilities.extend(file_vulns)
            except Exception as e:
                logger.warning(f"Failed to scan {config_file}: {e}")

        # Count severities
        for vuln in vulnerabilities:
            severity_counts[vuln["severity"]] += 1

        scan_duration = time.time() - start_time

        report = VulnerabilityReport(
            scan_id=scan_id,
            timestamp=datetime.now(UTC),
            scan_path=str(codebase_path),
            vulnerabilities=vulnerabilities,
            total_vulnerabilities=len(vulnerabilities),
            severity_counts=dict(severity_counts),
            scan_duration_seconds=scan_duration,
        )

        # Save report
        self._save_vulnerability_report(report)

        logger.info(f"Vulnerability scan completed: {len(vulnerabilities)} issues found")
        return report

    def audit_permissions(self, user_context: dict[str, Any]) -> AuditResult:
        """
        Audit user permissions and access rights.

        Args:
            user_context: User context including roles and permissions

        Returns:
            Security audit result
        """
        audit_id = f"audit_{int(time.time())}"

        user_id = user_context.get("user_id", "unknown")
        roles = user_context.get("roles", [])
        permissions = user_context.get("permissions", [])
        recent_actions = user_context.get("recent_actions", [])

        violations = []
        permissions_checked = []

        # 1. Check for privilege escalation attempts
        for action in recent_actions:
            action_permissions = action.get("required_permissions", [])
            user_permissions = set(permissions)

            missing_perms = [p for p in action_permissions if p not in user_permissions]
            if missing_perms:
                violations.append(
                    {
                        "type": "privilege_escalation",
                        "action": action.get("action", "unknown"),
                        "missing_permissions": missing_perms,
                        "timestamp": action.get("timestamp"),
                    }
                )
                permissions_checked.extend(action_permissions)

        # 2. Check for unusual access patterns
        sensitive_resources = user_context.get("accessed_resources", [])
        for resource in sensitive_resources:
            if resource.get("sensitivity_level", 0) > 7:  # High sensitivity
                user_sensitivity = user_context.get("max_sensitivity_allowed", 5)
                if resource["sensitivity_level"] > user_sensitivity:
                    violations.append(
                        {
                            "type": "unauthorized_access",
                            "resource": resource["name"],
                            "sensitivity_level": resource["sensitivity_level"],
                            "allowed_level": user_sensitivity,
                            "timestamp": resource.get("access_timestamp"),
                        }
                    )

        # 3. Check for role conflicts
        if "admin" in roles and "service_account" in roles:
            violations.append(
                {
                    "type": "role_conflict",
                    "conflicting_roles": ["admin", "service_account"],
                    "description": "Service accounts should not have admin privileges",
                }
            )

        # Calculate compliance score
        violation_weight = {
            "privilege_escalation": 3,
            "unauthorized_access": 2,
            "role_conflict": 1,
        }

        total_weight = sum(violation_weight.get(v["type"], 1) for v in violations)
        compliance_score = max(0, 100 - (total_weight * 10))

        # Generate recommendations
        recommendations = []
        if violations:
            recommendations.append("Review user permissions and access rights")
            recommendations.append("Implement principle of least privilege")

        if any(v["type"] == "privilege_escalation" for v in violations):
            recommendations.append("Investigate potential privilege escalation attempts")

        if any(v["type"] == "role_conflict" for v in violations):
            recommendations.append("Resolve role conflicts in user assignments")

        audit_result = AuditResult(
            audit_id=audit_id,
            timestamp=datetime.now(UTC),
            user_context=user_context,
            permissions_checked=permissions_checked,
            violations=violations,
            compliance_score=compliance_score,
            recommendations=recommendations,
        )

        # Save audit result
        self._save_audit_result(audit_result)

        logger.info(f"Security audit completed for {user_id}: score {compliance_score}")
        return audit_result

    def _detect_sql_injection(
        self,
        source_ip: str,
        user_agent: str,
        query_params: dict[str, Any],
        body: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect SQL injection attempts."""
        alerts = []

        # Check query parameters
        for param_name, param_value in query_params.items():
            if isinstance(param_value, str) and self._matches_sql_injection(param_value):
                alerts.append(
                    self._create_threat_alert(
                        ThreatType.SQL_INJECTION,
                        ThreatLevel.HIGH,
                        f"SQL injection detected in query parameter: {param_name}",
                        source_ip,
                        user_agent,
                        request_data,
                        {
                            "parameter": param_name,
                            "value": param_value[:100],  # Truncate for storage
                            "patterns_matched": [p for p in self._sql_injection_patterns if p.search(param_value)],
                        },
                    )
                )

        # Check request body
        if body and self._matches_sql_injection(body):
            alerts.append(
                self._create_threat_alert(
                    ThreatType.SQL_INJECTION,
                    ThreatLevel.HIGH,
                    "SQL injection detected in request body",
                    source_ip,
                    user_agent,
                    request_data,
                    {
                        "body_sample": body[:200],  # Truncate for storage
                        "patterns_matched": [p for p in self._sql_injection_patterns if p.search(body)],
                    },
                )
            )

        return alerts

    def _detect_xss(
        self,
        source_ip: str,
        user_agent: str,
        query_params: dict[str, Any],
        body: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect XSS attempts."""
        alerts = []

        # Check query parameters
        for param_name, param_value in query_params.items():
            if isinstance(param_value, str) and self._matches_xss(param_value):
                alerts.append(
                    self._create_threat_alert(
                        ThreatType.XSS,
                        ThreatLevel.MEDIUM,
                        f"XSS detected in query parameter: {param_name}",
                        source_ip,
                        user_agent,
                        request_data,
                        {
                            "parameter": param_name,
                            "value": param_value[:100],
                            "patterns_matched": [p for p in self._xss_patterns if p.search(param_value)],
                        },
                    )
                )

        # Check request body
        if body and self._matches_xss(body):
            alerts.append(
                self._create_threat_alert(
                    ThreatType.XSS,
                    ThreatLevel.MEDIUM,
                    "XSS detected in request body",
                    source_ip,
                    user_agent,
                    request_data,
                    {
                        "body_sample": body[:200],
                        "patterns_matched": [p for p in self._xss_patterns if p.search(body)],
                    },
                )
            )

        return alerts

    def _detect_malicious_user_agent(
        self,
        source_ip: str,
        user_agent: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect malicious user agents."""
        alerts = []

        for pattern, threat_level in self._malicious_user_agents:
            if pattern.search(user_agent.lower()):
                alerts.append(
                    self._create_threat_alert(
                        ThreatType.MALICIOUS_USER_AGENT,
                        threat_level,
                        f"Malicious user agent detected: {user_agent[:50]}",
                        source_ip,
                        user_agent,
                        request_data,
                        {
                            "user_agent": user_agent,
                            "pattern_matched": pattern.pattern,
                        },
                    )
                )
                break

        return alerts

    def _detect_rate_limit_abuse(
        self,
        source_ip: str,
        user_agent: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect rate limit abuse."""
        alerts = []

        now = time.time()
        window = 300  # 5 minutes
        max_requests = 100  # Max requests per window

        # Track requests from this IP
        ip_requests = self._rate_tracker[source_ip]
        ip_requests.append(now)

        # Clean old requests
        cutoff = now - window
        while ip_requests and ip_requests[0] < cutoff:
            ip_requests.popleft()

        if len(ip_requests) > max_requests:
            alerts.append(
                self._create_threat_alert(
                    ThreatType.RATE_LIMIT_ABUSE,
                    ThreatLevel.MEDIUM,
                    f"Rate limit abuse detected: {len(ip_requests)} requests in {window}s",
                    source_ip,
                    user_agent,
                    request_data,
                    {
                        "request_count": len(ip_requests),
                        "time_window": window,
                        "threshold": max_requests,
                    },
                )
            )

        return alerts

    def _detect_anomalous_patterns(
        self,
        source_ip: str,
        user_agent: str,
        method: str,
        path: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect anomalous access patterns."""
        alerts = []

        # Check for suspicious path patterns
        suspicious_paths = [
            r"/admin",
            r"/api/admin",
            r"/\.env",
            r"/config",
            r"/backup",
            r"/dump",
            r"/phpmyadmin",
            r"/wp-admin",
        ]

        for pattern in suspicious_paths:
            if re.search(pattern, path, re.IGNORECASE):
                alerts.append(
                    self._create_threat_alert(
                        ThreatType.ANOMALOUS_ACCESS,
                        ThreatLevel.MEDIUM,
                        f"Suspicious path access: {path}",
                        source_ip,
                        user_agent,
                        request_data,
                        {
                            "path": path,
                            "method": method,
                            "pattern_matched": pattern,
                        },
                    )
                )
                break

        return alerts

    def _detect_suspicious_payload(
        self,
        source_ip: str,
        user_agent: str,
        body: str,
        request_data: dict[str, Any],
    ) -> list[ThreatAlert]:
        """Detect suspicious payload patterns."""
        alerts: list[ThreatAlert] = []

        if not body:
            return alerts

        # Check for common attack patterns
        suspicious_patterns = [
            (r"<\?php", ThreatLevel.HIGH, "PHP code injection"),
            (r"<script[^>]*>", ThreatLevel.MEDIUM, "Script tag injection"),
            (r"eval\s*\(", ThreatLevel.HIGH, "Code execution attempt"),
            (r"base64_decode", ThreatLevel.MEDIUM, "Base64 encoding usage"),
            (r"system\s*\(", ThreatLevel.HIGH, "System command execution"),
            (r"exec\s*\(", ThreatLevel.HIGH, "Command execution attempt"),
        ]

        for pattern, threat_level, description in suspicious_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                alerts.append(
                    self._create_threat_alert(
                        ThreatType.SUSPICIOUS_PAYLOAD,
                        threat_level,
                        f"Suspicious payload: {description}",
                        source_ip,
                        user_agent,
                        request_data,
                        {
                            "description": description,
                            "body_sample": body[:200],
                            "pattern_matched": pattern,
                        },
                    )
                )

        return alerts

    def _create_threat_alert(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        description: str,
        source_ip: str,
        user_agent: str,
        request_data: dict[str, Any],
        evidence: dict[str, Any],
    ) -> ThreatAlert:
        """Create a threat alert."""
        alert_id = f"alert_{int(time.time())}_{hashlib.md5(description.encode()).hexdigest()[:8]}"  # noqa: S324 non-cryptographic use

        mitigations = self._get_mitigations(threat_type, threat_level)

        return ThreatAlert(
            alert_id=alert_id,
            threat_type=threat_type,
            threat_level=threat_level,
            description=description,
            source_ip=source_ip,
            user_id=request_data.get("user_id"),
            timestamp=datetime.now(UTC),
            request_data={
                "method": request_data.get("method", ""),
                "path": request_data.get("path", ""),
                "user_agent": user_agent[:100],  # Truncate
            },
            evidence=evidence,
            mitigations=mitigations,
        )

    def _get_mitigations(self, threat_type: ThreatType, threat_level: ThreatLevel) -> list[str]:
        """Get recommended mitigations for a threat."""
        mitigations_map = {
            ThreatType.SQL_INJECTION: [
                "Block IP address temporarily",
                "Sanitize all input parameters",
                "Review database access logs",
            ],
            ThreatType.XSS: [
                "Sanitize user input",
                "Implement Content Security Policy",
                "Review output encoding",
            ],
            ThreatType.BRUTE_FORCE: [
                "Implement account lockout",
                "Add CAPTCHA verification",
                "Block IP after threshold",
            ],
            ThreatType.ANOMALOUS_ACCESS: [
                "Verify user authentication",
                "Review access permissions",
                "Log suspicious activity",
            ],
        }

        base_mitigations = mitigations_map.get(threat_type, ["Review security logs"])

        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            base_mitigations.append("Immediate security team notification")

        return base_mitigations

    def _store_alert(self, alert: ThreatAlert) -> None:
        """Store a security alert."""
        # Add to in-memory tracking
        self._recent_alerts.append(alert)

        # Save to file
        alert_file = self.alert_storage_path / f"{alert.alert_id}.json"
        with open(alert_file, "w") as f:
            json.dump(alert.to_dict(), f, indent=2)

    def _update_threat_tracking(self, alert: ThreatAlert) -> None:
        """Update threat tracking statistics."""
        key = (alert.source_ip, alert.threat_type, alert.threat_level)
        self._threat_counts[key] += 1

        # Update IP reputation
        if alert.source_ip not in self._ip_reputation:
            self._ip_reputation[alert.source_ip] = {
                "first_seen": alert.timestamp,
                "threat_count": 0,
                "last_activity": alert.timestamp,
            }

        self._ip_reputation[alert.source_ip]["threat_count"] += 1
        self._ip_reputation[alert.source_ip]["last_activity"] = alert.timestamp

    def _matches_sql_injection(self, text: str) -> bool:
        """Check if text matches SQL injection patterns."""
        return any(pattern.search(text) for pattern in self._sql_injection_patterns)

    def _matches_xss(self, text: str) -> bool:
        """Check if text matches XSS patterns."""
        return any(pattern.search(text, re.IGNORECASE) for pattern in self._xss_patterns)

    def _load_sql_injection_patterns(self) -> list[re.Pattern]:
        """Load SQL injection detection patterns."""
        patterns = [
            r"(union|select|insert|update|delete|drop|create|alter|exec|execute)",
            r"(or|and)\s+\d+\s*=\s*\d+",
            r"(or|and)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
            r"['\"]\s*(or|and)\s*['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
            r"(waitfor\s+delay|sleep\s*\()",
            r"(cast|convert)\s*\(",
            r"(char|varchar|nvarchar)\s*\(",
            r"(--|#|/\*|\*/)",
            r"(information_schema|sysobjects|syscolumns)",
        ]

        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    def _load_xss_patterns(self) -> list[re.Pattern]:
        """Load XSS detection patterns."""
        patterns = [
            r"(<script[^>]*>)",
            r"(</script>)",
            r"(javascript\s*:)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<link[^>]*>)",
            r"(<meta[^>]*>)",
            r"(\beval\s*\()",
            r"(\balert\s*\()",
            r"(\bconfirm\s*\()",
            r"(\bprompt\s*\()",
        ]

        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    def _load_malicious_user_agents(self) -> list[tuple[re.Pattern, ThreatLevel]]:
        """Load malicious user agent patterns."""
        patterns = [
            (re.compile(r"sqlmap", re.IGNORECASE), ThreatLevel.HIGH),
            (re.compile(r"nikto", re.IGNORECASE), ThreatLevel.HIGH),
            (re.compile(r"nmap", re.IGNORECASE), ThreatLevel.MEDIUM),
            (re.compile(r"masscan", re.IGNORECASE), ThreatLevel.MEDIUM),
            (re.compile(r"zap", re.IGNORECASE), ThreatLevel.MEDIUM),
            (re.compile(r"burp", re.IGNORECASE), ThreatLevel.MEDIUM),
            (re.compile(r"scanner", re.IGNORECASE), ThreatLevel.LOW),
            (re.compile(r"bot", re.IGNORECASE), ThreatLevel.LOW),
            (re.compile(r"crawler", re.IGNORECASE), ThreatLevel.LOW),
            (re.compile(r"spider", re.IGNORECASE), ThreatLevel.LOW),
        ]

        return patterns

    def _scan_python_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Scan a Python file for security vulnerabilities."""
        vulnerabilities = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Check for security issues
            for node in ast.walk(tree):
                # Hardcoded secrets
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.lower()
                            if any(secret in var_name for secret in ["password", "secret", "key", "token"]):
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    vulnerabilities.append(
                                        {
                                            "type": "hardcoded_secret",
                                            "severity": "high",
                                            "file": str(file_path),
                                            "line": node.lineno,
                                            "variable": var_name,
                                            "description": f"Hardcoded {var_name} detected",
                                        }
                                    )

                # Dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id.lower()
                        dangerous_funcs = ["eval", "exec", "compile", "__import__"]
                        if func_name in dangerous_funcs:
                            vulnerabilities.append(
                                {
                                    "type": "dangerous_function",
                                    "severity": "high",
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "function": func_name,
                                    "description": f"Use of dangerous function: {func_name}",
                                }
                            )

                # SQL injection risks
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr.lower() in ["execute", "executemany"]:
                        if isinstance(node.func.value, ast.Name):
                            if "sql" in node.func.value.id.lower():
                                vulnerabilities.append(
                                    {
                                        "type": "sql_injection_risk",
                                        "severity": "medium",
                                        "file": str(file_path),
                                        "line": node.lineno,
                                        "description": "Potential SQL injection - use parameterized queries",
                                    }
                                )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        return vulnerabilities

    def _scan_config_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Scan a configuration file for security issues."""
        vulnerabilities = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check for exposed secrets
            secret_patterns = [
                (r"password\s*:\s*['\"][^'\"]+['\"]", "high"),
                (r"secret\s*:\s*['\"][^'\"]+['\"]", "high"),
                (r"api_key\s*:\s*['\"][^'\"]+['\"]", "high"),
                (r"token\s*:\s*['\"][^'\"]+['\"]", "medium"),
            ]

            for pattern, severity in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                vulnerabilities.extend(
                        {
                            "type": "exposed_secret",
                            "severity": severity,
                            "file": str(file_path),
                            "line": content[: match.start()].count("\n") + 1,
                            "description": "Potential exposed secret in configuration",
                            "match": match.group()[:50],
                        }
                    for match in matches
                )

            # Check for insecure configurations
            insecure_patterns = [
                (r"debug\s*:\s*true", "medium", "Debug mode enabled in production"),
                (r"ssl_verify\s*:\s*false", "medium", "SSL verification disabled"),
                (r"allow_all_origins\s*:\s*true", "low", "CORS allows all origins"),
            ]

            for pattern, severity, description in insecure_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append(
                        {
                            "type": "insecure_configuration",
                            "severity": severity,
                            "file": str(file_path),
                            "description": description,
                        }
                    )

        except Exception as e:
            logger.warning(f"Failed to scan config {file_path}: {e}")

        return vulnerabilities

    def _save_vulnerability_report(self, report: VulnerabilityReport) -> None:
        """Save vulnerability report to file."""
        report_file = self.alert_storage_path / f"vulnerability_{report.scan_id}.json"
        with open(report_file, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

    def _save_audit_result(self, result: AuditResult) -> None:
        """Save audit result to file."""
        audit_file = self.alert_storage_path / f"audit_{result.audit_id}.json"
        with open(audit_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def get_security_stats(self) -> dict[str, Any]:
        """Get security monitoring statistics."""
        # Count recent alerts by type and level
        alert_counts: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
        for alert in self._recent_alerts:
            alert_counts[alert.threat_type.value][alert.threat_level.value] += 1

        return {
            "total_alerts": len(self._recent_alerts),
            "alert_counts": dict(alert_counts),
            "ip_reputation": dict(self._ip_reputation),
            "threat_thresholds": {k.value: v for k, v in self.threat_thresholds.items()},
        }


# Global security monitor instance
_global_security_monitor: SecurityMonitor | None = None


def get_security_monitor() -> SecurityMonitor:
    """Get or create global security monitor instance."""
    global _global_security_monitor
    if _global_security_monitor is None:
        _global_security_monitor = SecurityMonitor()
    return _global_security_monitor


def set_security_monitor(monitor: SecurityMonitor) -> None:
    """Set global security monitor instance."""
    global _global_security_monitor
    _global_security_monitor = monitor
