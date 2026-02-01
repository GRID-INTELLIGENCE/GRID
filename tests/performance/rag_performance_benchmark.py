#!/usr/bin/env python3
"""
Performance benchmarking framework for GRID conversational RAG system.

Measures:
- Query latency and throughput
- Memory usage and session management
- Multi-hop reasoning performance
- Streaming API performance
- Comparison with original RAG system
"""

import asyncio
import json
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from tools.rag.config import RAGConfig
from tools.rag.conversational_rag import ConversationalRAGEngine
from tools.rag.rag_engine import RAGEngine


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""

    operation: str
    duration_ms: float
    memory_usage_mb: float
    success: bool
    metadata: dict[str, Any]
    timestamp: datetime = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "success": self.success,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark run."""

    test_name: str
    metrics: list[PerformanceMetrics]
    config: dict[str, Any]
    start_time: datetime = datetime.now()
    end_time: datetime = datetime.now()

    def add_metric(self, metric: PerformanceMetrics) -> None:
        """Add a performance metric."""
        self.metrics.append(metric)

    def calculate_stats(self) -> dict[str, Any]:
        """Calculate performance statistics."""
        durations = [m.duration_ms for m in self.metrics if m.success]
        memory_usage = [m.memory_usage_mb for m in self.metrics if m.success]

        return {
            "test_name": self.test_name,
            "total_operations": len(self.metrics),
            "successful_operations": sum(1 for m in self.metrics if m.success),
            "failed_operations": sum(1 for m in self.metrics if not m.success),
            "success_rate": sum(1 for m in self.metrics if m.success) / len(self.metrics) if self.metrics else 0,
            "total_duration_ms": round(sum(durations), 2) if durations else 0,
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "min_duration_ms": round(min(durations), 2) if durations else 0,
            "max_duration_ms": round(max(durations), 2) if durations else 0,
            "avg_memory_usage_mb": round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
            "min_memory_usage_mb": round(min(memory_usage), 2) if memory_usage else 0,
            "max_memory_usage_mb": round(max(memory_usage), 2) if memory_usage else 0,
            "throughput_ops_per_sec": round(len(durations) / (sum(durations) / 1000), 2) if durations else 0,
            "config": self.config,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
        }

    def save_to_file(self, filename: str) -> None:
        """Save benchmark results to file."""
        stats = self.calculate_stats()

        result = {"benchmark": stats, "metrics": [m.to_dict() for m in self.metrics]}

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


class RAGPerformanceBenchmark:
    """Performance benchmarking for RAG systems."""

    def __init__(self, config: RAGConfig | None = None):
        """Initialize benchmark with optional configuration."""
        self.config = config or RAGConfig()
        self.original_engine = RAGEngine(self.config)
        self.conversational_engine = ConversationalRAGEngine(self.config)

        # Create test queries
        self.test_queries = [
            "What is the GRID system?",
            "How does RAG work in GRID?",
            "What are the 9 cognition patterns?",
            "Explain the agentic system architecture",
            "How does conversation memory work?",
            "What is multi-hop reasoning?",
            "Describe the streaming API capabilities",
            "How are citations improved in conversational RAG?",
            "What performance optimizations are implemented?",
            "Explain the session management system",
        ]

        # Create session IDs for testing
        self.session_ids = [f"test-session-{i}" for i in range(10)]

    async def measure_query_performance(self, engine, query: str, session_id: str | None = None) -> PerformanceMetrics:
        """Measure performance of a single query."""
        tracemalloc.start()
        start_time = time.perf_counter()

        try:
            if session_id:
                result = await engine.query(query, session_id=session_id)
            else:
                result = await engine.query(query)

            success = "answer" in result

        except Exception as e:
            success = False
            result = {"error": str(e)}

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        memory_usage_mb = peak / (1024 * 1024)
        tracemalloc.stop()

        metadata = {
            "query": query,
            "session_id": session_id,
            "engine_type": type(engine).__name__,
            "result_size": len(str(result)) if success else 0,
            "source_count": len(result.get("sources", [])) if success else 0,
            "conversation_metadata": result.get("conversation_metadata", {}) if success else {},
        }

        return PerformanceMetrics(
            operation="query",
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            success=success,
            metadata=metadata,
        )

    async def measure_session_management(self, engine) -> list[PerformanceMetrics]:
        """Measure session management performance."""
        metrics = []

        # Test session creation
        for session_id in self.session_ids:
            tracemalloc.start()
            start_time = time.perf_counter()

            try:
                engine.create_session(session_id)
                success = True
            except Exception:
                success = False

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            current, peak = tracemalloc.get_traced_memory()
            memory_usage_mb = peak / (1024 * 1024)
            tracemalloc.stop()

            metrics.append(
                PerformanceMetrics(
                    operation="session_creation",
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_usage_mb,
                    success=success,
                    metadata={"session_id": session_id},
                )
            )

        # Test session retrieval
        for session_id in self.session_ids:
            tracemalloc.start()
            start_time = time.perf_counter()

            try:
                session_info = engine.get_session_info(session_id)
                success = session_info is not None
            except Exception:
                success = False
                session_info = None

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            current, peak = tracemalloc.get_traced_memory()
            memory_usage_mb = peak / (1024 * 1024)
            tracemalloc.stop()

            metrics.append(
                PerformanceMetrics(
                    operation="session_retrieval",
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_usage_mb,
                    success=success,
                    metadata={
                        "session_id": session_id,
                        "turn_count": session_info.get("turn_count", 0) if session_info else 0,
                    },
                )
            )

        return metrics

    async def measure_multi_hop_performance(self, engine) -> list[PerformanceMetrics]:
        """Measure multi-hop reasoning performance."""
        metrics = []

        # Enable multi-hop for this test
        original_setting = None
        if hasattr(engine.config, "multi_hop_enabled"):
            original_setting = engine.config.multi_hop_enabled
            engine.config.multi_hop_enabled = True

        for i, query in enumerate(self.test_queries[:5]):  # Use subset for multi-hop
            session_id = self.session_ids[i % len(self.session_ids)]

            tracemalloc.start()
            start_time = time.perf_counter()

            try:
                result = await engine.query(query, session_id=session_id, enable_multi_hop=True)
                success = "answer" in result

                if success:
                    hops = result.get("hops_performed", 1)
                else:
                    hops = 0

            except Exception as e:
                success = False
                result = {"error": str(e)}
                hops = 0

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            current, peak = tracemalloc.get_traced_memory()
            memory_usage_mb = peak / (1024 * 1024)
            tracemalloc.stop()

            metadata = {
                "query": query,
                "session_id": session_id,
                "hops_performed": hops,
                "multi_hop_used": result.get("multi_hop_used", False) if success else False,
            }

            metrics.append(
                PerformanceMetrics(
                    operation="multi_hop_query",
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_usage_mb,
                    success=success,
                    metadata=metadata,
                )
            )

        # Restore original setting
        if hasattr(engine.config, "multi_hop_enabled"):
            engine.config.multi_hop_enabled = original_setting

        return metrics

    async def measure_batch_performance(self, engine) -> PerformanceMetrics:
        """Measure batch query performance."""
        tracemalloc.start()
        start_time = time.perf_counter()

        batch = []
        results = []
        success = False

        try:
            # Create batch of queries
            batch = [
                {"query": query, "session_id": self.session_ids[i % len(self.session_ids)]}
                for i, query in enumerate(self.test_queries)
            ]

            # For conversational engine, we'd use the streaming API
            # For this test, we'll simulate batch processing
            results = []
            for item in batch:
                result = await engine.query(item["query"], session_id=item.get("session_id"))
                results.append(result)

            success = len(results) == len(batch)

        except Exception:
            success = False
            results = []

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        current, peak = tracemalloc.get_traced_memory()
        memory_usage_mb = peak / (1024 * 1024)
        tracemalloc.stop()

        metadata = {
            "batch_size": len(batch),
            "successful_queries": sum(1 for r in results if "answer" in r),
            "failed_queries": sum(1 for r in results if "answer" not in r),
        }

        return PerformanceMetrics(
            operation="batch_query",
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            success=success,
            metadata=metadata,
        )

    async def run_comprehensive_benchmark(self) -> BenchmarkResult:
        """Run comprehensive performance benchmark."""
        result = BenchmarkResult(
            test_name="comprehensive_rag_performance",
            metrics=[],
            config={
                "engine_config": {
                    "conversation_enabled": getattr(self.config, "conversation_enabled", False),
                    "multi_hop_enabled": getattr(self.config, "multi_hop_enabled", False),
                    "conversation_memory_size": getattr(self.config, "conversation_memory_size", 10),
                    "embedding_model": getattr(self.config, "embedding_model", "nomic-embed-text:latest"),
                    "llm_model_local": getattr(self.config, "llm_model_local", "ministral-3:3b"),
                },
                "test_queries_count": len(self.test_queries),
                "test_sessions_count": len(self.session_ids),
            },
        )

        print("Running Comprehensive RAG Performance Benchmark")
        print(f"Test Configuration: {len(self.test_queries)} queries, {len(self.session_ids)} sessions")
        print(f"Engine: {type(self.conversational_engine).__name__}")

        # Test 1: Single query performance
        print("\nTesting Single Query Performance...")
        for i, query in enumerate(self.test_queries):
            session_id = self.session_ids[i % len(self.session_ids)]
            metric = await self.measure_query_performance(self.conversational_engine, query, session_id)
            result.add_metric(metric)
            status = "OK" if metric.success else "FAILED"
            print(f"  Query {i+1}: {metric.duration_ms:.1f}ms, {metric.memory_usage_mb:.2f}MB, {status}")

        # Test 2: Session management
        print("\nTesting Session Management...")
        session_metrics = await self.measure_session_management(self.conversational_engine)
        for metric in session_metrics:
            result.add_metric(metric)

        creation_times = [m.duration_ms for m in session_metrics if m.operation == "session_creation"]
        retrieval_times = [m.duration_ms for m in session_metrics if m.operation == "session_retrieval"]

        if creation_times:
            print(f"  Session Creation: Avg {sum(creation_times)/len(creation_times):.1f}ms")
        if retrieval_times:
            print(f"  Session Retrieval: Avg {sum(retrieval_times)/len(retrieval_times):.1f}ms")

        # Test 3: Multi-hop performance
        if hasattr(self.conversational_engine.config, "multi_hop_enabled"):
            print("\nTesting Multi-hop Reasoning...")
            multi_hop_metrics = await self.measure_multi_hop_performance(self.conversational_engine)
            for metric in multi_hop_metrics:
                result.add_metric(metric)

            hop_times = [m.duration_ms for m in multi_hop_metrics]
            if hop_times:
                print(f"  Multi-hop Queries: Avg {sum(hop_times)/len(hop_times):.1f}ms")

        # Test 4: Batch performance
        print("\nTesting Batch Query Performance...")
        batch_metric = await self.measure_batch_performance(self.conversational_engine)
        result.add_metric(batch_metric)
        status = "OK" if batch_metric.success else "FAILED"
        print(
            f"  Batch Query: {batch_metric.duration_ms:.1f}ms for {batch_metric.metadata.get('batch_size', 0)} queries, {status}"
        )

        # Test 5: Comparison with original RAG
        print("\nComparing with Original RAG...")
        for i, query in enumerate(self.test_queries[:3]):  # Sample subset
            original_metric = await self.measure_query_performance(self.original_engine, query)
            conversational_metric = await self.measure_query_performance(self.conversational_engine, query)

            result.add_metric(original_metric)
            result.add_metric(conversational_metric)

            orig_status = "OK" if original_metric.success else "FAILED"
            conv_status = "OK" if conversational_metric.success else "FAILED"
            print(
                f"  Query {i+1}: Original {original_metric.duration_ms:.1f}ms ({orig_status}) vs Conversational {conversational_metric.duration_ms:.1f}ms ({conv_status})"
            )

        result.end_time = datetime.now()
        print(f"\nBenchmark completed in {(result.end_time - result.start_time).total_seconds():.1f} seconds")

        return result

    async def run_streaming_benchmark(self) -> BenchmarkResult:
        """Run streaming API performance benchmark."""
        result = BenchmarkResult(
            test_name="streaming_api_performance",
            metrics=[],
            config={
                "engine_config": {
                    "conversation_enabled": getattr(self.config, "conversation_enabled", False),
                    "multi_hop_enabled": getattr(self.config, "multi_hop_enabled", False),
                },
                "test_type": "streaming_api",
            },
        )

        print("Running Streaming API Performance Benchmark")

        # Import streaming components
        try:
            from application.mothership.routers.rag_streaming import StreamChunk, chunk_text

            # Test text chunking performance
            sample_text = (
                "This is a sample response that will be streamed to the client in chunks for real-time display."
            )

            tracemalloc.start()
            start_time = time.perf_counter()

            chunks = chunk_text(sample_text, chunk_size=20)

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            current, peak = tracemalloc.get_traced_memory()
            memory_usage_mb = peak / (1024 * 1024)
            tracemalloc.stop()

            result.add_metric(
                PerformanceMetrics(
                    operation="text_chunking",
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_usage_mb,
                    success=True,
                    metadata={"text_length": len(sample_text), "chunk_count": len(chunks), "chunk_size": 20},
                )
            )

            print(f"  Text Chunking: {duration_ms:.2f}ms for {len(chunks)} chunks")

            # Test stream chunk creation
            tracemalloc.start()
            start_time = time.perf_counter()

            chunk = StreamChunk("answer_chunk", {"chunk": "Sample", "chunk_number": 1})
            json_data = chunk.to_json()

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            current, peak = tracemalloc.get_traced_memory()
            memory_usage_mb = peak / (1024 * 1024)
            tracemalloc.stop()

            result.add_metric(
                PerformanceMetrics(
                    operation="stream_chunk_creation",
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_usage_mb,
                    success=True,
                    metadata={"chunk_size": len(json_data)},
                )
            )

            print(f"  Stream Chunk Creation: {duration_ms:.2f}ms")

        except ImportError as e:
            print(f"  ⚠️ Streaming components not available: {e}")
            result.add_metric(
                PerformanceMetrics(
                    operation="streaming_import",
                    duration_ms=0,
                    memory_usage_mb=0,
                    success=False,
                    metadata={"error": str(e)},
                )
            )

        result.end_time = datetime.now()
        return result


async def main():
    """Run performance benchmarks."""
    print("=" * 60)
    print("GRID RAG Performance Benchmarking")
    print("=" * 60)

    # Create benchmark
    benchmark = RAGPerformanceBenchmark()

    # Run comprehensive benchmark
    print("\nRunning Comprehensive Performance Benchmark...")
    comprehensive_result = await benchmark.run_comprehensive_benchmark()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"rag_performance_benchmark_{timestamp}.json"
    comprehensive_result.save_to_file(output_file)
    print(f"\nResults saved to: {output_file}")

    # Show summary
    stats = comprehensive_result.calculate_stats()
    print("\nComprehensive Benchmark Summary:")
    print(f"  Total Operations: {stats['total_operations']}")
    print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")
    print(f"  Avg Query Time: {stats['avg_duration_ms']:.1f}ms")
    print(f"  Avg Memory Usage: {stats['avg_memory_usage_mb']:.2f}MB")
    print(f"  Throughput: {stats['throughput_ops_per_sec']:.1f} ops/sec")

    # Run streaming benchmark
    print("\nRunning Streaming API Benchmark...")
    streaming_result = await benchmark.run_streaming_benchmark()

    # Save streaming results
    streaming_file = f"streaming_performance_benchmark_{timestamp}.json"
    streaming_result.save_to_file(streaming_file)
    print(f"\nStreaming results saved to: {streaming_file}")

    # Show streaming summary
    streaming_stats = streaming_result.calculate_stats()
    print("\nStreaming Benchmark Summary:")
    print(f"  Total Operations: {streaming_stats['total_operations']}")
    print(f"  Success Rate: {streaming_stats['success_rate'] * 100:.1f}%")
    print(f"  Avg Operation Time: {streaming_stats['avg_duration_ms']:.2f}ms")

    print("\n" + "=" * 60)
    print("Performance Benchmarking Completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
