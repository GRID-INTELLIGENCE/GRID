"""Hello GRID -- minimal example demonstrating core pattern analysis.

Requirements: pip install grid-intelligence
Usage: uv run python examples/hello_grid.py
"""

import asyncio

from grid.essence.core_state import EssentialState
from grid.patterns.recognition import PatternRecognition


async def main() -> None:
    state = EssentialState(
        pattern_signature="hello",
        quantum_state={"blended_val": 0.7},
        context_depth=1.0,
        coherence_factor=0.5,
    )
    print(f"State: {state.pattern_signature}, coherence={state.coherence_factor}")

    recognizer = PatternRecognition()
    patterns = await recognizer.recognize(state)
    print(f"Patterns detected: {patterns}")


if __name__ == "__main__":
    asyncio.run(main())
