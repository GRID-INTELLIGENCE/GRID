"""
Unified CLI for workspace utilities.

Provides a single entry point for all workspace utility commands
with Cascade-friendly JSON output support.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .repo_analyzer import RepositoryAnalyzer
from .project_comparator import ProjectComparator
from .eufle_verifier import EUFLEVerifier
from .config import config
from .exceptions import ValidationError, AnalysisError, OutputError, ComparisonError
from .validators import (
    validate_root_path,
    validate_output_dir,
    validate_max_depth,
    validate_exclude_patterns
)
from .logging_config import (
    setup_logging,
    log_command_start,
    log_command_end,
    get_logger
)


def analyze_command(args):
    """Run repository analysis."""
    logger = get_logger("cli", command="analyze")

    try:
        log_command_start("analyze", {
            "root": args.root,
            "output": args.out,
            "max_depth": args.max_depth,
            "exclude": args.exclude
        })

        # Validate inputs
        root_path = validate_root_path(args.root)
        output_dir = validate_output_dir(args.out, create=True)
        max_depth = validate_max_depth(args.max_depth)

        logger.info(f"Starting repository analysis: {root_path}")

        analyzer = RepositoryAnalyzer(
            root_path=str(root_path),
            output_dir=str(output_dir),
            max_depth=max_depth
        )

        if args.exclude:
            exclude_patterns = validate_exclude_patterns(args.exclude)
            analyzer.excluded_dirs.update(exclude_patterns)

        candidates = analyzer.analyze_repository()
        analyzer.save_outputs(candidates)
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        print("\nSuggestions:")
        print("  - Check that the root path exists and is a directory")
        print("  - Ensure the output directory is writable")
        print("  - Verify max_depth is between 1 and 20")
        print("  - Check exclude patterns format (comma-separated directory names)")
        raise
    except AnalysisError as e:
        print(f"Analysis Error: {e}", file=sys.stderr)
        print("\nSuggestions:")
        print("  - Check file permissions in the repository")
        print("  - Ensure Python has access to all files")
        print("  - Try reducing max_depth if analysis is slow")
        raise
    except OutputError as e:
        print(f"Output Error: {e}", file=sys.stderr)
        print("\nSuggestions:")
        print("  - Check that output directory is writable")
        print("  - Ensure sufficient disk space is available")
        raise

    # Output summary JSON for Cascade
    if config.should_output_json():
        summary = {
            'command': 'analyze',
            'root_path': args.root,
            'output_dir': str(analyzer.output_dir),
            'files_analyzed': len(analyzer.file_metrics),
            'refactor_candidates': len(candidates['candidates_for_refactor']),
            'high_value_components': len(candidates['reference_high_value_components'])
        }
        summary_file = analyzer.output_dir / 'analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        log_command_end("analyze", True,
                       files_analyzed=len(analyzer.file_metrics),
                       refactor_candidates=len(candidates['candidates_for_refactor']))
        logger.info(f"Analysis complete: {len(analyzer.file_metrics)} files analyzed")


def compare_command(args):
    """Compare two analyzed projects."""
    logger = get_logger("cli", command="compare")

    try:
        from .validators import validate_analysis_dir

        log_command_start("compare", {
            "project1": args.project1,
            "project2": args.project2,
            "output": args.out
        })

        # Validate inputs
        project1_dir = validate_analysis_dir(args.project1)
        project2_dir = validate_analysis_dir(args.project2)
        output_dir = validate_output_dir(args.out, create=True)

        logger.info(f"Starting project comparison: {project1_dir} vs {project2_dir}")

        comparator = ProjectComparator(
            project1_analysis_dir=str(project1_dir),
            project2_analysis_dir=str(project2_dir),
            output_dir=str(output_dir)
        )

        report = comparator.save_comparison_report()
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        print("\nSuggestions:")
        print("  - Ensure both analysis directories exist")
        print("  - Check that analysis directories contain candidates.json and module_graph.json")
        print("  - Verify output directory is writable")
        raise
    except ComparisonError as e:
        print(f"Comparison Error: {e}", file=sys.stderr)
        print("\nSuggestions:")
        print("  - Ensure analysis outputs are valid JSON files")
        print("  - Check file permissions on analysis directories")
        raise

    # Output summary JSON for Cascade
    if config.should_output_json():
        summary = {
            'command': 'compare',
            'project1': args.project1,
            'project2': args.project2,
            'output_dir': str(comparator.output_dir),
            'similar_modules': report['summary']['similar_modules_found'],
            'high_traffic_comparisons': report['summary']['high_traffic_comparisons'],
            'recommendations_count': len(report['recommendations'])
        }
        summary_file = comparator.output_dir / 'comparison_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        log_command_end("compare", True,
                       similar_modules=report['summary']['similar_modules_found'],
                       recommendations=len(report['recommendations']))
        logger.info("Comparison complete")


def verify_command(args):
    """Verify EUFLE setup."""
    logger = get_logger("cli", command="verify")

    log_command_start("verify", {})
    logger.info("Starting EUFLE verification")

    verifier = EUFLEVerifier()
    result = verifier.run_all_checks()

    log_command_end("verify", result["all_checks_passed"],
                   results=result["results"])
    logger.info(f"Verification {'passed' if result['all_checks_passed'] else 'failed'}")

    # Always output JSON for Cascade
    if config.should_output_json():
        output_file = config.get_output_dir() / "eufle_verification.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nJSON report saved to: {output_file}")

    return 0 if result["all_checks_passed"] else 1


def config_command(args):
    """Manage workspace configuration."""
    if args.show:
        print(json.dumps(config.config, indent=2))
    elif args.set:
        key, value = args.set.split('=', 1)
        config.set(key, value)
        config.save()
        print(f"Set {key} = {value}")
    elif args.get:
        value = config.get(args.get)
        print(f"{args.get} = {value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Workspace utilities unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  workspace-utils analyze --root ./project --out ./analysis
  workspace-utils compare --project1 ./grid_analysis --project2 ./eufle_analysis --out ./comparison
  workspace-utils verify
  workspace-utils config --show
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze repository')
    analyze_parser.add_argument('--root', required=True, help='Root path of repository to analyze')
    analyze_parser.add_argument('--out', required=True, help='Output directory for artifacts')
    analyze_parser.add_argument('--max-depth', type=int, default=6, help='Maximum recursion depth')
    analyze_parser.add_argument('--exclude', help='Comma-separated list of directories to exclude')
    analyze_parser.set_defaults(func=analyze_command)

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare two analyzed projects')
    compare_parser.add_argument('--project1', required=True, help='Path to first project analysis output')
    compare_parser.add_argument('--project2', required=True, help='Path to second project analysis output')
    compare_parser.add_argument('--out', required=True, help='Output directory for comparison report')
    compare_parser.set_defaults(func=compare_command)

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify EUFLE setup')
    verify_parser.set_defaults(func=verify_command)

    # Config command
    config_parser = subparsers.add_parser('config', help='Manage workspace configuration')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--show', action='store_true', help='Show current configuration')
    config_group.add_argument('--get', help='Get configuration value')
    config_group.add_argument('--set', help='Set configuration value (key=value)')
    config_parser.set_defaults(func=config_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        result = args.func(args)
        if result is not None:
            sys.exit(result)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except (ValidationError, AnalysisError, ComparisonError, OutputError) as e:
        # These errors already have detailed messages
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        print("\nIf this error persists, please report it with:")
        print(f"  - Error message: {str(e)}")
        print(f"  - Command: {' '.join(sys.argv)}")
        print(f"  - Python version: {sys.version}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
