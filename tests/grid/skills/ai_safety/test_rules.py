"""Tests for AI Safety Rules Skill."""

from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel
from grid.skills.ai_safety.rules import evaluate_rules, load_rules, rules_handler


class TestLoadRules:
    """Test rule loading functionality."""

    def test_load_default_rules(self):
        """Test loading default rules when no file specified."""
        rules = load_rules()
        assert len(rules) > 0
        assert all("id" in rule for rule in rules)

    def test_load_rules_from_nonexistent_file(self):
        """Test fallback to defaults when file doesn't exist."""
        rules = load_rules("/nonexistent/path/rules.json")
        assert len(rules) > 0  # Should return defaults


class TestEvaluateRules:
    """Test rule evaluation functionality."""

    def test_no_violations_for_safe_content(self):
        """Test that safe content produces no violations."""
        content = "This is a perfectly safe message about puppies and sunshine."
        rules = load_rules()
        violations = evaluate_rules(content, rules)
        assert len(violations) == 0

    def test_detects_harmful_content(self):
        """Test detection of harmful content patterns."""
        content = "This message contains violence and weapon references."
        rules = load_rules()
        violations = evaluate_rules(content, rules)
        assert len(violations) > 0
        assert violations[0].category == SafetyCategory.HARMFUL_CONTENT

    def test_detects_privacy_violation_email(self):
        """Test detection of email addresses."""
        content = "Contact me at user@example.com for more info."
        rules = load_rules()
        violations = evaluate_rules(content, rules)
        email_violations = [v for v in violations if v.category == SafetyCategory.PRIVACY_VIOLATION]
        assert len(email_violations) > 0

    def test_detects_mental_health_risk(self):
        """Test detection of mental health risk indicators."""
        content = "I feel like I want to die and end my life."
        rules = load_rules()
        violations = evaluate_rules(content, rules)
        mental_health_violations = [v for v in violations if v.category == SafetyCategory.MENTAL_HEALTH_RISK]
        assert len(mental_health_violations) > 0
        assert mental_health_violations[0].severity == ThreatLevel.HIGH

    def test_rule_confidence_scores(self):
        """Test that violations have appropriate confidence scores."""
        content = "This contains hate and harassment."
        rules = load_rules()
        violations = evaluate_rules(content, rules)
        for violation in violations:
            assert 0.0 <= violation.confidence <= 1.0


class TestRulesHandler:
    """Test the rules skill handler."""

    def test_handler_with_safe_content(self):
        """Test handler with safe content."""
        args = {"content": "Safe content here."}
        result = rules_handler(args)
        assert result["success"] is True
        assert result["violation_count"] == 0

    def test_handler_with_violations(self):
        """Test handler with violating content."""
        args = {"content": "This contains violence and hate."}
        result = rules_handler(args)
        assert result["success"] is True
        assert result["violation_count"] > 0
        assert len(result["violations"]) > 0

    def test_handler_with_no_content(self):
        """Test handler with no content."""
        args = {"content": ""}
        result = rules_handler(args)
        assert result["success"] is True
        assert result["violation_count"] == 0

    def test_handler_preserves_violation_structure(self):
        """Test that violations have correct structure."""
        args = {"content": "Contact: test@example.com"}
        result = rules_handler(args)
        if result["violation_count"] > 0:
            violation = result["violations"][0]
            assert "category" in violation
            assert "severity" in violation
            assert "confidence" in violation
            assert "description" in violation
            assert "provider" in violation
