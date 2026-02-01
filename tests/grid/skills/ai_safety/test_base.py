"""Tests for AI Safety Base Module."""


from grid.skills.ai_safety.base import (
    ActionResult,
    ActionType,
    SafetyCategory,
    SafetyReport,
    SafetyViolation,
    ThreatLevel,
    calculate_safety_score,
    determine_threat_level,
)


def test_safety_violation_creation():
    violation = SafetyViolation(
        category=SafetyCategory.HARMFUL_CONTENT,
        severity=ThreatLevel.HIGH,
        confidence=0.8,
        description="Test violation",
    )
    assert violation.category == SafetyCategory.HARMFUL_CONTENT
    assert violation.severity == ThreatLevel.HIGH


def test_safety_report_safe():
    report = SafetyReport(overall_score=0.9, threat_level=ThreatLevel.LOW, violations=[])
    assert report.is_safe is True
    assert report.should_block is False


def test_safety_report_critical():
    violation = SafetyViolation(
        category=SafetyCategory.HARMFUL_CONTENT,
        severity=ThreatLevel.CRITICAL,
        confidence=0.9,
        description="Critical",
    )
    report = SafetyReport(overall_score=0.1, threat_level=ThreatLevel.CRITICAL, violations=[violation])
    assert report.is_safe is False
    assert report.should_block is True


def test_calculate_safety_score_no_violations():
    score = calculate_safety_score([])
    assert score == 1.0


def test_calculate_safety_score_with_violations():
    violations = [
        SafetyViolation(category=SafetyCategory.HARMFUL_CONTENT, severity=ThreatLevel.MEDIUM, confidence=0.5, description="Test"),
    ]
    score = calculate_safety_score(violations)
    assert score < 1.0


def test_determine_threat_level_critical():
    violations = [
        SafetyViolation(category=SafetyCategory.HARMFUL_CONTENT, severity=ThreatLevel.CRITICAL, confidence=0.9, description="Critical"),
    ]
    level = determine_threat_level(0.5, violations)
    assert level == ThreatLevel.CRITICAL


def test_action_result_to_dict():
    result = ActionResult(action=ActionType.BLOCK, success=True, message="Blocked")
    data = result.to_dict()
    assert data["action"] == "block"
    assert data["success"] is True
