"""Wealth Management Skill for GRID.

This skill processes Mamun Kabir Bhuiyan's wealth data and integrates it with GRID.
"""

import csv
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from grid.security.pii_redaction import redact_wealth_data
from grid.skills.base import SimpleSkill

logger = logging.getLogger(__name__)


class WealthManagementSkill:
    """Skill for managing and analyzing personal wealth data."""

    id = "wealth.management"
    name = "Wealth Management"
    description = "Process and analyze wealth management data for Mamun Kabir Bhuiyan"
    version = "1.0.0"

    def __init__(self, data_dir: str = "e:/grid/data/wealth_management"):
        self.data_dir = Path(data_dir)

    def _read_csv(self, filename: str) -> list[dict[str, str]]:
        path = self.data_dir / filename
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []

        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def run(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run the wealth management analysis."""
        import json

        from grid.knowledge.structural_learning import StructuralLearningLayer

        # 1. Load Data
        self._read_csv("00_personal_profile.csv")
        assets = self._read_csv("01_asset_registry.csv")
        revenue = self._read_csv("03_revenue_streams.csv")
        dependencies = self._read_csv("05_dependencies.csv")
        self._read_csv("04_capital_holdings.csv")

        # 2. Initialize KG and Awareness
        kg = StructuralLearningLayer()
        from grid.awareness.domain_tracking import WealthDomainTracker

        wealth_tracker = WealthDomainTracker()

        # 3. Add Entities
        # Client
        kg.add_entity("PER-001", "Person", {"name": "[REDACTED]", "occupation": "Businessman"})

        # Dependents
        for dep in dependencies:
            dep_id = f"PER-DEP-{dep['dependent_id']}"
            kg.add_entity(
                dep_id,
                "Person",
                {
                    "name": dep["dependent_name"],
                    "relationship": dep["relationship"],
                    "financial_support": dep["financial_support_required"],
                },
            )
            if dep["financial_support_required"].lower() == "yes":
                kg.add_relationship(dep_id, "PER-001", "DEPENDS_ON_FINANCIALLY")

        # Assets
        total_assets_value = 0.0
        for asset in assets:
            try:
                val = float(asset.get("current_value", 0))
                total_assets_value += val
                kg.add_entity(
                    asset["asset_id"],
                    "Asset",
                    {"name": asset["asset_name"], "category": asset["category"], "current_value": val},
                )
                kg.add_relationship("PER-001", asset["asset_id"], "OWNS")
            except (ValueError, TypeError):
                pass

        # Revenue
        total_monthly_income = 0.0
        for stream in revenue:
            try:
                val = float(stream.get("base_amount", 0))
                total_monthly_income += val
                kg.add_entity(
                    stream["stream_id"],
                    "RevenueStream",
                    {"name": stream["stream_name"], "amount": val, "frequency": stream["frequency"]},
                )
                kg.add_relationship(stream["stream_id"], "PER-001", "PROVIDES_INCOME")
            except (ValueError, TypeError):
                pass

        # 4. Calculate Summary Metrics
        dependents_count = len([d for d in dependencies if d.get("financial_support_required", "").lower() == "yes"])

        # 5. Export KG
        kg_data = {
            "entities": {eid: {"type": e.entity_type, "properties": e.properties} for eid, e in kg.entities.items()},
            "relationships": [
                {"source": r.source_id, "target": r.target_id, "type": r.relationship_type, "strength": r.strength}
                for r in kg.relationship_model.relationships.values()
            ],
        }

        kg_path = self.data_dir / "knowledge_graph.json"
        with open(kg_path, "w", encoding="utf-8") as f:
            json.dump(kg_data, f, indent=2)

        # 6. Awareness Tracking
        savings_rate = 0.0  # TBD
        dependency_ratio = dependents_count / 1.0  # 1 earner

        snapshot = wealth_tracker.track_wealth_metrics(
            net_worth=total_assets_value,
            monthly_income=total_monthly_income,
            savings_rate=savings_rate,
            dependency_ratio=dependency_ratio,
            patterns=["STABLE_ASSETS" if total_assets_value > 0 else "NO_ASSETS"],
        )

        # 7. Compile Results
        results = {
            "client_name": "[REDACTED - PERSONAL_DATA]",
            "metrics": {
                "net_worth": total_assets_value,
                "monthly_income": total_monthly_income,
                "dependents_count": dependents_count,
            },
            "knowledge_graph": {
                "entities_count": len(kg.entities),
                "relationships_count": len(kg.relationship_model.relationships),
                "path": str(kg_path),
            },
            "awareness": {
                "domain": "wealth",
                "timestamp": snapshot.timestamp.isoformat(),
                "metrics": snapshot.metrics,
                "patterns": snapshot.patterns,
            },
            "status": "success",
            "message": f"Analyzed {len(assets)} assets and {len(revenue)} revenue streams. KG & Awareness updated.",
            "confidence": 0.99,
        }

        # 8. Apply PII redaction to results
        results = redact_wealth_data(results)

        return results


# Register the skill instance
wealth_management = SimpleSkill(
    id=WealthManagementSkill.id,
    name=WealthManagementSkill.name,
    description=WealthManagementSkill.description,
    handler=WealthManagementSkill().run,
    version=WealthManagementSkill.version,
)
