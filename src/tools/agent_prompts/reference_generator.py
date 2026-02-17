#!/usr/bin/env python3
"""Reference Generator

Loads initial structure against comprehensive suite (agent evolution system)
and generates reference files for cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .case_filing import CaseCategory, CaseStructure  # type: ignore[import-not-found]
except ImportError:
    # For standalone execution
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from case_filing import CaseCategory, CaseStructure  # type: ignore[import-not-found]

try:
    from application.mothership.config.inference_abrasiveness import (
        AbrasivenessThresholds,
        InferenceAbrasivenessConfig,
        InferenceAbrasivenessLevel,
    )
except ImportError:
    InferenceAbrasivenessConfig = None
    InferenceAbrasivenessLevel = None
    AbrasivenessThresholds = None


class ReferenceGenerator:
    """Generates reference files by loading structure against comprehensive suite."""

    def __init__(self, knowledge_base_path: Path, output_path: Path):
        """Initialize reference generator.

        Args:
            knowledge_base_path: Path to knowledge base (comprehensive suite)
            output_path: Path where reference files are stored
        """
        self.knowledge_base_path = knowledge_base_path
        self.output_path = output_path

        # Load comprehensive suite components
        self.system_prompt_path = knowledge_base_path / "system_prompt.md"
        self.role_templates_path = knowledge_base_path / "role_templates.md"
        self.task_prompts_path = knowledge_base_path / "task_prompts.md"
        self.agent_prompts_json = knowledge_base_path / "agent_prompts.json"

        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)

    def generate_reference(
        self, case_id: str, structured_data: CaseStructure, raw_input: str, event_bus: Any | None = None
    ) -> str:
        """Generate reference file for a case.

        Args:
            case_id: Unique case identifier
            structured_data: Structured case data
            raw_input: Original raw input

        Returns:
            Path to generated reference file
        """
        # Load comprehensive suite mappings
        suite_mappings = self._load_suite_mappings()

        # Map case structure to relevant suite components
        relevant_components = self._map_to_suite_components(structured_data, suite_mappings)

        # Generate reference file structure
        reference = {
            "case_id": case_id,
            "timestamp": structured_data.timestamp,
            "raw_input": raw_input,
            "structured_data": self._structure_to_dict(structured_data),
            "comprehensive_suite_mapping": relevant_components,
            "recommended_roles": self._recommend_roles(structured_data),
            "recommended_tasks": self._recommend_tasks(structured_data),
            "recommended_workflow": self._recommend_workflow(structured_data),
            "context_for_agent": self._generate_agent_context(structured_data, relevant_components),
            "user_context": {
                "examples": structured_data.user_examples,
                "scenarios": structured_data.user_scenarios,
                "phenomena": structured_data.user_phenomena,
            },
            "metadata": {
                "category": structured_data.category.value,
                "priority": structured_data.priority,
                "confidence": structured_data.confidence,
                "labels": structured_data.labels,
            },
        }

        # Save reference file
        reference_file_path = self.output_path / f"{case_id}_reference.json"
        with open(reference_file_path, "w") as f:
            json.dump(self._make_json_serializable(reference), f, indent=2)

        # Emit event if event bus is available
        if event_bus:
            try:
                import asyncio

                from grid.agentic.events import CaseReferenceGeneratedEvent

                reference_event = CaseReferenceGeneratedEvent(
                    case_id=case_id,
                    reference_file_path=str(reference_file_path),
                    recommended_roles=relevant_components.get("category_mappings", {}).get("roles", []),
                    recommended_tasks=relevant_components.get("keyword_mappings", {}).get("tasks", []),
                    workflow=self._recommend_workflow(structured_data),
                )

                # Publish event asynchronously (non-blocking)
                asyncio.create_task(event_bus.publish(reference_event.to_dict()))
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to emit reference_generated event: {e}")

        return str(reference_file_path)

    def _load_suite_mappings(self) -> dict[str, Any]:
        """Load mappings from comprehensive suite."""
        mappings = {
            "system_prompt": {"path": str(self.system_prompt_path), "exists": self.system_prompt_path.exists()},
            "role_templates": {
                "path": str(self.role_templates_path),
                "exists": self.role_templates_path.exists(),
                "roles": ["Analyst", "Architect", "Planner", "Executor", "Evaluator", "SafetyOfficer"],
            },
            "task_prompts": {
                "path": str(self.task_prompts_path),
                "exists": self.task_prompts_path.exists(),
                "tasks": ["/inventory", "/gapanalysis", "/plan", "/execute", "/validate", "/safety review"],
            },
            "agent_prompts_json": {"path": str(self.agent_prompts_json), "exists": self.agent_prompts_json.exists()},
        }

        # Load JSON package if exists
        if self.agent_prompts_json.exists():
            try:
                with open(self.agent_prompts_json) as f:
                    mappings["agent_prompts_data"] = json.load(f)
            except Exception:  # noqa: S110 intentional silent handling
                pass

        return mappings

    def _map_to_suite_components(self, structure: CaseStructure, suite_mappings: dict[str, Any]) -> dict[str, Any]:
        """Map case structure to relevant suite components."""
        relevant = {"category_mappings": {}, "keyword_mappings": {}, "priority_mappings": {}}

        # Map category to relevant roles
        category_role_map = {
            CaseCategory.CODE_ANALYSIS: ["Analyst", "Executor"],
            CaseCategory.ARCHITECTURE: ["Architect", "Planner"],
            CaseCategory.TESTING: ["Executor", "Evaluator"],
            CaseCategory.DOCUMENTATION: ["Analyst", "Executor"],
            CaseCategory.DEPLOYMENT: ["Executor", "SafetyOfficer"],
            CaseCategory.SECURITY: ["SafetyOfficer", "Architect"],
            CaseCategory.PERFORMANCE: ["Analyst", "Evaluator"],
            CaseCategory.BUG_FIX: ["Analyst", "Executor", "Evaluator"],
            CaseCategory.FEATURE_REQUEST: ["Planner", "Architect", "Executor"],
            CaseCategory.REFACTORING: ["Architect", "Planner", "Executor"],
            CaseCategory.INTEGRATION: ["Architect", "Executor", "Evaluator"],
        }

        relevant["category_mappings"]["roles"] = category_role_map.get(structure.category, ["Analyst", "Planner"])

        # Map keywords to relevant tasks
        keyword_task_map = {
            "inventory": "/inventory",
            "gap": "/gapanalysis",
            "plan": "/plan",
            "execute": "/execute",
            "validate": "/validate",
            "safety": "/safety review",
        }

        relevant_tasks = [keyword_task_map[keyword] for keyword in structure.keywords if keyword in keyword_task_map]

        relevant["keyword_mappings"]["tasks"] = relevant_tasks or ["/inventory", "/gapanalysis"]

        return relevant

    def _recommend_roles(self, structure: CaseStructure) -> list[str]:
        """Recommend roles based on case structure."""
        category_role_map = {
            CaseCategory.CODE_ANALYSIS: ["Analyst", "Executor"],
            CaseCategory.ARCHITECTURE: ["Architect", "Planner"],
            CaseCategory.TESTING: ["Executor", "Evaluator"],
            CaseCategory.DOCUMENTATION: ["Analyst", "Executor"],
            CaseCategory.DEPLOYMENT: ["Executor", "SafetyOfficer"],
            CaseCategory.SECURITY: ["SafetyOfficer", "Architect"],
            CaseCategory.PERFORMANCE: ["Analyst", "Evaluator"],
            CaseCategory.BUG_FIX: ["Analyst", "Executor", "Evaluator"],
            CaseCategory.FEATURE_REQUEST: ["Planner", "Architect", "Executor"],
            CaseCategory.REFACTORING: ["Architect", "Planner", "Executor"],
            CaseCategory.INTEGRATION: ["Architect", "Executor", "Evaluator"],
        }

        return category_role_map.get(structure.category, ["Analyst"])

    def _recommend_tasks(self, structure: CaseStructure) -> list[str]:
        """Recommend tasks based on case structure."""
        # Default workflow
        tasks = ["/inventory", "/gapanalysis"]

        # Add planning if feature request or refactoring
        if structure.category in [CaseCategory.FEATURE_REQUEST, CaseCategory.REFACTORING]:
            tasks.append("/plan")

        # Add execution for most categories
        if structure.category != CaseCategory.RARE:
            tasks.append("/execute")

        # Add validation for testing, deployment, security
        if structure.category in [CaseCategory.TESTING, CaseCategory.DEPLOYMENT, CaseCategory.SECURITY]:
            tasks.append("/validate")
            tasks.append("/safety review")

        # Add EUFLE Sync
        if any(kw in ["eufle", "resonance"] for kw in structure.keywords):
            tasks.append("/eufle_sync")

        return tasks

    def _recommend_workflow(self, structure: CaseStructure) -> list[str]:
        """Recommend workflow steps."""
        workflow = []

        # Always start with inventory
        workflow.append("1. Run /inventory to discover system state")

        # Gap analysis for most cases
        if structure.category != CaseCategory.RARE:
            workflow.append("2. Run /gapanalysis to identify gaps")

        # Planning for feature requests
        if structure.category == CaseCategory.FEATURE_REQUEST:
            workflow.append("3. Run /plan to create backlog")

        # Execution
        workflow.append("4. Run /execute to generate artifacts")

        # Validation
        if structure.category in [CaseCategory.TESTING, CaseCategory.DEPLOYMENT, CaseCategory.SECURITY]:
            workflow.append("5. Run /validate to verify changes")
            workflow.append("6. Run /safety review for governance")

        # EUFLE Sync
        if any(kw in ["eufle", "resonance"] for kw in structure.keywords):
            workflow.append("7. Run /eufle_sync to synchronize settings with EUFLE Studio")

        return workflow

    def _generate_agent_context(self, structure: CaseStructure, suite_mappings: dict[str, Any]) -> str:
        """Generate context string for agent (lawyer)."""
        context_parts = [
            f"Case Category: {structure.category.value}",
            f"Priority: {structure.priority}",
            f"Confidence: {structure.confidence:.2f}",
            "",
            "Keywords: " + ", ".join(structure.keywords[:10]),
            "",
            "Recommended Roles: " + ", ".join(self._recommend_roles(structure)),
            "Recommended Tasks: " + ", ".join(self._recommend_tasks(structure)),
        ]

        if structure.user_examples:
            context_parts.append("")
            context_parts.append("User Examples:")
            for i, example in enumerate(structure.user_examples, 1):
                context_parts.append(f"  {i}. {example}")

        if structure.user_scenarios:
            context_parts.append("")
            context_parts.append("User Scenarios:")
            for i, scenario in enumerate(structure.user_scenarios, 1):
                context_parts.append(f"  {i}. {scenario}")

        return "\n".join(context_parts)

    def _structure_to_dict(self, structure: CaseStructure) -> dict[str, Any]:
        """Convert CaseStructure to dictionary."""
        return {
            "timestamp": structure.timestamp,
            "labels": structure.labels,
            "category": structure.category.value,
            "priority": structure.priority,
            "keywords": structure.keywords,
            "entities": structure.entities,
            "relationships": structure.relationships,
            "confidence": structure.confidence,
            "logging_iterations": structure.logging_iterations,
        }

    def suggest_abrasive_settings(
        self,
        structure: CaseStructure,
        current_config: InferenceAbrasivenessConfig,
    ) -> dict[str, Any]:
        """Suggest abrasive settings based on case structure.

        Args:
            structure: Case structure for context
            current_config: Current abrasive configuration

        Returns:
            Dictionary with suggested abrasive settings adjustments
        """
        if InferenceAbrasivenessLevel is None or current_config is None:
            return {}

        suggestions: dict[str, Any] = {}

        # Map case categories to abrasive levels
        category_abrasive_map = {
            CaseCategory.RARE: InferenceAbrasivenessLevel.AGGRESSIVE,
            CaseCategory.BUG_FIX: InferenceAbrasivenessLevel.AGGRESSIVE,
            CaseCategory.CODE_ANALYSIS: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.ARCHITECTURE: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.TESTING: InferenceAbrasivenessLevel.PASSIVE,
            CaseCategory.DEPLOYMENT: InferenceAbrasivenessLevel.PASSIVE,
            CaseCategory.SECURITY: InferenceAbrasivenessLevel.PASSIVE,
            CaseCategory.PERFORMANCE: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.FEATURE_REQUEST: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.REFACTORING: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.INTEGRATION: InferenceAbrasivenessLevel.BALANCED,
            CaseCategory.DOCUMENTATION: InferenceAbrasivenessLevel.BALANCED,
        }

        # Get suggested level
        suggested_level = category_abrasive_map.get(
            structure.category,
            InferenceAbrasivenessLevel.BALANCED,
        )

        # Only suggest if different from current
        if suggested_level != current_config.abrasiveness_level:
            suggestions["abrasiveness_level"] = suggested_level.value

        # Suggest threshold adjustments based on case characteristics
        threshold_adjustments: dict[str, float] = {}

        # Import quality gates for adjustment factors
        try:
            from config.qualityGates import QualityGates

            adjustment_factors = QualityGates.get("inferenceAbrasiveness", {}).get("adjustmentFactors", {})
            low_conf_mult = adjustment_factors.get("lowConfidenceMultiplier", 0.8)
            high_conf_mult = adjustment_factors.get("highConfidenceMultiplier", 1.1)
            critical_mult = adjustment_factors.get("criticalPriorityMultiplier", 1.5)
            low_priority_mult = adjustment_factors.get("lowPriorityMultiplier", 0.8)
            rare_conf_mult = adjustment_factors.get("rareCaseConfidenceMultiplier", 0.7)
            rare_dev_mult = adjustment_factors.get("rareCaseDeviationMultiplier", 1.3)
        except ImportError:
            # Fallback to defaults
            low_conf_mult = 0.8
            high_conf_mult = 1.1
            critical_mult = 1.5
            low_priority_mult = 0.8
            rare_conf_mult = 0.7
            rare_dev_mult = 1.3

        # Adjust confidence threshold based on case confidence
        if structure.confidence < 0.3:
            # Low confidence cases: lower threshold to be more aggressive
            threshold_adjustments["confidence_threshold"] = max(
                0.5,
                current_config.thresholds.confidence_threshold * low_conf_mult,
            )
        elif structure.confidence > 0.8:
            # High confidence cases: raise threshold to be more selective
            threshold_adjustments["confidence_threshold"] = min(
                0.9,
                current_config.thresholds.confidence_threshold * high_conf_mult,
            )

        # Adjust pattern deviation threshold based on priority
        if structure.priority == "critical":
            # Critical cases: more tolerance for deviation
            threshold_adjustments["pattern_deviation_threshold"] = min(
                0.5,
                current_config.thresholds.pattern_deviation_threshold * critical_mult,
            )
        elif structure.priority == "low":
            # Low priority: less tolerance
            threshold_adjustments["pattern_deviation_threshold"] = max(
                0.1,
                current_config.thresholds.pattern_deviation_threshold * low_priority_mult,
            )

        # Adjust based on RARE category
        if structure.category == CaseCategory.RARE:
            # Rare cases: lower thresholds for more results
            if "confidence_threshold" not in threshold_adjustments:
                threshold_adjustments["confidence_threshold"] = max(
                    0.5,
                    current_config.thresholds.confidence_threshold * rare_conf_mult,
                )
            if "pattern_deviation_threshold" not in threshold_adjustments:
                threshold_adjustments["pattern_deviation_threshold"] = min(
                    0.5,
                    current_config.thresholds.pattern_deviation_threshold * rare_dev_mult,
                )

        if threshold_adjustments:
            suggestions["threshold_adjustments"] = threshold_adjustments

        return suggestions

    def _make_json_serializable(self, obj: Any) -> Any:
        """Recursively convert objects to JSON-serializable format."""
        from enum import Enum

        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Try to convert to string as fallback
            try:
                return str(obj)
            except Exception:
                return None


if __name__ == "__main__":
    from .case_filing import CaseFilingSystem

    # Example usage
    filing_system = CaseFilingSystem()
    generator = ReferenceGenerator(
        knowledge_base_path=Path("tools/agent_prompts"), output_path=Path(".case_references")
    )

    test_input = "I need to add contract testing to the CI pipeline"
    structure = filing_system.log_and_categorize(raw_input=test_input)

    reference_path = generator.generate_reference(case_id="TEST-001", structured_data=structure, raw_input=test_input)

    print(f"Reference file generated: {reference_path}")
