import os
import sys
import json
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path("src")))

from tools.security.vulnerability_scanner import VulnerabilityScanner, VulnerabilitySeverity

def main():
    scanner = VulnerabilityScanner()
    # Scan only relevant files/directories for efficiency or scan all
    print("Running Security Verification Scan...")
    results = scanner.scan_path(Path("src"))
    vulnerabilities = results.vulnerabilities

    # Filter and categorize
    findings = [v.to_dict() for v in vulnerabilities]

    summary = {
        "critical": len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL]),
        "high": len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH]),
        "medium": len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM]),
        "low": len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.LOW]),
    }

    report = {
        "summary": summary,
        "findings": findings
    }

    os.makedirs("reports/security/findings", exist_ok=True)
    report_path = "reports/security/findings/remediation_final_verify.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Scan complete. Report saved to {report_path}")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    main()
