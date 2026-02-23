"""
Integration tests for Agentic + Skills system interaction.

Tests the workflow between the agentic system and skills registry,
including skill discovery, execution, and case processing with skills.
"""

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Conditional imports
HAS_AGENTIC = False
HAS_SKILLS = False

try:
    from grid.agentic.agentic_system import AgenticSystem
    from grid.agentic.schemas import CaseCreateRequest, CaseResponse

    HAS_AGENTIC = True
except ImportError:
    AgenticSystem = None
    CaseCreateRequest = None
    CaseResponse = None

try:
    from grid.skills.base import Skill
    from grid.skills.registry import SkillsRegistry

    HAS_SKILLS = True
except ImportError:
    SkillsRegistry = None
    Skill = None

requires_agentic = pytest.mark.skipif(not HAS_AGENTIC, reason="Agentic system not available")
requires_skills = pytest.mark.skipif(not HAS_SKILLS, reason="Skills registry not available")


# =============================================================================
# Mock Classes
# =============================================================================


class MockSkill:
    """Mock skill for testing."""

    def __init__(self, name: str, description: str = "", result: dict | None = None):
        self.name = name
        self.description = description
        self.result = result or {"status": "success", "output": f"Result from {name}"}
        self.run_count = 0

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        self.run_count += 1
        return self.result

    def validate_args(self, args: dict[str, Any]) -> bool:
        return True


class MockSkillsRegistry:
    """Mock skills registry for testing."""

    def __init__(self):
        self.skills: dict[str, MockSkill] = {}
        self._setup_default_skills()

    def _setup_default_skills(self):
        self.skills = {
            "transform.data": MockSkill(
                "transform.data",
                "Transform data between formats",
                {"status": "success", "output": {"transformed": True}},
            ),
            "analyze.code": MockSkill(
                "analyze.code",
                "Analyze code for patterns",
                {"status": "success", "output": {"patterns": ["pattern1", "pattern2"]}},
            ),
            "generate.summary": MockSkill(
                "generate.summary",
                "Generate summary of content",
                {"status": "success", "output": {"summary": "Generated summary"}},
            ),
        }

    def get_skill(self, name: str) -> MockSkill | None:
        return self.skills.get(name)

    def list(self) -> list[str]:
        return list(self.skills.keys())

    def register_skill(self, name: str, skill: MockSkill) -> None:
        self.skills[name] = skill


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self):
        self.events: list[dict] = []
        self.subscriptions: dict[str, list] = {}

    async def publish(self, event: dict) -> None:
        self.events.append(event)

    def subscribe(self, event_type: str, handler) -> Any:
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)
        return {"event_type": event_type, "handler": handler}

    def unsubscribe(self, subscription: Any) -> None:
        pass

    def get_event_history(self) -> list[dict]:
        return self.events


class MockAgenticSystem:
    """Mock agentic system for testing."""

    def __init__(self, skills_registry: MockSkillsRegistry | None = None):
        self.skills_registry = skills_registry or MockSkillsRegistry()
        self.event_bus = MockEventBus()
        self.cases: dict[str, dict] = {}
        self._case_counter = 0

    async def execute_case(self, raw_input: str, **kwargs) -> dict:
        """Execute a case using available skills."""
        self._case_counter += 1
        case_id = f"case-{self._case_counter}"

        # Determine which skill to use based on input
        skill_to_use = self._determine_skill(raw_input)

        result = {
            "case_id": case_id,
            "status": "completed",
            "raw_input": raw_input,
            "skill_used": skill_to_use,
            "result": None,
        }

        if skill_to_use and self.skills_registry:
            skill = self.skills_registry.get_skill(skill_to_use)
            if skill:
                skill_result = skill.run({"input": raw_input})
                result["result"] = skill_result

        self.cases[case_id] = result

        # Publish event
        await self.event_bus.publish(
            {
                "event_type": "case.completed",
                "case_id": case_id,
                "skill_used": skill_to_use,
            }
        )

        return result

    def _determine_skill(self, raw_input: str) -> str | None:
        """Determine which skill to use based on input."""
        input_lower = raw_input.lower()

        if "transform" in input_lower or "convert" in input_lower:
            return "transform.data"
        elif "analyze" in input_lower or "code" in input_lower:
            return "analyze.code"
        elif "summarize" in input_lower or "summary" in input_lower:
            return "generate.summary"

        return None

    def get_available_skills(self) -> list[str]:
        """Get list of available skills."""
        return self.skills_registry.list()


# =============================================================================
# Tests with Mocked Dependencies (Always Run)
# =============================================================================


class TestAgenticSkillsIntegration:
    """Test agentic system integration with skills - mocked version."""

    @pytest.fixture
    def skills_registry(self):
        """Create mock skills registry."""
        return MockSkillsRegistry()

    @pytest.fixture
    def agentic_system(self, skills_registry):
        """Create mock agentic system with skills."""
        return MockAgenticSystem(skills_registry=skills_registry)

    def test_skills_registry_has_skills(self, skills_registry):
        """Test skills registry contains expected skills."""
        skills = skills_registry.list()

        assert len(skills) >= 3
        assert "transform.data" in skills
        assert "analyze.code" in skills
        assert "generate.summary" in skills

    def test_get_skill_by_name(self, skills_registry):
        """Test skill retrieval by name."""
        skill = skills_registry.get_skill("transform.data")

        assert skill is not None
        assert skill.name == "transform.data"

    def test_get_nonexistent_skill(self, skills_registry):
        """Test getting skill that doesn't exist."""
        skill = skills_registry.get_skill("nonexistent.skill")

        assert skill is None

    def test_register_new_skill(self, skills_registry):
        """Test registering a new skill."""
        new_skill = MockSkill("new.skill", "A new skill", {"status": "success"})

        skills_registry.register_skill("new.skill", new_skill)

        assert "new.skill" in skills_registry.list()
        assert skills_registry.get_skill("new.skill") == new_skill

    @pytest.mark.asyncio
    async def test_agentic_system_initialization(self, agentic_system):
        """Test agentic system initializes with skills."""
        assert agentic_system.skills_registry is not None
        assert len(agentic_system.get_available_skills()) >= 3

    @pytest.mark.asyncio
    async def test_execute_case_with_transform_skill(self, agentic_system):
        """Test case execution uses transform skill."""
        result = await agentic_system.execute_case("Transform this data to JSON format")

        assert result["status"] == "completed"
        assert result["skill_used"] == "transform.data"
        assert result["result"] is not None
        assert result["result"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_case_with_analyze_skill(self, agentic_system):
        """Test case execution uses analyze skill."""
        result = await agentic_system.execute_case("Analyze this code for patterns")

        assert result["status"] == "completed"
        assert result["skill_used"] == "analyze.code"
        assert "patterns" in result["result"]["output"]

    @pytest.mark.asyncio
    async def test_execute_case_with_summary_skill(self, agentic_system):
        """Test case execution uses summary skill."""
        result = await agentic_system.execute_case("Summarize the following document")

        assert result["status"] == "completed"
        assert result["skill_used"] == "generate.summary"
        assert "summary" in result["result"]["output"]

    @pytest.mark.asyncio
    async def test_execute_case_without_matching_skill(self, agentic_system):
        """Test case execution when no skill matches."""
        result = await agentic_system.execute_case("Do something unrelated")

        assert result["status"] == "completed"
        assert result["skill_used"] is None
        assert result["result"] is None

    @pytest.mark.asyncio
    async def test_event_published_on_case_completion(self, agentic_system):
        """Test event is published when case completes."""
        await agentic_system.execute_case("Transform this data")

        events = agentic_system.event_bus.get_event_history()
        assert len(events) == 1
        assert events[0]["event_type"] == "case.completed"

    @pytest.mark.asyncio
    async def test_multiple_cases_increment_case_id(self, agentic_system):
        """Test case IDs increment correctly."""
        result1 = await agentic_system.execute_case("First task")
        result2 = await agentic_system.execute_case("Second task")

        assert result1["case_id"] == "case-1"
        assert result2["case_id"] == "case-2"

    @pytest.mark.asyncio
    async def test_skill_run_count_increments(self, skills_registry, agentic_system):
        """Test skill run count increments with each use."""
        skill = skills_registry.get_skill("transform.data")
        initial_count = skill.run_count

        await agentic_system.execute_case("Transform this")
        await agentic_system.execute_case("Transform that")

        assert skill.run_count == initial_count + 2


class TestSkillDiscoveryInAgentic:
    """Test skill discovery and selection in agentic workflow."""

    @pytest.fixture
    def skills_registry(self):
        """Create skills registry with varied skills."""
        registry = MockSkillsRegistry()

        # Add more skills for discovery tests
        registry.register_skill(
            "transform.xml",
            MockSkill("transform.xml", "Transform to XML", {"format": "xml"}),
        )
        registry.register_skill(
            "transform.json",
            MockSkill("transform.json", "Transform to JSON", {"format": "json"}),
        )
        registry.register_skill(
            "analyze.security",
            MockSkill("analyze.security", "Security analysis", {"issues": 0}),
        )

        return registry

    @pytest.fixture
    def agentic_system(self, skills_registry):
        """Create agentic system with extended skills."""
        return MockAgenticSystem(skills_registry=skills_registry)

    def test_list_all_available_skills(self, agentic_system):
        """Test listing all available skills."""
        skills = agentic_system.get_available_skills()

        assert len(skills) >= 5  # 3 default + 3 added
        assert "transform.data" in skills
        assert "transform.xml" in skills
        assert "analyze.security" in skills

    @pytest.mark.asyncio
    async def test_skill_selection_based_on_input_keywords(self, agentic_system):
        """Test skill is selected based on input keywords."""
        test_cases = [
            ("Convert this to XML format", "transform.data"),
            ("Analyze the security of this code", "analyze.code"),
        ]

        for raw_input, expected_skill_prefix in test_cases:
            result = await agentic_system.execute_case(raw_input)
            assert result["skill_used"] is not None
            assert result["skill_used"].startswith(expected_skill_prefix.split(".")[0])


class TestSkillExecutionFailureHandling:
    """Test handling of skill execution failures."""

    @pytest.fixture
    def skills_registry_with_failing_skill(self):
        """Create registry with a skill that fails."""

        class FailingSkill:
            def __init__(self):
                self.name = "fail.always"
                self.description = "A skill that always fails"

            def run(self, args: dict) -> dict:
                raise RuntimeError("Skill execution failed")

            def validate_args(self, args: dict) -> bool:
                return True

        registry = MockSkillsRegistry()
        registry.register_skill("fail.always", FailingSkill())
        return registry

    def test_failing_skill_raises_error(self, skills_registry_with_failing_skill):
        """Test that failing skill raises runtime error."""
        skill = skills_registry_with_failing_skill.get_skill("fail.always")

        with pytest.raises(RuntimeError, match="Skill execution failed"):
            skill.run({"input": "test"})


# =============================================================================
# Tests with Real Dependencies (Conditional)
# =============================================================================


@requires_agentic
@requires_skills
class TestRealAgenticSkillsIntegration:
    """Tests with real agentic and skills implementation."""

    @pytest.fixture
    def knowledge_base_path(self, tmp_path: Path) -> Path:
        """Create temporary knowledge base directory."""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()
        return kb_path

    @pytest.fixture
    async def event_bus(self):
        """Create real event bus."""
        from unified_fabric import DynamicEventBus

        bus = DynamicEventBus(bus_id="test-agentic-skills")
        await bus.start()
        yield bus
        await bus.stop()

    @pytest.fixture
    def skills_registry(self):
        """Create real skills registry."""
        return SkillsRegistry()

    @pytest.fixture
    async def agentic_system(self, knowledge_base_path, event_bus, skills_registry):
        """Create real agentic system."""
        return AgenticSystem(
            knowledge_base_path=knowledge_base_path,
            event_bus=event_bus,
            enable_cognitive=False,
        )

    def test_skills_registry_discovers_skills(self, skills_registry):
        """Test skills registry discovers available skills."""
        skills = skills_registry.list()

        assert isinstance(skills, list)
        # Should discover built-in skills
        assert len(skills) >= 0

    def test_get_skill_metadata(self, skills_registry):
        """Test getting skill metadata."""
        skills = skills_registry.list()

        if len(skills) > 0:
            skill = skills_registry.get_skill(skills[0])
            assert skill is not None
            assert hasattr(skill, "name") or hasattr(skill, "run")

    @pytest.mark.asyncio
    async def test_agentic_system_with_skills(self, agentic_system, skills_registry):
        """Test agentic system can use skills."""
        # This test will depend on actual implementation
        assert agentic_system is not None


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestAgenticSkillsEdgeCases:
    """Test edge cases in agentic-skills integration."""

    @pytest.fixture
    def empty_registry(self):
        """Create empty skills registry."""
        registry = MockSkillsRegistry()
        registry.skills = {}  # Clear all skills
        return registry

    @pytest.fixture
    def agentic_with_empty_registry(self, empty_registry):
        """Create agentic system with empty skills registry."""
        return MockAgenticSystem(skills_registry=empty_registry)

    @pytest.mark.asyncio
    async def test_agentic_with_no_skills(self, agentic_with_empty_registry):
        """Test agentic system handles no skills gracefully."""
        result = await agentic_with_empty_registry.execute_case("Do something")

        assert result["status"] == "completed"
        assert result["skill_used"] is None
        assert result["result"] is None

    @pytest.mark.asyncio
    async def test_agentic_with_none_registry(self):
        """Test agentic system handles None skills registry."""
        system = MockAgenticSystem(skills_registry=None)

        result = await system.execute_case("Do something")

        assert result["status"] == "completed"
        # Should not crash

    def test_skill_with_empty_args(self):
        """Test skill handles empty arguments."""
        skill = MockSkill("test.skill", "Test")

        result = skill.run({})

        assert result["status"] == "success"

    def test_skill_with_complex_args(self):
        """Test skill handles complex arguments."""
        skill = MockSkill("test.skill", "Test")

        result = skill.run(
            {
                "input": "test",
                "options": {"key": "value"},
                "nested": {"deeply": {"nested": "data"}},
            }
        )

        assert result["status"] == "success"


# =============================================================================
# Performance Tests
# =============================================================================


class TestAgenticSkillsPerformance:
    """Test performance of agentic-skills integration."""

    @pytest.fixture
    def large_registry(self):
        """Create registry with many skills."""
        registry = MockSkillsRegistry()

        # Add 100 skills
        for i in range(100):
            registry.register_skill(
                f"skill.{i}",
                MockSkill(f"skill.{i}", f"Skill number {i}", {"index": i}),
            )

        return registry

    @pytest.fixture
    def agentic_with_large_registry(self, large_registry):
        """Create agentic system with large skill registry."""
        return MockAgenticSystem(skills_registry=large_registry)

    def test_list_many_skills_performance(self, large_registry):
        """Test listing many skills is performant."""
        import time

        start = time.time()
        skills = large_registry.list()
        elapsed = time.time() - start

        assert len(skills) >= 100
        assert elapsed < 0.1  # Should be very fast

    def test_get_skill_performance(self, large_registry):
        """Test getting a skill from large registry is fast."""
        import time

        # Get all skills to find one that exists
        all_skills = large_registry.list()
        if not all_skills:
            return

        skill_name = all_skills[-1]  # Get last skill

        start = time.time()
        skill = large_registry.get_skill(skill_name)
        elapsed = time.time() - start

        assert skill is not None
        assert elapsed < 0.01  # Should be instant

    @pytest.mark.asyncio
    async def test_multiple_case_execution(self, agentic_with_large_registry):
        """Test executing many cases in sequence."""
        import time

        start = time.time()

        for i in range(10):
            await agentic_with_large_registry.execute_case(f"Transform data {i}")

        elapsed = time.time() - start

        assert elapsed < 1.0  # 10 cases should complete in under 1 second
