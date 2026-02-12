"""
Google Safety Engine - Implementation of Google DeepMind's AI Safety Framework
Incorporates Gemini Safety Filters, Frontier Safety Framework redlines, and AI Principles.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


class GoogleSafetyEngine:
    """
    Engine responsible for evaluating content against Google-specific safety standards,
    including the Frontier Safety Framework and Gemini-specific safety classifiers.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.base_path = config_dir or Path(__file__).parent

        # Load safety configuration files
        self.schema = self._load_json("GOOGLE_AI_SAFETY_SCHEMA.json")
        self.actions_matrix = self._load_json("ACTIONS_MATRIX.json")
        self.thresholds = self._load_json("THRESHOLDS.json")

        self.provider_name = self.schema.get("provider", "Google DeepMind")
        self.version = self.schema.get("version", "1.0.0")

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.base_path / filename
        if not path.exists():
            self.logger.error(f"Configuration file not found: {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {filename}: {e}")
            return {}

    def validate_content(
        self, content: str, safety_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validates content using provided safety scores against Google's thresholds.

        Args:
            content: The text content to analyze (prompt or response).
            safety_scores: A dictionary of safety metrics and their corresponding scores (0.0 to 1.0).
                          Expected keys include categories from THRESHOLDS.json.

        Returns:
            A dictionary containing the safety assessment, violations, and recommended actions.
        """
        violations = []
        is_safe = True

        # 1. Evaluate Gemini Safety Filters
        gemini_results = self._check_gemini_filters(safety_scores)
        violations.extend(gemini_results)

        # 2. Evaluate Frontier Safety Redlines
        frontier_results = self._check_frontier_redlines(safety_scores)
        violations.extend(frontier_results)

        # 3. Evaluate Privacy and Security Signals
        privacy_results = self._check_privacy_security(safety_scores)
        violations.extend(privacy_results)

        if violations:
            is_safe = False

        # Map detected violations to prescribed actions
        recommended_actions = self._determine_actions(violations, safety_scores)

        return {
            "is_safe": is_safe,
            "provider": self.provider_name,
            "version": self.version,
            "violations": violations,
            "recommended_actions": recommended_actions,
            "timestamp": self._get_timestamp(),
        }

    def _check_gemini_filters(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        violations = []
        filter_thresholds = self.thresholds.get("signal_thresholds", {}).get(
            "gemini_safety_filters", {}
        )

        for category, threshold in filter_thresholds.items():
            score = scores.get(category, 0.0)
            if score >= threshold:
                violations.append(
                    {
                        "category": f"GEMINI_{category.upper()}",
                        "severity": "HIGH" if score > 0.8 else "MEDIUM",
                        "score": score,
                        "threshold": threshold,
                        "description": f"Exceeded Google Gemini safety threshold for {category}.",
                    }
                )
        return violations

    def _check_frontier_redlines(
        self, scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        violations = []
        frontier_thresholds = self.thresholds.get("signal_thresholds", {}).get(
            "frontier_safety", {}
        )

        for redline, threshold in frontier_thresholds.items():
            score = scores.get(redline, 0.0)
            if score >= threshold:
                violations.append(
                    {
                        "category": f"FRONTIER_{redline.upper()}",
                        "severity": "CRITICAL" if score > 0.5 else "HIGH",
                        "score": score,
                        "threshold": threshold,
                        "description": f"Frontier Safety Redline breached: {redline}.",
                    }
                )
        return violations

    def _check_privacy_security(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        violations = []
        privacy_thresholds = self.thresholds.get("signal_thresholds", {}).get(
            "privacy_and_security", {}
        )

        for metric, threshold in privacy_thresholds.items():
            score = scores.get(metric, 0.0)
            if score >= threshold:
                violations.append(
                    {
                        "category": f"PRIVACY_{metric.upper()}",
                        "severity": "HIGH",
                        "score": score,
                        "threshold": threshold,
                        "description": f"Privacy or security threshold reached for {metric}.",
                    }
                )
        return violations

    def _determine_actions(
        self, violations: List[Dict[str, Any]], scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Maps violations to actions defined in the ACTIONS_MATRIX.json
        """
        triggered_action_ids = set()
        trigger_definitions = self.actions_matrix.get("trigger_definitions", [])
        mapping = self.actions_matrix.get("mapping", [])
        action_catalog = self.actions_matrix.get("action_catalog", {})

        for trigger in trigger_definitions:
            condition = trigger.get("condition", "")
            if self._evaluate_trigger_condition(condition, scores):
                trigger_id = trigger.get("trigger_id")
                # Find associated actions in mapping
                for m in mapping:
                    if m.get("trigger_id") == trigger_id:
                        for act_id in m.get("actions", []):
                            triggered_action_ids.add(act_id)

        # Assemble the action details
        actions = []
        for act_id in triggered_action_ids:
            if act_id in action_catalog:
                action_info = action_catalog[act_id].copy()
                action_info["id"] = act_id
                actions.append(action_info)

        return actions

    def _evaluate_trigger_condition(
        self, condition: str, scores: Dict[str, float]
    ) -> bool:
        """
        Evaluates the logic string from the ACTIONS_MATRIX triggers.
        Handles simple comparisons and logical OR.
        """
        try:
            # Handle Gemini score trigger: "gemini_safety_filters.score > 0.9"
            if "gemini_safety_filters.score" in condition:
                val = float(condition.split(">")[-1].strip())
                # Check if any gemini-related score in input exceeds this
                gemini_categories = [
                    "hate_speech",
                    "harassment",
                    "sexually_explicit",
                    "dangerous_content",
                ]
                return any(scores.get(cat, 0.0) > val for cat in gemini_categories)

            # Handle Frontier Redline trigger: "frontier_safety.cbrn_uplift_score > 0.5 || frontier_safety.cyber_attack_utility > 0.5"
            if "frontier_safety" in condition:
                parts = condition.split("||")
                for part in parts:
                    if ">" in part:
                        metric_path = part.split(">")[
                            0
                        ].strip()  # e.g. frontier_safety.cbrn_uplift_score
                        metric = metric_path.split(".")[-1]
                        val = float(part.split(">")[-1].strip())
                        if scores.get(metric, 0.0) > val:
                            return True
                return False

            # Handle PII trigger: "privacy_and_security.pii_leakage_probability > 0.01"
            if "pii_leakage_probability" in condition:
                val = float(condition.split(">")[-1].strip())
                return scores.get("pii_leakage_probability", 0.0) > val

        except Exception as e:
            self.logger.warning(
                f"Error evaluating trigger condition '{condition}': {e}"
            )

        return False

    def _get_timestamp(self) -> str:
        import datetime

        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def generate_safety_summary(self, result: Dict[str, Any]) -> str:
        """
        Generates a human-readable summary of the safety check.
        Useful for inclusion in the REPORT_TEMPLATE.md
        """
        if result["is_safe"]:
            return "Content evaluated against Google AI Principles and found to be compliant."

        summary = [f"Safety Check Failed (Provider: {result['provider']})"]
        summary.append("Violations Detected:")
        for v in result["violations"]:
            summary.append(
                f"- [{v['severity']}] {v['category']}: {v['description']} (Score: {v['score']})"
            )

        summary.append("\nMitigation Actions Applied:")
        for a in result["recommended_actions"]:
            summary.append(f"- {a['type']}: {a['description']}")

        return "\n".join(summary)


if __name__ == "__main__":
    # Example usage
    engine = GoogleSafetyEngine()
    test_scores = {
        "hate_speech": 0.95,
        "cbrn_uplift_score": 0.1,
        "pii_leakage_probability": 0.0001,
    }
    assessment = engine.validate_content("Example content", test_scores)
    print(engine.generate_safety_summary(assessment))
