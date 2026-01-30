from typing import Any, Protocol

import pytest


class Skill(Protocol):
    id: str
    name: str
    description: str
    version: str
    handler: Any


@pytest.fixture(scope="module")
def skill_test_validator():
    """Validator fixture for Skill structure and metadata."""

    def validate(skill_obj: Any) -> None:
        # Compliance check
        required_attrs = ["id", "name", "description", "handler"]
        for attr in required_attrs:
            assert hasattr(skill_obj, attr), f"Skill missing required attribute: {attr}"

        assert skill_obj.id, "Skill ID cannot be empty"
        assert skill_obj.name, "Skill name cannot be empty"
        assert callable(skill_obj.handler), "Skill handler must be callable"

        # Version check if present
        if hasattr(skill_obj, "version"):
            assert isinstance(skill_obj.version, str), "Version must be a string"

    return validate
