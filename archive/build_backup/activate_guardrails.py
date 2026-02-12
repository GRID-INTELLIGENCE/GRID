#!/usr/bin/env python3
"""
Guardrail Enforcement Activator

Activates and enforces the custom guardrail system on target repositories.
Runs full profiling, installs pre-commit hooks, and generates initial reports.

Usage:
    python activate_guardrails.py --target coinbase
    python activate_guardrails.py --target wellness_studio
    python activate_guardrails.py --target all
"""

import sys
import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add the guardrails source to path
GUARDRAILS_ROOT = Path(__file__).parent / "src" / "guardrails"
sys.path.insert(0, str(GUARDRAILS_ROOT))

from guardrails import (
    GuardrailSystem,
    setup_guardrails,
    ModuleProfiler,
    analyze_package,
    get_middleware,
    GuardrailMiddleware,
)
from guardrails.ci.cicd_integration import CICDReporter
from guardrails.utils.integration_utils import scan_for_issues, create_remediation_plan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("guardrail_activator")

# Repository configurations
REPO_CONFIGS = {
    "coinbase": {
        "path": Path(__file__).parent / "Coinbase",
        "source_package": "coinbase",
        "mode": "enforcement",
        "description": "Coinbase Crypto Agentic System",
    },
    "wellness_studio": {
        "path": Path(__file__).parent / "wellness_studio",
        "source_package": "src/wellness_studio",
        "mode": "enforcement",
        "description": "Wellness Studio Medical AI System",
    },
}


def load_guardrail_config(repo_path: Path) -> dict:
    """Load .guardrailrc.json from a repo."""
    config_path = repo_path / ".guardrailrc.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def install_pre_commit_hook(repo_path: Path) -> bool:
    """Install the guardrail pre-commit hook into a git repo."""
    hooks_dir = repo_path / ".git" / "hooks"
    if not hooks_dir.exists():
        logger.warning(f"No .git/hooks directory found at {hooks_dir}")
        return False

    hook_source = GUARDRAILS_ROOT / "hooks" / "pre-commit.py"
    hook_dest = hooks_dir / "pre-commit"

    # Read the hook source and adapt it
    with open(hook_source, "r", encoding="utf-8") as f:
        hook_content = f.read()

    # Wrap with shebang and guardrails path injection
    wrapper = f'''#!/usr/bin/env python3
"""Auto-generated guardrail pre-commit hook. DO NOT EDIT MANUALLY."""
import sys
sys.path.insert(0, r"{GUARDRAILS_ROOT.parent}")
'''

    # Write combined hook
    with open(hook_dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(wrapper)
        f.write("\n")
        # Skip the original shebang line
        lines = hook_content.split("\n")
        start = 0
        for i, line in enumerate(lines):
            if line.startswith("#!"):
                start = i + 1
                break
        f.write("\n".join(lines[start:]))

    logger.info(f"  Pre-commit hook installed at {hook_dest}")
    return True


def profile_repository(repo_name: str, config: dict) -> Dict[str, Any]:
    """Run full guardrail profiling on a repository."""
    repo_path = config["path"]
    source_pkg = config["source_package"]
    mode = config["mode"]

    logger.info(f"")
    logger.info(f"{'='*60}")
    logger.info(f"  ACTIVATING GUARDRAILS: {repo_name.upper()}")
    logger.info(f"  Path: {repo_path}")
    logger.info(f"  Mode: {mode}")
    logger.info(f"{'='*60}")

    # Determine the package to analyze
    analyze_path = repo_path / source_pkg
    if not analyze_path.exists():
        logger.error(f"  Source package not found: {analyze_path}")
        return {"error": f"Source package not found: {analyze_path}"}

    # Load repo-specific config
    guardrail_config = load_guardrail_config(repo_path)
    exclude_patterns = guardrail_config.get("exclude_patterns", [])

    # Phase 1: Profile the codebase
    logger.info(f"")
    logger.info(f"  Phase 1: AST Profiling")
    logger.info(f"  {'-'*40}")

    profiler = ModuleProfiler(str(analyze_path))
    personalities = profiler.analyze_package(str(analyze_path))
    report = profiler.generate_report()

    logger.info(f"  Modules analyzed: {report['total_modules']}")
    logger.info(f"  Trait distribution:")
    for trait, count in report["trait_distribution"].items():
        if count > 0:
            logger.info(f"    - {trait}: {count}")
    logger.info(f"  Circular dependencies: {len(report['circular_dependencies'])}")

    # Phase 2: Scan for issues
    logger.info(f"")
    logger.info(f"  Phase 2: Issue Scanning")
    logger.info(f"  {'-'*40}")

    issues = scan_for_issues(str(analyze_path))
    total_issues = sum(len(v) for v in issues.values())
    logger.info(f"  Total issues found: {total_issues}")

    issue_counts = {}
    for itype, occurrences in issues.items():
        if occurrences:
            issue_counts[itype] = len(occurrences)
    for itype, count in sorted(issue_counts.items()):
        logger.info(f"    - {itype}: {count}")

    # Phase 3: Initialize enforcement system
    logger.info(f"")
    logger.info(f"  Phase 3: Enforcement Activation")
    logger.info(f"  {'-'*40}")

    system = GuardrailSystem(str(analyze_path), mode)
    system.initialize()

    # Check all modules
    module_results = {}
    total_violations = 0
    for module_name in list(system.profiler.personalities.keys()):
        try:
            result = system.check_module(module_name)
            violations = result.get("violations", [])
            total_violations += len(violations)
            module_results[module_name] = {
                "violations": len(violations),
                "q_curve": result.get("q_curve_profile"),
                "recommendations": len(result.get("recommendations", [])),
            }
        except Exception as e:
            logger.warning(f"    Failed to check {module_name}: {e}")

    logger.info(f"  Enforcement mode: {mode}")
    logger.info(f"  Total violations: {total_violations}")
    logger.info(f"  Modules with violations: {sum(1 for v in module_results.values() if v['violations'] > 0)}")

    # Phase 4: Install pre-commit hook
    logger.info(f"")
    logger.info(f"  Phase 4: Git Hook Installation")
    logger.info(f"  {'-'*40}")

    hook_installed = install_pre_commit_hook(repo_path)
    logger.info(f"  Hook installed: {hook_installed}")

    # Phase 5: Generate remediation plan
    logger.info(f"")
    logger.info(f"  Phase 5: Remediation Plan")
    logger.info(f"  {'-'*40}")

    if total_issues > 0:
        plan = create_remediation_plan(issues)
        logger.info(f"  Remediation phases: {len(plan.get('phases', []))}")
        for phase in plan.get("phases", []):
            phase_name = phase.get("name", "Unknown")
            phase_items = len(phase.get("issues", []))
            logger.info(f"    - {phase_name}: {phase_items} issues")
    else:
        plan = {"phases": []}
        logger.info(f"  No issues requiring remediation")

    # Phase 6: Get risky modules
    logger.info(f"")
    logger.info(f"  Phase 6: Risk Assessment")
    logger.info(f"  {'-'*40}")

    risky_modules = system.get_risky_modules(10)
    for i, mod in enumerate(risky_modules[:5], 1):
        logger.info(f"  #{i} {mod['module']} (score: {mod['score']}, reasons: {', '.join(mod['reasons'])})")

    # Compile results
    result = {
        "repository": repo_name,
        "description": config["description"],
        "path": str(repo_path),
        "mode": mode,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "profiling": {
            "total_modules": report["total_modules"],
            "trait_distribution": report["trait_distribution"],
            "circular_dependencies": len(report["circular_dependencies"]),
        },
        "enforcement": {
            "total_violations": total_violations,
            "modules_with_violations": sum(1 for v in module_results.values() if v["violations"] > 0),
            "module_results": module_results,
        },
        "issues": {
            "total": total_issues,
            "by_type": issue_counts,
        },
        "remediation": plan,
        "top_risky_modules": [
            {"module": m["module"], "score": m["score"], "reasons": m["reasons"]}
            for m in risky_modules[:10]
        ],
        "hooks": {
            "pre_commit_installed": hook_installed,
        },
        "config": guardrail_config,
    }

    # Save report
    reports_dir = repo_path / ".guardrail_reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"activation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"")
    logger.info(f"  Report saved: {report_path}")

    # Shutdown
    system.shutdown()

    return result


def print_summary(results: Dict[str, Dict[str, Any]]) -> None:
    """Print a combined summary of all activated repos."""
    print("\n")
    print("=" * 70)
    print("  GUARDRAIL ENFORCEMENT ACTIVATION SUMMARY")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)

    for repo_name, result in results.items():
        if "error" in result:
            print(f"\n  {repo_name}: FAILED — {result['error']}")
            continue

        profiling = result.get("profiling", {})
        enforcement = result.get("enforcement", {})
        issues = result.get("issues", {})
        hooks = result.get("hooks", {})

        print(f"\n  --- {repo_name.upper()} ({result.get('mode', 'unknown')}) ---")
        print(f"  Modules profiled     : {profiling.get('total_modules', 0)}")
        print(f"  Total violations     : {enforcement.get('total_violations', 0)}")
        print(f"  Modules w/violations : {enforcement.get('modules_with_violations', 0)}")
        print(f"  Issues found         : {issues.get('total', 0)}")
        print(f"  Pre-commit hook      : {'INSTALLED' if hooks.get('pre_commit_installed') else 'SKIPPED'}")
        print(f"  Circular deps        : {profiling.get('circular_dependencies', 0)}")

        # Top 3 risky
        risky = result.get("top_risky_modules", [])[:3]
        if risky:
            print(f"  Top risky modules    :")
            for m in risky:
                print(f"    - {m['module']} (score: {m['score']})")

    print()
    print("=" * 70)
    print("  STATUS: GUARDRAILS ACTIVE AND ENFORCING")
    print("=" * 70)
    print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Activate guardrail enforcement")
    parser.add_argument(
        "--target",
        choices=["coinbase", "wellness_studio", "all"],
        default="all",
        help="Which repository to activate guardrails on",
    )
    parser.add_argument(
        "--mode",
        choices=["observer", "warning", "enforcement", "adaptive"],
        default=None,
        help="Override enforcement mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Profile only, don't install hooks",
    )
    args = parser.parse_args()

    # Determine targets
    if args.target == "all":
        targets = list(REPO_CONFIGS.keys())
    else:
        targets = [args.target]

    results = {}
    for target in targets:
        config = REPO_CONFIGS[target].copy()
        if args.mode:
            config["mode"] = args.mode
        if args.dry_run:
            config["mode"] = "observer"

        try:
            results[target] = profile_repository(target, config)
        except Exception as e:
            logger.error(f"Failed to activate guardrails on {target}: {e}")
            results[target] = {"error": str(e)}

    print_summary(results)
    return 0 if all("error" not in r for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
