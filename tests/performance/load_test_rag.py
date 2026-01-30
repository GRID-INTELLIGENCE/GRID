#!/usr/bin/env python3
"""
Load Testing for Enhanced RAG Server

Simulates production traffic patterns and tests system under load.
"""

import asyncio
import os
import random
import statistics
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.rag.conversational_rag import create_conversational_rag_engine


class LoadTest:
    """Load testing for enhanced RAG server."""

    def __init__(self):
        self.engine = create_conversational_rag_engine()
        self.queries = [
            "What is GRID?",
            "How does the RAG system work?",
            "Explain the architecture",
            "What are the key components?",
            "How does conversation memory work?",
            "What is multi-hop reasoning?",
            "How do I query the knowledge base?",
            "What is the fallback mechanism?",
            "How are sessions managed?",
            "What is the performance target?",
        ]

    async def simulate_user_session(self, user_id: int, num_queries: int = 10) -> dict[str, any]:
        """Simulate a user session with multiple queries."""
        session_id = f"load-test-user-{user_id}"

        # Create session
        self.engine.create_session(session_id, {"user_id": user_id, "test": True})

        latencies = []
        errors = 0

        for i in range(num_queries):
            query = random.choice(self.queries)

            try:
                start = time.perf_counter()
                result = await self.engine.query(
                    query_text=query,
                    session_id=session_id,
                    enable_multi_hop=random.choice([True, False]),
                    temperature=0.7
                )
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)

                # Simulate think time between queries
                await asyncio.sleep(random.uniform(0.1, 0.5))

            except Exception as e:
                errors += 1
                print(f"  User {user_id} query {i+1} failed: {e}")

        # Delete session
        self.engine.delete_session(session_id)

        return {
            "user_id": user_id,
            "queries": num_queries,
            "errors": errors,
            "latencies": latencies,
            "mean_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies) if latencies else 0,
        }

    async def run_load_test(
        self,
        num_users: int = 100,
        queries_per_user: int = 10,
        concurrent_users: int = 10
    ) -> dict[str, any]:
        """Run load test with multiple concurrent users."""
        print(f"\n{'='*60}")
        print(f"LOAD TEST: {num_users} users, {queries_per_user} queries each")
        print(f"Concurrent users: {concurrent_users}")
        print(f"{'='*60}")

        start_time = time.perf_counter()

        # Create batches of concurrent users
        results = []
        for batch_start in range(0, num_users, concurrent_users):
            batch_end = min(batch_start + concurrent_users, num_users)
            batch_users = range(batch_start, batch_end)

            print(f"\nRunning batch {batch_start}-{batch_end}...")

            # Run users in parallel
            tasks = [
                self.simulate_user_session(user_id, queries_per_user)
                for user_id in batch_users
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Small delay between batches
            await asyncio.sleep(0.5)

        total_time = time.perf_counter() - start_time

        # Calculate aggregate statistics
        all_latencies = []
        total_errors = 0
        total_queries = 0

        for result in results:
            all_latencies.extend(result["latencies"])
            total_errors += result["errors"]
            total_queries += result["queries"]

        success_rate = ((total_queries - total_errors) / total_queries) * 100 if total_queries > 0 else 0
        queries_per_second = total_queries / total_time if total_time > 0 else 0

        print(f"\n{'='*60}")
        print("LOAD TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Users:     {num_users}")
        print(f"Total Queries:   {total_queries}")
        print(f"Total Errors:    {total_errors}")
        print(f"Success Rate:    {success_rate:.2f}%")
        print(f"Total Time:      {total_time:.2f}s")
        print(f"Queries/Second:  {queries_per_second:.2f}")
        print("\nLatency:")
        print(f"  Mean:          {statistics.mean(all_latencies):.2f}ms")
        print(f"  Median:        {statistics.median(all_latencies):.2f}ms")
        print(f"  P50:           {statistics.quantiles(all_latencies, n=100)[49]:.2f}ms")
        print(f"  P95:           {statistics.quantiles(all_latencies, n=100)[94]:.2f}ms")
        print(f"  P99:           {statistics.quantiles(all_latencies, n=100)[98]:.2f}ms")

        # Performance targets
        print(f"\n{'='*60}")
        print("PERFORMANCE TARGETS")
        print(f"{'='*60}")

        target_success = "✅ PASS" if success_rate >= 99 else "❌ FAIL"
        print(f"  Success Rate (≥99%):         {target_success} ({success_rate:.2f}%)")

        target_qps = "✅ PASS" if queries_per_second >= 50 else "❌ FAIL"
        print(f"  Queries/Second (≥50):         {target_qps} ({queries_per_second:.2f})")

        if all_latencies:
            p95 = statistics.quantiles(all_latencies, n=100)[94]
            target_p95 = "✅ PASS" if p95 < 500 else "❌ FAIL"
            print(f"  P95 Latency (< 500ms):        {target_p95} ({p95:.2f}ms)")

        return {
            "num_users": num_users,
            "queries_per_user": queries_per_user,
            "concurrent_users": concurrent_users,
            "total_queries": total_queries,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "total_time_s": total_time,
            "queries_per_second": queries_per_second,
            "mean_latency_ms": statistics.mean(all_latencies),
            "p95_latency_ms": statistics.quantiles(all_latencies, n=100)[94],
        }

    async def test_stress_load(self, max_users: int = 200) -> dict[str, any]:
        """Test system under increasing load."""
        print(f"\n{'='*60}")
        print("STRESS TEST: Increasing Load")
        print(f"{'='*60}")

        results = []

        for num_users in [10, 25, 50, 100, 150, 200]:
            if num_users > max_users:
                continue

            print(f"\nTesting with {num_users} concurrent users...")
            result = await self.run_load_test(
                num_users=num_users,
                queries_per_user=5,
                concurrent_users=num_users
            )
            results.append(result)

            # Check if system is failing
            if result["success_rate"] < 95:
                print(f"\n⚠️  System degraded at {num_users} users")
                break

        print(f"\n{'='*60}")
        print("STRESS TEST SUMMARY")
        print(f"{'='*60}")

        for i, result in enumerate(results):
            print(f"\n{result['num_users']} users:")
            print(f"  Success Rate:    {result['success_rate']:.2f}%")
            print(f"  Queries/Second:  {result['queries_per_second']:.2f}")
            print(f"  P95 Latency:     {result['p95_latency_ms']:.2f}ms")

        return results


async def main():
    """Run load tests."""
    load_test = LoadTest()

    # Standard load test
    await load_test.run_load_test(
        num_users=100,
        queries_per_user=10,
        concurrent_users=10
    )

    # Stress test
    await load_test.test_stress_load(max_users=200)


if __name__ == "__main__":
    asyncio.run(main())
