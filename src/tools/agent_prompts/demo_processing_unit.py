#!/usr/bin/env python3
"""Demo script showing Processing Unit System in action.

This demonstrates the complete workflow from raw input to reference file generation.
"""

from pathlib import Path

from continuous_learning import ContinuousLearningSystem
from processing_unit import ProcessingUnit


def demo_basic_processing():
    """Demonstrate basic case processing."""
    print("=" * 60)
    print("DEMO: Basic Case Processing")
    print("=" * 60)

    # Initialize processing unit
    processing_unit = ProcessingUnit(
        knowledge_base_path=Path(__file__).parent, reference_output_path=Path(".case_references")
    )

    # Example 1: Standard case
    print("\n1. Processing standard case:")
    print("   Input: 'I need to add contract testing to the CI pipeline'")

    result = processing_unit.process_input(
        raw_input="I need to add contract testing to the CI pipeline",
        examples=["Similar setup in project X uses pytest"],
        scenarios=["Run contract tests on every PR, fail if schemas invalid"],
    )

    print(f"\n   Case ID: {result.case_id}")
    print(f"   Category: {result.category.value}")
    print(f"   Priority: {result.structured_data.priority}")
    print(f"   Confidence: {result.structured_data.confidence:.2f}")
    print(f"   Labels: {', '.join(result.structured_data.labels[:5])}")
    print(f"   Is Rare Case: {result.is_rare_case}")
    print(f"   Reference File: {result.reference_file_path}")

    # Show reference file content
    reference = processing_unit.get_reference_file(result.case_id)
    if reference:
        print(f"\n   Recommended Roles: {', '.join(reference.get('recommended_roles', []))}")
        print(f"   Recommended Tasks: {', '.join(reference.get('recommended_tasks', []))}")

    return result


def demo_rare_case():
    """Demonstrate rare case handling."""
    print("\n" + "=" * 60)
    print("DEMO: Rare Case Processing")
    print("=" * 60)

    processing_unit = ProcessingUnit(
        knowledge_base_path=Path(__file__).parent, reference_output_path=Path(".case_references")
    )

    print("\n2. Processing rare case:")
    print("   Input: 'I have a very unusual integration requirement that doesn't fit standard patterns'")

    result = processing_unit.process_input(
        raw_input="I have a very unusual integration requirement that doesn't fit standard patterns",
        examples=["Custom protocol not in standard libraries"],
        scenarios=["Need to bridge legacy system with modern API"],
    )

    print(f"\n   Case ID: {result.case_id}")
    print(f"   Category: {result.category.value}")
    print(f"   Confidence: {result.structured_data.confidence:.2f}")
    print(f"   Is Rare Case: {result.is_rare_case}")

    if result.is_rare_case and result.processing_metadata:
        print("\n   Advanced Protocols Activated:")
        print(f"   - Memory Searches: {len(result.processing_metadata.get('memory_searches', []))}")
        print(f"   - Generated Queries: {len(result.processing_metadata.get('generated_queries', []))}")
        print(f"   - Nuances: {len(result.processing_metadata.get('nuances', []))}")
        print(f"   - Insights: {len(result.processing_metadata.get('insights', []))}")

        if result.processing_metadata.get("generated_queries"):
            print("\n   Contextualization Queries:")
            for i, query in enumerate(result.processing_metadata["generated_queries"][:3], 1):
                print(f"   {i}. {query['question']}")
                print(f"      Options: {', '.join(query['options'][:3])}...")

    return result


def demo_enrichment():
    """Demonstrate user enrichment."""
    print("\n" + "=" * 60)
    print("DEMO: User Enrichment")
    print("=" * 60)

    processing_unit = ProcessingUnit(
        knowledge_base_path=Path(__file__).parent, reference_output_path=Path(".case_references")
    )

    # Process initial case
    result = processing_unit.process_input(raw_input="Add authentication endpoint")

    print("\n3. Initial processing:")
    print(f"   Case ID: {result.case_id}")
    print(f"   Category: {result.category.value}")

    # Enrich with additional context
    print("\n4. Enriching with user input:")
    print("   Additional context: 'Need rate limiting and token refresh'")

    enriched = processing_unit.enrich_with_user_input(
        case_id=result.case_id,
        additional_context="Need rate limiting and token refresh",
        examples=["Rate limiting in API gateway", "Token refresh in mobile app"],
        scenarios=["Prevent brute force attacks", "Handle token expiration gracefully"],
    )

    print(f"   Updated reference file: {enriched.get('last_updated')}")
    print(f"   User enrichments: {len(enriched.get('user_enrichments', []))}")

    return result


def demo_continuous_learning():
    """Demonstrate continuous learning."""
    print("\n" + "=" * 60)
    print("DEMO: Continuous Learning")
    print("=" * 60)

    learning_system = ContinuousLearningSystem(memory_path=Path(".case_memory"))

    # Record some case completions
    print("\n5. Recording case completions...")

    from case_filing import CaseFilingSystem

    filing_system = CaseFilingSystem()

    cases = [
        ("Add authentication endpoint", "Implemented JWT endpoint", "success"),
        ("Fix login bug", "Fixed session timeout issue", "success"),
        ("Add rate limiting", "Implemented rate limiting middleware", "success"),
        ("Optimize database queries", "Added indexes and query optimization", "partial"),
    ]

    for i, (input_text, solution, outcome) in enumerate(cases, 1):
        structure = filing_system.log_and_categorize(raw_input=input_text)
        learning_system.record_case_completion(
            case_id=f"DEMO-{i:03d}",
            structure=structure,
            solution=solution,
            outcome=outcome,
            agent_experience={"lessons": [f"Lesson from case {i}"], "time_taken": f"{i} hours"},
        )
        print(f"   Recorded case {i}: {structure.category.value} -> {outcome}")

    # Get experience
    print("\n6. Agent Experience Summary:")
    experience = learning_system.get_agent_experience()
    print(f"   Total Cases: {experience['total_cases']}")
    print(f"   Success Rate: {experience['success_rate']:.1%}")
    print("   Category Distribution:")
    for category, count in experience["category_distribution"].items():
        print(f"     - {category}: {count}")

    if experience.get("learning_insights"):
        print("\n   Learning Insights:")
        for insight in experience["learning_insights"]:
            print(f"     - {insight}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("PROCESSING UNIT SYSTEM - DEMONSTRATION")
    print("=" * 60)

    try:
        # Demo 1: Basic processing
        demo_basic_processing()

        # Demo 2: Rare case
        demo_rare_case()

        # Demo 3: Enrichment
        demo_enrichment()

        # Demo 4: Continuous learning
        demo_continuous_learning()

        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nGenerated files:")
        print("  - Reference files: .case_references/")
        print("  - Memory files: .case_memory/")
        print("\nNext steps:")
        print("  1. Review reference files in .case_references/")
        print("  2. Use reference files as context for agent execution")
        print("  3. Record case completions for continuous learning")

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
