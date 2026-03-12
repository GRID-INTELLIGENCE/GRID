"""
GRID Search Sorter Demo
Demonstrates search result sorting with safety and relevance integration
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent))

from application.canvas.search_sorter import CanvasSearchSorter
from mycelium.search_safety import SearchSafetyGuard


def demo_canvas_search_sorter():
    """Demonstrate Canvas search sorter functionality."""
    print("=== GRID Canvas Search Sorter Demo ===\n")

    sorter = CanvasSearchSorter()

    # Example routes from GRID structure
    routes = [
        Path("src/application/canvas/relevance.py"),
        Path("src/mycelium/safety.py"),
        Path("src/application/mothership/main.py"),
        Path("docs/api/routing.md"),
        Path("tests/unit/test_relevance.py"),
        Path("src/application/canvas/search_sorter.py"),
    ]

    query = "relevance safety search"

    print(f"Query: '{query}'")
    print(f"Processing {len(routes)} routes...\n")

    # Create search results
    results = []
    for route in routes:
        # Mock content with varying characteristics
        if "safety" in route.name.lower():
            content = "Safety validation and PII detection for search results"
        elif "relevance" in route.name.lower():
            content = "Relevance scoring and semantic similarity algorithms"
        elif "search" in route.name.lower():
            content = "Search result sorting and filtering mechanisms"
        else:
            content = "General GRID framework functionality"

        # Add PII to some content for demonstration
        if "main" in route.name:
            content += " Contact: admin@example.com"

        result = sorter.create_search_result(route, query, content)
        results.append(result)

    print(f"Created {len(results)} search results\n")

    # Demonstrate different sorting methods
    print("--- Sorting Methods ---\n")

    # 1. Sort by relevance
    print("1. Sort by Relevance (Score + Confidence):")
    relevance_sorted = sorter.sort_by_relevance(results)
    for i, result in enumerate(relevance_sorted[:3], 1):
        print(f"   {i}. {result.route.name}")
        print(f"      Score: {result.score:.3f}, Confidence: {result.confidence:.3f}")
        print(f"      Safe: {result.is_safe}, PII: {result.pii_detected}")
    print()

    # 2. Sort by safety priority
    print("2. Sort by Safety Priority (Clean → PII → Unsafe):")
    safety_sorted = sorter.sort_by_safety_then_relevance(results)
    for i, result in enumerate(safety_sorted[:3], 1):
        status = "Clean" if result.is_safe and not result.pii_detected else "PII" if result.pii_detected else "Unsafe"
        print(f"   {i}. {result.route.name} ({status})")
        print(f"      Score: {result.score:.3f}")
    print()

    # 3. Sort by path complexity
    print("3. Sort by Path Complexity (Simple → Complex):")
    complexity_sorted = sorter.sort_by_path_complexity(results)
    for i, result in enumerate(complexity_sorted[:3], 1):
        complexity = result.relevance_metrics.get("path_complexity", 0.0)
        print(f"   {i}. {result.route.name} (complexity: {complexity:.3f})")
    print()

    # 4. Sort by recency
    print("4. Sort by Recency (Newest First):")
    # Create results with different timestamps
    time_results = []
    for i, result in enumerate(results):
        result.timestamp = datetime.now() - timedelta(hours=i)
        time_results.append(result)

    recency_sorted = sorter.sort_by_recency(time_results)
    for i, result in enumerate(recency_sorted[:3], 1):
        print(f"   {i}. {result.route.name}")
        print(f"      Time: {result.timestamp.strftime('%H:%M:%S')}")
    print()

    # Summary statistics
    print("--- Summary Statistics ---")
    total_results = len(results)
    safe_results = sum(1 for r in results if r.is_safe)
    pii_results = sum(1 for r in results if r.pii_detected)
    unsafe_results = total_results - safe_results

    print(f"Total results: {total_results}")
    print(f"Safe results: {safe_results}")
    print(f"PII detected: {pii_results}")
    print(f"Unsafe results: {unsafe_results}")
    print(f"Average score: {sum(r.score for r in results) / total_results:.3f}")
    print(f"Average confidence: {sum(r.confidence for r in results) / total_results:.3f}")


def demo_search_safety():
    """Demonstrate search safety validation."""
    print("\n=== GRID Search Safety Demo ===\n")

    guard = SearchSafetyGuard()

    # Test cases
    test_cases = [
        ("Safe content", "This is normal search result content"),
        ("Email PII", "Contact me at user@example.com for more information"),
        ("Phone PII", "Call me at 555-123-4567 to discuss"),
        ("Multiple PII", "Email: admin@company.com, Phone: 444-987-6543"),
        ("SSN PII", "Social security: 123-45-6789"),
        ("Empty content", ""),
        ("Oversized", "x" * 150_000),  # Exceeds 100KB limit
        ("Control chars", "Content with\x00null\x01bytes"),
    ]

    print("Testing different content types:\n")

    for name, content in test_cases:
        print(f"Testing: {name}")
        report = guard.validate_search_result(content)

        print(f"  Verdict: {report.verdict.value}")
        print(f"  Safe: {report.is_safe}")
        print(f"  PII detected: {report.pii_detected}")

        if report.pii_types:
            print(f"  PII types: {', '.join(report.pii_types)}")

        if report.reasons:
            print(f"  Reasons: {'; '.join(report.reasons)}")

        print(f"  Processing time: {report.processing_time_ms:.2f}ms")
        print()


def demo_integration():
    """Demonstrate integrated safety and relevance sorting."""
    print("=== Integrated Safety + Relevance Demo ===\n")

    sorter = CanvasSearchSorter()

    # Create mixed results
    mixed_results = [
        sorter.create_search_result(
            Path("src/safe/relevant.py"),
            "search",
            "Highly relevant content about search algorithms"
        ),
        sorter.create_search_result(
            Path("docs/pii_content.md"),
            "search",
            "Search documentation with contact@example.com"
        ),
        sorter.create_search_result(
            Path("src/unsafe/content.py"),
            "search",
            "Unsafe content" + "\x00" * 10  # Control chars
        ),
    ]

    print("Mixed results before sorting:")
    for i, result in enumerate(mixed_results, 1):
        print(f"  {i}. {result.route.name} - Safe: {result.is_safe}, Score: {result.score:.3f}")

    print("\nAfter integrated sorting:")
    sorted_results = sorter.sort_by_safety_then_relevance(mixed_results)

    for i, result in enumerate(sorted_results, 1):
        safety_status = "Clean" if result.is_safe and not result.pii_detected else "PII" if result.pii_detected else "Unsafe"
        print(f"  {i}. {result.route.name} ({safety_status}) - Score: {result.score:.3f}")


if __name__ == "__main__":
    demo_canvas_search_sorter()
    demo_search_safety()
    demo_integration()

    print("\n=== Demo Complete ===")
    print("The GRID Search Sorter provides:")
    print("• Safety-first result filtering")
    print("• Multi-criteria sorting (relevance, confidence, complexity)")
    print("• PII detection with non-punitive warnings")
    print("• Usage-based frequency scoring")
    print("• MCP server tool definitions")
