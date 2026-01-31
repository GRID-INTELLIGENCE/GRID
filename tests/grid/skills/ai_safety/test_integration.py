"""Integration tests for AI Safety Skills."""

import pytest

from grid.skills.ai_safety.base import ThreatLevel
from grid.skills.ai_safety.actions import actions_handler
from grid.skills.ai_safety.monitor import monitor_handler
from grid.skills.ai_safety.rules import rules_handler
from grid.skills.ai_safety.thresholds import thresholds_handler


class TestSafetyPipeline:
    """Test complete safety pipeline."""

    def test_content_moderation_pipeline(self):
        """Test full content moderation pipeline."""
        # Step 1: Check rules
        rules_result = rules_handler({"content": "This contains hate speech"})
        assert rules_result["success"] is True

        # Step 2: If violations, take action
        if rules_result["violation_count"] > 0:
            action_result = actions_handler({
                "violation": rules_result["violations"][0],
                "content": "This contains hate speech",
            })
            assert action_result["success"] is True

    def test_monitoring_with_violation_response(self):
        """Test monitoring and responding to violations."""
        # Create monitoring session
        create_result = monitor_handler({
            "operation": "create",
            "stream_id": "test_stream",
        })
        assert create_result["success"] is True
        session_id = create_result["session_id"]

        # Check harmful content
        check_result = monitor_handler({
            "operation": "check",
            "session_id": session_id,
            "content": "Violence and weapons",
        })
        assert check_result["success"] is True

        # Get stats
        stats_result = monitor_handler({
            "operation": "stats",
            "session_id": session_id,
        })
        assert stats_result["success"] is True

    def test_threshold_based_monitoring(self):
        """Test threshold-based safety monitoring."""
        # Set up metrics with baseline
        thresholds_result = thresholds_handler({
            "metrics": {"error_rate": 50.0},
            "baseline": {"error_rate": 5.0},
            "sensitivity": "high",
        })
        assert thresholds_result["success"] is True

        # If threshold violation detected, log it
        if thresholds_result["violation_count"] > 0:
            assert len(thresholds_result["violations"]) > 0


class TestMultiProviderSafety:
    """Test multi-provider safety checking."""

    def test_all_providers_check_content(self):
        """Test that all providers can check content."""
        from grid.skills.ai_safety.providers import PROVIDER_SKILLS

        content = "Test content for safety"
        results = {}

        for name, skill in PROVIDER_SKILLS.items():
            result = skill.run({"content": content})
            results[name] = result
            assert result["success"] is True

        # All providers should return results
        assert len(results) == len(PROVIDER_SKILLS)

    def test_provider_consistency(self):
        """Test that providers return consistent result structure."""
        from grid.skills.ai_safety.providers import PROVIDER_SKILLS

        content = "Harmful content test"

        for name, skill in PROVIDER_SKILLS.items():
            result = skill.run({"content": content})
            # All should have these fields
            assert "success" in result
            assert "violations" in result
            assert "provider" in result
            assert isinstance(result["violations"], list)


class TestSafetyReportGeneration:
    """Test safety report generation."""

    def test_comprehensive_safety_report(self):
        """Test generating comprehensive safety report."""
        from grid.skills.ai_safety.base import SafetyReport

        # Run rules check
        rules_result = rules_handler({"content": "Test content with email@example.com"})

        # Generate report from results
        violations = rules_result.get("violations", [])
        threat_level = ThreatLevel.LOW if not violations else ThreatLevel.MEDIUM

        report = SafetyReport(
            overall_score=0.7 if violations else 1.0,
            threat_level=threat_level,
            violations=[
                type('obj', (object,), v)() if isinstance(v, dict) else v
                for v in violations
            ],
        )

        assert report.threat_level == threat_level
        assert 0.0 <= report.overall_score <= 1.0
