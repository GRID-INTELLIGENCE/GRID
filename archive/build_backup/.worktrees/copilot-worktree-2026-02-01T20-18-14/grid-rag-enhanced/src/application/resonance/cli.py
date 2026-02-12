"""
CLI for Activity Resonance Tool - PowerShell Integration.

Provides terminal interface for left-to-right communication tool
with real-time feedback and path visualization.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from .activity_resonance import ActivityResonance, ResonanceFeedback


class ResonanceCLI:
    """CLI interface for Activity Resonance Tool."""

    def __init__(self):
        """Initialize CLI."""
        self.resonance: ActivityResonance | None = None
        self.last_feedback: ResonanceFeedback | None = None

    def feedback_handler(self, feedback: ResonanceFeedback) -> None:
        """
        Handle real-time feedback updates.

        Args:
            feedback: Resonance feedback
        """
        self.last_feedback = feedback

        # Print feedback in a concise format
        if feedback.envelope:
            phase_emoji = {
                "attack": "📈",
                "decay": "📉",
                "sustain": "🔄",
                "release": "📴",
                "idle": "⏸️",
            }
            emoji = phase_emoji.get(feedback.envelope.phase.value, "⚡")
            print(
                f"\r{emoji} {feedback.envelope.phase.value.upper()} "
                f"({feedback.envelope.amplitude:.2f}) | {feedback.message}",
                end="",
                flush=True,
            )

    def process(
        self,
        query: str,
        activity_type: str = "general",
        context: dict[str, Any] | None = None,
        show_paths: bool = True,
        show_context: bool = True,
        json_output: bool = False,
    ) -> int:
        """
        Process an activity query.

        Args:
            query: The query or goal
            activity_type: Type of activity ("code", "config", "general")
            context: Optional additional context
            show_paths: Whether to show path visualization
            show_context: Whether to show context
            json_output: Output as JSON

        Returns:
            Exit code (0 = success)
        """
        try:
            # Initialize resonance system
            self.resonance = ActivityResonance(feedback_callback=self.feedback_handler)

            # Start feedback loop for real-time updates
            self.resonance.start_feedback_loop(interval=0.05)

            # Process activity
            feedback = self.resonance.process_activity(activity_type=activity_type, query=query, context=context)

            # Wait for envelope to reach sustain
            time.sleep(0.2)

            # Stop feedback loop
            self.resonance.stop_feedback_loop()

            # Print final results
            print()  # New line after feedback updates

            if json_output:
                self._print_json(feedback)
            else:
                self._print_human_readable(feedback, show_context, show_paths)

            # Complete activity
            self.resonance.complete_activity()

            # Wait for release
            time.sleep(0.3)

            return 0

        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            if self.resonance:
                self.resonance.stop_feedback_loop()
            return 1
        except Exception as e:
            print(f"\n\n❌ Error: {e}", file=sys.stderr)
            if self.resonance:
                self.resonance.stop_feedback_loop()
            return 1

    def _print_json(self, feedback: ResonanceFeedback) -> None:
        """Print feedback as JSON."""
        output = {
            "state": feedback.state.value,
            "urgency": feedback.urgency,
            "message": feedback.message,
        }

        if feedback.context:
            output["context"] = {
                "content": feedback.context.content,
                "source": feedback.context.source,
                "metrics": {
                    "sparsity": feedback.context.metrics.sparsity,
                    "attention_tension": feedback.context.metrics.attention_tension,
                    "decision_pressure": feedback.context.metrics.decision_pressure,
                    "clarity": feedback.context.metrics.clarity,
                    "confidence": feedback.context.metrics.confidence,
                },
            }

        if feedback.paths:
            output["paths"] = {
                "goal": feedback.paths.goal,
                "total_options": feedback.paths.total_options,
                "glimpse_summary": feedback.paths.glimpse_summary,
                "recommended": (
                    {
                        "id": feedback.paths.recommended.id,
                        "name": feedback.paths.recommended.name,
                        "complexity": feedback.paths.recommended.complexity.value,
                        "estimated_time": feedback.paths.recommended.estimated_time,
                        "confidence": feedback.paths.recommended.confidence,
                    }
                    if feedback.paths.recommended
                    else None
                ),
                "options": [
                    {
                        "id": opt.id,
                        "name": opt.name,
                        "complexity": opt.complexity.value,
                        "estimated_time": opt.estimated_time,
                        "confidence": opt.confidence,
                        "recommendation_score": opt.recommendation_score,
                    }
                    for opt in feedback.paths.options
                ],
            }

        if feedback.envelope:
            output["envelope"] = {
                "phase": feedback.envelope.phase.value,
                "amplitude": feedback.envelope.amplitude,
                "velocity": feedback.envelope.velocity,
                "time_in_phase": feedback.envelope.time_in_phase,
            }

        print(json.dumps(output, indent=2))

    def _print_human_readable(self, feedback: ResonanceFeedback, show_context: bool, show_paths: bool) -> None:
        """Print feedback in human-readable format."""
        print("\n" + "=" * 80)
        print("🎯 ACTIVITY RESONANCE - LEFT TO RIGHT COMMUNICATION")
        print("=" * 80)

        # State and urgency
        urgency_emoji = "🔴" if feedback.urgency > 0.7 else "🟡" if feedback.urgency > 0.4 else "🟢"
        print(f"\n{urgency_emoji} State: {feedback.state.value.upper()} | Urgency: {feedback.urgency:.0%}")

        # Context (Left side)
        if show_context and feedback.context:
            print("\n" + "-" * 80)
            print("📋 LEFT: FAST CONTEXT (application/)")
            print("-" * 80)
            print(f"Source: {feedback.context.source}")
            print(f"\n{feedback.context.content}")

            metrics = feedback.context.metrics
            print("\n📊 Metrics:")
            print(
                f"   Sparsity: {metrics.sparsity:.0%} | "
                f"Attention Tension: {metrics.attention_tension:.0%} | "
                f"Decision Pressure: {metrics.decision_pressure:.0%}"
            )
            print(f"   Clarity: {metrics.clarity:.0%} | Confidence: {metrics.confidence:.0%}")

        # Paths (Right side)
        if show_paths and feedback.paths:
            print("\n" + "-" * 80)
            print("🛤️  RIGHT: PATH VISUALIZATION (light_of_the_seven/)")
            print("-" * 80)
            print(f"Goal: {feedback.paths.goal}")
            print(f"\n{feedback.paths.glimpse_summary}")

            if feedback.paths.recommended:
                print("\n" + "⭐ RECOMMENDED PATH:")
                print(
                    self.resonance.path_visualizer.visualize_path(feedback.paths.recommended)
                    if self.resonance and feedback.paths and feedback.paths.recommended
                    else "No path available"
                )

            if len(feedback.paths.options) > 1:
                print("\n" + "📊 ALL OPTIONS:")
                for i, option in enumerate(feedback.paths.options, 1):
                    marker = "⭐" if feedback.paths.recommended and option.id == feedback.paths.recommended.id else "  "
                    print(
                        f"{marker} {i}. {option.name} - "
                        f"{option.complexity.value}, {option.estimated_time:.1f}s, "
                        f"confidence: {option.confidence:.0%}"
                    )

        # Envelope
        if feedback.envelope:
            print("\n" + "-" * 80)
            print("🎵 ADSR ENVELOPE (Haptic Feedback)")
            print("-" * 80)
            print(f"Phase: {feedback.envelope.phase.value.upper()}")
            print(f"Amplitude: {feedback.envelope.amplitude:.2f} | Velocity: {feedback.envelope.velocity:.3f}")
            print(
                f"Time in Phase: {feedback.envelope.time_in_phase:.3f}s | "
                f"Total Time: {feedback.envelope.total_time:.3f}s"
            )

        print("\n" + "=" * 80)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Activity Resonance Tool - Left-to-Right Communication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a general query
  python -m application.resonance.cli "create a new service"

  # Process a code query with path visualization
  python -m application.resonance.cli "add authentication endpoint" --type code

  # Output as JSON
  python -m application.resonance.cli "configure database" --type config --json

  # Show only paths (no context)
  python -m application.resonance.cli "implement feature" --no-context
        """,
    )

    parser.add_argument("query", type=str, help="Query or goal to process")

    parser.add_argument(
        "--type",
        type=str,
        choices=["general", "code", "config"],
        default="general",
        help="Type of activity (default: general)",
    )

    parser.add_argument("--json", action="store_true", help="Output as JSON")

    parser.add_argument("--no-context", action="store_true", help="Don't show context (left side)")

    parser.add_argument("--no-paths", action="store_true", help="Don't show paths (right side)")

    parser.add_argument("--context", type=str, help="Additional context as JSON string")

    args = parser.parse_args()

    # Parse context if provided
    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in --context: {args.context}", file=sys.stderr)
            return 1

    # Create CLI and process
    cli = ResonanceCLI()
    return cli.process(
        query=args.query,
        activity_type=args.type,
        context=context,
        show_paths=not args.no_paths,
        show_context=not args.no_context,
        json_output=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
