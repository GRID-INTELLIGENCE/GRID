"""CLI entry point for the motivator - run progress checks during shifts."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from grid.progress.motivator import MotivationEngine, save_progress


def main():
    """Run the motivator."""
    engine = MotivationEngine()

    # Measure current state
    metrics = engine.measure_current_state()

    # Save to history
    save_progress(metrics)

    # Print motivational report
    print(engine.generate_report(metrics))

    # Return exit code based on RPM
    if metrics.rpm < 1000:
        return 1  # Still broken
    elif metrics.rpm < 3000:
        return 2  # Climbing but not ready
    else:
        return 0  # Ready to shift!


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
