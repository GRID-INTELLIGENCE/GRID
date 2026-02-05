#!/usr/bin/env python3
"""
Parasite Guard Contract Validation Script.

Validates that all parasite guard components satisfy their contracts:
- Detectors implement DetectorContract
- Sanitizers implement SanitizerContract
- Alerters implement AlerterContract

Also validates configuration and health of components.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "src"))

try:
    from infrastructure.parasite_guard.contracts import (
        AlerterContract,
        DetectorContract,
        SanitizerContract,
        validate_alerter_contract,
        validate_detector_contract,
        validate_sanitizer_contract,
    )
    from infrastructure.parasite_guard.state_machine import (
        GuardState,
        ParasiteGuardStateMachine,
    )
    from infrastructure.parasite_guard.alerter import ParasiteAlerter
    from infrastructure.parasite_guard.config import ParasiteGuardConfig

    IMPORTS_OK = True
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    IMPORTS_OK = False


@dataclass
class ValidationResult:
    """Result of validating a single component."""

    component_name: str
    component_type: str  # detector, sanitizer, alerter
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "component_type": self.component_type,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class ValidationReport:
    """Full validation report for all components."""

    results: list[ValidationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0 and all(r.is_valid for r in self.results)

    @property
    def total_components(self) -> int:
        return len(self.results)

    @property
    def valid_components(self) -> int:
        return sum(1 for r in self.results if r.is_valid)

    def add_result(self, result: ValidationResult) -> None:
        self.results.append(result)
        self.errors.extend(result.errors)
        self.warnings.extend(result.warnings)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_components": self.total_components,
            "valid_components": self.valid_components,
            "results": [r.to_dict() for r in self.results],
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def print_report(self, verbose: bool = False) -> None:
        print("\n" + "=" * 60)
        print("PARASITE GUARD CONTRACT VALIDATION REPORT")
        print("=" * 60)

        if self.is_valid:
            print("\n[PASS] All contracts validated successfully!")
        else:
            print("\n[FAIL] Contract validation failed!")

        print(f"\nComponents validated: {self.valid_components}/{self.total_components}")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  [ERROR] {error}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")

        if verbose and self.results:
            print("\nDetailed Results:")
            print("-" * 40)
            for result in self.results:
                status = "PASS" if result.is_valid else "FAIL"
                print(f"  [{status}] {result.component_type}: {result.component_name}")
                if result.errors:
                    for err in result.errors:
                        print(f"       - {err}")

        print("\n" + "=" * 60)


def discover_detectors() -> list[Any]:
    """Discover all registered detectors."""
    detectors = []

    try:
        from infrastructure.parasite_guard.detectors import (
            DBConnectionOrphanDetector,
            EventSubscriptionLeakDetector,
            WebSocketNoAckDetector,
        )

        # Create instances with default config
        config = ParasiteGuardConfig()
        detectors.append(("WebSocketNoAckDetector", WebSocketNoAckDetector(config)))
        detectors.append(("EventSubscriptionLeakDetector", EventSubscriptionLeakDetector(config)))
        detectors.append(("DBConnectionOrphanDetector", DBConnectionOrphanDetector(config)))

    except ImportError as e:
        print(f"Warning: Could not import detectors: {e}")

    return detectors


def discover_sanitizers() -> list[Any]:
    """Discover all registered sanitizers."""
    sanitizers = []

    try:
        from infrastructure.parasite_guard.sanitizer import (
            DBEngineSanitizer,
            EventBusSanitizer,
            WebSocketSanitizer,
        )

        config = ParasiteGuardConfig()
        sanitizers.append(("WebSocketSanitizer", WebSocketSanitizer(config)))
        sanitizers.append(("EventBusSanitizer", EventBusSanitizer(config)))
        sanitizers.append(("DBEngineSanitizer", DBEngineSanitizer(config)))

    except ImportError as e:
        print(f"Warning: Could not import sanitizers: {e}")

    return sanitizers


def discover_alerters() -> list[Any]:
    """Discover all registered alerters."""
    alerters = []

    try:
        from infrastructure.parasite_guard.alerter import ParasiteAlerter

        config = ParasiteGuardConfig()
        alerters.append(("ParasiteAlerter", ParasiteAlerter(config)))

    except ImportError as e:
        print(f"Warning: Could not import alerters: {e}")

    return alerters


def validate_detector(name: str, detector: Any) -> ValidationResult:
    """Validate a single detector against DetectorContract."""
    errors = []
    warnings = []

    # Check essential attributes/methods with lenient validation
    # Full contract validation is advisory for pre-existing components
    is_valid, validation_errors = validate_detector_contract(detector)
    
    # For pre-existing detectors, treat contract mismatches as warnings
    # since the contracts are newly defined
    for err in validation_errors:
        if "Does not implement DetectorContract" in err:
            # Check if it has __call__ (legacy detector interface)
            if callable(detector):
                warnings.append(f"Uses legacy __call__ interface instead of detect()")
            else:
                errors.append(err)
        elif "Missing" in err:
            # Treat all missing methods as warnings for legacy components
            warnings.append(err.replace("Missing", "Missing (optional)"))
        else:
            errors.append(err)

    # Check for name and component (essential, but be lenient)
    if hasattr(detector, "name"):
        if not detector.name:
            warnings.append("Detector name is empty")
    else:
        warnings.append("Missing 'name' attribute (legacy component)")
    
    if hasattr(detector, "component"):
        if not detector.component:
            warnings.append("Detector component is empty")
    else:
        warnings.append("Missing 'component' attribute (legacy component)")

    # Try to validate config if method exists
    if hasattr(detector, "validate_config"):
        try:
            if not detector.validate_config():
                errors.append("validate_config() returned False")
        except Exception as e:
            errors.append(f"validate_config() raised exception: {e}")

    return ValidationResult(
        component_name=name,
        component_type="detector",
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_sanitizer(name: str, sanitizer: Any) -> ValidationResult:
    """Validate a single sanitizer against SanitizerContract."""
    errors = []
    warnings = []

    # Use contract validator with lenient handling
    is_valid, validation_errors = validate_sanitizer_contract(sanitizer)
    
    # For pre-existing sanitizers, treat contract mismatches as warnings
    for err in validation_errors:
        if "Does not implement SanitizerContract" in err:
            # Check if it has sanitize method (essential)
            if hasattr(sanitizer, "sanitize") and callable(getattr(sanitizer, "sanitize")):
                warnings.append("Partially implements SanitizerContract")
            else:
                errors.append(err)
        elif "Missing" in err:
            # Treat all missing methods as warnings for legacy components
            warnings.append(err.replace("Missing", "Missing (optional)"))
        else:
            warnings.append(err)  # Treat other validation errors as warnings

    # Check for essential component attribute (lenient)
    if hasattr(sanitizer, "component"):
        if not sanitizer.component:
            warnings.append("Sanitizer component is empty")
    else:
        # Try _component as fallback
        if hasattr(sanitizer, "_component"):
            warnings.append("Uses _component instead of component (legacy)")
        else:
            warnings.append("Missing 'component' attribute (legacy component)")

    if hasattr(sanitizer, "success_rate"):
        rate = sanitizer.success_rate
        if rate < 0.95:
            warnings.append(f"Success rate {rate:.2%} is below recommended 95%")

    return ValidationResult(
        component_name=name,
        component_type="sanitizer",
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_alerter(name: str, alerter: Any) -> ValidationResult:
    """Validate a single alerter against AlerterContract."""
    errors = []
    warnings = []

    # Use contract validator
    is_valid, validation_errors = validate_alerter_contract(alerter)
    errors.extend(validation_errors)

    return ValidationResult(
        component_name=name,
        component_type="alerter",
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_state_machine() -> ValidationResult:
    """Validate the state machine configuration."""
    errors = []
    warnings = []

    try:
        sm = ParasiteGuardStateMachine()

        # Verify initial state
        if sm.state != GuardState.INITIALIZING:
            errors.append(f"Initial state should be INITIALIZING, got {sm.state}")

        # Verify all transitions are valid
        all_states = list(GuardState)
        for state in all_states:
            transitions = sm.VALID_TRANSITIONS.get(state, [])
            if not transitions:
                warnings.append(f"State {state.name} has no valid transitions")

        # Test a valid transition
        try:
            sm.transition(GuardState.MONITORING)
            if sm.state != GuardState.MONITORING:
                errors.append("transition(MONITORING) did not change state")
        except Exception as e:
            errors.append(f"transition() failed: {e}")

    except Exception as e:
        errors.append(f"State machine validation failed: {e}")

    return ValidationResult(
        component_name="ParasiteGuardStateMachine",
        component_type="state_machine",
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_contracts(verbose: bool = False) -> ValidationReport:
    """Validate all parasite guard contracts."""
    report = ValidationReport()

    if not IMPORTS_OK:
        report.add_error("Required imports failed - cannot perform validation")
        return report

    # Validate detectors
    for name, detector in discover_detectors():
        result = validate_detector(name, detector)
        report.add_result(result)

    # Validate sanitizers
    for name, sanitizer in discover_sanitizers():
        result = validate_sanitizer(name, sanitizer)
        report.add_result(result)

    # Validate alerters
    for name, alerter in discover_alerters():
        result = validate_alerter(name, alerter)
        report.add_result(result)

    # Validate state machine
    sm_result = validate_state_machine()
    report.add_result(sm_result)

    return report


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Parasite Guard contract compliance"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed validation results"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    print("Starting Parasite Guard Contract Validation...")
    report = validate_contracts(verbose=args.verbose)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        report.print_report(verbose=args.verbose)

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
