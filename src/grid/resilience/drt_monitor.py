#!/usr/bin/env python3
"""
DRT (Don't Repeat Themselves) Behavioral Pattern Monitoring System
Detects endpoint behavioral similarities to previous attack vectors and escalates protections
"""

import hashlib
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from grid.resilience.data_corruption_penalty import (
    CorruptionSeverity,
    CorruptionType,
    record_corruption_event,
)

logger = logging.getLogger(__name__)


class BehavioralFingerprint:
    """Represents a behavioral fingerprint of an endpoint interaction."""

    def __init__(self, endpoint: str, method: str, client_ip: str, user_agent: str = ""):
        self.endpoint = endpoint
        self.method = method.upper()
        self.client_ip = client_ip
        self.user_agent = user_agent
        self.timestamp = datetime.utcnow()
        self.features = self._extract_features()

    def _extract_features(self) -> dict[str, Any]:
        """Extract behavioral features from the interaction."""
        return {
            "endpoint_hash": hashlib.md5(self.endpoint.encode()).hexdigest()[:8],
            "method": self.method,
            "ip_prefix": ".".join(self.client_ip.split(".")[:3]) if self.client_ip != "unknown" else "unknown",
            "user_agent_family": self._categorize_user_agent(),
            "time_of_day": self.timestamp.hour,
            "day_of_week": self.timestamp.weekday(),
        }

    def _categorize_user_agent(self) -> str:
        """Categorize user agent into families."""
        ua = self.user_agent.lower()
        if "mozilla" in ua and "chrome" in ua:
            return "chrome"
        elif "mozilla" in ua and "firefox" in ua:
            return "firefox"
        elif "safari" in ua and "chrome" not in ua:
            return "safari"
        elif "postman" in ua:
            return "postman"
        elif "curl" in ua:
            return "curl"
        elif "python" in ua:
            return "python"
        else:
            return "other"

    def to_vector(self) -> np.ndarray:
        """Convert fingerprint to numerical vector for similarity calculation."""
        # Convert categorical features to numerical
        method_map = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3, "PATCH": 4, "HEAD": 5, "OPTIONS": 6}
        ua_map = {"chrome": 0, "firefox": 1, "safari": 2, "postman": 3, "curl": 4, "python": 5, "other": 6}

        return np.array(
            [
                hash(self.endpoint) % 1000,  # Endpoint hash
                method_map.get(self.method, 7),  # HTTP method
                hash(self.features["ip_prefix"]) % 100,  # IP prefix hash
                ua_map.get(self.features["user_agent_family"], 7),  # User agent
                self.features["time_of_day"],  # Hour of day
                self.features["day_of_week"],  # Day of week
            ]
        )

    def calculate_similarity(self, other: "BehavioralFingerprint") -> float:
        """Calculate similarity score with another fingerprint."""
        vec1 = self.to_vector()
        vec2 = other.to_vector()

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class AttackVectorDatabase:
    """Database of known attack vector patterns."""

    def __init__(self):
        self.attack_vectors: list[BehavioralFingerprint] = []
        self.attack_patterns: dict[str, list[BehavioralFingerprint]] = defaultdict(list)
        self.threat_levels: dict[str, str] = {}

    def add_attack_vector(self, fingerprint: BehavioralFingerprint, attack_type: str, severity: str):
        """Add a known attack vector pattern."""
        self.attack_vectors.append(fingerprint)
        self.attack_patterns[attack_type].append(fingerprint)
        self.threat_levels[attack_type] = severity

    def find_similar_attacks(self, fingerprint: BehavioralFingerprint, threshold: float = 0.8) -> list[dict[str, Any]]:
        """Find attack vectors similar to the given fingerprint."""
        similar_attacks = []

        for attack_vector in self.attack_vectors:
            similarity = fingerprint.calculate_similarity(attack_vector)
            if similarity >= threshold:
                # Find the attack type for this vector
                attack_type = None
                for atype, vectors in self.attack_patterns.items():
                    if attack_vector in vectors:
                        attack_type = atype
                        break

                similar_attacks.append(
                    {
                        "attack_type": attack_type,
                        "similarity_score": similarity,
                        "threat_level": self.threat_levels.get(attack_type, "unknown"),
                        "timestamp": attack_vector.timestamp.isoformat(),
                    }
                )

        return sorted(similar_attacks, key=lambda x: x["similarity_score"], reverse=True)


class ProtectionEscalationEngine:
    """Engine for escalating protections when attack patterns are detected."""

    def __init__(self):
        self.escalated_endpoints: dict[str, dict[str, Any]] = {}
        self.websocket_overheads: dict[str, set[str]] = defaultdict(set)

    def escalate_endpoint(self, endpoint: str, attack_type: str, similarity_score: float, threat_level: str):
        """Escalate protections for an endpoint."""

        escalation_config = {
            "attack_type": attack_type,
            "similarity_score": similarity_score,
            "threat_level": threat_level,
            "escalation_time": datetime.utcnow().isoformat(),
            "architectural_hardening": self._apply_architectural_hardening(endpoint),
            "api_enforcement": self._apply_api_enforcement(endpoint),
            "websocket_overhead": self._apply_websocket_overhead(endpoint),
        }

        self.escalated_endpoints[endpoint] = escalation_config

        logger.warning(f"Protection escalation applied to endpoint {endpoint}")
        logger.warning(f"Attack type: {attack_type}, Threat level: {threat_level}, Similarity: {similarity_score:.3f}")

        # Record in corruption penalty system
        record_corruption_event(
            endpoint=endpoint,
            severity=CorruptionSeverity.CRITICAL if threat_level == "critical" else CorruptionSeverity.HIGH,
            corruption_type=CorruptionType.SECURITY,
            description=f"Behavioral similarity to attack vector '{attack_type}' detected. Protections escalated.",
            correlation_id=f"escalation_{endpoint}_{datetime.utcnow().timestamp()}",
            affected_resources=[endpoint, "security_infrastructure"],
            metadata={
                "attack_type": attack_type,
                "similarity_score": similarity_score,
                "threat_level": threat_level,
                "escalation_applied": True,
            },
        )

        return escalation_config

    def _apply_architectural_hardening(self, endpoint: str) -> dict[str, Any]:
        """Apply architectural hardening measures."""
        return {
            "rate_limiting_multiplier": 0.5,  # 50% of normal rate
            "circuit_breaker_enabled": True,
            "request_queueing": True,
            "fail_fast_mode": True,
            "isolation_level": "strict",
        }

    def _apply_api_enforcement(self, endpoint: str) -> dict[str, Any]:
        """Apply API enforcement measures."""
        return {
            "strict_validation": True,
            "schema_enforcement": True,
            "authentication_boost": True,  # Require stronger auth
            "audit_logging": True,
            "response_filtering": True,
            "request_sanitization": True,
        }

    def _apply_websocket_overhead(self, endpoint: str) -> dict[str, Any]:
        """Apply unique WebSocket overhead for suspicious endpoints."""
        overhead_id = f"ws_overhead_{hash(endpoint + str(datetime.utcnow())) % 10000}"

        # Generate unique overhead measures
        overhead_measures = {
            "overhead_id": overhead_id,
            "message_encryption": True,
            "connection_pinning": True,
            "heartbeat_frequency": 10,  # seconds
            "message_validation": True,
            "traffic_shaping": True,
            "anomaly_detection": True,
            "session_isolation": True,
        }

        self.websocket_overheads[endpoint].add(overhead_id)

        return overhead_measures

    def get_endpoint_escalation(self, endpoint: str) -> dict[str, Any] | None:
        """Get current escalation status for an endpoint."""
        return self.escalated_endpoints.get(endpoint)

    def is_endpoint_escalated(self, endpoint: str) -> bool:
        """Check if an endpoint has escalated protections."""
        return endpoint in self.escalated_endpoints

    def get_websocket_overheads(self, endpoint: str) -> set[str]:
        """Get WebSocket overhead IDs for an endpoint."""
        return self.websocket_overheads.get(endpoint, set())


class DRTMonitor:
    """DRT (Don't Repeat Themselves) monitoring system."""

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        retention_hours: int = 168,  # 7 days
        enforcement_mode: str = "monitor",
        escalation_timeout_minutes: int = 60,
    ):
        self.similarity_threshold = similarity_threshold
        self.retention_hours = retention_hours
        self.enforcement_mode = enforcement_mode
        self.escalation_timeout_minutes = escalation_timeout_minutes

        self.behavioral_history: dict[str, list[BehavioralFingerprint]] = defaultdict(list)
        self.attack_database = AttackVectorDatabase()
        self.escalation_engine = ProtectionEscalationEngine()

        # Initialize with known attack vectors
        self._initialize_attack_vectors()

    def _initialize_attack_vectors(self):
        """Initialize database with known attack vector patterns."""
        # Common attack patterns
        attack_patterns = [
            # SQL Injection attempts
            ("/api/v1/data/query", "POST", "malicious_ip", "python-requests", "sql_injection", "high"),
            ("/api/v1/search", "GET", "scanner_ip", "curl", "directory_traversal", "medium"),
            ("/api/v1/auth/login", "POST", "brute_force_ip", "postman", "credential_stuffing", "high"),
            ("/api/v1/upload", "POST", "malware_ip", "python", "malware_upload", "critical"),
            ("/api/v1/admin/config", "PUT", "admin_ip", "curl", "privilege_escalation", "critical"),
        ]

        for endpoint, method, ip, ua, attack_type, severity in attack_patterns:
            fingerprint = BehavioralFingerprint(endpoint, method, ip, ua)
            self.attack_database.add_attack_vector(fingerprint, attack_type, severity)

    def monitor_endpoint(
        self,
        endpoint: str,
        method: str,
        client_ip: str,
        user_agent: str = "",
        headers: dict | None = None,
        allow_escalation: bool | None = None,
    ) -> dict[str, Any]:
        """Monitor an endpoint interaction for behavioral patterns."""

        if allow_escalation is None:
            allow_escalation = self.enforcement_mode == "enforce"

        # Create behavioral fingerprint
        fingerprint = BehavioralFingerprint(endpoint, method, client_ip, user_agent)

        # Add to history
        self.behavioral_history[endpoint].append(fingerprint)

        # Clean old entries
        self._cleanup_old_entries(endpoint)

        # Check for attack vector similarities
        similar_attacks = self.attack_database.find_similar_attacks(fingerprint, self.similarity_threshold)

        monitoring_result = {
            "endpoint": endpoint,
            "fingerprint_created": True,
            "similar_attacks_detected": len(similar_attacks),
            "similar_attacks": similar_attacks,
            "escalation_applied": False,
            "current_escalation_level": "normal",
        }

        if similar_attacks:
            # Find the most similar attack
            top_attack = similar_attacks[0]

            # Check if endpoint is already escalated
            if allow_escalation:
                if not self.escalation_engine.is_endpoint_escalated(endpoint):
                    # Apply escalation
                    escalation_config = self.escalation_engine.escalate_endpoint(
                        endpoint=endpoint,
                        attack_type=top_attack["attack_type"],
                        similarity_score=top_attack["similarity_score"],
                        threat_level=top_attack["threat_level"],
                    )

                    monitoring_result["escalation_applied"] = True
                    monitoring_result["escalation_config"] = escalation_config
                    monitoring_result["current_escalation_level"] = "escalated"

                    logger.warning(
                        "DRT violation detected for %s: %s (similarity: %.3f)",
                        endpoint,
                        top_attack["attack_type"],
                        top_attack["similarity_score"],
                    )
                else:
                    monitoring_result["current_escalation_level"] = "already_escalated"
            else:
                monitoring_result["current_escalation_level"] = "monitor_only"

        return monitoring_result

    def cleanup_expired_escalations(self) -> int:
        """Clean up expired escalations based on timeout."""
        if self.escalation_timeout_minutes <= 0:
            return 0

        now = datetime.utcnow()
        expired = []
        for endpoint, config in self.escalation_engine.escalated_endpoints.items():
            escalation_time = config.get("escalation_time")
            if isinstance(escalation_time, str):
                try:
                    escalation_time_dt = datetime.fromisoformat(escalation_time)
                except ValueError:
                    escalation_time_dt = None
            else:
                escalation_time_dt = escalation_time if isinstance(escalation_time, datetime) else None

            if escalation_time_dt is None:
                continue

            if now - escalation_time_dt > timedelta(minutes=self.escalation_timeout_minutes):
                expired.append(endpoint)

        for endpoint in expired:
            del self.escalation_engine.escalated_endpoints[endpoint]

        return len(expired)

    def _cleanup_old_entries(self, endpoint: str):
        """Clean up old behavioral entries beyond retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

        self.behavioral_history[endpoint] = [
            fp for fp in self.behavioral_history[endpoint] if fp.timestamp >= cutoff_time
        ]

    def get_endpoint_behavior_summary(self, endpoint: str) -> dict[str, Any]:
        """Get behavioral summary for an endpoint."""
        fingerprints = self.behavioral_history.get(endpoint, [])

        if not fingerprints:
            return {"endpoint": endpoint, "behavior_count": 0}

        # Analyze behavioral patterns
        methods = Counter(fp.method for fp in fingerprints)
        user_agents = Counter(fp.features["user_agent_family"] for fp in fingerprints)
        hours = Counter(fp.features["time_of_day"] for fp in fingerprints)

        return {
            "endpoint": endpoint,
            "behavior_count": len(fingerprints),
            "time_range": {
                "oldest": min(fp.timestamp for fp in fingerprints).isoformat(),
                "newest": max(fp.timestamp for fp in fingerprints).isoformat(),
            },
            "method_distribution": dict(methods),
            "user_agent_distribution": dict(user_agents),
            "hourly_distribution": dict(hours),
            "escalated": self.escalation_engine.is_endpoint_escalated(endpoint),
            "websocket_overheads": list(self.escalation_engine.get_websocket_overheads(endpoint)),
        }

    def get_system_drt_status(self) -> dict[str, Any]:
        """Get overall DRT system status."""
        total_endpoints = len(self.behavioral_history)
        escalated_endpoints = sum(
            1 for endpoint in self.behavioral_history.keys() if self.escalation_engine.is_endpoint_escalated(endpoint)
        )

        return {
            "total_monitored_endpoints": total_endpoints,
            "escalated_endpoints": escalated_endpoints,
            "escalation_rate": escalated_endpoints / total_endpoints if total_endpoints > 0 else 0,
            "known_attack_vectors": len(self.attack_database.attack_vectors),
            "retention_hours": self.retention_hours,
            "similarity_threshold": self.similarity_threshold,
        }


# Singleton instance
drt_monitor = DRTMonitor()


def check_drt_violation(
    endpoint: str, method: str, client_ip: str, user_agent: str = "", headers: dict = None
) -> dict[str, Any]:
    """Check for DRT violations in endpoint behavior."""
    return drt_monitor.monitor_endpoint(endpoint, method, client_ip, user_agent, headers)


def get_drt_status() -> dict[str, Any]:
    """Get current DRT system status."""
    return drt_monitor.get_system_drt_status()


def get_endpoint_drt_summary(endpoint: str) -> dict[str, Any]:
    """Get DRT behavioral summary for an endpoint."""
    return drt_monitor.get_endpoint_behavior_summary(endpoint)
