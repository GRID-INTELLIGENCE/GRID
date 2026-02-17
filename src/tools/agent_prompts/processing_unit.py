#!/usr/bin/env python3
"""Processing Unit - Receptionist System

Acts as the initial processing layer that structures raw input, categorizes cases,
and creates reference files before passing to the agent (lawyer).

This is the "receptionist" that handles initial client intake and case filing.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .advanced_protocols import AdvancedProtocolHandler  # type: ignore[import-not-found]
    from .case_filing import CaseCategory, CaseFilingSystem, CaseStructure  # type: ignore[import-not-found]
    from .reference_generator import ReferenceGenerator  # type: ignore[import-not-found]
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from advanced_protocols import AdvancedProtocolHandler  # type: ignore[import-not-found]
    from case_filing import CaseCategory, CaseFilingSystem, CaseStructure  # type: ignore[import-not-found]
    from reference_generator import ReferenceGenerator  # type: ignore[import-not-found]

# Optional imports for abrasive analysis integration
try:
    from application.mothership.config.inference_abrasiveness import (
        InferenceAbrasivenessConfig,
    )

    ABRASIVE_AVAILABLE = True
except ImportError:
    InferenceAbrasivenessConfig = None
    ABRASIVE_AVAILABLE = False


@dataclass
class ProcessingResult:
    """Result from processing unit."""

    case_id: str
    timestamp: str
    raw_input: str
    structured_data: CaseStructure
    reference_file_path: str
    category: CaseCategory
    is_rare_case: bool
    processing_metadata: dict[str, Any]


class ProcessingUnit:
    """Main processing unit that acts as receptionist."""

    def __init__(
        self,
        knowledge_base_path: Path,
        reference_output_path: Path,
        enable_advanced_protocols: bool = True,
        event_bus: Any | None = None,
        enable_recursive_extraction: bool = False,
        abrasive_config: InferenceAbrasivenessConfig | None = None,
    ):
        """Initialize processing unit.

        Args:
            knowledge_base_path: Path to knowledge base (comprehensive suite)
            reference_output_path: Path where reference files are stored
            enable_advanced_protocols: Enable advanced protocols for rare cases
            event_bus: Optional event bus for emitting events
            enable_recursive_extraction: Enable recursive extraction with abrasive analysis
            abrasive_config: Optional abrasive configuration (creates from env if None and enabled)
        """
        self.knowledge_base_path = knowledge_base_path
        self.reference_output_path = reference_output_path
        self.enable_advanced_protocols = enable_advanced_protocols
        self.event_bus = event_bus
        self.enable_recursive_extraction = enable_recursive_extraction

        # Initialize abrasive config if enabled
        if enable_recursive_extraction:
            if abrasive_config is None:
                if ABRASIVE_AVAILABLE and InferenceAbrasivenessConfig is not None:
                    self.abrasive_config = InferenceAbrasivenessConfig.from_env()
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "Recursive extraction enabled but InferenceAbrasivenessConfig not available. "
                        "Disabling recursive extraction."
                    )
                    self.enable_recursive_extraction = False
                    self.abrasive_config = None
            else:
                self.abrasive_config = abrasive_config
        else:
            self.abrasive_config = None

        # Initialize subsystems
        self.case_filing = CaseFilingSystem()
        self.reference_generator = ReferenceGenerator(
            knowledge_base_path=knowledge_base_path, output_path=reference_output_path
        )
        self.advanced_protocols = AdvancedProtocolHandler() if enable_advanced_protocols else None

        # Ensure output directory exists
        self.reference_output_path.mkdir(parents=True, exist_ok=True)

    def process_input(
        self,
        raw_input: str,
        user_context: dict[str, Any] | None = None,
        examples: list[str] | None = None,
        scenarios: list[str] | None = None,
    ) -> ProcessingResult:
        """Process raw input through receptionist workflow.

        Args:
            raw_input: Raw user input (client case)
            user_context: Optional user context (personal experience, phenomena)
            examples: Optional examples from user
            scenarios: Optional scenarios from user

        Returns:
            ProcessingResult with structured data and reference file
        """
        # Step 1: Initial logging and categorization
        case_id = self._generate_case_id(raw_input)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 2: Structure raw input with iterative logging
        structured_data = self.case_filing.log_and_categorize(
            raw_input=raw_input, user_context=user_context, examples=examples, scenarios=scenarios
        )

        # Step 3: Check if rare case
        is_rare_case = self.case_filing.is_rare_case(structured_data)

        # Step 4: Load structure against comprehensive suite and generate reference
        reference_file_path = self.reference_generator.generate_reference(
            case_id=case_id, structured_data=structured_data, raw_input=raw_input, event_bus=self.event_bus
        )

        # Step 5: Advanced protocols for rare cases
        processing_metadata = {}
        if is_rare_case and self.advanced_protocols:
            processing_metadata = self.advanced_protocols.handle_rare_case(
                case_id=case_id,
                structured_data=structured_data,
                raw_input=raw_input,
                reference_file_path=reference_file_path,
            )

        # Step 5.5: Enable recursive extraction if needed
        # This prepares the configuration for when semantic_grep is called elsewhere
        if self.enable_recursive_extraction and self.abrasive_config:
            # Enable recursive extraction for rare cases or when confidence < threshold
            should_enable_recursion = (
                is_rare_case or structured_data.confidence < self.abrasive_config.thresholds.confidence_threshold
            )

            if should_enable_recursion:
                processing_metadata["recursive_extraction"] = {
                    "enabled": True,
                    "abrasive_config": (
                        self.abrasive_config.to_dict() if hasattr(self.abrasive_config, "to_dict") else {}
                    ),
                    "case_structure": {
                        "category": structured_data.category.value,
                        "priority": structured_data.priority,
                        "confidence": structured_data.confidence,
                    },
                    "max_recursion_limit": 10,  # Default system maximum
                }
                processing_metadata["abrasive_analysis"] = {
                    "applied": True,
                    "level": (
                        self.abrasive_config.abrasiveness_level.value
                        if hasattr(self.abrasive_config, "abrasiveness_level")
                        else "balanced"
                    ),
                    "confidence_threshold": (
                        self.abrasive_config.thresholds.confidence_threshold
                        if hasattr(self.abrasive_config, "thresholds")
                        else 0.7
                    ),
                }

        # Step 6: Emit events if event bus is available
        if self.event_bus:
            try:
                # Emit case.created event
                from grid.agentic.events import CaseCategorizedEvent, CaseCreatedEvent, CaseReferenceGeneratedEvent

                created_event = CaseCreatedEvent(
                    case_id=case_id,
                    raw_input=raw_input,
                    user_id=None,  # Would be passed if available
                    examples=examples or [],
                    scenarios=scenarios or [],
                )

                categorized_event = CaseCategorizedEvent(
                    case_id=case_id,
                    category=structured_data.category.value,
                    priority=structured_data.priority,
                    confidence=structured_data.confidence,
                    structured_data=asdict(structured_data),
                    labels=structured_data.labels,
                    keywords=structured_data.keywords,
                )

                reference_event = CaseReferenceGeneratedEvent(
                    case_id=case_id,
                    reference_file_path=reference_file_path,
                    recommended_roles=[],  # Would be populated from reference
                    recommended_tasks=[],  # Would be populated from reference
                )

                # Publish events asynchronously (non-blocking)
                asyncio.create_task(self.event_bus.publish(created_event.to_dict()))
                asyncio.create_task(self.event_bus.publish(categorized_event.to_dict()))
                asyncio.create_task(self.event_bus.publish(reference_event.to_dict()))
            except Exception as e:
                # Log but don't fail if event emission fails
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to emit events: {e}")

        return ProcessingResult(
            case_id=case_id,
            timestamp=timestamp,
            raw_input=raw_input,
            structured_data=structured_data,
            reference_file_path=reference_file_path,
            category=structured_data.category,
            is_rare_case=is_rare_case,
            processing_metadata=processing_metadata,
        )

    def _generate_case_id(self, raw_input: str) -> str:
        """Generate unique case ID from input."""
        # Use hash of input + timestamp for uniqueness
        hash_input = f"{raw_input}{datetime.now(timezone.utc).isoformat()}"
        case_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"CASE-{case_hash}"

    def get_reference_file(self, case_id: str) -> dict[str, Any] | None:
        """Retrieve reference file for a case."""
        reference_file = self.reference_output_path / f"{case_id}_reference.json"
        if reference_file.exists():
            with open(reference_file) as f:
                return json.load(f)
        return None

    def enrich_with_user_input(
        self,
        case_id: str,
        additional_context: str,
        examples: list[str] | None = None,
        scenarios: list[str] | None = None,
    ) -> dict[str, Any]:
        """Enrich existing case with additional user input.

        This allows users to reflect/resurface seed instances or provide
        additional context after initial processing.
        """
        reference_file = self.get_reference_file(case_id)
        if not reference_file:
            raise ValueError(f"Case {case_id} not found")

        # Update reference with additional context
        if "user_enrichments" not in reference_file:
            reference_file["user_enrichments"] = []

        enrichment = {
            "timestamp": datetime.now().isoformat(),
            "additional_context": additional_context,
            "examples": examples or [],
            "scenarios": scenarios or [],
        }

        reference_file["user_enrichments"].append(enrichment)

        # Re-process with enriched data
        structured_data = self.case_filing.log_and_categorize(
            raw_input=reference_file["raw_input"],
            user_context={**(reference_file.get("user_context", {}) or {}), "additional_context": additional_context},
            examples=(reference_file.get("examples", []) or []) + (examples or []),
            scenarios=(reference_file.get("scenarios", []) or []) + (scenarios or []),
        )

        # Update reference file
        reference_file["structured_data"] = self._make_json_serializable(asdict(structured_data))
        reference_file["last_updated"] = datetime.now().isoformat()

        # Save updated reference
        reference_file_path = self.reference_output_path / f"{case_id}_reference.json"
        with open(reference_file_path, "w") as f:
            json.dump(self._make_json_serializable(reference_file), f, indent=2)

        return reference_file

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

    def sync_settings_with_eufle(self) -> dict[str, Any]:
        """Implementation point for syncing settings with EUFLE Studio."""
        try:
            from grid.distribution.eufle_bridge import EUFLEBridge

            bridge = EUFLEBridge()
            return bridge.sync_settings()
        except ImportError:
            return {"status": "error", "message": "EUFLEBridge not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main() -> int:
    """CLI entry point for processing unit."""
    import argparse

    parser = argparse.ArgumentParser(description="Process raw input through receptionist workflow")
    parser.add_argument("input", help="Raw input text")
    parser.add_argument("--knowledge-base", default="tools/agent_prompts", help="Knowledge base path")
    parser.add_argument("--output", default=".case_references", help="Reference files output path")
    parser.add_argument("--context", help="User context JSON file")
    parser.add_argument("--examples", nargs="+", help="User examples")
    parser.add_argument("--scenarios", nargs="+", help="User scenarios")

    args = parser.parse_args()

    # Load user context if provided
    user_context = None
    if args.context:
        with open(args.context) as f:
            user_context = json.load(f)

    # Initialize processing unit
    processing_unit = ProcessingUnit(
        knowledge_base_path=Path(args.knowledge_base), reference_output_path=Path(args.output)
    )

    # Process input
    result = processing_unit.process_input(
        raw_input=args.input, user_context=user_context, examples=args.examples, scenarios=args.scenarios
    )

    # Output result
    print(json.dumps(processing_unit._make_json_serializable(asdict(result)), indent=2))

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
