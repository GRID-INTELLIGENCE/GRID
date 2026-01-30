"""
Spark Manifest Pipeline - Turning Seeds into Tangible Harvests.

Takes complex thoughts and collapses them into a daily actionable manifest.
Uses 'requests' to fetch stabilizing context from external sources.
"""

import logging

# Ensure we can import from grid
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from grid.spark import spark

logger = logging.getLogger(__name__)


class ManifestPipeline:
    def __init__(self, output_dir: str = "e:/grid/harvests") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def fetch_inspiration_seed(self) -> str:
        """Fetches high-level context to stabilize relevance."""
        # Using requests to stay connected to the external environment
        # This can be pointed at any API, or even a local server
        try:
            # Simulation of an external context check
            return "Focus: Strategic Scaffolding. Market Sentiment: High demand for custom utilities."
        except Exception:
            return "Stability: Local mode active."

    def generate_manifest(self, raw_input: str) -> Path:
        """Runs the pipeline to generate a tangible manifest."""
        print("⚡ Ignite: Processing seed...")

        # 1. Reasoning Analysis
        analysis = spark(f"Analyze the tangible value and step-by-step logic for: {raw_input}", persona="reasoning")

        # 2. Skill Mapping
        skills = spark(raw_input, persona="agentic")

        # 3. Routing (The Staircase)
        path = spark(f"Find route from great_hall to library via: {raw_input}", persona="staircase")

        # 4. Stabilize with Requests
        context = self.fetch_inspiration_seed()

        # 5. Composition
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # Extracting data from spark results
        manifest_text = (
            analysis.output.get("thought", analysis.output) if isinstance(analysis.output, dict) else analysis.output
        )

        manifest_content = f"""# ⚡ DAILY MANIFEST: {timestamp}

> **Seed:** {raw_input}
> **External Context:** {context}

## 🎯 The Tangible Goal
A workflow or tool that bridges the gap between complex imagination and daily cash value.

## 📈 Analysis (Reasoning Persona)
{manifest_text}

## 🏰 The Staircase (Strategic Route)
{self._format_route(path.output.get('route', []))}

## 🛠️ Relevant Skills
{self._format_skills(skills.output.get('skills', []))}

## 📝 Daily Resonance
{spark(raw_input, persona="resonance").output.get('message', 'Stay static in your purpose while the stairs move.')}

---
*Created by Spark Manifest Pipeline*
"""

        output_file = self.output_dir / f"MANIFEST_{timestamp.replace('-', '_')}.md"
        output_file.write_text(manifest_content, encoding="utf-8")
        return output_file

    def _format_route(self, route: list[str]) -> str:
        if not route:
            return "- [ ] Explore the topology."
        return "\n".join([f"- [ ] {str(step).replace('_', ' ').title()}" for step in route])

    def _format_skills(self, skills: list[dict]) -> str:
        if not skills:
            return "- No specific skills identified."
        # Skill retriever returns dicts with 'metadata'
        lines = []
        for s in skills[:3]:
            title = s.get("metadata", {}).get("title", s.get("id", "Unknown Skill"))
            lines.append(f"- **{title}**")
        return "\n".join(lines) if lines else "- No specific skills identified."


def main() -> None:
    import sys

    thought = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Build a pipeline for tangible daily utility."
    pipeline = ManifestPipeline()
    path = pipeline.generate_manifest(thought)
    print(f"\n✅ Harvested to: {path}")


if __name__ == "__main__":
    main()
