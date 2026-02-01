"""
Performance Benchmarks: Arena Structure Fixes

Measures performance impact of:
1. Honor decay calculations
2. Auto de-escalation checks
3. Effective priority calculations
4. Sustain phase checks
5. Overall cache operations with decay
"""

import sys
import time
from pathlib import Path

# Add Arena path to sys.path
arena_path = Path(__file__).parent.parent / "Arena" / "the_chase" / "python" / "src"
if not (arena_path / "the_chase").exists():
    raise ImportError("the_chase path does not exist")
if str(arena_path) not in sys.path:
    sys.path.insert(0, str(arena_path))

from the_chase.core.cache import CacheLayer, CacheMeta, MemoryTier
from the_chase.overwatch.rewards import (
    Achievement,
    AchievementType,
    CharacterRewardState,
    RewardEscalator,
)


def benchmark_honor_decay(n_iterations: int = 10000) -> dict:
    """Benchmark honor decay performance."""
    state = CharacterRewardState(entity_id="bench1")

    # Add achievement
    achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Benchmark achievement")
    state.add_achievement(achievement)

    start = time.perf_counter()
    for _ in range(n_iterations):
        state.decay_honor(decay_rate=0.01, time_elapsed=86400.0)
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = n_iterations / elapsed

    return {
        "operation": "honor_decay",
        "iterations": n_iterations,
        "elapsed_seconds": elapsed,
        "ops_per_second": ops_per_sec,
        "avg_time_per_op_us": (elapsed / n_iterations) * 1_000_000,
    }


def benchmark_de_escalation_check(n_iterations: int = 10000) -> dict:
    """Benchmark de-escalation check performance."""
    state = CharacterRewardState(entity_id="bench2")

    # Escalate to PROMOTED
    for _ in range(6):
        achievement = Achievement(achievement_type=AchievementType.MODERATE, description="Achievement")
        state.add_achievement(achievement)
        action = RewardEscalator.determine_action(state, achievement)
        reward = RewardEscalator.create_reward(action, achievement)
        state.add_reward(reward)

    start = time.perf_counter()
    for _ in range(n_iterations):
        state.check_and_de_escalate(inactivity_threshold_seconds=86400.0)
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = n_iterations / elapsed

    return {
        "operation": "de_escalation_check",
        "iterations": n_iterations,
        "elapsed_seconds": elapsed,
        "ops_per_second": ops_per_sec,
        "avg_time_per_op_us": (elapsed / n_iterations) * 1_000_000,
    }


def benchmark_effective_priority(n_iterations: int = 10000) -> dict:
    """Benchmark effective priority calculation performance."""
    meta = CacheMeta(
        created_at=time.time() - 50.0, ttl_seconds=100.0, soft_ttl_seconds=50.0, priority=0.8, sustain_time_seconds=30.0
    )

    start = time.perf_counter()
    for _ in range(n_iterations):
        _ = meta.get_effective_priority()
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = n_iterations / elapsed

    return {
        "operation": "effective_priority",
        "iterations": n_iterations,
        "elapsed_seconds": elapsed,
        "ops_per_second": ops_per_sec,
        "avg_time_per_op_us": (elapsed / n_iterations) * 1_000_000,
    }


def benchmark_sustain_phase_check(n_iterations: int = 10000) -> dict:
    """Benchmark sustain phase check performance."""
    meta = CacheMeta(
        created_at=time.time() - 10.0, ttl_seconds=100.0, soft_ttl_seconds=50.0, priority=0.5, sustain_time_seconds=30.0
    )

    start = time.perf_counter()
    for _ in range(n_iterations):
        _ = meta.is_in_sustain_phase()
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = n_iterations / elapsed

    return {
        "operation": "sustain_phase_check",
        "iterations": n_iterations,
        "elapsed_seconds": elapsed,
        "ops_per_second": ops_per_sec,
        "avg_time_per_op_us": (elapsed / n_iterations) * 1_000_000,
    }


def benchmark_cache_operations_with_decay(n_entries: int = 1000, n_ops: int = 10000) -> dict:
    """Benchmark cache operations with decay mechanisms."""
    cache = CacheLayer(mem=MemoryTier(max_size=n_entries * 2))

    # Populate cache
    for i in range(n_entries):
        cache.set(
            key=f"entry_{i}",
            value={"data": f"value_{i}"},
            ttl_seconds=100.0,
            priority=0.5 + (i % 10) / 20.0,  # Vary priority
            sustain_time_seconds=30.0,
        )

    # Benchmark get operations (which now use effective priority)
    start = time.perf_counter()
    for i in range(n_ops):
        _ = cache.get(f"entry_{i % n_entries}")
    end = time.perf_counter()

    elapsed = end - start
    ops_per_sec = n_ops / elapsed

    return {
        "operation": "cache_get_with_decay",
        "cache_size": n_entries,
        "iterations": n_ops,
        "elapsed_seconds": elapsed,
        "ops_per_second": ops_per_sec,
        "avg_time_per_op_us": (elapsed / n_ops) * 1_000_000,
    }


def benchmark_eviction_with_effective_priority(n_entries: int = 1000) -> dict:
    """Benchmark eviction using effective priority."""
    cache = CacheLayer(mem=MemoryTier(max_size=n_entries // 2))

    # Add entries with varying ages
    start = time.perf_counter()
    for i in range(n_entries):
        cache.set(
            key=f"entry_{i}", value={"data": f"value_{i}"}, ttl_seconds=100.0, priority=0.5, sustain_time_seconds=30.0
        )
        # Age some entries
        if i % 10 == 0:
            entry = cache.mem.get(f"entry_{i}")
            if entry:
                entry.meta.created_at = time.time() - 50.0  # Past sustain phase
    end = time.perf_counter()

    elapsed = end - start

    return {
        "operation": "eviction_with_effective_priority",
        "entries_added": n_entries,
        "cache_max_size": n_entries // 2,
        "elapsed_seconds": elapsed,
        "entries_per_second": n_entries / elapsed,
        "avg_time_per_entry_us": (elapsed / n_entries) * 1_000_000,
    }


def run_all_benchmarks() -> dict:
    """Run all benchmarks and return results."""
    print("Running performance benchmarks...")
    print("=" * 80)

    results = {}

    print("\n1. Honor Decay Benchmark...")
    results["honor_decay"] = benchmark_honor_decay(10000)
    print(f"   {results['honor_decay']['ops_per_second']:.0f} ops/sec")

    print("\n2. De-escalation Check Benchmark...")
    results["de_escalation"] = benchmark_de_escalation_check(10000)
    print(f"   {results['de_escalation']['ops_per_second']:.0f} ops/sec")

    print("\n3. Effective Priority Benchmark...")
    results["effective_priority"] = benchmark_effective_priority(10000)
    print(f"   {results['effective_priority']['ops_per_second']:.0f} ops/sec")

    print("\n4. Sustain Phase Check Benchmark...")
    results["sustain_phase"] = benchmark_sustain_phase_check(10000)
    print(f"   {results['sustain_phase']['ops_per_second']:.0f} ops/sec")

    print("\n5. Cache Operations with Decay Benchmark...")
    results["cache_ops"] = benchmark_cache_operations_with_decay(1000, 10000)
    print(f"   {results['cache_ops']['ops_per_second']:.0f} ops/sec")

    print("\n6. Eviction with Effective Priority Benchmark...")
    results["eviction"] = benchmark_eviction_with_effective_priority(1000)
    print(f"   {results['eviction']['entries_per_second']:.0f} entries/sec")

    print("\n" + "=" * 80)
    print("Benchmarks complete!")

    return results


if __name__ == "__main__":
    import json

    results = run_all_benchmarks()

    # Save results
    output_file = Path(__file__).parent.parent / "data" / "benchmark_arena_structure.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
