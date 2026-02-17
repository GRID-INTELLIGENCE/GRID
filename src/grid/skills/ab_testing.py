"""
A/B testing framework for skills comparison.

Audio engineering-inspired approach:
- Parallel tracking of variants
- Statistical significance evaluation
- Gradual rollout (Fading in the new variant)
- Automated transition to winner
"""

import json
import logging
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .execution_tracker import SkillExecutionRecord
from .intelligence_inventory import IntelligenceInventory


@dataclass
class ABTestConfig:
    """Configuration for an A/B test."""

    test_id: str
    skill_id: str
    variant_a_id: str
    variant_b_id: str
    rollout_pct: float = 0.0  # 0.0 to 1.0 (portion of traffic to B)
    start_time: float = 0.0
    status: str = "draft"  # draft, running, completed
    winner: str | None = None


@dataclass
class ABTestMetrics:
    """Metrics for a variant during a test."""

    executions: int = 0
    successes: int = 0
    total_time_ms: float = 0.0
    confidence_sum: float = 0.0


class ABTestManager:
    """
    Manages A/B tests for skill optimization.
    """

    STORAGE_DIR = Path("./data/skills_ab_tests")

    def __init__(self, storage_dir: Path | None = None):
        self._logger = logging.getLogger(__name__)
        self._storage_dir = storage_dir or self.STORAGE_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._inventory = IntelligenceInventory()
        self._active_tests: dict[str, ABTestConfig] = self._load_all_configs()

    def _load_all_configs(self) -> dict[str, ABTestConfig]:
        configs = {}
        for c_file in self._storage_dir.glob("*.json"):
            try:
                with open(c_file) as f:
                    data = json.load(f)
                    configs[data["test_id"]] = ABTestConfig(**data)
            except Exception:
                pass
        return configs

    def create_test(self, skill_id: str, variant_b_id: str, initial_rollout: float = 0.1) -> ABTestConfig:
        """Create a new A/B test comparing current (A) to new version (B)."""
        test_id = f"test_{skill_id}_{int(time.time())}"

        # Assume variant A is current baseline
        config = ABTestConfig(
            test_id=test_id,
            skill_id=skill_id,
            variant_a_id="baseline",
            variant_b_id=variant_b_id,
            rollout_pct=initial_rollout,
            start_time=time.time(),
            status="running",
        )

        self._save_config(config)
        self._active_tests[test_id] = config
        return config

    def _save_config(self, config: ABTestConfig):
        with open(self._storage_dir / f"{config.test_id}.json", "w") as f:
            json.dump(asdict(config), f, indent=2)

    def select_variant(self, skill_id: str) -> str:
        """Select which variant to use based on active tests."""
        # Find active test for this skill
        active_test = next(
            (t for t in self._active_tests.values() if t.skill_id == skill_id and t.status == "running"), None
        )

        if not active_test:
            return "baseline"

        if random.random() < active_test.rollout_pct:
            return active_test.variant_b_id
        return active_test.variant_a_id

    def record_result(self, test_id: str, variant_id: str, record: SkillExecutionRecord):
        """Record execution result for a variant in a test."""
        # In a real implementation, this would save to a specialized table in SQLite
        # For Phase 4, we log it so it can be aggregated
        self._logger.debug(f"ABTest {test_id}: Variant {variant_id} executed. Status: {record.status}")

    def evaluate_winner(self, test_id: str) -> tuple[str | None, str]:
        """Evaluate if a winner can be determined."""
        config = self._active_tests.get(test_id)
        if not config:
            return None, "Test not found"

        # 1. Fetch metrics from inventory (aggregated by metadata variant_id)
        # This requires execution_records to have a variant_id column or metadata JSON
        # For now, we simulate the logic

        # winner_id = ...
        # if winner_id:
        #     config.winner = winner_id
        #     config.status = "completed"
        #     self._save_config(config)

        return None, "Insufficient data for statistical significance"

    def update_rollout(self, test_id: str, new_pct: float):
        """Update rollout percentage (Fading)."""
        config = self._active_tests.get(test_id)
        if config:
            config.rollout_pct = max(0.0, min(1.0, new_pct))
            self._save_config(config)
            self._logger.info(f"Updated rollout for {test_id} to {config.rollout_pct:.1%}")
