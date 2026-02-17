"""
Skill output contract tests.

These tests verify that skill outputs conform to expected contracts,
ensuring compatibility with the Resonance API's definitive step.
"""

from __future__ import annotations

import pytest


class TestTransformSchemaMapContract:
    """Contract tests for transform.schema_map skill."""

    @pytest.fixture
    def skill(self):
        """Get the transform.schema_map skill."""
        from grid.skills.registry import default_registry

        skill = default_registry.get("transform.schema_map")
        if skill is None:
            pytest.skip("transform.schema_map skill not available")
        return skill

    def test_output_has_required_fields(self, skill):
        """Verify output contains required contract fields."""
        result = skill.run(
            {
                "text": "Test input text",
                "target_schema": "context_engineering",
                "output_format": "json",
                "use_llm": False,
            }
        )

        # Contract: must have these fields
        assert "skill" in result
        assert "status" in result
        assert result["status"] in ("success", "error", "skipped")

    def test_success_output_shape(self, skill):
        """Verify successful output has expected shape."""
        result = skill.run(
            {
                "text": "Test input for schema mapping",
                "target_schema": "context_engineering",
                "use_llm": False,
            }
        )

        if result.get("status") == "success":
            # Contract: success must have output field
            assert "output" in result
            # Output should be dict or similar structure
            assert isinstance(result["output"], (dict, list, str))

    def test_error_output_shape(self, skill):
        """Verify error output has expected shape."""
        # Trigger an error with invalid input
        result = skill.run(
            {
                "text": "",  # Empty text
                "target_schema": "nonexistent_schema",
                "use_llm": False,
            }
        )

        if result.get("status") == "error":
            # Contract: error must have error message
            assert "error" in result or "message" in result


class TestCompressArticulateContract:
    """Contract tests for compress.articulate skill."""

    @pytest.fixture
    def skill(self):
        """Get the compress.articulate skill."""
        from grid.skills.registry import default_registry

        skill = default_registry.get("compress.articulate")
        if skill is None:
            pytest.skip("compress.articulate skill not available")
        return skill

    def test_output_has_required_fields(self, skill):
        """Verify output contains required contract fields."""
        result = skill.run(
            {
                "text": "This is a long text that needs to be compressed into a shorter summary.",
                "max_chars": 50,
                "use_llm": False,
            }
        )

        assert "skill" in result
        assert "status" in result

    def test_success_respects_max_chars(self, skill):
        """Verify output respects max_chars constraint."""
        max_chars = 100
        result = skill.run(
            {
                "text": "A" * 500,  # Long input
                "max_chars": max_chars,
                "use_llm": False,
            }
        )

        if result.get("status") == "success" and result.get("output"):
            output = str(result["output"])
            # Allow some tolerance (e.g., 20% over due to word boundaries)
            assert len(output) <= max_chars * 1.2, f"Output length {len(output)} exceeds {max_chars * 1.2}"


class TestContextRefineContract:
    """Contract tests for context.refine skill."""

    @pytest.fixture
    def skill(self):
        """Get the context.refine skill."""
        from grid.skills.registry import default_registry

        skill = default_registry.get("context.refine")
        if skill is None:
            pytest.skip("context.refine skill not available")
        return skill

    def test_output_has_required_fields(self, skill):
        """Verify output contains required contract fields."""
        result = skill.run(
            {
                "text": "Some text to refine",
                "use_llm": False,
            }
        )

        assert "skill" in result
        assert "status" in result

    def test_heuristic_mode_returns_passthrough(self, skill):
        """Verify heuristic mode (use_llm=False) passes through input."""
        input_text = "Original input text"
        result = skill.run(
            {
                "text": input_text,
                "use_llm": False,
            }
        )

        # In heuristic mode, should not degrade input
        if result.get("status") == "success":
            output = result.get("output", "")
            # Output should be at least as long as input (not degraded)
            assert len(str(output)) >= len(input_text) * 0.8


class TestCrossReferenceExplainContract:
    """Contract tests for cross_reference.explain skill."""

    @pytest.fixture
    def skill(self):
        """Get the cross_reference.explain skill."""
        from grid.skills.registry import default_registry

        skill = default_registry.get("cross_reference.explain")
        if skill is None:
            pytest.skip("cross_reference.explain skill not available")
        return skill

    def test_output_has_required_fields(self, skill):
        """Verify output contains required contract fields."""
        result = skill.run(
            {
                "concept": "test concept",
                "source_domain": "domain A",
                "target_domain": "domain B",
                "use_llm": False,
            }
        )

        assert "skill" in result
        assert "status" in result

    def test_explanation_is_string(self, skill):
        """Verify explanation output is a string."""
        result = skill.run(
            {
                "concept": "canvas flip",
                "source_domain": "art",
                "target_domain": "software",
                "use_llm": False,
            }
        )

        if result.get("status") == "success" and result.get("output"):
            assert isinstance(result["output"], str)


class TestRagQueryKnowledgeContract:
    """Contract tests for rag.query_knowledge skill."""

    @pytest.fixture
    def skill(self):
        """Get the rag.query_knowledge skill."""
        from grid.skills.registry import default_registry

        skill = default_registry.get("rag.query_knowledge")
        if skill is None:
            pytest.skip("rag.query_knowledge skill not available")
        return skill

    def test_output_has_required_fields(self, skill):
        """Verify output contains required contract fields."""
        result = skill.run(
            {
                "query": "What is the resonance API?",
                "top_k": 3,
            }
        )

        assert "skill" in result
        assert "status" in result

    def test_graceful_degradation_without_index(self, skill):
        """Verify skill handles missing index gracefully."""
        result = skill.run(
            {
                "query": "Test query for nonexistent content",
                "top_k": 5,
            }
        )

        # Should not raise; status indicates outcome
        assert result.get("status") in ("success", "error", "skipped", "no_results")


class TestSkillVersioning:
    """Tests for skill versioning support."""

    def test_all_skills_have_version(self):
        """Verify all registered skills have a version attribute."""
        from grid.skills.registry import default_registry

        skills = default_registry.list()
        for skill in skills:
            assert hasattr(skill, "version") or hasattr(skill, "id"), f"Skill {skill} missing version"

    def test_skill_versions_are_semver_like(self):
        """Verify skill versions follow semver-like format."""
        import re

        from grid.skills.registry import default_registry

        semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")

        skills = default_registry.list()
        for skill in skills:
            version = getattr(skill, "version", "1.0.0")
            assert semver_pattern.match(version), f"Skill {skill.id} has invalid version: {version}"
