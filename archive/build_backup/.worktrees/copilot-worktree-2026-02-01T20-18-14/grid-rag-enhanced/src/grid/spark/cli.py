#!/usr/bin/env python
"""
Spark CLI - Universal invoker from command line.

Usage:
    python -m grid.spark "your request here"
    python -m grid.spark --persona navigator "diagnose import errors"
    python -m grid.spark --list  # List available personas
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from grid.spark import Spark, spark


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Spark ⚡ - Universal Morphable Invoker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    spark "diagnose import errors"
    spark --persona navigator "check path resolution"
    spark --persona reasoning "what is semantic reasoning?"
    spark --list
        """,
    )

    parser.add_argument("request", nargs="?", help="Natural language request")

    parser.add_argument(
        "--persona",
        "-p",
        choices=["navigator", "resonance", "agentic", "reasoning", "staircase"],
        help="Persona to use",
    )

    parser.add_argument("--list", "-l", action="store_true", help="List available personas")

    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # List personas
    if args.list:
        spark_instance = Spark()
        print("⚡ Spark Personas:\n")
        for name in spark_instance.available_personas:
            persona = spark_instance._personas[name]
            print(f"  {name}: {persona.description}")
        return 0

    # Require request
    if not args.request:
        parser.print_help()
        return 1

    # Invoke spark
    result = spark(args.request, persona=args.persona)

    if args.json:
        output = {
            "request": result.request,
            "persona": result.persona,
            "duration_ms": result.duration_ms,
            "output": result.output,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"⚡ Spark ({result.persona}) - {result.duration_ms}ms\n")

        if isinstance(result.output, dict):
            for key, value in result.output.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value[:5]:  # Limit to 5
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {result.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
