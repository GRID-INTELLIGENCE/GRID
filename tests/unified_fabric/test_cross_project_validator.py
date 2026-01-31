"""
Tests for Unified Fabric - Cross Project Validator
"""
from unified_fabric.cross_project_validator import (
    CrossProjectPolicyValidator,
    get_policy_validator,
)

def test_policy_validator_init():
    validator = CrossProjectPolicyValidator(
        allowed_projects=["p1"],
        allowed_domains=["d1"]
    )
    assert "p1" in validator.allowed_projects
    assert "d1" in validator.allowed_domains

def test_validate_context_allowed():
    validator = get_policy_validator() # Uses default grid, coinbase, etc.
    result = validator.validate_context({"project": "grid", "domain": "safety"})
    assert result.allowed is True

def test_validate_context_not_allowed_project():
    validator = get_policy_validator()
    result = validator.validate_context({"project": "malicious_project"})
    assert result.allowed is False
    assert "not permitted" in result.reason
    assert result.severity == "high"

def test_validate_context_not_allowed_domain():
    validator = get_policy_validator()
    result = validator.validate_context({"domain": "unauthorized_domain"})
    assert result.allowed is False
    assert "not permitted" in result.reason
    assert result.severity == "medium"

def test_validate_payload():
    validator = get_policy_validator()
    payload = {"context": {"project": "grid"}}
    result = validator.validate_payload(payload)
    assert result.allowed is True
    
    bad_payload = {"context": {"project": "bad_one"}}
    result = validator.validate_payload(bad_payload)
    assert result.allowed is False
