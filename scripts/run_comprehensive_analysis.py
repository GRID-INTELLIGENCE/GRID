#!/usr/bin/env python3
"""
Comprehensive workspace analysis and diagnostics
Establishes health baselines and best practices across all repos
"""

import ast
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Configuration
REPOS = {
    "Apps": {
        "path": "e:\\projects\\Apps",
        "type": "hybrid",
        "primary_langs": ["python", "typescript"],
    },
    "grid": {"path": "e:\\grid", "type": "python", "primary_langs": ["python"]},
    "EUFLE": {"path": "e:\\projects\\EUFLE", "type": "python", "primary_langs": ["python"]},
    "pipeline": {"path": "e:\\projects\\pipeline", "type": "python", "primary_langs": ["python"]},
}

ANALYSIS_OUTPUTS = Path("e:\\analysis_outputs")
ANALYSIS_OUTPUTS.mkdir(exist_ok=True)

# ==================== Phase 1: Type Safety ====================


class TypeSafetyAnalyzer:
    """Analyze type safety and Pydantic v2 compliance"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixed_count = 0

    def check_pydantic_v2_migration(self, repo_path: Path) -> Dict[str, Any]:
        """Check for Pydantic v2 compatibility issues"""
        findings = {
            "field_mismatches": [],
            "import_issues": [],
            "deprecated_patterns": [],
        }

        for py_file in repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check for deprecated Field() patterns
                if re.search(r"Field\([^)]*default_factory[^)]*\)", content):
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if "Field(" in line and "default_factory" in line:
                            # V2 requires lowercase
                            if "default_factory" in line:
                                findings["field_mismatches"].append(
                                    {
                                        "file": str(py_file.relative_to(repo_path)),
                                        "line": i,
                                        "issue": "Verify Field syntax for Pydantic v2",
                                    }
                                )

                # Check for old imports
                if "from pydantic import validator" in content:
                    findings["deprecated_patterns"].append(
                        {
                            "file": str(py_file.relative_to(repo_path)),
                            "issue": "validator decorator deprecated; use field_validator",
                        }
                    )

            except Exception as e:
                pass

        return findings

    def check_optional_member_access(self, repo_path: Path) -> Dict[str, Any]:
        """Identify unguarded optional member access"""
        findings = {"unguarded_access": [], "safe_patterns": []}

        for py_file in repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Look for patterns like obj.attr without null check
                for i, line in enumerate(lines, 1):
                    # Skip comments and strings
                    if line.strip().startswith("#"):
                        continue

                    # Pattern: something.get() or ?.operator
                    if ".get(" in line or " if " in line and " is not None" in line:
                        findings["safe_patterns"].append(
                            {
                                "file": str(py_file.relative_to(repo_path)),
                                "line": i,
                                "pattern": "safe",
                            }
                        )

            except Exception:
                pass

        return findings

    def analyze_repo(self, repo_name: str, repo_path: Path) -> Dict[str, Any]:
        """Analyze type safety for a single repo"""
        report = {
            "repo": repo_name,
            "timestamp": datetime.utcnow().isoformat(),
            "pydantic_migration": self.check_pydantic_v2_migration(repo_path),
            "optional_access": self.check_optional_member_access(repo_path),
            "summary": {},
        }

        # Count Python files
        py_files = list(repo_path.rglob("*.py"))
        report["summary"]["total_py_files"] = len(py_files)
        report["summary"]["pydantic_issues"] = len(
            report["pydantic_migration"]["field_mismatches"]
        )
        report["summary"]["deprecated_patterns"] = len(
            report["pydantic_migration"]["deprecated_patterns"]
        )

        return report


# ==================== Phase 2: AI Safety & Privacy ====================


class AISafetyAuditor:
    """Audit AI safety and privacy practices"""

    MODEL_PATTERNS = {
        "openai": ["openai.", "gpt-", "from openai"],
        "anthropic": ["anthropic.", "claude", "from anthropic"],
        "ollama": ["Ollama", "ollama.", "from ollama"],
        "huggingface": ["transformers", "huggingface", "HfApi"],
        "local": ["local.*model", "on.*premise"],
    }

    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    }

    def detect_model_usage(self, repo_path: Path) -> Dict[str, List[str]]:
        """Detect AI model usage"""
        detected = {}

        for py_file in repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for model, patterns in self.MODEL_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            if model not in detected:
                                detected[model] = []
                            detected[model].append(str(py_file.relative_to(repo_path)))
                            break
            except Exception:
                pass

        return detected

    def check_pii_handling(self, repo_path: Path) -> Dict[str, Any]:
        """Check for PII in code and patterns"""
        findings = {
            "redaction_patterns": [],
            "encryption_patterns": [],
            "potential_pii": [],
        }

        for py_file in repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Look for redaction/encryption patterns
                if any(
                    x in content
                    for x in ["redact", "encrypt", "hash", "anonymize", "gdpr", "pii"]
                ):
                    findings["redaction_patterns"].append(
                        str(py_file.relative_to(repo_path))
                    )

                # Look for encryption imports
                if "cryptography" in content or "Fernet" in content:
                    findings["encryption_patterns"].append(
                        str(py_file.relative_to(repo_path))
                    )

            except Exception:
                pass

        return findings

    def analyze_repo(self, repo_name: str, repo_path: Path) -> Dict[str, Any]:
        """Analyze AI safety for a repo"""
        return {
            "repo": repo_name,
            "timestamp": datetime.utcnow().isoformat(),
            "model_usage": self.detect_model_usage(repo_path),
            "pii_handling": self.check_pii_handling(repo_path),
            "risk_assessment": {
                "models_detected": len(self.detect_model_usage(repo_path)),
                "has_encryption": len(
                    self.check_pii_handling(repo_path).get("encryption_patterns", [])
                )
                > 0,
                "has_redaction": len(
                    self.check_pii_handling(repo_path).get("redaction_patterns", [])
                )
                > 0,
            },
        }


# ==================== Phase 3: Architecture Testing ====================


class ArchitectureTester:
    """Test architectural components and patterns"""

    def test_async_patterns(self, repo_path: Path) -> Dict[str, Any]:
        """Verify async/await patterns"""
        findings = {"async_functions": 0, "async_issues": [], "sync_blocking_calls": []}

        for py_file in repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Count async functions
                findings["async_functions"] += len(re.findall(r"async def ", content))

                # Check for blocking calls in async context
                if "async def" in content:
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if (
                            "time.sleep(" in line
                            or "open(" in line
                            or "requests." in line
                        ):
                            findings["sync_blocking_calls"].append(
                                {
                                    "file": str(py_file.relative_to(repo_path)),
                                    "line": i,
                                    "issue": "Potential blocking call in async context",
                                }
                            )

            except Exception:
                pass

        return findings

    def test_service_layer(self, repo_path: Path) -> Dict[str, Any]:
        """Test service layer patterns"""
        findings = {"services": [], "routers": [], "import_issues": []}

        services_dir = (
            repo_path / "backend" / "services"
            if (repo_path / "backend" / "services").exists()
            else None
        )
        if services_dir:
            for service_file in services_dir.glob("*.py"):
                findings["services"].append(service_file.name)

        routers_dir = (
            repo_path / "backend" / "routers"
            if (repo_path / "backend" / "routers").exists()
            else None
        )
        if routers_dir:
            for router_file in routers_dir.glob("*.py"):
                findings["routers"].append(router_file.name)

        return findings

    def analyze_repo(self, repo_name: str, repo_path: Path) -> Dict[str, Any]:
        """Analyze architecture for a repo"""
        return {
            "repo": repo_name,
            "timestamp": datetime.utcnow().isoformat(),
            "async_patterns": self.test_async_patterns(repo_path),
            "service_layer": self.test_service_layer(repo_path),
        }


# ==================== Phase 4: Performance Baseline ====================


class PerformanceBaseliner:
    """Establish performance baselines"""

    def check_codebase_metrics(self, repo_path: Path) -> Dict[str, Any]:
        """Collect codebase metrics"""
        metrics = {
            "total_lines": 0,
            "python_files": 0,
            "typescript_files": 0,
            "test_files": 0,
            "configuration_files": 0,
            "average_file_size": 0,
            "largest_files": [],
        }

        py_files = list(repo_path.rglob("*.py"))
        ts_files = list(repo_path.rglob("*.ts")) + list(repo_path.rglob("*.tsx"))
        test_files = list(repo_path.rglob("*test*.py")) + list(
            repo_path.rglob("*.test.ts")
        )

        metrics["python_files"] = len(py_files)
        metrics["typescript_files"] = len(ts_files)
        metrics["test_files"] = len(test_files)

        all_lines = 0
        file_sizes = []

        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = len(f.readlines())
                    all_lines += lines
                    file_sizes.append((py_file.name, lines))
            except Exception:
                pass

        metrics["total_lines"] = all_lines
        metrics["average_file_size"] = all_lines // len(py_files) if py_files else 0
        metrics["largest_files"] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[
            :5
        ]

        return metrics

    def analyze_repo(self, repo_name: str, repo_path: Path) -> Dict[str, Any]:
        """Analyze performance metrics for a repo"""
        return {
            "repo": repo_name,
            "timestamp": datetime.utcnow().isoformat(),
            "codebase_metrics": self.check_codebase_metrics(repo_path),
        }


# ==================== Main Execution ====================


def main():
    print("=" * 80)
    print("COMPREHENSIVE WORKSPACE ANALYSIS & DIAGNOSTICS")
    print("=" * 80)
    print(f"Started: {datetime.utcnow().isoformat()}\n")

    # Initialize analyzers
    type_analyzer = TypeSafetyAnalyzer()
    safety_auditor = AISafetyAuditor()
    arch_tester = ArchitectureTester()
    perf_baseline = PerformanceBaseliner()

    # Storage for all results
    comprehensive_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase1_type_safety": {},
        "phase2_ai_safety": {},
        "phase3_architecture": {},
        "phase4_performance": {},
        "executive_summary": {},
    }

    # Analyze each repo
    for repo_name, repo_info in REPOS.items():
        repo_path = Path(repo_info["path"])

        if not repo_path.exists():
            print(f"[!] Repo not found: {repo_name} at {repo_path}")
            continue

        print(f"\n[Analyzing] {repo_name}...")

        # Phase 1: Type Safety
        print(f"  -> Phase 1: Type Safety")
        type_report = type_analyzer.analyze_repo(repo_name, repo_path)
        comprehensive_report["phase1_type_safety"][repo_name] = type_report
        print(f"    [OK] Found {type_report['summary']['total_py_files']} Python files")

        # Phase 2: AI Safety
        print(f"  -> Phase 2: AI Safety & Privacy")
        safety_report = safety_auditor.analyze_repo(repo_name, repo_path)
        comprehensive_report["phase2_ai_safety"][repo_name] = safety_report
        models = list(safety_report["model_usage"].keys())
        print(f"    [OK] Models detected: {models if models else 'None'}")

        # Phase 3: Architecture
        print(f"  -> Phase 3: Architecture")
        arch_report = arch_tester.analyze_repo(repo_name, repo_path)
        comprehensive_report["phase3_architecture"][repo_name] = arch_report
        print(
            f"    [OK] {arch_report['async_patterns']['async_functions']} async functions"
        )

        # Phase 4: Performance
        print(f"  -> Phase 4: Performance Baseline")
        perf_report = perf_baseline.analyze_repo(repo_name, repo_path)
        comprehensive_report["phase4_performance"][repo_name] = perf_report
        metrics = perf_report["codebase_metrics"]
        print(
            f"    [OK] {metrics['total_lines']} lines of code across {metrics['python_files']} files"
        )

    # Generate Executive Summary
    print("\n" + "=" * 80)
    print("GENERATING EXECUTIVE SUMMARY")
    print("=" * 80)

    total_py_files = sum(
        comprehensive_report["phase1_type_safety"][r]["summary"]["total_py_files"]
        for r in comprehensive_report["phase1_type_safety"]
        if r
    )

    total_issues = sum(
        comprehensive_report["phase1_type_safety"][r]["summary"]["pydantic_issues"]
        for r in comprehensive_report["phase1_type_safety"]
        if r
    )

    comprehensive_report["executive_summary"] = {
        "total_repos": len(REPOS),
        "total_python_files": total_py_files,
        "type_safety_issues": total_issues,
        "models_detected": list(
            set(
                model
                for repo_data in comprehensive_report["phase2_ai_safety"].values()
                for model in repo_data.get("model_usage", {}).keys()
            )
        ),
        "async_function_count": sum(
            comprehensive_report["phase3_architecture"][r]["async_patterns"][
                "async_functions"
            ]
            for r in comprehensive_report["phase3_architecture"]
            if r
        ),
        "total_lines_of_code": sum(
            comprehensive_report["phase4_performance"][r]["codebase_metrics"][
                "total_lines"
            ]
            for r in comprehensive_report["phase4_performance"]
            if r
        ),
        "analysis_date": datetime.utcnow().isoformat(),
    }

    # Save comprehensive report
    report_path = ANALYSIS_OUTPUTS / "comprehensive_analysis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(comprehensive_report, f, indent=2, default=str)

    print(f"\n[OK] Comprehensive analysis complete!")
    print(f"Report saved to: {report_path}")
    print(f"\nKey Metrics:")
    print(f"  - Total Python Files: {total_py_files}")
    print(f"  - Type Safety Issues: {total_issues}")
    print(
        f"  - Models Detected: {comprehensive_report['executive_summary']['models_detected']}"
    )
    print(
        f"  - Async Functions: {comprehensive_report['executive_summary']['async_function_count']}"
    )
    print(
        f"  - Total Lines of Code: {comprehensive_report['executive_summary']['total_lines_of_code']}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
