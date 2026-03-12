"""
Transition Gate Toolkit CLI - Main entry point.

Provides a comprehensive command-line interface for:
- Sealing artifacts into cryptographically bound envelopes
- Verifying envelopes through the 9-step pipeline
- Running test scenarios and demonstrations
- Generating audit reports
- Managing configuration

Usage:
    python -m boundaries.toolkit --help
    python -m boundaries.toolkit seal --payload-file data.json
    python -m boundaries.toolkit verify --envelope-file envelope.json
    python -m boundaries.toolkit test --all
    python -m boundaries.toolkit demo --all
    python -m boundaries.toolkit report --generate html
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from boundaries.toolkit.config import ToolkitConfig, get_config_from_env
from boundaries.toolkit.demo import list_demos, run_all_demos, run_demo_by_name
from boundaries.toolkit.reports import ReportGenerator, format_verification_result
from boundaries.toolkit.test_scenarios import (
    SCENARIOS,
    format_scenario_result,
    get_scenario_info,
    run_comprehensive_test_suite,
    run_scenario,
)
from boundaries.transition_gate.envelope import (
    PERM_DEPLOY,
    PERM_NETWORK,
    PERM_READ_ONLY,
    PERM_RUN_TESTS,
    PERM_START_SERVER,
    PERM_WRITE_RESULTS,
    ScopeDeclaration,
    TransitionEnvelope,
    seal_envelope,
)
from boundaries.transition_gate.gate_keeper import GateKeeper, verify_envelope
from boundaries.transition_gate.nonce import NonceRegistry


def get_version() -> str:
    """Return the toolkit version."""
    from boundaries.toolkit import __version__

    return __version__


def cmd_seal(args: argparse.Namespace) -> int:
    """
    Seal a payload into a cryptographically bound envelope.

    This is the 'seal side' operation that prepares artifacts for secure
    transfer across the partition boundary.
    """
    config = ToolkitConfig.from_file(args.config) if args.config else get_config_from_env()

    # Validate configuration
    issues = config.validate()
    if issues:
        print("Configuration errors:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    # Load payload
    if args.payload_file:
        payload_path = Path(args.payload_file)
        if not payload_path.exists():
            print(f"Payload file not found: {payload_path}", file=sys.stderr)
            return 1
        with open(payload_path, encoding="utf-8") as f:
            payload = json.load(f)
    elif args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON payload: {e}", file=sys.stderr)
            return 1
    else:
        print("Either --payload-file or --payload is required", file=sys.stderr)
        return 1

    # Parse permissions
    permissions = []
    if args.permissions:
        perm_map = {
            "deploy": PERM_DEPLOY,
            "read_only": PERM_READ_ONLY,
            "run_tests": PERM_RUN_TESTS,
            "start_server": PERM_START_SERVER,
            "write_results": PERM_WRITE_RESULTS,
            "network": PERM_NETWORK,
        }
        for p in args.permissions.split(","):
            p = p.strip()
            if p in perm_map:
                permissions.append(perm_map[p])
            else:
                print(f"Unknown permission: {p}", file=sys.stderr)
                return 1

    if not permissions:
        permissions = [PERM_READ_ONLY]

    # Create scope
    scope = ScopeDeclaration(
        permissions=tuple(permissions),
        target_project=args.target_project,
        target_path=args.target_path,
        max_execution_time_seconds=args.max_time,
        network_allowed=args.network,
        notes=args.notes,
    )

    # Initialize nonce registry
    nonce_registry = NonceRegistry(
        config.nonce_registry_path,
        max_age_seconds=config.nonce_max_age_seconds,
    )

    # Seal the envelope
    try:
        envelope = seal_envelope(
            payload,
            user_secret=config.user_secret,
            nonce_registry=nonce_registry,
            scope=scope,
            source_partition=config.source_partition,
            target_partition=config.target_partition,
            sealed_by=args.sealed_by,
            tests_passed=args.tests_passed,
            lint_passed=args.lint_passed,
            machine_fingerprint_overrides=config.machine_overrides or None,
            extra_fingerprint_context=config.extra_fingerprint_context,
            metadata={"sealed_via": "toolkit_cli", "cli_args": vars(args)},
        )
    except Exception as e:
        print(f"Failed to seal envelope: {e}", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = int(envelope.timestamp)
        output_path = config.staging_dir / f"envelope_{timestamp}_{envelope.envelope_id[:8]}.json"

    # Write envelope
    try:
        envelope.write_to_file(output_path)
    except Exception as e:
        print(f"Failed to write envelope: {e}", file=sys.stderr)
        return 1

    # Output summary
    if args.json:
        result = {
            "success": True,
            "envelope_id": envelope.envelope_id,
            "output_path": str(output_path),
            "payload_hash": envelope.payload_hash,
            "nonce": envelope.nonce,
            "timestamp": envelope.timestamp,
            "permissions": list(scope.permissions),
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"✅ Envelope sealed successfully")
        print(f"   Envelope ID: {envelope.envelope_id}")
        print(f"   Output: {output_path}")
        print(f"   Payload hash: {envelope.payload_hash}")
        print(f"   Permissions: {', '.join(scope.permissions)}")
        print(f"   Nonce: {envelope.nonce[:16]}...")

    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """
    Verify a sealed envelope through the 9-step pipeline.

    This is the 'verify side' operation that validates envelopes
    before allowing actions on the payload.
    """
    config = ToolkitConfig.from_file(args.config) if args.config else get_config_from_env()

    # Validate configuration
    issues = config.validate()
    if issues:
        print("Configuration errors:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    envelope_path = Path(args.envelope_file)
    if not envelope_path.exists():
        print(f"Envelope file not found: {envelope_path}", file=sys.stderr)
        return 1

    # Initialize nonce registry
    nonce_registry = NonceRegistry(
        config.nonce_registry_path,
        max_age_seconds=config.nonce_max_age_seconds,
    )

    # Initialize GateKeeper
    audit_path = config.audit_log_path if config.enable_audit_logging else None

    gate_keeper = GateKeeper(
        user_secret=config.user_secret,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        max_age_seconds=config.envelope_max_age_seconds,
        require_tests=config.require_tests,
        require_lint=config.require_lint,
        machine_fingerprint_overrides=config.machine_overrides or None,
        extra_fingerprint_context=config.extra_fingerprint_context,
    )

    # Determine action
    requested_action = args.action or "read_only"

    # Run verification
    try:
        result = gate_keeper.verify_from_file(
            envelope_path,
            requested_action=requested_action,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"Verification error: {e}", file=sys.stderr)
        return 1

    # Output results
    if args.json:
        print(result.to_json())
    else:
        print(format_verification_result(result, verbose=args.verbose))

    return 0 if result.passed else 1


def cmd_test(args: argparse.Namespace) -> int:
    """
    Run test scenarios demonstrating each verification step.

    Each scenario tests a specific security measure or attack vector.
    """
    if args.list:
        # List available scenarios
        scenarios = get_scenario_info()
        if args.json:
            print(json.dumps(scenarios, indent=2))
        else:
            print(f"{'=' * 70}")
            print("Available Test Scenarios")
            print(f"{'=' * 70}")
            print()

            # Group by step
            by_step = {}
            for s in scenarios:
                step = s["step"]
                if step not in by_step:
                    by_step[step] = []
                by_step[step].append(s)

            for step, items in sorted(by_step.items()):
                print(f"\n{step.upper()}")
                print("-" * 40)
                for item in items:
                    attack = f" [Attack: {item['attack_vector']}]" if item["attack_vector"] else ""
                    print(f"  {item['name']:25} - {item['description']}{attack}")
        return 0

    if args.all:
        # Run comprehensive test suite
        print("Running comprehensive test suite...")
        print(f"This will execute {len(SCENARIOS)} scenarios.")
        print()

        results = run_comprehensive_test_suite()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            summary = results["summary"]
            print(f"{'=' * 70}")
            print("Test Suite Results")
            print(f"{'=' * 70}")
            print()
            print(f"Total scenarios: {summary['total_scenarios']}")
            print(f"Passed: {summary['passed']} ({summary['pass_rate']:.1f}%)")
            print(f"Failed: {summary['failed']}")
            print()
            print(f"Security tests: {summary['security_tests']}")
            print(f"Security passed: {summary['security_passed']}")
            print()

            # Show failed scenarios
            failed = [name for name, r in results["results"].items() if not r["scenario_passed"]]
            if failed:
                print("Failed scenarios:")
                for name in failed:
                    print(f"  - {name}")

        return 0 if results["summary"]["failed"] == 0 else 1

    if args.scenario:
        # Run specific scenario
        if args.scenario not in SCENARIOS:
            print(f"Unknown scenario: {args.scenario}", file=sys.stderr)
            print(f"Available: {', '.join(SCENARIOS.keys())}", file=sys.stderr)
            return 1

        with tempfile.TemporaryDirectory() as td:
            result = run_scenario(args.scenario, Path(td))

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(format_scenario_result(result, verbose=True))

        return 0 if result.passed else 1

    print("No test action specified. Use --all, --scenario, or --list", file=sys.stderr)
    return 1


def cmd_demo(args: argparse.Namespace) -> int:
    """
    Run interactive demonstrations.

    Hands-on walkthroughs showing how the transition gate works.
    """
    if args.list:
        demos = list_demos()
        if args.json:
            print(json.dumps(demos, indent=2))
        else:
            print(f"{'=' * 70}")
            print("Available Demonstrations")
            print(f"{'=' * 70}")
            print()
            for i, demo in enumerate(demos, 1):
                print(f"{i}. {demo['title']} ({demo['name']})")
                print(f"   {demo['description']}")
                print()
        return 0

    if args.all:
        try:
            run_all_demos()
        except KeyboardInterrupt:
            print("\n\nDemo interrupted.")
            return 130
        return 0

    if args.name:
        try:
            run_demo_by_name(args.name)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\n\nDemo interrupted.")
            return 130
        return 0

    print("No demo specified. Use --all, --name, or --list", file=sys.stderr)
    return 1


def cmd_report(args: argparse.Namespace) -> int:
    """
    Generate audit reports from verification history.
    """
    config = ToolkitConfig.from_file(args.config) if args.config else get_config_from_env()

    audit_path = config.audit_log_path if args.audit_file is None else Path(args.audit_file)

    if not audit_path.exists():
        print(f"No audit file found: {audit_path}", file=sys.stderr)
        return 1

    generator = ReportGenerator(audit_path)

    if args.format == "json":
        output = args.output or "report.json"
        generator.generate_json_report(output)
        print(f"JSON report generated: {output}")

    elif args.format == "markdown" or args.format == "md":
        output = args.output or "report.md"
        generator.generate_markdown_report(output)
        print(f"Markdown report generated: {output}")

    elif args.format == "html":
        output = args.output or "report.html"
        generator.generate_html_report(output)
        print(f"HTML report generated: {output}")

    elif args.format == "compliance":
        compliance = generator.generate_compliance_summary()
        if args.json:
            print(json.dumps(compliance, indent=2))
        else:
            print(f"{'=' * 70}")
            print("Compliance Summary")
            print(f"{'=' * 70}")
            print()
            print(f"Compliance Score: {compliance['compliance_score']:.1f}%")
            print()
            print("Criteria:")
            for criterion, passed in compliance["criteria"].items():
                status = "✅" if passed else "❌"
                print(f"  {status} {criterion}")
            print()
            if compliance["recommendations"]:
                print("Recommendations:")
                for rec in compliance["recommendations"]:
                    print(f"  - {rec}")

    else:
        print(f"Unknown format: {args.format}", file=sys.stderr)
        return 1

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """
    Manage toolkit configuration.
    """
    if args.init:
        # Initialize new configuration
        config_path = Path(args.init)
        config = ToolkitConfig()

        # Interactive configuration
        print("Transition Gate Toolkit Configuration")
        print(f"{'=' * 50}")
        print()

        secret = input("Shared secret (or set TRANSITION_GATE_SECRET env var): ").strip()
        if secret:
            config.user_secret = secret

        source = input(f"Source partition [{config.source_partition}]: ").strip()
        if source:
            config.source_partition = source

        target = input(f"Target partition [{config.target_partition}]: ").strip()
        if target:
            config.target_partition = target

        staging = input(f"Staging directory [{config.staging_dir}]: ").strip()
        if staging:
            config.staging_dir = Path(staging)

        audit = input(f"Audit directory [{config.audit_dir}]: ").strip()
        if audit:
            config.audit_dir = Path(audit)

        try:
            config.to_file(config_path)
            print(f"\nConfiguration saved to: {config_path}")
        except Exception as e:
            print(f"Failed to save configuration: {e}", file=sys.stderr)
            return 1

        return 0

    if args.validate:
        config_path = Path(args.validate)
        if not config_path.exists():
            print(f"Config file not found: {config_path}", file=sys.stderr)
            return 1

        try:
            config = ToolkitConfig.from_file(config_path)
        except Exception as e:
            print(f"Failed to load configuration: {e}", file=sys.stderr)
            return 1

        issues = config.validate()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print("Configuration is valid")
            return 0

    if args.show:
        config_path = Path(args.show)
        if not config_path.exists():
            print(f"Config file not found: {config_path}", file=sys.stderr)
            return 1

        try:
            config = ToolkitConfig.from_file(config_path)
        except Exception as e:
            print(f"Failed to load configuration: {e}", file=sys.stderr)
            return 1

        print(f"{'=' * 70}")
        print("Configuration")
        print(f"{'=' * 70}")
        print()
        print(f"Source partition: {config.source_partition}")
        print(f"Target partition: {config.target_partition}")
        print(f"Staging directory: {config.staging_dir}")
        print(f"Audit directory: {config.audit_dir}")
        print(f"Nonce registry: {config.nonce_registry_path}")
        print(f"Audit log: {config.audit_log_path}")
        print(f"Max envelope age: {config.envelope_max_age_seconds}s")
        print(f"Require tests: {config.require_tests}")
        print(f"Require lint: {config.require_lint}")
        print(f"User secret: {'[SET]' if config.user_secret else '[NOT SET]'}")

        return 0

    print("No config action specified. Use --init, --validate, or --show", file=sys.stderr)
    return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="transition-gate-toolkit",
        description="Comprehensive toolkit for sealed envelope operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seal a payload
  %(prog)s seal --payload '{"key": "value"}' --permissions deploy,read_only

  # Verify an envelope
  %(prog)s verify --envelope-file envelope.json --action deploy

  # Run all test scenarios
  %(prog)s test --all

  # List available demos
  %(prog)s demo --list

  # Run a specific demo
  %(prog)s demo --name replay

  # Generate HTML report
  %(prog)s report --format html --output report.html

  # Initialize configuration
  %(prog)s config --init toolkit.json
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Seal command
    seal_parser = subparsers.add_parser(
        "seal",
        help="Seal a payload into a cryptographically bound envelope",
    )
    seal_parser.add_argument(
        "--payload-file",
        "-f",
        help="Path to JSON payload file",
    )
    seal_parser.add_argument(
        "--payload",
        "-p",
        help="JSON payload string",
    )
    seal_parser.add_argument(
        "--permissions",
        default="read_only",
        help="Comma-separated permissions (deploy,read_only,run_tests,start_server,write_results,network)",
    )
    seal_parser.add_argument(
        "--target-project",
        help="Target project name",
    )
    seal_parser.add_argument(
        "--target-path",
        help="Target path for deployment",
    )
    seal_parser.add_argument(
        "--max-time",
        type=int,
        default=300,
        help="Maximum execution time in seconds",
    )
    seal_parser.add_argument(
        "--network",
        action="store_true",
        help="Allow network access",
    )
    seal_parser.add_argument(
        "--sealed-by",
        help="Identifier of the person/system sealing",
    )
    seal_parser.add_argument(
        "--tests-passed",
        action="store_true",
        default=True,
        help="Mark tests as passed",
    )
    seal_parser.add_argument(
        "--lint-passed",
        action="store_true",
        default=True,
        help="Mark lint as passed",
    )
    seal_parser.add_argument(
        "--notes",
        help="Optional notes about this envelope",
    )
    seal_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: auto-generated in staging directory)",
    )
    seal_parser.add_argument(
        "--config",
        "-c",
        help="Path to configuration file",
    )
    seal_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    seal_parser.set_defaults(func=cmd_seal)

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a sealed envelope through the 9-step pipeline",
    )
    verify_parser.add_argument(
        "envelope_file",
        help="Path to envelope JSON file",
    )
    verify_parser.add_argument(
        "--action",
        "-a",
        default="read_only",
        help="Action to verify (deploy, read_only, run_tests, etc.)",
    )
    verify_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't burn nonce or write audit log",
    )
    verify_parser.add_argument(
        "--config",
        "-c",
        help="Path to configuration file",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    verify_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed step information",
    )
    verify_parser.set_defaults(func=cmd_verify)

    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Run test scenarios",
    )
    test_parser.add_argument(
        "--all",
        action="store_true",
        help="Run all test scenarios",
    )
    test_parser.add_argument(
        "--scenario",
        "-s",
        help="Run specific scenario by name",
    )
    test_parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available scenarios",
    )
    test_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    test_parser.set_defaults(func=cmd_test)

    # Demo command
    demo_parser = subparsers.add_parser(
        "demo",
        help="Run interactive demonstrations",
    )
    demo_parser.add_argument(
        "--all",
        action="store_true",
        help="Run all demonstrations",
    )
    demo_parser.add_argument(
        "--name",
        "-n",
        help="Run specific demo by name",
    )
    demo_parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available demos",
    )
    demo_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for --list)",
    )
    demo_parser.set_defaults(func=cmd_demo)

    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate audit reports",
    )
    report_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "md", "html", "compliance"],
        default="markdown",
        help="Report format",
    )
    report_parser.add_argument(
        "--output",
        "-o",
        help="Output file path",
    )
    report_parser.add_argument(
        "--audit-file",
        help="Path to audit log file (default: from config)",
    )
    report_parser.add_argument(
        "--config",
        "-c",
        help="Path to configuration file",
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for compliance format)",
    )
    report_parser.set_defaults(func=cmd_report)

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
    )
    config_parser.add_argument(
        "--init",
        metavar="FILE",
        help="Initialize new configuration file",
    )
    config_parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validate configuration file",
    )
    config_parser.add_argument(
        "--show",
        metavar="FILE",
        help="Show configuration file",
    )
    config_parser.set_defaults(func=cmd_config)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
