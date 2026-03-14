"""Unit tests for infrastructure.config.validation module."""

from __future__ import annotations

import pytest

from infrastructure.config.validation import (
    EnvironmentAwareValidator,
    ValidationBuilder,
    ValidationIssue,
    ValidationMode,
    ValidationSeverity,
    validate_production_ready,
)


class TestValidationEnums:
    """Tests for validation enums."""

    def test_validation_mode_values(self):
        """Test ValidationMode enum values."""
        assert ValidationMode.WARN_ONLY.value == "warn"
        assert ValidationMode.FAIL_FAST.value == "fail"
        assert ValidationMode.SILENT.value == "silent"

    def test_validation_severity_values(self):
        """Test ValidationSeverity enum values."""
        assert ValidationSeverity.INFO.value == "info"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.CRITICAL.value == "critical"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_creation(self):
        """Test ValidationIssue creation."""
        issue = ValidationIssue(
            message="Test issue",
            severity=ValidationSeverity.WARNING,
        )
        assert issue.message == "Test issue"
        assert issue.severity == ValidationSeverity.WARNING

    def test_repr(self):
        """Test string representation."""
        issue = ValidationIssue(message="Test", severity=ValidationSeverity.WARNING)
        assert "Test" in repr(issue)


class TestEnvironmentAwareValidator:
    """Tests for EnvironmentAwareValidator class."""

    def test_development_mode_warns(self):
        """Test development mode issues are warnings."""
        validator = EnvironmentAwareValidator("development")
        assert validator.mode == ValidationMode.WARN_ONLY

    def test_production_mode_fails_fast(self):
        """Test production mode determination."""
        validator = EnvironmentAwareValidator("production")
        assert validator.mode == ValidationMode.FAIL_FAST

    def test_test_mode_silent(self):
        """Test test mode is silent."""
        validator = EnvironmentAwareValidator("test")
        assert validator.mode == ValidationMode.SILENT

    def test_determine_mode_development(self):
        """Test mode determination for development."""
        validator = EnvironmentAwareValidator("development")
        assert validator.mode == ValidationMode.WARN_ONLY

    def test_determine_mode_production(self):
        """Test mode determination for production."""
        validator = EnvironmentAwareValidator("production")
        assert validator.mode == ValidationMode.FAIL_FAST

    def test_determine_mode_test(self):
        """Test mode determination for test."""
        validator = EnvironmentAwareValidator("test")
        assert validator.mode == ValidationMode.SILENT


class TestValidationBuilder:
    """Tests for ValidationBuilder class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        class MockSettings:
            environment = "development"
            secret_key = "test-secret-key"
            
            def validate(self):
                return []
        return MockSettings()

    def test_basic_validation(self, mock_settings):
        """Test basic validation chain."""
        builder = ValidationBuilder(mock_settings)
        result = builder.build()
        assert isinstance(result, list)

    def test_validation_with_issues(self, mock_settings):
        """Test validation that produces issues."""
        builder = ValidationBuilder(mock_settings)
        builder.require("secret_key", min_length=10)
        result = builder.build()
        assert len(result) == 0  # secret_key is long enough

    def test_require_missing_field(self, mock_settings):
        """Test validation when required field is missing."""
        builder = ValidationBuilder(mock_settings)
        builder.require("nonexistent_field")
        result = builder.build()
        assert len(result) == 1
        assert "nonexistent_field" in result[0].message


class TestValidateProductionReady:
    """Tests for validate_production_ready function."""

    def test_function_importable(self):
        """Test function can be imported."""
        # Just verify the function exists
        assert validate_production_ready is not None


class TestValidationIntegration:
    """Integration tests for validation system."""

    def test_imports_work(self):
        """Test all validation imports work together."""
        from infrastructure.config.validation import (
            EnvironmentAwareValidator,
            ValidationBuilder,
            ValidationIssue,
            ValidationMode,
            ValidationSeverity,
        )
        # Just verify all can be imported together
        assert EnvironmentAwareValidator is not None
        assert ValidationBuilder is not None
        assert ValidationIssue is not None
