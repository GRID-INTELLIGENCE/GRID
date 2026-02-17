#!/usr/bin/env python3
"""
GRID Prevention Framework
=========================

Systematic prevention system to future-proof the codebase.
Implements code hardening, policy enforcement, and continuous security validation.

Usage:
    python tools/prevention_framework.py --harden
    python tools/prevention_framework.py --policy <policy_file>
    python tools/prevention_framework.py --validate
    python tools/prevention_framework.py --monitor
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    
    name: str
    version: str
    description: str
    rules: list[dict] = field(default_factory=list)
    enforcement_level: str = "warn"  # warn, block, audit
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CodeFinding:
    """Security finding in code."""
    
    file: str
    line: int
    severity: str
    category: str
    message: str
    suggestion: str
    rule_id: str


class PreventionFramework:
    """Framework for systematic security prevention."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.policies_path = project_root / "config" / "security" / "policies"
        self.findings_path = project_root / "reports" / "security" / "findings"
        self.findings_path.mkdir(parents=True, exist_ok=True)
        
        # Security patterns to detect (regex avoids false positives)
        # Note: eval/exec are detected via AST only (_analyze_ast) to avoid docstring/blocklist false positives
        self.dangerous_patterns = {
            "subprocess_shell": {
                "pattern": r"subprocess\..*shell\s*=\s*True",
                "severity": "high",
                "message": "subprocess with shell=True - command injection risk",
                "suggestion": "Use shell=False and pass command as list",
            },
            "pickle_load": {
                "pattern": r"pickle\.load|pickle\.loads",
                "severity": "high",
                "message": "pickle.load() detected - deserialization vulnerability",
                "suggestion": "Use json or safe serialization alternatives",
            },
            "yaml_load": {
                "pattern": r"yaml\.load\([^)]*\)(?!.*Loader\s*=\s*SafeLoader)",
                "severity": "high",
                "message": "yaml.load() without SafeLoader - arbitrary code execution",
                "suggestion": "Use yaml.safe_load() or yaml.load(..., Loader=SafeLoader)",
            },
            "hardcoded_password": {
                "pattern": r'(password|passwd|pwd|secret|key|token)\s*=\s*["\'][^"\']{4,}["\']',
                "severity": "medium",
                "message": "Potential hardcoded credential",
                "suggestion": "Use secrets manager or environment variables",
            },
            "sql_string_concat": {
                # SQL keyword at start of f-string or with + concat; avoid prose ("Profile update failed")
                "pattern": r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b\s+.*[\+%].*[\"']|f[\"']\s*(?:SELECT|INSERT|UPDATE|DELETE)\s+",
                "severity": "high",
                "message": "SQL query string concatenation - injection risk",
                "suggestion": "Use parameterized queries or ORM",
            },
            "debug_mode": {
                "pattern": r"debug\s*=\s*True|DEBUG\s*=\s*True",
                "severity": "medium",
                "message": "Debug mode enabled",
                "suggestion": "Disable debug mode in production",
            },
            "disabled_verification": {
                "pattern": r"verify\s*=\s*False|verify_ssl\s*=\s*False",
                "severity": "medium",
                "message": "SSL/TLS verification disabled",
                "suggestion": "Enable certificate verification",
            },
        }
    
    def scan_codebase(self, path: Path | None = None) -> list[CodeFinding]:
        """Scan codebase for security issues."""
        if path is None:
            path = self.project_root / "src"
        
        findings = []
        
        for py_file in path.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8")
                file_findings = self._scan_file(py_file, content)
                findings.extend(file_findings)
            except Exception as e:
                print(f"Warning: Could not scan {py_file}: {e}")
        
        return findings
    
    def _scan_file(self, file_path: Path, content: str) -> list[CodeFinding]:
        """Scan a single file for security issues."""
        findings = []
        lines = content.split("\n")
        
        for rule_name, rule in self.dangerous_patterns.items():
            for line_num, line in enumerate(lines, 1):
                # Search only code part (before #) to avoid flagging comments
                code_part = line.split("#", 1)[0]
                if re.search(rule["pattern"], code_part, re.IGNORECASE):
                    finding = CodeFinding(
                        file=str(file_path.relative_to(self.project_root)),
                        line=line_num,
                        severity=rule["severity"],
                        category="security_pattern",
                        message=rule["message"],
                        suggestion=rule["suggestion"],
                        rule_id=rule_name,
                    )
                    findings.append(finding)
        
        # AST-based analysis for more complex patterns
        try:
            tree = ast.parse(content)
            ast_findings = self._analyze_ast(file_path, tree)
            findings.extend(ast_findings)
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return findings
    
    def _analyze_ast(self, file_path: Path, tree: ast.AST) -> list[CodeFinding]:
        """Analyze AST for security issues."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("pickle", "yaml", "marshal"):
                        findings.append(CodeFinding(
                            file=str(file_path.relative_to(self.project_root)),
                            line=node.lineno or 0,
                            severity="info",
                            category="import",
                            message=f"Import of {alias.name} - review for safe usage",
                            suggestion="Ensure safe serialization practices",
                            rule_id=f"import_{alias.name}",
                        ))
            
            # Check for function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec"):
                        findings.append(CodeFinding(
                            file=str(file_path.relative_to(self.project_root)),
                            line=node.lineno or 0,
                            severity="critical",
                            category="dangerous_call",
                            message=f"Call to {node.func.id}() detected",
                            suggestion="Refactor to avoid dynamic code execution",
                            rule_id=f"call_{node.func.id}",
                        ))
        
        return findings
    
    def harden_codebase(self, dry_run: bool = True) -> dict:
        """Apply automated hardening to codebase."""
        results = {
            "hardened_files": 0,
            "skipped_files": 0,
            "changes": [],
        }
        
        # Findings to auto-fix
        auto_fixable = ["debug_mode", "disabled_verification"]
        
        findings = self.scan_codebase()
        
        for finding in findings:
            if finding.rule_id in auto_fixable:
                if dry_run:
                    results["changes"].append({
                        "file": finding.file,
                        "line": finding.line,
                        "action": f"Would fix: {finding.message}",
                    })
                else:
                    # Apply fix
                    file_path = self.project_root / finding.file
                    if self._apply_fix(file_path, finding):
                        results["hardened_files"] += 1
                        results["changes"].append({
                            "file": finding.file,
                            "line": finding.line,
                            "action": f"Fixed: {finding.message}",
                        })
            else:
                results["skipped_files"] += 1
        
        return results
    
    def _apply_fix(self, file_path: Path, finding: CodeFinding) -> bool:
        """Apply automated fix to a finding."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            if finding.rule_id == "debug_mode":
                lines[finding.line - 1] = lines[finding.line - 1].replace(
                    "debug = True", "debug = False"
                ).replace(
                    "DEBUG = True", "DEBUG = False"
                )
            
            elif finding.rule_id == "disabled_verification":
                lines[finding.line - 1] = lines[finding.line - 1].replace(
                    "verify = False", "verify = True"
                ).replace(
                    "verify_ssl = False", "verify_ssl = True"
                )
            
            file_path.write_text("\n".join(lines), encoding="utf-8")
            return True
            
        except Exception as e:
            print(f"Failed to fix {file_path}:{finding.line}: {e}")
            return False
    
    def generate_security_policy(self, name: str = "default") -> SecurityPolicy:
        """Generate default security policy."""
        policy = SecurityPolicy(
            name=name,
            version="1.0.0",
            description=f"GRID Security Policy - {name}",
            enforcement_level="warn",
            rules=[
                {
                    "id": "no_eval_exec",
                    "description": "Prohibit eval() and exec() usage (enforced via AST in _analyze_ast)",
                    "severity": "critical",
                    "check": "ast",
                },
                {
                    "id": "safe_yaml",
                    "description": "Require SafeLoader for yaml.load",
                    "severity": "high",
                    "check": "pattern",
                    "pattern": r"yaml\.load\([^)]*\)(?!.*Loader\s*=\s*SafeLoader)",
                },
                {
                    "id": "no_shell",
                    "description": "Prohibit shell=True in subprocess",
                    "severity": "high",
                    "check": "pattern",
                    "pattern": r"subprocess\..*shell\s*=\s*True",
                },
                {
                    "id": "parameterized_sql",
                    "description": "Use parameterized queries",
                    "severity": "high",
                    "check": "pattern",
                    "pattern": r'(SELECT|INSERT|UPDATE|DELETE).*\+.*"|f".*(SELECT|INSERT|UPDATE|DELETE)',
                },
            ],
        )
        
        # Save policy
        self.policies_path.mkdir(parents=True, exist_ok=True)
        policy_file = self.policies_path / f"{name}.json"
        with open(policy_file, "w") as f:
            json.dump(policy.to_dict(), f, indent=2)
        
        return policy
    
    def validate_against_policy(self, policy_name: str = "default") -> list[CodeFinding]:
        """Validate codebase against security policy."""
        policy_file = self.policies_path / f"{policy_name}.json"
        
        if not policy_file.exists():
            print(f"Policy not found: {policy_name}")
            return []
        
        with open(policy_file) as f:
            policy = SecurityPolicy(**json.load(f))
        
        findings = self.scan_codebase()
        
        # Filter findings based on policy rules
        policy_violations = []
        for finding in findings:
            for rule in policy.rules:
                if finding.rule_id == rule["id"]:
                    policy_violations.append(finding)
                    break
        
        return policy_violations
    
    def generate_findings_report(self, findings: list[CodeFinding]) -> Path:
        """Generate report of security findings."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_file = self.findings_path / f"security_findings_{timestamp}.json"
        
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_findings": len(findings),
            "by_severity": {},
            "by_category": {},
            "findings": [asdict(f) for f in findings],
        }
        
        for finding in findings:
            sev = finding.severity
            report["by_severity"][sev] = report["by_severity"].get(sev, 0) + 1
            
            cat = finding.category
            report["by_category"][cat] = report["by_category"].get(cat, 0) + 1
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        return report_file
    
    def setup_continuous_monitoring(self) -> dict:
        """Setup continuous security monitoring."""
        config = {
            "scan_schedule": "daily",
            "scan_time": "02:00",
            "alert_threshold": "medium",
            "notification_channels": ["log", "webhook"],
            "auto_harden": False,
            "enabled_rules": list(self.dangerous_patterns.keys()),
        }
        
        config_path = self.project_root / "config" / "security" / "monitoring.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        return config


def main():
    parser = argparse.ArgumentParser(description="GRID Prevention Framework")
    parser.add_argument("--scan", action="store_true", help="Scan codebase for issues")
    parser.add_argument("--harden", action="store_true", help="Apply hardening fixes")
    parser.add_argument("--policy", metavar="NAME", help="Generate security policy")
    parser.add_argument("--validate", metavar="POLICY", help="Validate against policy")
    parser.add_argument("--setup", action="store_true", help="Setup continuous monitoring")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).resolve().parent.parent
    framework = PreventionFramework(project_root)
    
    if args.scan:
        print("🔍 Scanning codebase for security issues...")
        findings = framework.scan_codebase()
        
        if findings:
            print(f"\n⚠️ Found {len(findings)} security issues:")
            
            # Group by severity
            by_severity = {}
            for f in findings:
                by_severity.setdefault(f.severity, []).append(f)
            
            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity in by_severity:
                    print(f"\n{severity.upper()} ({len(by_severity[severity])}):")
                    for finding in by_severity[severity][:5]:  # Show first 5
                        print(f"  {finding.file}:{finding.line} - {finding.message}")
                    if len(by_severity[severity]) > 5:
                        print(f"  ... and {len(by_severity[severity]) - 5} more")
            
            # Generate report
            report_file = framework.generate_findings_report(findings)
            print(f"\n✓ Report saved: {report_file}")
        else:
            print("✅ No security issues found!")
    
    elif args.harden:
        dry_run = args.dry_run
        print(f"🔒 Hardening codebase{' (dry-run)' if dry_run else ''}...")
        results = framework.harden_codebase(dry_run=dry_run)
        
        print(f"\nResults:")
        print(f"  Files to harden: {results['hardened_files']}")
        print(f"  Files skipped: {results['skipped_files']}")
        
        if results["changes"]:
            print(f"\nChanges:")
            for change in results["changes"][:10]:
                print(f"  {change['file']}:{change['line']} - {change['action']}")
            if len(results["changes"]) > 10:
                print(f"  ... and {len(results['changes']) - 10} more")
    
    elif args.policy:
        policy_name = args.policy
        print(f"📋 Generating security policy: {policy_name}")
        policy = framework.generate_security_policy(policy_name)
        print(f"✓ Policy created with {len(policy.rules)} rules")
        print(f"  Location: config/security/policies/{policy_name}.json")
    
    elif args.validate:
        policy_name = args.validate
        print(f"🔍 Validating against policy: {policy_name}")
        violations = framework.validate_against_policy(policy_name)
        
        if violations:
            print(f"\n❌ {len(violations)} policy violations found:")
            for v in violations:
                print(f"  {v.severity}: {v.file}:{v.line} - {v.message}")
        else:
            print("✅ No policy violations!")
    
    elif args.setup:
        print("⚙️ Setting up continuous monitoring...")
        config = framework.setup_continuous_monitoring()
        print(f"✓ Monitoring configured")
        print(f"  Schedule: {config['scan_schedule']} at {config['scan_time']}")
        print(f"  Alert threshold: {config['alert_threshold']}")
        print(f"  Enabled rules: {len(config['enabled_rules'])}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
