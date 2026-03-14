#!/usr/bin/env python
"""CLI demo of TemporalResonance system - Gaussian resonance calculation with XAI explanations.

Run: uv run python demos/temporal_resonance_demo.py
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class TemporalIntent:
    """Parsed temporal intent from a query."""

    query: str
    era_type: str  # "none", "specific_year", "range", "modern", "historical"
    start_year: int | None
    end_year: int | None
    confidence: float


@dataclass
class TemporalResonance:
    """Temporal resonance result with audio engineering metaphor."""

    score: float
    q_factor: float
    distance: float
    decay: float
    explanation: str


def calculate_temporal_resonance(
    temporal_intent: TemporalIntent,
    doc_year: int,
    q_factor: float = 0.5,
    damping: float = 0.3,
) -> TemporalResonance:
    """Calculate Gaussian resonance between query intent and document year."""
    current_year = datetime.now(UTC).year

    # Determine target year based on era type
    if temporal_intent.era_type == "specific_year":
        target_year = temporal_intent.start_year
    elif temporal_intent.era_type == "range":
        target_year = (temporal_intent.start_year + temporal_intent.end_year) / 2
    elif temporal_intent.era_type == "modern":
        target_year = current_year - 5
    else:  # historical
        target_year = 1990

    # Normalize distance (0-100 years → 0-1)
    distance = min(abs(doc_year - target_year) / 100.0, 1.0)

    # Gaussian resonance: e^(-distance² / 2Q²)
    resonance = math.exp(-(distance**2) / (2 * (q_factor**2)))

    # Apply decay/damping
    decay = 1.0
    if temporal_intent.era_type == "modern":
        years_from_now = current_year - doc_year
        decay = math.exp(-damping * years_from_now / 10.0)
    elif temporal_intent.era_type == "historical":
        decay = 1.0 - (damping * 0.2)

    score = resonance * decay

    # Generate explanation
    q_desc = "narrow (specific)" if q_factor < 0.3 else "wide (general)" if q_factor > 0.7 else "moderate"
    explanation = f"Score: {score:.3f} | Q={q_factor:.1f} ({q_desc}) | Distance: {distance:.3f} | Decay: {decay:.3f}"

    return TemporalResonance(score=score, q_factor=q_factor, distance=distance, decay=decay, explanation=explanation)


def explain_temporal_resonance(resonance: TemporalResonance) -> str:
    """Generate human-readable XAI explanation."""
    # Q factor interpretation
    if resonance.q_factor < 0.3:
        q_desc = "narrow (high specificity)"
    elif resonance.q_factor > 0.7:
        q_desc = "wide (general coverage)"
    else:
        q_desc = "moderate (balanced specificity)"

    # Resonance strength
    if resonance.score > 0.8:
        strength = "strong resonance peak detected"
    elif resonance.score > 0.5:
        strength = "moderate resonance alignment"
    else:
        strength = "weak resonance signal"

    # Distance interpretation
    if resonance.distance < 0.2:
        dist_desc = "at resonance peak (near-perfect alignment)"
    elif resonance.distance < 0.5:
        dist_desc = "close to resonance (good alignment)"
    else:
        dist_desc = "outside resonance zone (low alignment)"

    # Damping interpretation
    if resonance.decay > 0.8:
        damp_desc = "minimal damping (signal preserved)"
    elif resonance.decay > 0.5:
        damp_desc = "moderate damping (signal attenuated)"
    else:
        damp_desc = "significant damping (signal decayed)"

    return f"[XAI] {strength}. Q-factor {resonance.q_factor:.2f} ({q_desc}), {dist_desc}. Damping: {damp_desc}."


def demo():
    """Run CLI demonstration."""
    print("=" * 70)
    print("TEMPORAL RESONANCE DEMO - Gaussian Resonance & XAI Explanation")
    print("=" * 70)

    # Simulated documents
    docs = [
        {"title": "AI Research 2024", "year": 2024},
        {"title": "Deep Learning 2020", "year": 2020},
        {"title": "Neural Networks 2015", "year": 2015},
        {"title": "Machine Learning 2010", "year": 2010},
        {"title": "Expert Systems 1990", "year": 1990},
        {"title": "AI Winter 1985", "year": 1985},
    ]

    # Query scenarios
    queries = [
        ("Show me recent AI research", TemporalIntent("recent AI", "modern", 2010, 2030, 0.9)),
        ("Papers from 2020", TemporalIntent("2020", "specific_year", 2020, 2020, 0.9)),
        ("AI history 1980-2000", TemporalIntent("1980-2000", "range", 1980, 2000, 0.85)),
    ]

    for query_text, intent in queries:
        print(f"\n>> QUERY: '{query_text}' (era_type={intent.era_type})")
        print("-" * 60)

        # Try different Q-factors
        for q_factor, q_label in [(0.2, "Narrow"), (0.5, "Moderate"), (0.8, "Wide")]:
            print(f"\n  Q-factor: {q_factor} ({q_label})")
            print("  " + "-" * 40)

            for doc in docs:
                resonance = calculate_temporal_resonance(intent, doc["year"], q_factor=q_factor)
                status = "[+]" if resonance.score >= 0.5 else "[ ]"
                print(f"    {status} {doc['title']:25} (year={doc['year']}) -> score={resonance.score:.3f}")

        # Best match explanation
        best_doc = max(docs, key=lambda d: calculate_temporal_resonance(intent, d["year"]).score)
        best_resonance = calculate_temporal_resonance(intent, best_doc["year"])
        print(f"\n  ** BEST MATCH: {best_doc['title']}")
        print(f"  {explain_temporal_resonance(best_resonance)}")

    # Gaussian curve visualization
    print("\n" + "=" * 70)
    print("GAUSSIAN RESONANCE CURVE (visualized)")
    print("=" * 70)
    print("\nDistance from target year -> Resonance score")
    print("Formula: e^(-distance² / 2Q²)")
    print()

    for q in [0.2, 0.5, 0.8]:
        print(f"Q={q}: ", end="")
        for dist in [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]:
            res = math.exp(-(dist**2) / (2 * q**2))
            bar_len = int(res * 20)
            print("#" * bar_len + " ", end="")
        print(f"  ({'narrow' if q < 0.3 else 'wide' if q > 0.7 else 'moderate'} peak)")

    print("\n" + "=" * 70)
    print("KEY INSIGHT: Lower Q = sharper peak (specific year matching)")
    print("             Higher Q = broader peak (flexible year range)")
    print("=" * 70)


if __name__ == "__main__":
    demo()
