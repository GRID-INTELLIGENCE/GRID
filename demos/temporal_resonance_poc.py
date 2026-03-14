"""Temporal Resonance Proof of Concept with Synthetic Data Generation.

This script generates synthetic test data for the GRID TemporalResonance system
and validates the Gaussian resonance calculations against expected behavior.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class TemporalIntent:
    """Represents parsed temporal intent from a query."""

    query: str
    era_type: str  # "specific_year", "range", "modern", "historical", "none"
    start_year: int | None
    end_year: int | None
    confidence: float


@dataclass
class TemporalResonance:
    """Result of temporal resonance calculation."""

    score: float
    q_factor: float
    distance: float
    decay: float
    explanation: str


@dataclass
class Document:
    """Synthetic document with temporal metadata."""

    id: str
    title: str
    year: int
    category: str
    content: str


def parse_temporal_intent(query: str) -> TemporalIntent:
    """Extract temporal intent from natural language query."""
    import re

    # Look for year patterns
    year_match = re.search(r"\b(19|20)\d{2}\b", query)
    decade_match = re.search(r"\b(\d{2})s\b", query)

    # Check for era keywords
    text_lower = query.lower()
    has_modern = any(kw in text_lower for kw in ["modern", "contemporary", "recent", "current"])
    has_historical = any(kw in text_lower for kw in ["historical", "ancient", "old", "past"])

    if year_match:
        year = int(year_match.group())
        return TemporalIntent(
            query=query,
            era_type="specific_year",
            start_year=year,
            end_year=year,
            confidence=0.9 if str(year) in query else 0.7,
        )
    elif decade_match:
        decade = int(decade_match.group(1))
        start_year = 1900 + decade if decade >= 50 else 2000 + decade
        return TemporalIntent(
            query=query, era_type="range", start_year=start_year, end_year=start_year + 9, confidence=0.8
        )
    elif has_modern:
        current_year = datetime.now(UTC).year
        return TemporalIntent(
            query=query, era_type="modern", start_year=current_year - 20, end_year=current_year, confidence=0.7
        )
    elif has_historical:
        return TemporalIntent(query=query, era_type="historical", start_year=1900, end_year=1980, confidence=0.6)
    else:
        return TemporalIntent(query=query, era_type="none", start_year=None, end_year=None, confidence=0.0)


def calculate_temporal_resonance(
    temporal_intent: TemporalIntent,
    document: Document,
    q_factor: float = 0.5,
    damping: float = 0.3,
) -> TemporalResonance:
    """Calculate Gaussian resonance between query and document.

    Core formula: resonance = exp(-distance² / (2 * Q²))
    - Q-factor controls peak width (0.1=narrow/specific, 0.9=wide/general)
    - Damping controls temporal decay (0.1=slow, 0.5=fast)
    """
    current_year = datetime.now(UTC).year
    doc_year = document.year

    if temporal_intent.era_type == "none":
        return TemporalResonance(
            score=1.0,
            q_factor=0.5,
            distance=0.0,
            decay=1.0,
            explanation="No temporal constraints - full resonance.",
        )

    # Determine target year
    if temporal_intent.era_type == "specific_year":
        target_year = temporal_intent.start_year or current_year
    elif temporal_intent.era_type == "range":
        target_year = ((temporal_intent.start_year or 0) + (temporal_intent.end_year or 0)) / 2
    elif temporal_intent.era_type == "modern":
        target_year = current_year - 5
    else:  # historical
        target_year = 1990

    # Normalize distance (0-1 range over 100-year span)
    distance = min(abs(doc_year - target_year) / 100.0, 1.0)

    # Gaussian resonance curve
    resonance = math.exp(-(distance**2) / (2 * (q_factor**2)))

    # Apply damping based on era
    decay = 1.0
    if temporal_intent.era_type == "modern":
        years_from_now = current_year - doc_year
        decay = math.exp(-damping * years_from_now / 10.0)
    elif temporal_intent.era_type == "historical":
        decay = 1.0 - (damping * 0.2)

    score = resonance * decay

    # Generate explanation
    q_desc = "narrow (specific)" if q_factor < 0.3 else "wide (general)" if q_factor > 0.7 else "moderate"
    explanation = f"Temporal resonance: {score:.2f}. Q-factor: {q_factor:.2f} ({q_desc})."

    if score > 0.8:
        explanation += " Strong temporal alignment."
    elif score > 0.5:
        explanation += " Moderate temporal relevance."
    else:
        explanation += " Low temporal alignment."

    return TemporalResonance(score, q_factor, distance, decay, explanation)


def generate_synthetic_documents(count: int = 50) -> list[Document]:
    """Generate synthetic documents with temporal metadata."""
    categories = ["Technology", "Science", "History", "Politics", "Culture"]
    templates = [
        "The evolution of {topic} in {year}",
        "Key developments in {topic} during the {decade}s",
        "Understanding {topic}: A {year} perspective",
        "The rise of {topic} in modern era",
        "Historical analysis of {topic} in {year}",
    ]

    topics = {
        "Technology": ["AI", "computing", "internet", "mobile devices", "cloud"],
        "Science": ["quantum physics", "genomics", "climate", "space exploration", "neuroscience"],
        "History": ["industrial revolution", "cold war", "renaissance", "world wars", "ancient civilizations"],
        "Politics": ["democracy", "globalization", "diplomacy", "governance", "movements"],
        "Culture": ["cinema", "music", "literature", "art movements", "social trends"],
    }

    documents = []
    current_year = datetime.now(UTC).year

    for i in range(count):
        category = random.choice(categories)
        topic = random.choice(topics[category])

        # Distribute years with some clustering
        if random.random() < 0.3:
            year = random.randint(1950, 1980)  # Historical cluster
        elif random.random() < 0.5:
            year = random.randint(1980, 2000)  # Recent past
        else:
            year = random.randint(2000, current_year)  # Modern

        decade = (year // 10) * 10
        template = random.choice(templates)
        title = template.format(topic=topic, year=year, decade=decade // 10 % 100)

        doc = Document(
            id=f"doc_{i:03d}",
            title=title,
            year=year,
            category=category,
            content=f"Sample content about {topic} from {year}",
        )
        documents.append(doc)

    return documents


def validate_gaussian_behavior() -> dict[str, Any]:
    """Validate that resonance calculations follow expected Gaussian behavior."""
    results = {"tests": [], "passed": 0, "failed": 0}

    # Test 1: Peak at distance=0
    intent = TemporalIntent("test 2020", "specific_year", 2020, 2020, 1.0)
    doc = Document("test", "test", 2020, "test", "test")
    resonance = calculate_temporal_resonance(intent, doc, q_factor=0.5, damping=0.0)

    test_result = {
        "name": "Peak at distance=0",
        "expected": "score ~ 1.0 at distance=0",
        "actual": f"score={resonance.score:.4f}, distance={resonance.distance:.4f}",
        "passed": resonance.score > 0.95 and resonance.distance == 0.0,
    }
    results["tests"].append(test_result)
    results["passed" if test_result["passed"] else "failed"] += 1

    # Test 2: Narrow Q-factor = faster decay
    intent = TemporalIntent("test 2000", "specific_year", 2000, 2000, 1.0)
    narrow = calculate_temporal_resonance(intent, Document("t", "t", 2010, "t", "t"), q_factor=0.2)
    wide = calculate_temporal_resonance(intent, Document("t", "t", 2010, "t", "t"), q_factor=0.8)

    test_result = {
        "name": "Narrow Q-factor decay",
        "expected": "narrow Q < wide Q at same distance",
        "actual": f"narrow={narrow.score:.4f}, wide={wide.score:.4f}",
        "passed": narrow.score < wide.score,
    }
    results["tests"].append(test_result)
    results["passed" if test_result["passed"] else "failed"] += 1

    # Test 3: Gaussian symmetry (distance 10 years either side)
    intent_center = TemporalIntent("test 2000", "specific_year", 2000, 2000, 1.0)
    left = calculate_temporal_resonance(intent_center, Document("t", "t", 1990, "t", "t"), q_factor=0.5)
    right = calculate_temporal_resonance(intent_center, Document("t", "t", 2010, "t", "t"), q_factor=0.5)

    test_result = {
        "name": "Gaussian symmetry",
        "expected": "+/-10 years from center = equal scores",
        "actual": f"left={left.score:.4f}, right={right.score:.4f}, diff={abs(left.score - right.score):.6f}",
        "passed": abs(left.score - right.score) < 0.001,
    }
    results["tests"].append(test_result)
    results["passed" if test_result["passed"] else "failed"] += 1

    # Test 4: Damping effect on modern queries
    current_year = datetime.now(UTC).year
    modern_intent = TemporalIntent("modern technology", "modern", current_year - 20, current_year, 0.8)
    recent_doc = Document("r", "r", current_year - 2, "t", "t")
    old_doc = Document("o", "o", current_year - 15, "t", "t")

    recent_res = calculate_temporal_resonance(modern_intent, recent_doc, damping=0.3)
    old_res = calculate_temporal_resonance(modern_intent, old_doc, damping=0.3)

    test_result = {
        "name": "Damping effect",
        "expected": "recent doc > old doc due to damping",
        "actual": f"recent={recent_res.decay:.4f}, old={old_res.decay:.4f}",
        "passed": recent_res.decay > old_res.decay,
    }
    results["tests"].append(test_result)
    results["passed" if test_result["passed"] else "failed"] += 1

    # Test 5: No temporal constraints = full resonance
    no_temporal = TemporalIntent("general query", "none", None, None, 0.0)
    any_doc = Document("t", "t", 1850, "t", "t")
    full_res = calculate_temporal_resonance(no_temporal, any_doc)

    test_result = {
        "name": "No constraints = full resonance",
        "expected": "score=1.0 when no temporal intent",
        "actual": f"score={full_res.score:.4f}",
        "passed": full_res.score == 1.0,
    }
    results["tests"].append(test_result)
    results["passed" if test_result["passed"] else "failed"] += 1

    return results


def generate_experiment_data() -> dict[str, Any]:
    """Generate complete experiment data for visualization."""
    documents = generate_synthetic_documents(100)

    # Define test queries with different temporal intents
    queries = [
        "What happened in 1985?",
        "Modern technology trends",
        "Historical analysis of the 1960s",
        "Recent developments in AI",
        "Cold war era politics",
        "Contemporary art movements",
    ]

    # Q-factor configurations to compare
    q_configs = [0.2, 0.5, 0.8]  # narrow, moderate, wide

    # Run experiments
    experiments = []
    for query in queries:
        intent = parse_temporal_intent(query)
        query_results = {"query": query, "intent": asdict(intent), "configs": []}

        for q in q_configs:
            doc_scores = []
            for doc in documents:
                resonance = calculate_temporal_resonance(intent, doc, q_factor=q)
                doc_scores.append(
                    {
                        "doc_id": doc.id,
                        "year": doc.year,
                        "category": doc.category,
                        "score": resonance.score,
                        "distance": resonance.distance,
                        "decay": resonance.decay,
                    }
                )

            # Sort by score
            doc_scores.sort(key=lambda x: x["score"], reverse=True)

            query_results["configs"].append(
                {
                    "q_factor": q,
                    "top_results": doc_scores[:10],
                    "score_distribution": {
                        "high": len([d for d in doc_scores if d["score"] > 0.8]),
                        "medium": len([d for d in doc_scores if 0.5 <= d["score"] <= 0.8]),
                        "low": len([d for d in doc_scores if d["score"] < 0.5]),
                    },
                    "mean_score": sum(d["score"] for d in doc_scores) / len(doc_scores),
                }
            )

        experiments.append(query_results)

    # Generate resonance curves for visualization
    curves = []
    for q in [0.1, 0.3, 0.5, 0.7, 0.9]:
        curve_points = []
        for distance in [i / 100 for i in range(0, 101, 5)]:
            resonance = math.exp(-(distance**2) / (2 * (q**2)))
            curve_points.append({"distance": distance, "resonance": resonance})
        curves.append({"q_factor": q, "points": curve_points})

    validation = validate_gaussian_behavior()

    return {
        "documents": [asdict(d) for d in documents],
        "experiments": experiments,
        "resonance_curves": curves,
        "validation": validation,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main():
    """Run proof of concept and save data."""
    print("Generating Temporal Resonance Proof of Concept Data...")
    print()

    # Generate experiment data
    data = generate_experiment_data()

    # Print validation results
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    val = data["validation"]
    for test in val["tests"]:
        status = "[PASS]" if test["passed"] else "[FAIL]"
        print(f"\n{status}: {test['name']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Actual:   {test['actual']}")

    print(f"\n{'=' * 60}")
    print(f"Summary: {val['passed']}/{val['passed'] + val['failed']} tests passed")
    print("=" * 60)

    # Save to JSON
    output_path = Path("temporal_resonance_poc_data.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nData saved to: {output_path}")
    print(f"Total documents: {len(data['documents'])}")
    print(f"Experiments run: {len(data['experiments'])}")

    return data


if __name__ == "__main__":
    main()
