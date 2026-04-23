import asyncio
import json
from cognition.core.processor import CognitiveProcessor
from cognition.models.core import CoffeeMode

async def run_simulation():
    processor = CognitiveProcessor()
    
    # 1. Set optimal state for System 2 (Cold Brew Mode)
    processor.metrics.cognitive_load = 5.0
    processor.metrics.attention_level = 0.9
    processor.metrics.decision_confidence = 0.4  # Low confidence triggers multi-pass
    
    # 2. Mock pattern detection to simulate complexity
    async def mock_detect_patterns(data):
        return ["COMPLEX_PATTERN", "URGENT_PATTERN"]
    processor._detect_patterns = mock_detect_patterns
    
    print("\n[SIMULATION: Multi-Pass Reasoning Flow]")
    print(f"Initial Confidence: {processor.metrics.decision_confidence}")
    print(f"Initial Coffee Mode: {processor.metrics.get_coffee_mode().value}")
    print(f"Initial Chunk Size: {processor.metrics.get_coffee_mode().chunk_size}")
    
    # 3. Process complex input
    input_text = "Analyze the structural resonance between the Cognitive Engine and the Boundary Security gates."
    result = await processor.process_input(input_text)
    
    # 4. Wardrobe Output
    print("\n## Wardrobe: REASONING OUTPUT")
    print(f"[GATE: Cognitive Engine] ✓ COMPLETE — Processed in {result.pass_count} passes.")
    
    print("\n| Metric             | Value               |")
    print("|--------------------|---------------------|")
    print(f"| Final Confidence   | {processor.metrics.decision_confidence:.2f}              |")
    print(f"| Pass Count         | {result.pass_count}                   |")
    print(f"| Processing Mode    | {result.cognitive_context.processing_mode}            |")
    print(f"| Coffee Mode        | {result.cognitive_context.coffee_mode}             |")
    print(f"| Final Chunk Size   | {processor.context.coffee_mode.chunk_size}                 |")

    print("\n**Refinement Insights:**")
    for i, insight in enumerate(result.output['insights'], 1):
        print(f"{i}. {insight}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
