#!/usr/bin/env python3
"""
AI Safety Integration for Server Denylist System
Structured logging and monitoring with safety tracing
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Safety event types"""

    SERVER_DENIED = "server_denied"
    SERVER_ALLOWED = "server_allowed"
    RULE_EVALUATED = "rule_evaluated"
    CONFIG_SANITIZED = "config_sanitized"
    VIOLATION_DETECTED = "violation_detected"
    SAFETY_BOUNDARY_ENFORCED = "safety_boundary_enforced"


class Severity(Enum):
    """Event severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskLevel(Enum):
    """Risk level classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyEvent:
    """AI Safety event structure"""

    timestamp: str
    event_type: str
    severity: str
    trace_id: str
    server_name: str | None = None
    denylist_reason: str | None = None
    safety_score: float | None = None
    risk_level: str | None = None
    context: dict | None = None
    metadata: dict | None = None
    parent_trace_id: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class SafetyLogger:
    """Structured safety logging system"""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different log types
        (self.log_dir / "enforcement").mkdir(exist_ok=True)
        (self.log_dir / "violation").mkdir(exist_ok=True)
        (self.log_dir / "metrics").mkdir(exist_ok=True)
        (self.log_dir / "audit").mkdir(exist_ok=True)

        # Initialize metrics
        self.metrics = DenylistSafetyMetrics()

    def log_event(self, event: SafetyEvent):
        """Log a safety event"""
        # Determine log file based on event type
        if event.event_type in [EventType.SERVER_DENIED.value, EventType.SERVER_ALLOWED.value]:
            log_file = self.log_dir / "enforcement" / f"enforcement_{datetime.now():%Y%m%d}.jsonl"
        elif event.event_type == EventType.VIOLATION_DETECTED.value:
            log_file = self.log_dir / "violation" / f"violation_{datetime.now():%Y%m%d}.jsonl"
        else:
            log_file = self.log_dir / "audit" / f"audit_{datetime.now():%Y%m%d}.jsonl"

        # Append to log file (JSONL format)
        with open(log_file, "a") as f:
            f.write(event.to_json() + "\n")

        # Update metrics
        if event.event_type == EventType.SERVER_DENIED.value:
            self.metrics.record_denial(
                event.server_name or "unknown", event.denylist_reason or "unknown", event.safety_score or 0.0
            )

        # Log to standard logger
        log_level = getattr(logging, event.severity.upper(), logging.INFO)
        logger.log(log_level, f"{event.event_type}: {event.server_name} - {event.denylist_reason}")

    def save_metrics(self):
        """Save current metrics snapshot"""
        metrics_file = self.log_dir / "metrics" / f"metrics_{datetime.now():%Y%m%d_%H%M%S}.json"
        summary = self.metrics.get_summary()

        with open(metrics_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Metrics saved to {metrics_file}")
        return summary


class DenylistSafetyMetrics:
    """Safety metrics tracking"""

    def __init__(self):
        self.metrics = {
            "total_evaluations": 0,
            "denials_by_reason": {},
            "safety_scores": [],
            "high_risk_servers": [],
            "configuration_sanitizations": 0,
            "violation_detections": 0,
        }

    def record_denial(self, server: str, reason: str, safety_score: float):
        """Record a server denial event"""
        self.metrics["total_evaluations"] += 1
        self.metrics["denials_by_reason"][reason] = self.metrics["denials_by_reason"].get(reason, 0) + 1
        self.metrics["safety_scores"].append(safety_score)

        if safety_score < 0.5:
            self.metrics["high_risk_servers"].append(
                {"server": server, "reason": reason, "score": safety_score, "timestamp": datetime.now().isoformat()}
            )

    def get_summary(self) -> dict:
        """Get safety metrics summary"""
        total = self.metrics["total_evaluations"]
        scores = self.metrics["safety_scores"]

        return {
            "timestamp": datetime.now().isoformat(),
            "total_evaluations": total,
            "total_denials": len(scores),
            "denial_rate": len(scores) / max(1, total),
            "average_safety_score": sum(scores) / max(1, len(scores)),
            "min_safety_score": min(scores) if scores else 0.0,
            "max_safety_score": max(scores) if scores else 1.0,
            "high_risk_count": len(self.metrics["high_risk_servers"]),
            "denials_by_reason": self.metrics["denials_by_reason"],
            "high_risk_servers": self.metrics["high_risk_servers"],
        }


def calculate_safety_score(reason: str) -> float:
    """Calculate safety score based on denylist reason"""
    risk_weights = {
        "startup-failure": 0.9,
        "security-concern": 1.0,
        "missing-dependencies": 0.7,
        "resource-intensive": 0.6,
        "network-dependent": 0.5,
        "deprecated": 0.4,
        "redundant": 0.3,
        "development-only": 0.2,
        "user-disabled": 0.1,
    }

    # Higher score = higher risk (inverse of safety)
    risk_score = risk_weights.get(reason, 0.5)
    safety_score = 1.0 - risk_score

    return safety_score


def determine_risk_level(safety_score: float) -> str:
    """Determine risk level from safety score"""
    if safety_score >= 0.7:
        return RiskLevel.LOW.value
    elif safety_score >= 0.4:
        return RiskLevel.MEDIUM.value
    elif safety_score >= 0.2:
        return RiskLevel.HIGH.value
    else:
        return RiskLevel.CRITICAL.value


def generate_trace_id() -> str:
    """Generate unique trace ID"""
    import uuid

    return str(uuid.uuid4())


def create_safety_event(
    event_type: EventType,
    severity: Severity,
    server_name: str | None = None,
    denylist_reason: str | None = None,
    context: dict | None = None,
    metadata: dict | None = None,
    parent_trace_id: str | None = None,
) -> SafetyEvent:
    """Create a safety event with calculated safety metrics"""

    safety_score = None
    risk_level = None

    if denylist_reason:
        safety_score = calculate_safety_score(denylist_reason)
        risk_level = determine_risk_level(safety_score)

    return SafetyEvent(
        timestamp=datetime.now().isoformat(),
        event_type=event_type.value,
        severity=severity.value,
        trace_id=generate_trace_id(),
        server_name=server_name,
        denylist_reason=denylist_reason,
        safety_score=safety_score,
        risk_level=risk_level,
        context=context or {},
        metadata=metadata or {},
        parent_trace_id=parent_trace_id,
    )


def init_safety_logging(target_dir: str):
    """Initialize safety logging infrastructure"""
    logger.info("Initializing AI Safety logging infrastructure...")

    target = Path(target_dir)

    # Create directory structure
    dirs = [
        target / "logs" / "enforcement",
        target / "logs" / "violation",
        target / "logs" / "safety_metrics",
        target / "logs" / "audit",
        target / "monitoring",
        target / "config",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

    # Create safety logger instance
    safety_logger = SafetyLogger(target / "logs")

    # Log initialization event
    event = create_safety_event(
        event_type=EventType.CONFIG_SANITIZED,
        severity=Severity.INFO,
        context={"action": "safety_logging_initialized", "target_directory": str(target)},
    )
    safety_logger.log_event(event)

    logger.info(f"✓ AI Safety logging initialized at: {target}")

    return safety_logger


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize AI Safety logging for Server Denylist System")
    parser.add_argument("--target", required=True, help="Target directory for safety logging")

    args = parser.parse_args()

    safety_logger = init_safety_logging(args.target)

    # Generate sample metrics
    print("\n" + "=" * 80)
    print("SAFETY LOGGING INITIALIZED")
    print("=" * 80)
    print(f"\nLog Directory: {Path(args.target) / 'logs'}")
    print("\nLog Structure:")
    print("  ├── enforcement/     - Server denial/allow decisions")
    print("  ├── violation/       - Policy violation events")
    print("  ├── safety_metrics/  - Aggregated safety metrics")
    print("  └── audit/           - Complete audit trail")
    print("\n" + "=" * 80)
