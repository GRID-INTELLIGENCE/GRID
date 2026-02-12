"""
CI/CD Integration for Guardrail System

Provides integration with CI/CD pipelines for automated guardrail checks.
Supports GitHub Actions, GitLab CI, Azure DevOps, and generic CI systems.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class CICDReporter:
    """Reporter for CI/CD integration."""
    
    def __init__(self, output_format: str = "auto"):
        """
        Initialize CI/CD reporter.
        
        Args:
            output_format: "auto" (detect from env), "github", "gitlab", 
                          "azure", "junit", or "json"
        """
        self.format = output_format if output_format != "auto" else self._detect_ci()
        self.violations: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        
    def _detect_ci(self) -> str:
        """Detect which CI system we're running in."""
        import os
        
        if os.getenv("GITHUB_ACTIONS"):
            return "github"
        elif os.getenv("GITLAB_CI"):
            return "gitlab"
        elif os.getenv("AZURE_PIPELINES"):
            return "azure"
        elif os.getenv("JENKINS_URL"):
            return "jenkins"
        else:
            return "json"
            
    def add_violation(self, violation: Dict[str, Any]) -> None:
        """Add a violation to the report."""
        self.violations.append(violation)
        
    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set metrics for the report."""
        self.metrics = metrics
        
    def generate_report(self) -> str:
        """Generate report in the appropriate format."""
        if self.format == "github":
            return self._generate_github_report()
        elif self.format == "gitlab":
            return self._generate_gitlab_report()
        elif self.format == "azure":
            return self._generate_azure_report()
        elif self.format == "junit":
            return self._generate_junit_report()
        else:
            return self._generate_json_report()
            
    def _generate_github_report(self) -> str:
        """Generate GitHub Actions workflow commands."""
        output = []
        
        # Group by severity
        by_severity = {}
        for v in self.violations:
            sev = v.get("severity", "unknown")
            by_severity.setdefault(sev, []).append(v)
            
        # Output annotations for errors and warnings
        for severity in ["critical", "high", "medium"]:
            for violation in by_severity.get(severity, []):
                file_path = violation.get("file", "")
                line = violation.get("line", 1)
                message = violation.get("message", "Unknown issue")
                vtype = violation.get("type", "unknown")
                
                # GitHub Actions annotation format
                if severity in ["critical", "high"]:
                    output.append(f"::error file={file_path},line={line}::{vtype}: {message}")
                else:
                    output.append(f"::warning file={file_path},line={line}::{vtype}: {message}")
                    
        # Summary
        total = len(self.violations)
        critical = len(by_severity.get("critical", []))
        high = len(by_severity.get("high", []))
        
        output.append(f"\n## Guardrail Summary")
        output.append(f"- Total violations: {total}")
        output.append(f"- Critical: {critical}")
        output.append(f"- High: {high}")
        output.append(f"- Medium: {len(by_severity.get('medium', []))}")
        output.append(f"- Low: {len(by_severity.get('low', []))}")
        
        if critical > 0:
            output.append(f"\n::error::Found {critical} critical violation(s)")
            
        return "\n".join(output)
        
    def _generate_gitlab_report(self) -> str:
        """Generate GitLab CI code quality report."""
        # GitLab code quality report format (JSON)
        report = []
        
        for violation in self.violations:
            report.append({
                "description": violation.get("message", ""),
                "check_name": violation.get("type", "unknown"),
                "fingerprint": f"{violation.get('file', '')}:{violation.get('line', 0)}:{violation.get('type', '')}",
                "severity": self._map_severity(violation.get("severity", "unknown")),
                "location": {
                    "path": violation.get("file", ""),
                    "lines": {
                        "begin": violation.get("line", 1)
                    }
                }
            })
            
        return json.dumps(report, indent=2)
        
    def _generate_azure_report(self) -> str:
        """Generate Azure DevOps logging commands."""
        output = []
        
        for violation in self.violations:
            severity = violation.get("severity", "unknown")
            file_path = violation.get("file", "")
            line = violation.get("line", 1)
            message = violation.get("message", "")
            vtype = violation.get("type", "unknown")
            
            # Azure logging format
            if severity in ["critical", "high"]:
                output.append(f"##vso[task.logissue type=error;sourcepath={file_path};linenumber={line};code={vtype};]{message}")
            else:
                output.append(f"##vso[task.logissue type=warning;sourcepath={file_path};linenumber={line};code={vtype};]{message}")
                
        # Set task result
        critical_count = sum(1 for v in self.violations if v.get("severity") == "critical")
        if critical_count > 0:
            output.append(f"##vso[task.complete result=Failed;]Found {critical_count} critical violations")
            
        return "\n".join(output)
        
    def _generate_junit_report(self) -> str:
        """Generate JUnit XML report for test integration."""
        import xml.etree.ElementTree as ET
        
        # Create root element
        testsuites = ET.Element("testsuites")
        testsuite = ET.SubElement(testsuites, "testsuite", {
            "name": "Guardrail Checks",
            "tests": str(len(self.violations)),
            "failures": str(sum(1 for v in self.violations if v.get("severity") in ["critical", "high"])),
            "errors": "0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Add each violation as a test case
        for violation in self.violations:
            testcase = ET.SubElement(testsuite, "testcase", {
                "name": f"{violation.get('type', 'unknown')} - {violation.get('file', 'unknown')}",
                "classname": violation.get("module", "unknown"),
                "time": "0"
            })
            
            if violation.get("severity") in ["critical", "high"]:
                failure = ET.SubElement(testcase, "failure", {
                    "message": violation.get("message", ""),
                    "type": violation.get("severity", "")
                })
                failure.text = violation.get("suggestion", "")
                
        return ET.tostring(testsuites, encoding='unicode')
        
    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "format": "guardrail-ci-report",
            "version": "1.0",
            "summary": {
                "total_violations": len(self.violations),
                "by_severity": self._count_by_severity(),
                "by_type": self._count_by_type()
            },
            "violations": self.violations,
            "metrics": self.metrics
        }
        
        return json.dumps(report, indent=2)
        
    def _map_severity(self, severity: str) -> str:
        """Map internal severity to GitLab severity."""
        mapping = {
            "critical": "blocker",
            "high": "critical",
            "medium": "major",
            "low": "minor"
        }
        return mapping.get(severity, "info")
        
    def _count_by_severity(self) -> Dict[str, int]:
        """Count violations by severity."""
        counts = {}
        for v in self.violations:
            sev = v.get("severity", "unknown")
            counts[sev] = counts.get(sev, 0) + 1
        return counts
        
    def _count_by_type(self) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for v in self.violations:
            vtype = v.get("type", "unknown")
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
        
    def should_fail_build(self) -> bool:
        """Determine if the build should fail based on violations."""
        critical_count = sum(1 for v in self.violations if v.get("severity") == "critical")
        high_count = sum(1 for v in self.violations if v.get("severity") == "high")
        
        # Fail on critical, or more than 5 high
        return critical_count > 0 or high_count > 5


# Configuration templates for CI systems
GITHUB_ACTION_TEMPLATE = """
name: Guardrail Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  guardrail:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run Guardrail checks
      run: |
        python -m guardrails.ci.run_checks --format github
      continue-on-error: true
    
    - name: Upload report
      uses: actions/upload-artifact@v3
      with:
        name: guardrail-report
        path: guardrail-report.json
"""

GITLAB_CI_TEMPLATE = """
guardrail-checks:
  stage: test
  script:
    - python -m guardrails.ci.run_checks --format gitlab --output gl-code-quality-report.json
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
    paths:
      - gl-code-quality-report.json
  allow_failure: true
"""

AZURE_DEVOPS_TEMPLATE = """
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.10'
  displayName: 'Use Python 3.10'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  displayName: 'Install dependencies'

- script: |
    python -m guardrails.ci.run_checks --format azure
  displayName: 'Run Guardrail checks'
  continueOnError: true
"""


def write_ci_config(ci_system: str, output_path: str) -> None:
    """Write CI configuration template to file."""
    templates = {
        "github": GITHUB_ACTION_TEMPLATE,
        "gitlab": GITLAB_CI_TEMPLATE,
        "azure": AZURE_DEVOPS_TEMPLATE
    }
    
    template = templates.get(ci_system)
    if not template:
        raise ValueError(f"Unknown CI system: {ci_system}")
        
    with open(output_path, 'w') as f:
        f.write(template.strip())
        
    print(f"CI configuration written to: {output_path}")


# Main runner for CI execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Guardrail CI Integration")
    parser.add_argument("--format", choices=["github", "gitlab", "azure", "junit", "json", "auto"],
                     default="auto", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--generate-config", choices=["github", "gitlab", "azure"],
                       help="Generate CI configuration template")
    
    args = parser.parse_args()
    
    if args.generate_config:
        output_file = {
            "github": ".github/workflows/guardrail.yml",
            "gitlab": ".gitlab-ci.yml",
            "azure": "azure-pipelines.yml"
        }[args.generate_config]
        write_ci_config(args.generate_config, output_file)
        sys.exit(0)
        
    # Run checks and generate report
    reporter = CICDReporter(args.format)
    
    # TODO: Actually run guardrail checks here
    # For now, just demonstrate the reporter
    
    # Example violations
    reporter.add_violation({
        "type": "hardcoded_path",
        "severity": "high",
        "message": "Hardcoded path detected: E:/grid/logs",
        "file": "src/module.py",
        "line": 15,
        "suggestion": "Use environment variable"
    })
    
    reporter.add_violation({
        "type": "conditional_import",
        "severity": "medium",
        "message": "Conditional import of torch",
        "file": "src/ml.py",
        "line": 5,
        "suggestion": "Add to requirements.txt"
    })
    
    report = reporter.generate_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)
        
    # Exit with appropriate code
    sys.exit(1 if reporter.should_fail_build() else 0)
