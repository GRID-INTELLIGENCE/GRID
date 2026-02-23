import asyncio
import time

from cognitive.cognitive_engine import InteractionEvent, get_cognitive_engine
from cognitive.patterns.recognition import get_pattern_matcher


async def benchmark_cognitive_engine():
    engine = get_cognitive_engine()
    event = InteractionEvent(
        user_id="test_user", action="query", metadata={"complexity": 0.5, "information_density": 0.5}
    )

    print("Benchmarking CognitiveEngine.track_interaction()...")
    start_time = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        await engine.track_interaction(event)
    end_time = time.perf_counter()

    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    print(f"Average time per track_interaction: {avg_time_ms:.4f} ms")
    return avg_time_ms


def benchmark_pattern_matcher():
    matcher = get_pattern_matcher()
    data = {
        "cognitive_load": 5.0,
        "engagement": 0.5,
        "focus": 0.5,
        "time_distortion": 0.1,
        "timestamps": [time.time() - i for i in range(10)],
        "values": list(range(10)),
        "coordinates": [(i, i) for i in range(10)],
        "sequence": ["a", "b", "c", "a", "b", "c"],
        "events": ["click", "scroll", "click"],
        "dimensions": {"x": 0.1, "y": 0.2, "z": 0.3},
    }

    print("Benchmarking PatternMatcher.recognize_all()...")
    start_time = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        matcher.recognize_all(data)
    end_time = time.perf_counter()

    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    print(f"Average time per recognize_all (all 9 patterns): {avg_time_ms:.4f} ms")
    return avg_time_ms


async def main():
    engine_ms = await benchmark_cognitive_engine()
    matcher_ms = benchmark_pattern_matcher()

    print("-" * 40)
    total_overhead = engine_ms + matcher_ms
    print(f"Total Cognitive Overhead: {total_overhead:.4f} ms")

    if total_overhead < 5.0:
        print("✅ PERFORMANCE GOAL MET (< 5ms)")
    else:
        print("❌ PERFORMANCE GOAL NOT MET (> 5ms)")


if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    asyncio.run(main())
