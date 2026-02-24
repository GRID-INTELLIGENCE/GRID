"""
Mycelium Demonstration — Backend Script
========================================
Generates a complete demonstration of Mycelium's universal comprehension
layer by processing the SAME source text through different personas and
sensory profiles.

Output: JSON to stdout (consumed by the presentation page).
Also prints a human-readable report to stderr.

Usage:
    uv run python demos/mycelium_demo.py
    uv run python demos/mycelium_demo.py --json  # JSON only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mycelium import Instrument
from mycelium.core import Depth
from mycelium.sensory import SensoryProfile

# ── Source texts ──────────────────────────────────────────────────
SCENARIOS = [
    {
        "id": "grid_analysis",
        "title": "GRID Platform Analysis",
        "context": "An Environmental Intelligence report from GRID's DRTP framework",
        "text": (
            "The Environmental Intelligence middleware detected dimensional imbalance "
            "in the DRTP framework during the latest Roundtable session. The Practical "
            "dimension scored 0.82 while Legal scored 0.31 and Psychological scored 0.45. "
            "This indicates the conversation was heavily skewed toward actionable items "
            "without sufficient consideration of regulatory constraints or emotional "
            "impact on stakeholders. The system applied a temperature adjustment of +0.15 "
            "to bias LLM responses toward legal and psychological grounding. Three nudge "
            "injections were triggered at turns 4, 7, and 11 to restore equilibrium. "
            "The overall balance coefficient improved from 0.39 to 0.67 over the session, "
            "representing a 72% improvement in dimensional balance. However, the Legal "
            "dimension remains below the 0.5 threshold and requires focused attention "
            "in the next session."
        ),
    },
    {
        "id": "machine_learning",
        "title": "Machine Learning Concepts",
        "context": "A textbook passage about neural network training",
        "text": (
            "Neural networks learn through backpropagation, an algorithm that computes "
            "the gradient of the loss function with respect to each weight by the chain "
            "rule, composing gradients from the output layer backward through the network. "
            "During training, the network feeds input data forward through layers of "
            "artificial neurons, each applying a nonlinear activation function such as "
            "ReLU or sigmoid. The predicted output is compared against the true label "
            "using a loss function like cross-entropy or mean squared error. The gradient "
            "of this loss tells each weight how much to change to reduce the error. "
            "Stochastic gradient descent then updates the weights in small steps "
            "proportional to the learning rate, iterating over batches of training data "
            "until the model converges to acceptable accuracy."
        ),
    },
    {
        "id": "legal_privacy",
        "title": "Data Privacy Regulation",
        "context": "A compliance briefing about local data handling requirements",
        "text": (
            "Under the framework's data governance requirements, all personally "
            "identifiable information must be processed exclusively on local infrastructure "
            "without transmission to external services. This includes but is not limited "
            "to biometric identifiers, geolocation data, device fingerprints, behavioral "
            "analytics, and session-correlated metadata. The retention period for "
            "interaction logs is capped at 90 days, after which automated purging must "
            "occur without manual intervention. Users retain the right to request "
            "immediate deletion of their profile data, including derived inferences "
            "and pattern analysis results. Non-compliance triggers a mandatory incident "
            "report within 72 hours and may result in automatic suspension of the "
            "affected processing module."
        ),
    },
]

PERSONAS = [
    {
        "id": "expert",
        "label": "Expert Analyst",
        "icon": "🔬",
        "expertise": "expert",
        "tone": "academic",
        "depth": "cold_brew",
        "description": "Deep technical understanding, wants precision and nuance",
    },
    {
        "id": "stakeholder",
        "label": "Business Stakeholder",
        "icon": "💼",
        "expertise": "familiar",
        "tone": "direct",
        "depth": "americano",
        "description": "Knows the basics, wants actionable takeaways",
    },
    {
        "id": "newcomer",
        "label": "New Team Member",
        "icon": "🌱",
        "expertise": "beginner",
        "tone": "warm",
        "depth": "espresso",
        "description": "First week on the job, needs gentle onboarding",
    },
]

SENSORY_PROFILES = ["default", "cognitive", "focus", "calm"]


def run_demo() -> dict:
    """Run the full demonstration and return structured results."""
    results: dict = {
        "scenarios": [],
        "concepts": [],
        "sensory_comparison": {},
    }

    for scenario in SCENARIOS:
        scenario_result = {
            "id": scenario["id"],
            "title": scenario["title"],
            "context": scenario["context"],
            "source_text": scenario["text"],
            "source_length": len(scenario["text"]),
            "personas": [],
        }

        for persona in PERSONAS:
            m = Instrument()
            m.set_user(expertise=persona["expertise"], tone=persona["tone"])

            result = m.synthesize(scenario["text"])

            scenario_result["personas"].append({
                "id": persona["id"],
                "label": persona["label"],
                "icon": persona["icon"],
                "description": persona["description"],
                "depth": persona["depth"],
                "gist": result.gist,
                "highlights": [
                    {
                        "text": h.text,
                        "priority": h.priority.name.lower(),
                        "context": h.context[:80] if h.context else "",
                        "category": h.category,
                    }
                    for h in result.highlights[:6]
                ],
                "summary": result.summary,
                "explanation": result.explanation,
                "analogy": result.analogy,
                "compression_ratio": round(result.compression_ratio, 3),
                "patterns": result.patterns_applied,
            })

        results["scenarios"].append(scenario_result)

    # Concept exploration
    m = Instrument()
    concept_names = ["cache", "recursion", "encryption", "api", "database"]
    for concept_name in concept_names:
        nav = m.explore(concept_name)
        if nav:
            concept_data = {
                "name": concept_name,
                "pattern": nav.lens.pattern,
                "eli5": nav.lens.eli5,
                "analogy": nav.lens.analogy,
                "visual_hint": nav.lens.visual_hint,
                "when_useful": nav.lens.when_useful,
                "alternatives": nav.alternatives_available,
            }
            # Try a different lens
            nav2 = m.try_different(concept_name)
            if nav2:
                concept_data["alt_pattern"] = nav2.lens.pattern
                concept_data["alt_eli5"] = nav2.lens.eli5
                concept_data["alt_analogy"] = nav2.lens.analogy
            results["concepts"].append(concept_data)

    # Sensory profile comparison
    sample_text = SCENARIOS[0]["text"]
    for profile in SENSORY_PROFILES:
        m = Instrument(sensory_profile=SensoryProfile(profile))
        result = m.synthesize(sample_text)
        results["sensory_comparison"][profile] = {
            "gist": result.gist,
            "info": m.sensory_info,
        }

    return results


def print_report(results: dict) -> None:
    """Print human-readable report to stderr."""
    w = sys.stderr.write

    w("\n" + "=" * 70 + "\n")
    w("  MYCELIUM DEMONSTRATION — Universal Comprehension Layer\n")
    w("=" * 70 + "\n\n")

    for scenario in results["scenarios"]:
        w(f"━━━ Scenario: {scenario['title']} ━━━\n")
        w(f"Context: {scenario['context']}\n")
        w(f"Source: {scenario['source_length']} characters\n\n")

        for persona in scenario["personas"]:
            w(f"  {persona['icon']} {persona['label']} ({persona['description']})\n")
            w(f"  {'─' * 50}\n")
            w(f"  Gist: {persona['gist'][:100]}...\n")
            w(f"  Keywords: {', '.join(h['text'] for h in persona['highlights'][:4])}\n")
            w(f"  Compression: {persona['compression_ratio'] * 100:.0f}% of original\n")
            if persona["patterns"]:
                w(f"  Patterns: {', '.join(persona['patterns'])}\n")
            w("\n")

    w("━━━ Concept Explorer ━━━\n\n")
    for concept in results["concepts"]:
        w(f"  📖 {concept['name'].upper()}\n")
        w(f"     ELI5: {concept['eli5']}\n")
        w(f"     Analogy: {concept['analogy']}\n")
        if concept.get("alt_eli5"):
            w(f"     Alt lens: {concept['alt_eli5']}\n")
        w("\n")

    w("━━━ Sensory Profiles ━━━\n\n")
    for profile, data in results["sensory_comparison"].items():
        w(f"  [{profile.upper()}] {data['info'][:80]}...\n")

    w("\n" + "=" * 70 + "\n")
    w("  Demo complete. Use --json for machine-readable output.\n")
    w("=" * 70 + "\n\n")


if __name__ == "__main__":
    results = run_demo()

    if "--json" in sys.argv:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_report(results)
        # Also write JSON to file for the presentation
        output_path = Path(__file__).parent / "mycelium_demo_data.json"
        output_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        sys.stderr.write(f"  JSON data written to: {output_path}\n\n")
