"""
Knowledge Base Performance Testing
===================================

Comprehensive performance testing and benchmarking suite for the GRID
Knowledge Base system. Tests search, generation, and ingestion performance.
"""

import logging
import time
import asyncio
import statistics
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import concurrent.futures
import json

from ..core.config import KnowledgeBaseConfig
from ..core.database import KnowledgeBaseDB
from ..embeddings.engine import EmbeddingEngine
from ..embeddings.llm_generator import LLMGenerator
from ..search.retriever import VectorRetriever
from ..ingestion.pipeline import DataIngestionPipeline

logger = logging.getLogger(__name__)


@dataclass
class PerformanceResult:
    """Result of a performance test."""
    test_name: str
    duration: float
    operations: int
    throughput: float  # operations per second
    avg_latency: float
    min_latency: float
    max_latency: float
    p95_latency: float
    p99_latency: float
    errors: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    duration_seconds: int = 60
    concurrency: int = 10
    warmup_seconds: int = 10
    ramp_up_seconds: int = 5


class SearchBenchmark:
    """Benchmark search performance."""

    def __init__(self, retriever: VectorRetriever):
        self.retriever = retriever
        self.sample_queries = [
            "What is machine learning?",
            "How does vector search work?",
            "Explain natural language processing",
            "What are embeddings in AI?",
            "How to implement RAG systems?",
            "What is the difference between supervised and unsupervised learning?",
            "How do transformers work?",
            "What is retrieval augmented generation?",
            "Explain the concept of semantic search",
            "How to optimize vector databases?"
        ]

    def run_benchmark(self, config: BenchmarkConfig) -> PerformanceResult:
        """Run search performance benchmark."""
        logger.info(f"Starting search benchmark: {config.concurrency} concurrent users for {config.duration_seconds}s")

        latencies = []
        errors = 0
        operations = 0
        start_time = time.time()

        def single_search():
            """Execute a single search operation."""
            query = self.sample_queries[operations % len(self.sample_queries)]

            op_start = time.time()
            try:
                results = self.retriever.search(query, limit=5)
                latency = time.time() - op_start
                return latency, None
            except Exception as e:
                latency = time.time() - op_start
                return latency, str(e)

        # Warmup phase
        logger.info("Warmup phase...")
        warmup_end = time.time() + config.warmup_seconds
        while time.time() < warmup_end:
            single_search()

        # Ramp-up phase
        logger.info("Ramp-up phase...")
        ramp_end = time.time() + config.ramp_up_seconds

        # Main test phase
        logger.info("Main test phase...")
        test_end = start_time + config.duration_seconds

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrency) as executor:
            futures = []

            while time.time() < test_end:
                # Submit concurrent requests
                for _ in range(config.concurrency):
                    if time.time() < test_end:
                        future = executor.submit(single_search)
                        futures.append(future)

                # Wait for completion and collect results
                for future in concurrent.futures.as_completed(futures):
                    try:
                        latency, error = future.result(timeout=30)
                        latencies.append(latency)
                        operations += 1
                        if error:
                            errors += 1
                    except Exception as e:
                        logger.error(f"Test execution error: {e}")
                        errors += 1

                futures = []

        duration = time.time() - start_time

        # Calculate statistics
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            throughput = operations / duration
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = throughput = 0

        result = PerformanceResult(
            test_name="search_benchmark",
            duration=duration,
            operations=operations,
            throughput=throughput,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            errors=errors,
            metadata={
                "concurrency": config.concurrency,
                "sample_queries": len(self.sample_queries),
                "avg_results_per_query": 5
            }
        )

        logger.info(f"Search benchmark completed: {throughput:.2f} ops/sec, {avg_latency:.3f}s avg latency")
        return result


class GenerationBenchmark:
    """Benchmark AI generation performance."""

    def __init__(self, llm_generator: LLMGenerator):
        self.llm_generator = llm_generator
        self.sample_queries = [
            "Explain what machine learning is in simple terms",
            "What are the benefits of using vector databases?",
            "How does retrieval augmented generation work?",
            "What is the difference between embeddings and tokens?",
            "How to optimize search performance in knowledge bases?"
        ]

    def run_benchmark(self, config: BenchmarkConfig) -> PerformanceResult:
        """Run generation performance benchmark."""
        logger.info(f"Starting generation benchmark: {config.concurrency} concurrent users for {config.duration_seconds}s")

        latencies = []
        errors = 0
        operations = 0
        total_tokens = 0
        start_time = time.time()

        def single_generation():
            """Execute a single generation operation."""
            query = self.sample_queries[operations % len(self.sample_queries)]

            op_start = time.time()
            try:
                # Create a minimal context for testing
                context = []  # Empty context for benchmark

                generation_request = self.llm_generator.GenerationRequest(
                    query=query,
                    context=context,
                    max_tokens=100
                )

                result = self.llm_generator.generate_answer(generation_request)
                latency = time.time() - op_start

                return latency, result.token_usage.get("total_tokens", 0), None
            except Exception as e:
                latency = time.time() - op_start
                return latency, 0, str(e)

        # Warmup phase
        logger.info("Warmup phase...")
        warmup_end = time.time() + config.warmup_seconds
        while time.time() < warmup_end:
            single_generation()

        # Main test phase
        logger.info("Main test phase...")
        test_end = start_time + config.duration_seconds

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrency) as executor:
            futures = []

            while time.time() < test_end:
                for _ in range(min(config.concurrency, 5)):  # Limit concurrent generations
                    if time.time() < test_end:
                        future = executor.submit(single_generation)
                        futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        latency, tokens, error = future.result(timeout=60)
                        latencies.append(latency)
                        total_tokens += tokens
                        operations += 1
                        if error:
                            errors += 1
                    except Exception as e:
                        logger.error(f"Generation test execution error: {e}")
                        errors += 1

                futures = []

        duration = time.time() - start_time

        # Calculate statistics
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]
            p99_latency = statistics.quantiles(latencies, n=100)[98]
            throughput = operations / duration
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = throughput = 0

        result = PerformanceResult(
            test_name="generation_benchmark",
            duration=duration,
            operations=operations,
            throughput=throughput,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            errors=errors,
            metadata={
                "concurrency": config.concurrency,
                "total_tokens_used": total_tokens,
                "tokens_per_second": total_tokens / duration if duration > 0 else 0,
                "sample_queries": len(self.sample_queries)
            }
        )

        logger.info(f"Generation benchmark completed: {throughput:.2f} ops/sec, {avg_latency:.3f}s avg latency")
        return result


class IngestionBenchmark:
    """Benchmark data ingestion performance."""

    def __init__(self, ingestion_pipeline: DataIngestionPipeline):
        self.ingestion_pipeline = ingestion_pipeline

    def run_benchmark(self, config: BenchmarkConfig) -> PerformanceResult:
        """Run ingestion performance benchmark."""
        logger.info(f"Starting ingestion benchmark for {config.duration_seconds}s")

        latencies = []
        errors = 0
        operations = 0
        total_chunks = 0
        start_time = time.time()

        def single_ingestion():
            """Execute a single ingestion operation."""
            # Generate sample document
            doc_id = f"bench_doc_{int(time.time() * 1000000) + operations}"
            title = f"Sample Document {operations}"
            content = f"This is a sample document for performance testing. " * 50  # ~2500 chars

            op_start = time.time()
            try:
                result = self.ingestion_pipeline._process_document(
                    self.ingestion_pipeline.DocumentData(
                        id=doc_id,
                        title=title,
                        content=content,
                        source_type="benchmark",
                        source_path="",
                        file_type="txt",
                        metadata={"benchmark": True}
                    )
                )

                latency = time.time() - op_start
                chunks_created = result.chunks_created if result.success else 0

                return latency, chunks_created, None if result.success else result.error_message
            except Exception as e:
                latency = time.time() - op_start
                return latency, 0, str(e)

        # Main test phase
        test_end = start_time + config.duration_seconds

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(config.concurrency, 3)) as executor:
            futures = []

            while time.time() < test_end:
                for _ in range(min(config.concurrency, 3)):
                    if time.time() < test_end:
                        future = executor.submit(single_ingestion)
                        futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        latency, chunks, error = future.result(timeout=30)
                        latencies.append(latency)
                        total_chunks += chunks
                        operations += 1
                        if error:
                            errors += 1
                    except Exception as e:
                        logger.error(f"Ingestion test execution error: {e}")
                        errors += 1

                futures = []

        duration = time.time() - start_time

        # Calculate statistics
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]
            p99_latency = statistics.quantiles(latencies, n=100)[98]
            throughput = operations / duration
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = throughput = 0

        result = PerformanceResult(
            test_name="ingestion_benchmark",
            duration=duration,
            operations=operations,
            throughput=throughput,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            errors=errors,
            metadata={
                "total_chunks_created": total_chunks,
                "chunks_per_second": total_chunks / duration if duration > 0 else 0,
                "avg_chunks_per_document": total_chunks / operations if operations > 0 else 0
            }
        )

        logger.info(f"Ingestion benchmark completed: {throughput:.2f} docs/sec, {avg_latency:.3f}s avg latency")
        return result


class PerformanceTestSuite:
    """Complete performance testing suite."""

    def __init__(self, config: KnowledgeBaseConfig, db: KnowledgeBaseDB,
                 ingestion_pipeline: DataIngestionPipeline,
                 embedding_engine: EmbeddingEngine,
                 retriever: VectorRetriever,
                 llm_generator: LLMGenerator):
        self.config = config
        self.db = db

        # Initialize benchmark components
        self.search_benchmark = SearchBenchmark(retriever)
        self.generation_benchmark = GenerationBenchmark(llm_generator)
        self.ingestion_benchmark = IngestionBenchmark(ingestion_pipeline)

        # Test results
        self.results: List[PerformanceResult] = []

    def run_full_suite(self, benchmark_config: Optional[BenchmarkConfig] = None) -> Dict[str, Any]:
        """Run the complete performance test suite."""
        if not benchmark_config:
            benchmark_config = BenchmarkConfig()

        logger.info("Starting full performance test suite")
        suite_start = time.time()

        # Run individual benchmarks
        results = []

        logger.info("Running search benchmark...")
        search_result = self.search_benchmark.run_benchmark(benchmark_config)
        results.append(search_result)

        logger.info("Running generation benchmark...")
        generation_result = self.generation_benchmark.run_benchmark(benchmark_config)
        results.append(generation_result)

        logger.info("Running ingestion benchmark...")
        ingestion_result = self.ingestion_benchmark.run_benchmark(benchmark_config)
        results.append(ingestion_result)

        suite_duration = time.time() - suite_start

        # Store results
        self.results = results

        # Generate comprehensive report
        report = {
            "suite_info": {
                "duration": suite_duration,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "duration_seconds": benchmark_config.duration_seconds,
                    "concurrency": benchmark_config.concurrency,
                    "warmup_seconds": benchmark_config.warmup_seconds
                }
            },
            "results": [self._result_to_dict(r) for r in results],
            "summary": self._generate_summary(results),
            "recommendations": self._generate_recommendations(results)
        }

        logger.info(f"Performance test suite completed in {suite_duration:.2f}s")
        return report

    def run_single_test(self, test_name: str, benchmark_config: Optional[BenchmarkConfig] = None) -> PerformanceResult:
        """Run a single performance test."""
        if not benchmark_config:
            benchmark_config = BenchmarkConfig()

        if test_name == "search":
            return self.search_benchmark.run_benchmark(benchmark_config)
        elif test_name == "generation":
            return self.generation_benchmark.run_benchmark(benchmark_config)
        elif test_name == "ingestion":
            return self.ingestion_benchmark.run_benchmark(benchmark_config)
        else:
            raise ValueError(f"Unknown test: {test_name}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for performance context."""
        import platform
        import psutil

        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_logical": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total,
            "config": {
                "database_host": self.config.database.host,
                "embedding_model": self.config.embeddings.model,
                "llm_model": self.config.llm.model,
                "search_top_k": self.config.search.top_k
            }
        }

    def _result_to_dict(self, result: PerformanceResult) -> Dict[str, Any]:
        """Convert performance result to dictionary."""
        return {
            "test_name": result.test_name,
            "duration": result.duration,
            "operations": result.operations,
            "throughput": result.throughput,
            "avg_latency": result.avg_latency,
            "min_latency": result.min_latency,
            "max_latency": result.max_latency,
            "p95_latency": result.p95_latency,
            "p99_latency": result.p99_latency,
            "errors": result.errors,
            "error_rate": result.errors / result.operations if result.operations > 0 else 0,
            "metadata": result.metadata
        }

    def _generate_summary(self, results: List[PerformanceResult]) -> Dict[str, Any]:
        """Generate performance summary."""
        total_operations = sum(r.operations for r in results)
        total_errors = sum(r.errors for r in results)
        avg_throughput = statistics.mean([r.throughput for r in results if r.throughput > 0])

        # Determine overall health
        error_rate = total_errors / total_operations if total_operations > 0 else 0
        avg_latency_p95 = statistics.mean([r.p95_latency for r in results if r.p95_latency > 0])

        if error_rate > 0.1:  # >10% errors
            health = "poor"
        elif avg_latency_p95 > 5.0:  # >5s p95 latency
            health = "fair"
        elif avg_throughput < 1.0:  # <1 op/sec average
            health = "fair"
        else:
            health = "good"

        return {
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "avg_throughput": avg_throughput,
            "avg_p95_latency": avg_latency_p95,
            "overall_health": health,
            "test_count": len(results)
        }

    def _generate_recommendations(self, results: List[PerformanceResult]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        for result in results:
            if result.test_name == "search_benchmark":
                if result.p95_latency > 2.0:
                    recommendations.append("Consider optimizing vector similarity search - high latency detected")
                if result.throughput < 5.0:
                    recommendations.append("Low search throughput - consider caching or index optimization")

            elif result.test_name == "generation_benchmark":
                if result.p95_latency > 10.0:
                    recommendations.append("AI generation is slow - consider response caching or model optimization")
                if result.throughput < 2.0:
                    recommendations.append("Low generation throughput - consider batch processing or model quantization")

            elif result.test_name == "ingestion_benchmark":
                if result.p95_latency > 5.0:
                    recommendations.append("Document ingestion is slow - consider async processing or chunk optimization")
                if result.throughput < 1.0:
                    recommendations.append("Low ingestion throughput - consider parallel processing or batch operations")

        if not recommendations:
            recommendations.append("Performance looks good - no major optimizations needed")

        return recommendations

    def export_results(self, filepath: str) -> None:
        """Export test results to JSON file."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "results": [self._result_to_dict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Performance results exported to {filepath}")
