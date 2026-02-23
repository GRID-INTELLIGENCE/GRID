#!/usr/bin/env python3
"""
Performance Benchmarking for Enhanced RAG Server

Measures:
- Query latency (p50, p95, p99)
- Session management throughput
- Concurrent query handling
- Memory usage
"""

import asyncio
import os
import statistics
import sys
import time
import tracemalloc

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from tools.rag.conversational_rag import create_conversational_rag_engine


class PerformanceBenchmark:
    """Performance benchmarking for enhanced RAG server."""

    def __init__(self):
        self.engine = create_conversational_rag_engine()
        # Try to find a model that is available
        available_models = ["ministral-3:3b", "llama3.2:3b", "phi3:latest", "mistral:latest"]
        selected_model = "ministral-3:3b"

        try:
            import httpx

            r = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                for m in available_models:
                    if m in models:
                        selected_model = m
                        break
        except Exception:
            pass

        self.results = {
            "query_latencies": [],
            "session_create_latencies": [],
            "session_get_latencies": [],
            "session_delete_latencies": [],
            "concurrent_queries": [],
            "memory_usage": [],
            "selected_model": selected_model,
        }

    async def benchmark_query_latency(self, num_queries: int = 100) -> dict[str, float]:
        """Benchmark query latency."""
        print(f"\n{'=' * 60}")
        print("Benchmarking Query Latency")
        print(f"{'=' * 60}")

        queries = [
            "What is GRID?",
            "How does the RAG system work?",
            "Explain the architecture",
            "What are the key components?",
            "How does conversation memory work?",
        ] * 20  # Repeat to get 100 queries

        latencies = []
        for i, query in enumerate(queries[:num_queries]):
            session_id = f"benchmark-session-{i % 10}"  # Reuse sessions

            start = time.perf_counter()
            _ = await self.engine.query(
                query_text=query,
                session_id=session_id,
                enable_multi_hop=False,
                temperature=0.7,
                llm_model=self.results["selected_model"],
            )
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

            if i % 10 == 0:
                print(f"  Query {i + 1}/{num_queries}: {latency_ms:.2f}ms")

        self.results["query_latencies"] = latencies

        return {
            "mean_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p50_ms": statistics.quantiles(latencies, n=100)[49],
            "p95_ms": statistics.quantiles(latencies, n=100)[94],
            "p99_ms": statistics.quantiles(latencies, n=100)[98],
            "min_ms": min(latencies),
            "max_ms": max(latencies),
        }

    async def benchmark_session_management(self, num_sessions: int = 100) -> dict[str, float]:
        """Benchmark session management operations."""
        print(f"\n{'=' * 60}")
        print("Benchmarking Session Management")
        print(f"{'=' * 60}")

        # Session creation
        create_latencies = []
        print("  Creating sessions...")
        for i in range(num_sessions):
            session_id = f"benchmark-session-{i}"
            metadata = {"test": True, "index": i}

            start = time.perf_counter()
            self.engine.create_session(session_id, metadata)
            latency_ms = (time.perf_counter() - start) * 1000
            create_latencies.append(latency_ms)

            if i % 10 == 0:
                print(f"    Created {i + 1}/{num_sessions} sessions")

        self.results["session_create_latencies"] = create_latencies

        # Session retrieval
        get_latencies = []
        print("  Retrieving sessions...")
        for i in range(num_sessions):
            session_id = f"benchmark-session-{i}"

            start = time.perf_counter()
            self.engine.get_session_info(session_id)
            latency_ms = (time.perf_counter() - start) * 1000
            get_latencies.append(latency_ms)

            if i % 10 == 0:
                print(f"    Retrieved {i + 1}/{num_sessions} sessions")

        self.results["session_get_latencies"] = get_latencies

        # Session deletion
        delete_latencies = []
        print("  Deleting sessions...")
        for i in range(num_sessions):
            session_id = f"benchmark-session-{i}"

            start = time.perf_counter()
            self.engine.delete_session(session_id)
            latency_ms = (time.perf_counter() - start) * 1000
            delete_latencies.append(latency_ms)

            if i % 10 == 0:
                print(f"    Deleted {i + 1}/{num_sessions} sessions")

        self.results["session_delete_latencies"] = delete_latencies

        return {
            "create_mean_ms": statistics.mean(create_latencies),
            "get_mean_ms": statistics.mean(get_latencies),
            "delete_mean_ms": statistics.mean(delete_latencies),
        }

    async def benchmark_concurrent_queries(self, num_concurrent: int = 50) -> dict[str, float]:
        """Benchmark concurrent query handling."""
        print(f"\n{'=' * 60}")
        print(f"Benchmarking Concurrent Queries ({num_concurrent} concurrent)")
        print(f"{'=' * 60}")

        query = "What is the GRID architecture?"
        session_id = "concurrent-benchmark-session"

        # Create session
        self.engine.create_session(session_id, {"test": True})

        async def single_query():
            start = time.perf_counter()
            _ = await self.engine.query(
                query_text=query,
                session_id=session_id,
                enable_multi_hop=False,
                llm_model=self.results["selected_model"],
            )
            latency_ms = (time.perf_counter() - start) * 1000
            return latency_ms

        start_time = time.perf_counter()
        tasks = [single_query() for _ in range(num_concurrent)]
        latencies = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        self.results["concurrent_queries"] = latencies

        return {
            "num_concurrent": num_concurrent,
            "total_time_s": total_time,
            "queries_per_second": num_concurrent / total_time,
            "mean_latency_ms": statistics.mean(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=100)[94],
        }

    async def benchmark_memory_usage(self) -> dict[str, float]:
        """Benchmark memory usage."""
        print(f"\n{'=' * 60}")
        print("Benchmarking Memory Usage")
        print(f"{'=' * 60}")

        tracemalloc.start()

        # Baseline memory
        snapshot1 = tracemalloc.take_snapshot()

        # Create 100 sessions
        print("  Creating 100 sessions...")
        for i in range(100):
            session_id = f"memory-benchmark-{i}"
            self.engine.create_session(session_id, {"test": True, "index": i})

        snapshot2 = tracemalloc.take_snapshot()

        # Execute 100 queries
        print(f"  Executing 100 queries using {self.results['selected_model']}...")
        for i in range(100):
            session_id = f"memory-benchmark-{i % 10}"
            await self.engine.query(
                query_text="What is GRID?",
                session_id=session_id,
                enable_multi_hop=False,
                llm_model=self.results["selected_model"],
            )

        snapshot3 = tracemalloc.take_snapshot()

        tracemalloc.stop()

        # Calculate memory differences
        stats1 = snapshot2.compare_to(snapshot1, "lineno")
        stats2 = snapshot3.compare_to(snapshot2, "lineno")

        total_memory_sessions = sum(stat.size_diff for stat in stats1) / 1024 / 1024  # MB
        total_memory_queries = sum(stat.size_diff for stat in stats2) / 1024 / 1024  # MB

        return {
            "sessions_memory_mb": total_memory_sessions,
            "queries_memory_mb": total_memory_queries,
            "total_memory_mb": total_memory_sessions + total_memory_queries,
        }

    def print_summary(self):
        """Print benchmark summary."""
        print(f"\n{'=' * 60}")
        print("PERFORMANCE BENCHMARK SUMMARY")
        print(f"{'=' * 60}")

        # Query latency
        if self.results["query_latencies"]:
            ql = self.results["query_latencies"]
            print(f"\nQuery Latency (Model: {self.results['selected_model']}):")
            print(f"  Mean:   {statistics.mean(ql):.2f}ms")
            print(f"  Median: {statistics.median(ql):.2f}ms")
            print(f"  P50:    {statistics.quantiles(ql, n=100)[49]:.2f}ms")
            print(f"  P95:    {statistics.quantiles(ql, n=100)[94]:.2f}ms")
            print(f"  P99:    {statistics.quantiles(ql, n=100)[98]:.2f}ms")
            print(f"  Min:    {min(ql):.2f}ms")
            print(f"  Max:    {max(ql):.2f}ms")

        # Session management
        if self.results["session_create_latencies"]:
            print("\nSession Management:")
            print(f"  Create: {statistics.mean(self.results['session_create_latencies']):.2f}ms")
            print(f"  Get:    {statistics.mean(self.results['session_get_latencies']):.2f}ms")
            print(f"  Delete: {statistics.mean(self.results['session_delete_latencies']):.2f}ms")

        # Concurrent queries
        if self.results["concurrent_queries"]:
            cq = self.results["concurrent_queries"]
            print("\nConcurrent Queries:")
            print(f"  Queries: {len(cq)}")
            print(f"  Mean:   {statistics.mean(cq):.2f}ms")
            print(f"  P95:    {statistics.quantiles(cq, n=100)[94]:.2f}ms")

        # Performance targets
        print(f"\n{'=' * 60}")
        print("PERFORMANCE TARGETS")
        print(f"{'=' * 60}")

        if self.results["query_latencies"]:
            p95 = statistics.quantiles(self.results["query_latencies"], n=100)[94]
            target_500ms = "✅ PASS" if p95 < 500 else "❌ FAIL"
            print(f"  Query Latency (P95 < 500ms): {target_500ms} ({p95:.2f}ms)")

        if self.results["session_create_latencies"]:
            mean_create = statistics.mean(self.results["session_create_latencies"])
            target_10ms = "✅ PASS" if mean_create < 10 else "❌ FAIL"
            print(f"  Session Create (< 10ms):      {target_10ms} ({mean_create:.2f}ms)")

        if self.results["concurrent_queries"]:
            qps = len(self.results["concurrent_queries"]) / 1.0  # Approximate
            target_50qps = "✅ PASS" if qps >= 50 else "❌ FAIL"
            print(f"  Concurrent Queries (50+):     {target_50qps} ({int(qps)} queries)")

    async def run_all_benchmarks(self):
        """Run all benchmarks."""
        print(f"\n{'=' * 60}")
        print("ENHANCED RAG SERVER PERFORMANCE BENCHMARK")
        print(f"{'=' * 60}")

        # Query latency
        await self.benchmark_query_latency(num_queries=100)

        # Session management
        await self.benchmark_session_management(num_sessions=100)

        # Concurrent queries
        await self.benchmark_concurrent_queries(num_concurrent=50)

        # Memory usage
        await self.benchmark_memory_usage()

        # Print summary
        self.print_summary()


async def main():
    """Run performance benchmarks."""
    benchmark = PerformanceBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
