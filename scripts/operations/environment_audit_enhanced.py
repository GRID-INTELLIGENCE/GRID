"""
Enhanced Environment Audit Script
==================================
Comprehensive environment auditing with package version checking,
PYTHONPATH validation, and security checks.
"""

import sys
import importlib.metadata
import json
import os
import warnings
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, UTC


SENSITIVE_MARKERS = (
    "KEY", "TOKEN", "SECRET", "PASSWORD", "PASS",
    "BEARER", "AUTH", "CREDENTIAL", "API"
)


def redact_environment(env: Dict[str, str]) -> Dict[str, str]:
    """Redact sensitive environment variables."""
    redacted: Dict[str, str] = {}
    for key, value in env.items():
        if any(marker in key.upper() for marker in SENSITIVE_MARKERS):
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted


class EnvironmentAuditor:
    """Comprehensive environment auditor with security checks."""

    def __init__(self):
        self.audit_results = {
            "timestamp": None,
            "environment_analysis": {
                "module_sources": {},
                "conflicts": {},
                "python_path": [],
                "environment_vars_count": 0,
                "environment_vars_redacted": 0,
                "loaded_modules": 0,
                "package_versions": {},
                "python_path_audit": {},
                "security_checks": {}
            },
            "memory_profile": {
                "total_objects": 0,
                "top_object_types": {},
                "garbage": 0
            },
            "system_resources": {
                "system": {},
                "process": {}
            },
            "recommendations": []
        }

    def run_audit(self) -> Dict[str, Any]:
        """Run all audit checks and return results."""
        self.audit_results["timestamp"] = self._get_timestamp()
        self._analyze_environment()
        self._check_package_versions()
        self._audit_python_path()
        self._run_security_checks()
        self._check_parasite_guard()
        self._generate_recommendations()
        return self.audit_results

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(UTC).isoformat()

    def _analyze_environment(self):
        """Analyze the Python environment and loaded modules."""
        self.audit_results["environment_analysis"]["loaded_modules"] = len(sys.modules)

        # Track module sources
        module_sources = {}
        for name, module in sys.modules.items():
            if hasattr(module, '__file__') and module.__file__:
                source = module.__file__
                module_sources[source] = module_sources.get(source, []) + [name]

        self.audit_results["environment_analysis"]["module_sources"] = module_sources

        # Find duplicate module names (excluding stdlib)
        name_to_paths = {}
        for path, modules in module_sources.items():
            for module in modules:
                base_name = module.split('.')[0]
                name_to_paths[base_name] = name_to_paths.get(base_name, set()) | {path}

        # Filter out stdlib conflicts
        import sysconfig
        stdlib_path = sysconfig.get_paths()["stdlib"]
        real_conflicts = {
            k: list(v) for k, v in name_to_paths.items()
            if len(v) > 1 and not k.startswith('_') and
            not any(stdlib_path in p for p in v)
        }

        self.audit_results["environment_analysis"]["conflicts"] = real_conflicts

        # Redact environment variables
        redacted_env = redact_environment(dict(os.environ))
        self.audit_results["environment_analysis"]["environment_vars_count"] = len(os.environ)
        self.audit_results["environment_analysis"]["environment_vars_redacted"] = sum(
            1 for k, v in redacted_env.items() if v == "***REDACTED***"
        )

    def _check_package_versions(self):
        """Check versions of key packages and their dependencies."""
        key_packages = [
            "pip", "setuptools", "wheel", "virtualenv",
            "fastapi", "sqlalchemy", "prometheus_client",
            "pytest", "uvicorn"
        ]

        for pkg in key_packages:
            try:
                version = importlib.metadata.version(pkg)
                self.audit_results["environment_analysis"]["package_versions"][pkg] = {
                    "version": version,
                    "status": "OK"
                }
            except importlib.metadata.PackageNotFoundError:
                self.audit_results["environment_analysis"]["package_versions"][pkg] = {
                    "status": "Not installed",
                    "severity": "warning"
                }
                self.audit_results["recommendations"].append({
                    "severity": "medium",
                    "issue": f"Package not installed: {pkg}",
                    "details": f"Consider installing {pkg} for better environment management",
                    "suggested_action": f"Run: pip install {pkg}"
                })

    def _audit_python_path(self):
        """Analyze and validate PYTHONPATH entries."""
        python_path = sys.path.copy()
        self.audit_results["environment_analysis"]["python_path"] = python_path

        for path in python_path:
            path_info = {
                "exists": os.path.exists(path),
                "is_directory": os.path.isdir(path) if os.path.exists(path) else False,
                "is_writable": os.access(path, os.W_OK) if os.path.exists(path) else False,
                "contains_python_files": False
            }

            if path_info["exists"] and path_info["is_directory"]:
                try:
                    files = os.listdir(path)
                    path_info["contains_python_files"] = any(
                        f.endswith('.py') or f.endswith('.pyd') or f.endswith('.so')
                        for f in files
                    )
                except (PermissionError, OSError):
                    path_info["contains_python_files"] = "Access denied"

            self.audit_results["environment_analysis"]["python_path_audit"][path] = path_info

        # Check for potential issues
        if any(not info["exists"] for info in self.audit_results["environment_analysis"]["python_path_audit"].values()):
            self.audit_results["recommendations"].append({
                "severity": "medium",
                "issue": "Non-existent paths in PYTHONPATH",
                "details": "Some paths in PYTHONPATH do not exist",
                "suggested_action": "Clean up PYTHONPATH to only include valid directories"
            })

    def _check_parasite_guard(self):
        """Check for parasite guard configuration."""
        self.audit_results["environment_analysis"]["security_checks"]["parasite_guard"] = {
            "status": "not_configured",
            "details": "Parasite guard not found in standard locations"
        }

        # Check if parasite_guard module exists
        try:
            from grid.security.parasite_guard import ParasiteDetectorMiddleware
            self.audit_results["environment_analysis"]["security_checks"]["parasite_guard"] = {
                "status": "configured",
                "module": "grid.security.parasite_guard",
                "middleware_available": True
            }
        except ImportError:
            pass

    def _run_security_checks(self):
        """Run basic security checks on the environment."""
        security_checks = self.audit_results["environment_analysis"]["security_checks"]

        # Check for writable directories in PATH (downgraded from "world-writable")
        writable_paths = []
        for path in os.environ.get("PATH", "").split(os.pathsep):
            if os.path.isdir(path) and os.access(path, os.W_OK):
                writable_paths.append(path)

        security_checks["writable_paths"] = {
            "found": bool(writable_paths),
            "paths": writable_paths,
            "severity": "medium",  # Downgraded from "high"
            "note": "These paths are writable by current user, not necessarily world-writable"
        }

        # Check for insecure file permissions
        security_checks["file_permissions"] = self._check_file_permissions()

    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for critical Python files."""
        critical_files = [
            sys.executable,
            sys.prefix,
            *[os.path.join(p, "site-packages") for p in sys.path if "site-packages" in p]
        ]

        results = {}
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    stat = os.stat(file_path)
                    results[file_path] = {
                        "mode": oct(stat.st_mode)[-3:],
                        "writable": os.access(file_path, os.W_OK),
                        "readable": os.access(file_path, os.R_OK),
                        "executable": os.access(file_path, os.X_OK)
                    }
                except (OSError, PermissionError):
                    results[file_path] = {"error": "Access denied"}

        return results

    def _generate_recommendations(self):
        """Generate recommendations based on audit findings."""
        # Add package version recommendations
        for pkg, info in self.audit_results["environment_analysis"]["package_versions"].items():
            if info.get("status") == "outdated":
                self.audit_results["recommendations"].append({
                    "severity": "medium",
                    "issue": f"Outdated package: {pkg}",
                    "details": f"Current version: {info.get('version')}, Latest version: {info.get('latest_version')}",
                    "suggested_action": f"Run: pip install --upgrade {pkg}"
                })

        # Add security recommendations
        security = self.audit_results["environment_analysis"]["security_checks"]
        if security.get("writable_paths", {}).get("found"):
            self.audit_results["recommendations"].append({
                "severity": "medium",
                "issue": "Writable directories in PATH",
                "details": "Some directories in PATH are writable by current user (not necessarily world-writable)",
                "suggested_action": "Review the following directories: " +
                                   ", ".join(security["writable_paths"]["paths"][:5]) +
                                   " (and others)"
            })

        # Check for missing parasite guard
        if self.audit_results["environment_analysis"]["security_checks"]["parasite_guard"]["status"] == "not_configured":
            self.audit_results["environment_analysis"]["security_checks"]["parasite_guard"]["recommendation"] = {
                "severity": "medium",
                "issue": "Parasite guard not configured",
                "details": "Parasite guard helps prevent dependency confusion attacks",
                "suggested_action": "Consider implementing parasite guard for additional security"
            }


def main():
    """Main function to run the environment audit."""
    try:
        auditor = EnvironmentAuditor()
        results = auditor.run_audit()

        # Save results to file
        output_file = "environment_audit_report.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Environment audit completed successfully. Report saved to {output_file}")

        # Print summary
        print("\n=== Audit Summary ===")
        print(f"Loaded modules: {results['environment_analysis']['loaded_modules']}")
        print(f"Package versions checked: {len(results['environment_analysis']['package_versions'])}")
        print(f"Module conflicts: {len(results['environment_analysis']['conflicts'])}")
        print(f"Security issues found: {len([r for r in results['recommendations'] if r['severity'] in ['high', 'critical']])}")
        print(f"Recommendations: {len(results['recommendations'])}")
        print(f"Environment variables: {results['environment_analysis']['environment_vars_count']} total, "
              f"{results['environment_analysis']['environment_vars_redacted']} redacted")

        # Print parasite guard status
        pg_status = results['environment_analysis']['security_checks']['parasite_guard']
        print(f"\nParasite Guard Status: {pg_status['status']}")

    except Exception as e:
        print(f"Error during environment audit: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
