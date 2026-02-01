"""Tests for AI Safety Actions Skill."""

from grid.skills.ai_safety.actions import (
    actions_handler,
    determine_action_type,
    generate_content_hash,
)
from grid.skills.ai_safety.base import ActionType, SafetyCategory, SafetyViolation, ThreatLevel


class TestGenerateContentHash:
    """Test content hash generation."""

    def test_hash_generation(self):
        """Test that hash is generated correctly."""
        content = "Test content"
        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        hash1 = generate_content_hash("Content A")
        hash2 = generate_content_hash("Content B")
        assert hash1 != hash2


class TestDetermineActionType:
    """Test action type determination."""

    def test_critical_severity_triggers_block(self):
        """Test that critical severity triggers BLOCK."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=ThreatLevel.CRITICAL,
            confidence=0.9,
            description="Test",
        )
        action = determine_action_type(violation)
        assert action == ActionType.BLOCK

    def test_high_severity_triggers_escalate(self):
        """Test that high severity triggers ESCALATE."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=ThreatLevel.HIGH,
            confidence=0.8,
            description="Test",
        )
        action = determine_action_type(violation)
        assert action == ActionType.ESCALATE

    def test_medium_severity_triggers_review(self):
        """Test that medium severity triggers REVIEW."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=ThreatLevel.MEDIUM,
            confidence=0.7,
            description="Test",
        )
        action = determine_action_type(violation)
        assert action == ActionType.REVIEW

    def test_low_severity_triggers_log(self):
        """Test that low severity triggers LOG."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=ThreatLevel.LOW,
            confidence=0.6,
            description="Test",
        )
        action = determine_action_type(violation)
        assert action == ActionType.LOG


class TestActionsHandler:
    """Test the actions skill handler."""

    def test_handler_requires_violation(self):
        """Test that handler requires violation."""
        args = {"content": "test content"}
        result = actions_handler(args)
        assert result["success"] is False
        assert "error" in result

    def test_handler_requires_content(self):
        """Test that handler requires content."""
        args = {"violation": {"category": "harmful_content"}}
        result = actions_handler(args)
        assert result["success"] is False
        assert "error" in result

    def test_handler_executes_block_action(self):
        """Test BLOCK action execution."""
        args = {
            "violation": {
                "category": "harmful_content",
                "severity": "critical",
                "confidence": 0.9,
                "description": "Test violation",
            },
            "content": "harmful content here",
            "action_type": "block",
        }
        result = actions_handler(args)
        assert result["success"] is True
        assert result["action"] == "block"

    def test_handler_executes_log_action(self):
        """Test LOG action execution."""
        args = {
            "violation": {
                "category": "harmful_content",
                "severity": "low",
                "confidence": 0.6,
                "description": "Minor violation",
            },
            "content": "content here",
            "action_type": "log",
        }
        result = actions_handler(args)
        assert result["success"] is True
        assert result["action"] == "log"

    def test_handler_auto_determines_action(self):
        """Test automatic action determination."""
        args = {
            "violation": {
                "category": "harmful_content",
                "severity": "high",
                "confidence": 0.8,
                "description": "Serious violation",
            },
            "content": "content here",
            # No action_type - should auto-determine
        }
        result = actions_handler(args)
        assert result["success"] is True
        # Should escalate for high severity
        assert result["action"] == "escalate"

    def test_handler_returns_action_details(self):
        """Test that handler returns action details."""
        args = {
            "violation": {
                "category": "privacy_violation",
                "severity": "medium",
                "confidence": 0.7,
                "description": "Privacy issue",
            },
            "content": "content with privacy issue",
            "action_type": "review",
        }
        result = actions_handler(args)
        assert result["success"] is True
        assert "details" in result
        assert "timestamp" in result
