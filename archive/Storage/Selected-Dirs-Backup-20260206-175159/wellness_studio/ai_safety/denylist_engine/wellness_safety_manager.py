#!/usr/bin/env python3
"""
Wellness Studio Safety-Aware Server Manager
Specialized denylist management for healthcare AI safety requirements
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys

# Add parent scripts path
_scripts_path = Path(__file__).parent.parent.parent.parent / "scripts"
if _scripts_path.exists():
    sys.path.insert(0, str(_scripts_path))

from safety_aware_server_manager import SafetyAwareServerManager  # type: ignore
from init_safety_logging import (  # type: ignore
    SafetyLogger,
    EventType,
    Severity,
    create_safety_event,
    calculate_safety_score,
    determine_risk_level,
)


class WellnessSafetyManager(SafetyAwareServerManager):
    """
    Wellness Studio-specific safety manager with healthcare compliance features

    Additional features:
    - PHI/HIPAA awareness in logging
    - Healthcare-specific server categories
    - Patient data flow tracing
    - Clinical decision support safety checks
    """

    # Healthcare-specific high-risk categories
    HEALTHCARE_CRITICAL_CATEGORIES = [
        "patient-data-processor",
        "clinical-decision-support",
        "medication-dispenser",
        "vitals-monitor",
        "ehr-integration",
    ]

    def __init__(self, config_path: str, safety_log_dir: Optional[str] = None):
        # Use wellness_studio ai_safety logs by default
        if safety_log_dir is None:
            safety_log_dir = str(Path(__file__).parent.parent / "logs")

        super().__init__(config_path, safety_log_dir)

        # Healthcare compliance settings
        self.phi_redaction_enabled = True
        self.audit_all_access = True

    def is_denied(self, server_name: str) -> tuple[bool, str]:
        """Enhanced denial check with healthcare compliance logging"""
        is_denied, reason = super().is_denied(server_name)

        # Additional healthcare-specific checks
        server = self.get_server(server_name)
        if server and server.category in self.HEALTHCARE_CRITICAL_CATEGORIES:
            # Always log access to healthcare-critical servers
            if self.safety_logger:
                event = create_safety_event(
                    event_type=EventType.SAFETY_BOUNDARY_ENFORCED,
                    severity=Severity.WARNING if is_denied else Severity.INFO,
                    server_name=server_name,
                    denylist_reason=reason,
                    context={
                        "healthcare_critical": True,
                        "category": server.category,
                        "action": "access_check",
                        "phi_redacted": self.phi_redaction_enabled,
                    },
                )
                self.safety_logger.log_event(event)

        return is_denied, reason

    def audit_server_access(self, server_name: str, user_context: Optional[Dict[str, Any]] = None):
        """Audit healthcare server access for compliance"""
        if not self.safety_logger:
            return

        # Redact PHI if enabled
        if self.phi_redaction_enabled and user_context:
            user_context = self._redact_phi(user_context)

        event = create_safety_event(
            event_type=EventType.RULE_EVALUATED,
            severity=Severity.INFO,
            server_name=server_name,
            context={
                "audit_type": "server_access",
                "timestamp": datetime.now().isoformat(),
                "user_context": user_context or {},
            },
        )
        self.safety_logger.log_event(event)

    def check_clinical_safety(self, server_name: str) -> Dict:
        """Check clinical safety requirements for a server"""
        server = self.get_server(server_name)
        is_denied, reason = self.is_denied(server_name)

        safety_assessment = {
            "server": server_name,
            "is_denied": is_denied,
            "denial_reason": reason,
            "healthcare_critical": False,
            "clinical_safety_score": 1.0,
            "risk_level": "low",
            "recommendations": [],
        }

        if server:
            # Check if healthcare-critical
            if server.category in self.HEALTHCARE_CRITICAL_CATEGORIES:
                safety_assessment["healthcare_critical"] = True
                safety_assessment["clinical_safety_score"] = 0.5  # Higher scrutiny
                safety_assessment["risk_level"] = "high"
                safety_assessment["recommendations"].append(
                    "Requires additional review for patient safety"
                )

            # Check resource profile for critical systems
            if server.resource_profile in ["high", "critical"]:
                safety_assessment["recommendations"].append(
                    "High resource usage - monitor for availability"
                )

            # Check network dependency for clinical systems
            if (
                server.requires_network
                and server.category in self.HEALTHCARE_CRITICAL_CATEGORIES
            ):
                safety_assessment["recommendations"].append(
                    "Network-dependent clinical system - ensure failover"
                )

        if reason:
            safety_score = calculate_safety_score(reason)
            safety_assessment["clinical_safety_score"] = safety_score
            safety_assessment["risk_level"] = determine_risk_level(safety_score)

        return safety_assessment

    def generate_hipaa_audit_report(self) -> str:
        """Generate HIPAA-compliant audit report"""
        report_lines = [
            "=" * 80,
            "WELLNESS STUDIO - HIPAA COMPLIANCE AUDIT REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            "",
            "SERVER INVENTORY AUDIT",
            "-" * 40,
        ]

        for server in self.inventory:
            is_denied, reason = self.is_denied(server.name)
            clinical_check = self.check_clinical_safety(server.name)

            status = "DENIED" if is_denied else "ACTIVE"
            report_lines.append(f"\nServer: {server.name}")
            report_lines.append(f"  Status: {status}")
            report_lines.append(f"  Category: {server.category}")
            report_lines.append(
                f"  Healthcare Critical: {clinical_check['healthcare_critical']}"
            )
            report_lines.append(
                f"  Clinical Safety Score: {clinical_check['clinical_safety_score']:.2f}"
            )
            report_lines.append(f"  Risk Level: {clinical_check['risk_level'].upper()}")

            if clinical_check["recommendations"]:
                report_lines.append("  Recommendations:")
                for rec in clinical_check["recommendations"]:
                    report_lines.append(f"    - {rec}")

        # Summary
        denied = self.get_denied_servers()
        allowed = self.get_allowed_servers()

        report_lines.extend(
            [
                "",
                "=" * 80,
                "SUMMARY",
                "=" * 80,
                f"Total Servers: {len(self.inventory)}",
                f"Denied/Blocked: {len(denied)}",
                f"Active/Allowed: {len(allowed)}",
                "",
                "COMPLIANCE STATUS: ENFORCED",
                "=" * 80,
            ]
        )

        return "\n".join(report_lines)

    def _redact_phi(self, data: Dict) -> Dict:
        """Redact potential PHI from data"""
        phi_keys = [
            "patient_id",
            "patient_name",
            "ssn",
            "dob",
            "date_of_birth",
            "medical_record",
            "mrn",
            "diagnosis",
            "medication",
            "address",
            "phone",
            "email",
            "insurance_id",
        ]

        redacted = {}
        for key, value in data.items():
            if any(phi_key in key.lower() for phi_key in phi_keys):
                redacted[key] = "[REDACTED-PHI]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_phi(value)
            else:
                redacted[key] = value

        return redacted


def main():
    """CLI for Wellness Studio Safety Manager"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Wellness Studio Safety-Aware Server Manager"
    )
    parser.add_argument("--config", required=True, help="Path to denylist config")
    parser.add_argument("--safety-logs", help="Path to safety log directory")
    parser.add_argument(
        "--report", action="store_true", help="Generate HIPAA audit report"
    )
    parser.add_argument("--check", help="Check clinical safety for a server")

    args = parser.parse_args()

    manager = WellnessSafetyManager(args.config, args.safety_logs)

    if args.report:
        print(manager.generate_hipaa_audit_report())

    if args.check:
        assessment = manager.check_clinical_safety(args.check)
        print(f"\nClinical Safety Assessment: {args.check}")
        print("-" * 40)
        for key, value in assessment.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
