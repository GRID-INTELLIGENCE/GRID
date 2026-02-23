"""
AI Safety and Compliance for Arena API Gateway
==============================================

This module implements comprehensive AI safety mechanisms and compliance
checks for the dynamic API system, ensuring responsible AI deployment
and adherence to safety standards.

Key Features:
- Input validation and sanitization
- Output filtering and safety checks
- Bias detection and mitigation
- Compliance monitoring and reporting
- Safety event logging and alerting
- Ethical AI guidelines enforcement
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class SafetyLevel(StrEnum):
    """AI safety levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStandard(StrEnum):
    """Compliance standards."""

    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class SafetyCheck:
    """Container for safety check results."""

    check_name: str
    passed: bool
    severity: SafetyLevel
    details: dict[str, Any]
    timestamp: datetime
    recommendations: list[str] | None = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class AISafetyManager:
    """
    Comprehensive AI safety and compliance management system.
    """

    def __init__(self):
        self.safety_checks = []
        self.compliance_rules = self._load_compliance_rules()
        self.safety_patterns = self._load_safety_patterns()
        self.bias_detectors = self._load_bias_detectors()
        self.monitoring = None  # Will be injected

        # Safety thresholds
        self.max_input_length = 10000
        self.max_output_length = 50000
        self.safety_score_threshold = 0.8

        # Compliance tracking
        self.compliance_violations = []
        self.audit_log = []

    def _load_compliance_rules(self) -> dict[str, Any]:
        """Load compliance rules for different standards."""
        return {
            "hipaa": {
                "pii_patterns": [
                    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                    r"\b\d{10}\b",  # Phone numbers
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                ],
                "phi_keywords": ["medical", "diagnosis", "treatment", "health"],
                "required_encryption": True,
            },
            "gdpr": {
                "personal_data_patterns": [
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    r"\b\d{2}/\d{2}/\d{4}\b",  # Dates of birth
                    r"\b\d{5}(-\d{4})?\b",  # ZIP codes
                ],
                "consent_required": True,
                "data_retention_limit": 2555,  # days (7 years)
            },
        }

    def _load_safety_patterns(self) -> dict[str, list[str]]:
        """Load patterns for detecting unsafe content."""
        return {
            "harmful_content": [
                r"(?i)(kill|murder|assassinate|suicide)",
                r"(?i)(bomb|explosive|weapon)",
                r"(?i)(hack|exploit|vulnerability)",
            ],
            "bias_indicators": [
                r"(?i)(all\s+(men|women|people)\s+(are|should))",
                r"(?i)(never\s+trust\s+(men|women|people))",
            ],
            "jailbreak_attempts": [
                r"(?i)(ignore\s+(previous|all)\s+instructions)",
                r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode)",
                r"(?i)(override\s+(safety|security)\s+protocols)",
            ],
        }

    def _load_bias_detectors(self) -> dict[str, Any]:
        """Load bias detection configurations."""
        return {
            "gender_bias": {
                "male_terms": ["he", "him", "his", "man", "men", "boy", "boys"],
                "female_terms": ["she", "her", "hers", "woman", "women", "girl", "girls"],
                "threshold": 0.3,  # Max allowed ratio difference
            },
            "racial_bias": {"ethnic_terms": ["race", "ethnic", "origin", "background"], "threshold": 0.2},
        }

    def set_monitoring(self, monitoring: Any) -> None:
        """Inject monitoring dependency."""
        self.monitoring = monitoring

    async def check_request(self, request: Any) -> dict[str, Any]:
        """
        Perform comprehensive safety check on incoming request.

        Args:
            request: FastAPI Request object

        Returns:
            Safety check results
        """
        try:
            safety_checks = []

            # 1. Input validation and sanitization
            input_check = await self._validate_input(request)
            safety_checks.append(input_check)

            # 2. Content safety analysis
            content_check = await self._analyze_content_safety(request)
            safety_checks.append(content_check)

            # 3. Compliance checks
            compliance_check = await self._check_compliance(request)
            safety_checks.append(compliance_check)

            # 4. Bias detection
            bias_check = await self._detect_bias(request)
            safety_checks.append(bias_check)

            # 5. Rate and anomaly detection
            anomaly_check = await self._detect_anomalies(request)
            safety_checks.append(anomaly_check)

            # Aggregate results
            overall_safe = all(check.passed for check in safety_checks)
            highest_severity = max(check.severity for check in safety_checks)

            # Store safety checks
            self.safety_checks.extend(safety_checks)

            # Log safety check
            await self._log_safety_check(request, safety_checks, overall_safe)

            # Record security event if unsafe
            if not overall_safe and self.monitoring:
                await self.monitoring.record_security_event(
                    "ai_safety_violation",
                    {
                        "request_path": request.url.path,
                        "client_ip": getattr(request.client, "host", None) if request.client else None,
                        "failed_checks": [check.check_name for check in safety_checks if not check.passed],
                    },
                    "WARNING" if highest_severity != SafetyLevel.CRITICAL else "CRITICAL",
                )

            return {
                "safe": overall_safe,
                "severity": highest_severity.value,
                "checks": [
                    {
                        "name": check.check_name,
                        "passed": check.passed,
                        "severity": check.severity.value,
                        "details": check.details,
                        "recommendations": check.recommendations,
                    }
                    for check in safety_checks
                ],
            }

        except Exception as e:
            logger.error(f"Safety check error: {str(e)}")
            return {"safe": False, "error": str(e), "severity": SafetyLevel.CRITICAL.value}

    async def _validate_input(self, request: Any) -> SafetyCheck:
        """Validate and sanitize input data."""
        try:
            # Check content length
            if hasattr(request, "headers"):
                content_length = int(request.headers.get("content-length", 0))
                if content_length > self.max_input_length:
                    return SafetyCheck(
                        check_name="input_validation",
                        passed=False,
                        severity=SafetyLevel.HIGH,
                        details={"reason": "Input too large", "size": content_length},
                        timestamp=datetime.now(UTC),
                        recommendations=["Reduce input size", "Implement streaming for large inputs"],
                    )

            # Check for malicious patterns
            body_content = ""
            if hasattr(request, "body"):
                try:
                    body_content = await request.body()
                    body_content = body_content.decode("utf-8", errors="ignore")
                except Exception:
                    pass

            # Check for SQL injection patterns
            sql_patterns = [r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)"]
            for pattern in sql_patterns:
                if re.search(pattern, body_content, re.IGNORECASE):
                    return SafetyCheck(
                        check_name="input_validation",
                        passed=False,
                        severity=SafetyLevel.CRITICAL,
                        details={"reason": "Potential SQL injection detected"},
                        timestamp=datetime.now(UTC),
                        recommendations=["Sanitize input", "Use parameterized queries"],
                    )

            # Check for XSS patterns
            xss_patterns = [r"<script[^>]*>.*?</script>", r"javascript:", r"on\w+\s*="]
            for pattern in xss_patterns:
                if re.search(pattern, body_content, re.IGNORECASE):
                    return SafetyCheck(
                        check_name="input_validation",
                        passed=False,
                        severity=SafetyLevel.HIGH,
                        details={"reason": "Potential XSS detected"},
                        timestamp=datetime.now(UTC),
                        recommendations=["Sanitize HTML input", "Use content security policies"],
                    )

            return SafetyCheck(
                check_name="input_validation",
                passed=True,
                severity=SafetyLevel.LOW,
                details={"input_length": len(body_content)},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            return SafetyCheck(
                check_name="input_validation",
                passed=False,
                severity=SafetyLevel.MEDIUM,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    async def _analyze_content_safety(self, request: Any) -> SafetyCheck:
        """Analyze content for safety violations."""
        try:
            content = await self._extract_request_content(request)

            violations = []

            # Check harmful content patterns
            for pattern in self.safety_patterns["harmful_content"]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append({"type": "harmful_content", "pattern": pattern, "matches": len(matches)})

            # Check jailbreak attempts
            for pattern in self.safety_patterns["jailbreak_attempts"]:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append({"type": "jailbreak_attempt", "pattern": pattern})

            if violations:
                severity = (
                    SafetyLevel.CRITICAL
                    if any(v["type"] == "jailbreak_attempt" for v in violations)
                    else SafetyLevel.HIGH
                )
                return SafetyCheck(
                    check_name="content_safety",
                    passed=False,
                    severity=severity,
                    details={"violations": violations},
                    timestamp=datetime.now(UTC),
                    recommendations=["Filter harmful content", "Implement content moderation"],
                )

            return SafetyCheck(
                check_name="content_safety",
                passed=True,
                severity=SafetyLevel.LOW,
                details={"content_length": len(content)},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            return SafetyCheck(
                check_name="content_safety",
                passed=False,
                severity=SafetyLevel.MEDIUM,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    async def _check_compliance(self, request: Any) -> SafetyCheck:
        """Check compliance with relevant standards."""
        try:
            content = await self._extract_request_content(request)
            violations = []

            # Check HIPAA compliance
            hipaa_config = self.compliance_rules.get("hipaa", {})
            for pattern in hipaa_config.get("pii_patterns", []):
                matches = re.findall(pattern, content)
                if matches:
                    violations.append(
                        {"standard": "HIPAA", "type": "PII_detection", "pattern": pattern, "matches": len(matches)}
                    )

            # Check GDPR compliance
            gdpr_config = self.compliance_rules.get("gdpr", {})
            for pattern in gdpr_config.get("personal_data_patterns", []):
                matches = re.findall(pattern, content)
                if matches:
                    violations.append(
                        {"standard": "GDPR", "type": "personal_data", "pattern": pattern, "matches": len(matches)}
                    )

            if violations:
                # Record compliance violation
                self.compliance_violations.append(
                    {
                        "timestamp": datetime.now(UTC),
                        "violations": violations,
                        "request_path": request.url.path,
                    }
                )

                return SafetyCheck(
                    check_name="compliance",
                    passed=False,
                    severity=SafetyLevel.HIGH,
                    details={"violations": violations},
                    timestamp=datetime.now(UTC),
                    recommendations=["Anonymize data", "Implement consent management", "Add data classification"],
                )

            return SafetyCheck(
                check_name="compliance",
                passed=True,
                severity=SafetyLevel.LOW,
                details={"standards_checked": ["HIPAA", "GDPR"]},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            return SafetyCheck(
                check_name="compliance",
                passed=False,
                severity=SafetyLevel.MEDIUM,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    async def _detect_bias(self, request: Any) -> SafetyCheck:
        """Detect potential bias in content."""
        try:
            content = await self._extract_request_content(request)
            bias_indicators = []

            # Check gender bias
            gender_config = self.bias_detectors.get("gender_bias", {})
            male_count = sum(
                len(re.findall(r"\b" + term + r"\b", content, re.IGNORECASE))
                for term in gender_config.get("male_terms", [])
            )
            female_count = sum(
                len(re.findall(r"\b" + term + r"\b", content, re.IGNORECASE))
                for term in gender_config.get("female_terms", [])
            )

            if male_count + female_count > 10:  # Only check if sufficient sample
                total_gender_refs = male_count + female_count
                if total_gender_refs > 0:
                    male_ratio = male_count / total_gender_refs
                    female_ratio = female_count / total_gender_refs

                    threshold = gender_config.get("threshold", 0.3)
                    if abs(male_ratio - female_ratio) > threshold:
                        bias_indicators.append(
                            {
                                "type": "gender_bias",
                                "male_ratio": male_ratio,
                                "female_ratio": female_ratio,
                                "threshold": threshold,
                            }
                        )

            # Check for bias patterns
            for pattern in self.safety_patterns.get("bias_indicators", []):
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    bias_indicators.append({"type": "bias_pattern", "pattern": pattern, "matches": len(matches)})

            if bias_indicators:
                return SafetyCheck(
                    check_name="bias_detection",
                    passed=False,
                    severity=SafetyLevel.MEDIUM,
                    details={"bias_indicators": bias_indicators},
                    timestamp=datetime.now(UTC),
                    recommendations=[
                        "Review content for bias",
                        "Implement bias mitigation",
                        "Add diverse training data",
                    ],
                )

            return SafetyCheck(
                check_name="bias_detection",
                passed=True,
                severity=SafetyLevel.LOW,
                details={"content_analyzed": len(content)},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            return SafetyCheck(
                check_name="bias_detection",
                passed=False,
                severity=SafetyLevel.LOW,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    async def _detect_anomalies(self, request: Any) -> SafetyCheck:
        """Detect anomalous request patterns."""
        try:
            # This would integrate with ML models for anomaly detection
            # For now, implement basic heuristics

            _client_ip = getattr(request.client, "host", None) if request.client else None
            _user_agent = request.headers.get("User-Agent", "")
            _path = request.url.path

            anomalies = []

            # Check for suspicious user agents
            suspicious_agents = ["curl", "wget", "python-requests", "postman"]
            if any(agent.lower() in _user_agent.lower() for agent in suspicious_agents):
                anomalies.append({"type": "suspicious_user_agent", "user_agent": _user_agent})

            # Check for unusual request patterns
            query_params = dict(request.query_params)
            if len(query_params) > 20:  # Too many parameters
                anomalies.append({"type": "excessive_parameters", "param_count": len(query_params)})

            if anomalies:
                return SafetyCheck(
                    check_name="anomaly_detection",
                    passed=False,
                    severity=SafetyLevel.MEDIUM,
                    details={"anomalies": anomalies},
                    timestamp=datetime.now(UTC),
                    recommendations=["Implement rate limiting", "Add bot detection", "Review suspicious patterns"],
                )

            return SafetyCheck(
                check_name="anomaly_detection",
                passed=True,
                severity=SafetyLevel.LOW,
                details={"checked_patterns": ["user_agent", "parameters"]},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            return SafetyCheck(
                check_name="anomaly_detection",
                passed=False,
                severity=SafetyLevel.LOW,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    async def _extract_request_content(self, request: Any) -> str:
        """Extract content from request for analysis."""
        try:
            if hasattr(request, "body"):
                body = await request.body()
                return body.decode("utf-8", errors="ignore")
            return ""
        except Exception:
            return ""

    async def _log_safety_check(self, request: Any, checks: list[SafetyCheck], overall_safe: bool) -> None:
        """Log safety check results."""
        try:
            log_entry = {
                "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
                "request_path": request.url.path,
                "client_ip": getattr(request.client, "host", None) if request.client else None,
                "overall_safe": overall_safe,
                "checks": [
                    {"name": check.check_name, "passed": check.passed, "severity": check.severity.value}
                    for check in checks
                ],
            }

            self.audit_log.append(log_entry)

            # Keep audit log size manageable
            if len(self.audit_log) > 10000:
                self.audit_log = self.audit_log[-5000:]

        except Exception as e:
            logger.error(f"Error logging safety check: {str(e)}")

    async def monitor_safety(self):
        """Continuous safety monitoring task."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Analyze recent safety checks for patterns
                recent_checks = [
                    check
                    for check in self.safety_checks
                    if (datetime.now(datetime.timezone.utc) - check.timestamp) < timedelta(hours=1)
                ]

                if recent_checks:
                    failed_checks = [check for check in recent_checks if not check.passed]
                    failure_rate = len(failed_checks) / len(recent_checks)

                    if failure_rate > 0.1:  # More than 10% failures
                        logger.warning(f"High safety check failure rate: {failure_rate:.2%}")

                        if self.monitoring:
                            await self.monitoring.record_security_event(
                                "high_safety_failure_rate",
                                {"failure_rate": failure_rate, "total_checks": len(recent_checks)},
                                "WARNING",
                            )

            except Exception as e:
                logger.error(f"Safety monitoring error: {str(e)}")
                await asyncio.sleep(60)

    def get_safety_report(self) -> dict[str, Any]:
        """Generate safety and compliance report."""
        recent_checks = [
            check
            for check in self.safety_checks
            if (datetime.now(datetime.timezone.utc) - check.timestamp) < timedelta(days=7)
        ]

        return {
            "total_checks": len(recent_checks),
            "passed_checks": len([c for c in recent_checks if c.passed]),
            "failed_checks": len([c for c in recent_checks if not c.passed]),
            "compliance_violations": len(self.compliance_violations),
            "safety_score": len([c for c in recent_checks if c.passed]) / len(recent_checks) if recent_checks else 1.0,
            "recent_audit_entries": len(self.audit_log[-100:]),
        }

    def get_compliance_violations(self, days: int = 30) -> list[dict[str, Any]]:
        """Get compliance violations from the last N days."""
        cutoff = datetime.now(datetime.timezone.utc) - timedelta(days=days)
        return [violation for violation in self.compliance_violations if violation["timestamp"] > cutoff]
