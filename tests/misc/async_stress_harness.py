import argparse
import asyncio
import json
import random
import time
from pathlib import Path
from statistics import mean
from typing import Any

try:
    import psutil  # optional
except ImportError:  # pragma: no cover
    psutil = None

from grid.application import IntelligenceApplication


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = int(0.95 * (len(values) - 1))
    return values[k]


def p99(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = int(0.99 * (len(values) - 1))
    return values[k]


async def run_once(app: IntelligenceApplication, seed: int) -> float:
    random.seed(seed)
    data = {
        "value": random.random(),
        "decay_rate": 0.99,
        "context_decay_rate": 0.995,
        "spatial_drift": 0.05,
    }
    ctx = {
        "temporal_depth": 1.0 + random.random() * 0.1,
        "spatial_field": {"x": random.random(), "y": random.random()},
        "coherence": 0.5 + random.random() * 0.1,
    }
    t0 = time.perf_counter()
    await app.process_input(data, ctx)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0  # ms


async def main(args):
    app = IntelligenceApplication()
    latencies: list[float] = []
    mem_samples: list[int] = []

    async def worker(worker_id: int):
        for i in range(args.repeats):
            ms = await run_once(app, seed=worker_id * 10_000 + i)
            latencies.append(ms)
            if psutil and args.mem_sample_every > 0 and i % args.mem_sample_every == 0:
                mem_samples.append(psutil.Process().memory_info().rss)

    tasks = [asyncio.create_task(worker(w)) for w in range(args.concurrency)]

    t0 = time.perf_counter()
    await asyncio.gather(*tasks)
    t1 = time.perf_counter()

    total_ms = (t1 - t0) * 1000.0
    summary: dict[str, Any] = {
        "concurrency": args.concurrency,
        "repeats_per_worker": args.repeats,
        "calls": len(latencies),
        "latency_ms_mean": mean(latencies) if latencies else 0.0,
        "latency_ms_p95": p95(latencies),
        "latency_ms_p99": p99(latencies),
        "wall_clock_ms": total_ms,
    }
    if mem_samples:
        summary["mem_rss_mean"] = mean(mem_samples)
        summary["mem_rss_max"] = max(mem_samples)

    out_path = Path(args.output)
    out_data: dict[str, Any] = {"summary": summary}
    if args.save_latencies:
        out_data["latencies_ms"] = latencies
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"Stress metrics saved to: {out_path}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async stress harness for GRID pipeline")
    parser.add_argument("--concurrency", type=int, default=100, help="Number of concurrent workers")
    parser.add_argument("--repeats", type=int, default=10, help="Number of calls per worker")
    parser.add_argument("--mem-sample-every", type=int, default=5, help="Sample memory every N calls (requires psutil)")
    parser.add_argument("--output", type=str, default="data/stress_metrics.json", help="Output JSON path")
    parser.add_argument("--save-latencies", action="store_true", help="Include per-call latencies in output")
    args = parser.parse_args()

    asyncio.run(main(args))
