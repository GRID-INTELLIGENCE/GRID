"""
Phase 3: Reasoning Layer - Integration Test Script

This script demonstrates the complete intelligent RAG pipeline:
1. Query Understanding (Intent + Entities)
2. Multi-Stage Retrieval (Hybrid + Multi-Hop + Reranking)
3. Evidence Extraction (Structured facts with provenance)
4. Chain-of-Thought Reasoning (Transparent reasoning steps)
5. Response Synthesis (Polished answer with citations)

Usage:
    python -m tools.rag.intelligence.test_phase3 --query "What is the GRID architecture?"
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(grid_root))

from tools.rag.config import RAGConfig
from tools.rag.rag_engine import RAGEngine


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def print_banner() -> None:
    """Print test banner."""
    print("\n" + "=" * 80)
    print("PHASE 3: REASONING LAYER - INTEGRATION TEST".center(80))
    print("=" * 80)
    print("\nThis test demonstrates the complete intelligent RAG pipeline:")
    print("  1. Query Understanding - Intent classification + entity extraction")
    print("  2. Multi-Stage Retrieval - Hybrid search + multi-hop + reranking")
    print("  3. Evidence Extraction - Structured facts with source attribution")
    print("  4. Chain-of-Thought Reasoning - Transparent reasoning steps")
    print("  5. Response Synthesis - Polished answer with citations")
    print("\n" + "=" * 80 + "\n")


def print_separator(title: str = "") -> None:
    """Print a section separator."""
    if title:
        print(f"\n{'─' * 80}")
        print(f"  {title}")
        print("─" * 80)
    else:
        print("─" * 80)


def print_result(result: Dict[str, Any], show_reasoning: bool = True, show_metrics: bool = True) -> None:
    """Pretty print query result."""
    print_separator("📝 ANSWER")
    print(result.get("answer", "No answer provided"))

    # Confidence
    confidence = result.get("confidence", 0.0)
    conf_emoji = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.5 else "🔴"
    print(f"\n{conf_emoji} Confidence: {confidence:.0%}")

    # Citations
    citations = result.get("citations", [])
    if citations:
        print_separator("📚 SOURCES")
        for i, citation in enumerate(citations, 1):
            print(f"{i}. {citation}")

    # Reasoning chain
    if show_reasoning and "reasoning" in result:
        reasoning = result["reasoning"]
        print_separator("🧠 REASONING CHAIN")

        steps = reasoning.get("steps", [])
        print(f"\nTotal steps: {len(steps)}")
        print(f"Is confident: {reasoning.get('is_confident', False)}")
        print(f"Has gaps: {reasoning.get('has_gaps', False)}\n")

        for step in steps:
            step_num = step.get("step", 0)
            step_type = step.get("type", "unknown")
            content = step.get("content", "")
            conf = step.get("confidence", 0.0)
            evidence_count = len(step.get("evidence_ids", []))

            # Emoji mapping
            emoji_map = {
                "observation": "👁️",
                "inference": "🧠",
                "synthesis": "🔗",
                "validation": "✓",
                "conclusion": "💡",
                "uncertainty": "❓",
            }
            emoji = emoji_map.get(step_type, "•")

            print(f"{emoji} Step {step_num}: [{step_type.upper()}] (confidence: {conf:.0%})")
            print(f"   {content}")
            if evidence_count > 0:
                print(f"   → Supported by {evidence_count} evidence piece(s)")
            print()

        # Warnings
        warnings = reasoning.get("warnings", [])
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")

        # Evidence usage
        used = reasoning.get("evidence_used_count", 0)
        unused = reasoning.get("evidence_unused_count", 0)
        total = used + unused
        if total > 0:
            print(f"\n📊 Evidence Usage: {used}/{total} ({used / total:.0%})")

    # Metrics
    if show_metrics and "metrics" in result:
        metrics = result["metrics"]
        print_separator("📊 PIPELINE METRICS")

        # Timing
        if "timing" in metrics:
            print("\n⏱️  Timing:")
            timing = metrics["timing"]
            for stage, time_str in timing.items():
                print(f"  • {stage:20s}: {time_str}")

        # Pipeline stats
        if "pipeline" in metrics:
            print("\n🔄 Pipeline:")
            pipeline = metrics["pipeline"]
            for key, val in pipeline.items():
                print(f"  • {key:20s}: {val}")

        # Quality indicators
        if "quality" in metrics:
            print("\n✨ Quality:")
            quality = metrics["quality"]
            for key, val in quality.items():
                print(f"  • {key:20s}: {val}")


async def run_test_query(
    engine: RAGEngine,
    query: str,
    top_k: int = 5,
    temperature: float = 0.3,
    show_reasoning: bool = True,
    show_metrics: bool = True,
) -> Dict[str, Any]:
    """Run a single test query."""
    print(f"\n🔍 Query: {query}")
    print_separator()

    result = await engine.intelligent_query(
        query_text=query,
        top_k=top_k,
        temperature=temperature,
        include_reasoning=show_reasoning,
        include_metrics=show_metrics,
    )

    print_result(result, show_reasoning=show_reasoning, show_metrics=show_metrics)

    return result


async def run_test_suite(engine: RAGEngine, verbose: bool = False) -> None:
    """Run a suite of test queries."""
    print_separator("🧪 RUNNING TEST SUITE")

    test_queries = [
        {
            "query": "What is the GRID architecture?",
            "description": "Definition query - tests intent classification and evidence extraction",
        },
        {
            "query": "How does RAGEngine handle retrieval?",
            "description": "Implementation query - tests code evidence extraction",
        },
        {
            "query": "Where is the embedding provider defined?",
            "description": "Location query - tests multi-hop retrieval",
        },
        {
            "query": "What are the 9 cognition patterns?",
            "description": "List query - tests synthesis across multiple sources",
        },
    ]

    results = []

    for i, test in enumerate(test_queries, 1):
        print(f"\n\n{'=' * 80}")
        print(f"TEST {i}/{len(test_queries)}: {test['description']}")
        print("=" * 80)

        try:
            result = await run_test_query(
                engine=engine,
                query=test["query"],
                top_k=5,
                temperature=0.3,
                show_reasoning=verbose,
                show_metrics=verbose,
            )
            results.append({"query": test["query"], "success": True, "confidence": result.get("confidence", 0.0)})
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            results.append({"query": test["query"], "success": False, "error": str(e)})

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUITE SUMMARY".center(80))
    print("=" * 80)

    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    avg_confidence = sum(r.get("confidence", 0.0) for r in results if r["success"]) / max(success_count, 1)

    print(f"\nTests Passed: {success_count}/{total_count}")
    print(f"Average Confidence: {avg_confidence:.0%}")

    print("\nResults:")
    for i, result in enumerate(results, 1):
        status = "✓" if result["success"] else "✗"
        conf_str = (
            f"({result['confidence']:.0%})" if result["success"] else f"(ERROR: {result.get('error', 'unknown')})"
        )
        print(f"  {status} Test {i}: {conf_str}")


async def run_comparison(engine: RAGEngine, query: str) -> None:
    """Compare standard RAG vs intelligent RAG."""
    print_separator("⚖️  COMPARISON: Standard vs Intelligent RAG")

    print("\n📍 Query:", query)

    # Standard RAG
    print("\n\n1️⃣  STANDARD RAG (baseline)")
    print("─" * 80)
    try:
        standard_result = await engine.query(query_text=query, top_k=5, temperature=0.3, include_sources=True)

        print("\nAnswer:")
        print(standard_result.get("answer", "No answer"))
        print(f"\nSources: {len(standard_result.get('sources', []))}")

        if "evaluation_metrics" in standard_result:
            metrics = standard_result["evaluation_metrics"]
            print(f"Relevance: {metrics.get('relevance_score', 0.0):.2f}")

    except Exception as e:
        print(f"Error: {e}")

    # Intelligent RAG
    print("\n\n2️⃣  INTELLIGENT RAG (Phase 3)")
    print("─" * 80)
    try:
        intelligent_result = await engine.intelligent_query(
            query_text=query,
            top_k=5,
            temperature=0.3,
            include_reasoning=True,
            include_metrics=True,
        )

        print("\nAnswer:")
        print(intelligent_result.get("answer", "No answer"))
        print(f"\nConfidence: {intelligent_result.get('confidence', 0.0):.0%}")
        print(f"Citations: {len(intelligent_result.get('citations', []))}")

        if "reasoning" in intelligent_result:
            reasoning = intelligent_result["reasoning"]
            print(f"Reasoning Steps: {len(reasoning.get('steps', []))}")
            print(f"Evidence Used: {reasoning.get('evidence_used_count', 0)}")

        if "metrics" in intelligent_result:
            metrics = intelligent_result["metrics"]
            if "timing" in metrics:
                print(f"Total Time: {metrics['timing'].get('total', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 80)


async def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(description="Phase 3: Reasoning Layer Integration Test")

    parser.add_argument("--query", type=str, help="Single query to test")
    parser.add_argument("--suite", action="store_true", help="Run full test suite")
    parser.add_argument("--compare", action="store_true", help="Compare standard vs intelligent RAG")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to retrieve")
    parser.add_argument("--temperature", type=float, default=0.3, help="LLM temperature")
    parser.add_argument("--no-reasoning", action="store_true", help="Hide reasoning chain")
    parser.add_argument("--no-metrics", action="store_true", help="Hide pipeline metrics")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--db-path", type=str, help="Path to vector store database")

    args = parser.parse_args()

    # Setup
    setup_logging(verbose=args.verbose)
    if not args.json:
        print_banner()

    # Check if RAG is indexed
    config = RAGConfig.from_env()
    if args.db_path:
        config.vector_store_path = args.db_path

    # Ensure intelligent RAG is enabled
    config.use_intelligent_rag = True

    try:
        print("🔧 Initializing RAG engine...")
        engine = RAGEngine(config=config)

        if engine.get_stats()["document_count"] == 0:
            print("\n❌ Error: No documents in the knowledge base!")
            print("\nPlease index a repository first:")
            print("  python -m tools.rag.cli index <repo_path>")
            return 1

        print(f"✓ RAG engine ready ({engine.get_stats()['document_count']} documents)")

        if not engine._intelligent_orchestrator:
            print("\n❌ Error: Intelligent RAG orchestrator not initialized!")
            print("This may be due to missing dependencies.")
            return 1

        print("✓ Intelligent orchestrator ready")

        # Run tests
        if args.suite:
            await run_test_suite(engine, verbose=args.verbose)

        elif args.compare:
            query = args.query or "What is the GRID architecture?"
            await run_comparison(engine, query)

        elif args.query:
            result = await run_test_query(
                engine=engine,
                query=args.query,
                top_k=args.top_k,
                temperature=args.temperature,
                show_reasoning=not args.no_reasoning,
                show_metrics=not args.no_metrics,
            )

            if args.json:
                print(json.dumps(result, indent=2))

        else:
            # Default: single demo query
            demo_query = "What is the GRID architecture strategy?"
            print(f"Running demo query: '{demo_query}'")
            print("(Use --query, --suite, or --compare for other modes)\n")

            await run_test_query(
                engine=engine,
                query=demo_query,
                top_k=args.top_k,
                temperature=args.temperature,
                show_reasoning=not args.no_reasoning,
                show_metrics=not args.no_metrics,
            )

        print("\n\n" + "=" * 80)
        print("✅ TEST COMPLETE".center(80))
        print("=" * 80 + "\n")

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "type": type(e).__name__}))
        else:
            print(f"\n❌ Fatal error: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
