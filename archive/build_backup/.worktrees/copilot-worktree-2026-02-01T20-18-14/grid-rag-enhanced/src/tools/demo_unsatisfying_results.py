#!/usr/bin/env python3
"""Demonstration: How the system handles when first result doesn't satisfy context.

This script shows:
1. How semantic_grep filters results by min_score threshold
2. How results are processed in score order (not just first)
3. Cross-checking behavior for conflicts
4. RAG engine fallback when no results found
5. What instructions are generated for different scenarios
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from datakit.tool.semantic_grep import _extract_instructions, run_semantic_grep
except ImportError:
    print("Error: Could not import semantic_grep. Make sure datakit is in path.")
    sys.exit(1)


def demonstrate_score_filtering():
    """Show how results are filtered by min_score threshold."""
    print("=" * 80)
    print("DEMONSTRATION 1: Score Threshold Filtering")
    print("=" * 80)
    print()

    # Example: Search for "database connection" with different thresholds
    query = "database connection configuration"
    refs_path = project_root / "docs"

    print(f"Query: '{query}'")
    print(f"Searching in: {refs_path}")
    print()

    # Test with strict threshold (only high scores)
    print("Test 1: Strict threshold (min_score=0.5)")
    print("-" * 80)
    result_strict = run_semantic_grep(
        context=query,
        refs_path=refs_path,
        mode="keyword",  # Use keyword mode for faster demo
        model="all-MiniLM-L6-v2",
        top_k=10,
        extensions=[".md", ".py"],
        chunk_lines=60,
        overlap_lines=10,
        max_file_bytes=100000,
        min_score=0.5,  # Strict threshold
    )

    print(f"Results found: {len(result_strict['matches'])}")
    print(f"Instructions generated: {len(result_strict['logical_instructions'])}")
    if result_strict["matches"]:
        print(f"Top score: {result_strict['matches'][0]['score']:.3f}")
    print()

    # Test with lenient threshold (lower scores included)
    print("Test 2: Lenient threshold (min_score=0.15)")
    print("-" * 80)
    result_lenient = run_semantic_grep(
        context=query,
        refs_path=refs_path,
        mode="keyword",
        model="all-MiniLM-L6-v2",
        top_k=10,
        extensions=[".md", ".py"],
        chunk_lines=60,
        overlap_lines=10,
        max_file_bytes=100000,
        min_score=0.15,  # Default threshold
    )

    print(f"Results found: {len(result_lenient['matches'])}")
    print(f"Instructions generated: {len(result_lenient['logical_instructions'])}")
    if result_lenient["matches"]:
        print(f"Top score: {result_lenient['matches'][0]['score']:.3f}")
    print()

    print("Key Insight: Results below min_score are filtered out BEFORE processing.")
    print("If first result has score < min_score, it's skipped entirely.")
    print()


def demonstrate_processing_order():
    """Show how results are processed in score order."""
    print("=" * 80)
    print("DEMONSTRATION 2: Processing Results in Score Order")
    print("=" * 80)
    print()

    query = "RAG query knowledge base"
    refs_path = project_root

    print(f"Query: '{query}'")
    print()

    result = run_semantic_grep(
        context=query,
        refs_path=refs_path,
        mode="keyword",
        model="all-MiniLM-L6-v2",
        top_k=5,
        extensions=[".py", ".md"],
        chunk_lines=60,
        overlap_lines=10,
        max_file_bytes=100000,
        min_score=0.15,
    )

    print("Results (in score order, highest first):")
    print("-" * 80)
    for i, match in enumerate(result["matches"][:5], 1):
        file_name = Path(match["file"]).name
        print(f"{i}. Score: {match['score']:.3f} | File: {file_name}")
        print(f"   Lines: {match['start_line']}-{match['end_line']}")
        print(f"   Preview: {match['text'][:80]}...")
        print()

    print("Key Instructions Generated:")
    print("-" * 80)
    for instruction in result["logical_instructions"]:
        print(f"• {instruction}")
    print()
    print("Key Insight: Instructions say 'Read matched line ranges IN ORDER OF SCORE'")
    print("This means process ALL top matches, not just the first one.")
    print()


def demonstrate_cross_checking():
    """Show cross-checking behavior for conflicts."""
    print("=" * 80)
    print("DEMONSTRATION 3: Cross-Checking Similar Matches")
    print("=" * 80)
    print()

    query = "implementation interface pattern"
    refs_path = project_root

    print(f"Query: '{query}'")
    print()

    result = run_semantic_grep(
        context=query,
        refs_path=refs_path,
        mode="keyword",
        model="all-MiniLM-L6-v2",
        top_k=8,
        extensions=[".py"],
        chunk_lines=60,
        overlap_lines=10,
        max_file_bytes=100000,
        min_score=0.15,
    )

    print(f"Found {len(result['matches'])} matches")
    print()

    # Show how instructions adapt based on results
    print("Instructions generated:")
    print("-" * 80)
    for instruction in result["logical_instructions"]:
        print(f"• {instruction}")
    print()

    if len(result["matches"]) > 1:
        print("Cross-Checking Logic:")
        print("-" * 80)
        print("When multiple matches exist, the system generates this instruction:")
        print('  "Cross-check similar matches for conflicts; prefer the most recent')
        print('   or most authoritative reference."')
        print()
        print("This means:")
        print("1. Don't trust the first result alone")
        print("2. Compare multiple matches for consistency")
        print("3. Prefer authoritative sources (e.g., canonical docs)")
        print("4. Prefer recent sources if there's a conflict")
    print()


def demonstrate_rag_fallback():
    """Show RAG engine behavior when no results found."""
    print("=" * 80)
    print("DEMONSTRATION 4: RAG Engine Fallback (No Results Found)")
    print("=" * 80)
    print()

    print("When RAG engine finds no documents, it returns:")
    print("-" * 80)
    print(
        """{
    "answer": "No relevant documents found in the knowledge base.",
    "sources": [],
    "context": ""
}"""
    )
    print()

    print("This is different from returning a low-quality first result.")
    print("The system explicitly acknowledges when no good matches exist.")
    print()

    print("Comparison with Semantic Grep:")
    print("-" * 80)
    print("Semantic Grep: Returns empty matches list if all scores < min_score")
    print("RAG Engine: Returns explicit 'No relevant documents found' message")
    print("Both systems avoid hallucinating answers from poor matches.")
    print()


def demonstrate_instruction_variation():
    """Show how instructions vary based on query type and results."""
    print("=" * 80)
    print("DEMONSTRATION 5: Instruction Variation Based on Context")
    print("=" * 80)
    print()

    test_cases = [
        {
            "query": "bug error fix broken issue",
            "description": "Bug-fixing query",
            "expected_instruction": "Locate error messages / stack traces",
        },
        {
            "query": "implement create add build tool",
            "description": "Implementation query",
            "expected_instruction": "Derive an interface from the matches",
        },
        {
            "query": "how does this work",
            "description": "General query",
            "expected_instruction": "Identify relevant files and sections",
        },
    ]

    project_root / "tools" / "rag"

    for case in test_cases:
        print(f"Query Type: {case['description']}")
        print(f"Query: '{case['query']}'")
        print("-" * 80)

        # Create mock matches to show instruction generation
        mock_matches = (
            [{"score": 0.5, "file": "example.py", "start_line": 10, "end_line": 20, "text": "Example code"}]
            if "bug" in case["query"] or "implement" in case["query"]
            else []
        )

        instructions = _extract_instructions(case["query"], mock_matches)

        print("Instructions generated:")
        for instruction in instructions:
            print(f"  • {instruction}")
        print()

        # Check if expected instruction is present
        if any(case["expected_instruction"].lower() in inst.lower() for inst in instructions):
            print(f"[OK] Found expected instruction pattern: '{case['expected_instruction']}'")
        print()


def demonstrate_threshold_impact():
    """Show practical impact of threshold selection."""
    print("=" * 80)
    print("DEMONSTRATION 6: Practical Impact of Threshold Selection")
    print("=" * 80)
    print()

    query = "metrics collection dashboard"
    refs_path = project_root / "tools" / "interfaces_dashboard"

    print(f"Query: '{query}'")
    print(f"Searching in: {refs_path}")
    print()

    thresholds = [0.8, 0.5, 0.3, 0.15, 0.05]

    print("Results count by threshold:")
    print("-" * 80)
    print(f"{'Threshold':<12} {'Results':<10} {'Top Score':<12} {'Status'}")
    print("-" * 80)

    for threshold in thresholds:
        result = run_semantic_grep(
            context=query,
            refs_path=refs_path,
            mode="keyword",
            model="all-MiniLM-L6-v2",
            top_k=10,
            extensions=[".py", ".html"],
            chunk_lines=60,
            overlap_lines=10,
            max_file_bytes=100000,
            min_score=threshold,
        )

        num_results = len(result["matches"])
        top_score = result["matches"][0]["score"] if result["matches"] else 0.0

        if num_results == 0:
            status = "[X] No results"
        elif num_results == 1:
            status = "[!] Only 1 result (may not satisfy)"
        elif num_results < 3:
            status = "[!] Few results"
        else:
            status = "[OK] Multiple options"

        print(
            f"{threshold:<12} {num_results:<10} {top_score:<12.3f} {status}".encode("utf-8", errors="replace").decode(
                "utf-8"
            )
        )

    print()
    print("Key Insights:")
    print("-" * 80)
    print("• Too high threshold (0.8): May return zero results")
    print("• Too low threshold (0.05): May include irrelevant results")
    print("• Default threshold (0.15): Balance between quality and quantity")
    print("• If first result doesn't satisfy, lower threshold to see more options")
    print()


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("DEEP SEARCH RESULTS: How System Handles Unsatisfying First Results")
    print("=" * 80)
    print()

    try:
        demonstrate_score_filtering()
        demonstrate_processing_order()
        demonstrate_cross_checking()
        demonstrate_rag_fallback()
        demonstrate_instruction_variation()
        demonstrate_threshold_impact()

        print("=" * 80)
        print("SUMMARY: Key Takeaways")
        print("=" * 80)
        print()
        print("1. THRESHOLD FILTERING:")
        print("   • Results below min_score are excluded BEFORE processing")
        print("   • If first result < threshold, it's skipped entirely")
        print("   • Default min_score=0.15 provides good balance")
        print()
        print("2. PROCESSING ORDER:")
        print("   • All results processed in score order (highest first)")
        print("   • Instructions: 'Read matched line ranges IN ORDER OF SCORE'")
        print("   • Don't stop at first result - evaluate all top matches")
        print()
        print("3. CROSS-CHECKING:")
        print("   • When multiple matches exist, cross-check for conflicts")
        print("   • Prefer most recent or most authoritative reference")
        print("   • This is automatic when top_chunks list is non-empty")
        print()
        print("4. FALLBACK BEHAVIOR:")
        print("   • RAG Engine: Returns explicit 'No relevant documents found'")
        print("   • Semantic Grep: Returns empty matches list")
        print("   • Both avoid hallucinating from poor matches")
        print()
        print("5. ADAPTIVE INSTRUCTIONS:")
        print("   • Instructions vary based on query type (bug fix vs implementation)")
        print("   • Instructions adapt based on number of matches found")
        print("   • System acknowledges when context is uncertain")
        print()
        print("=" * 80)

    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
