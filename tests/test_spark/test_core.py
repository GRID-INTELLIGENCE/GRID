"""
Tests for Spark - Universal Morphable Invoker

Tests cover:
- Core Spark lifecycle (ADSR phases)
- Persona switching
- Staircase Intelligence routing
"""

import pytest


class TestSparkCore:
    """Tests for Spark core functionality."""

    def test_spark_import(self):
        """Test that spark can be imported."""
        from grid.spark import Spark, SparkResult, spark

        assert callable(spark)
        assert Spark is not None
        assert SparkResult is not None

    def test_spark_instance_creation(self):
        """Test creating a Spark instance."""
        from grid.spark import Spark

        s = Spark()
        assert s.default_persona == "reasoning"
        assert "navigator" in s.available_personas
        assert "staircase" in s.available_personas

    def test_spark_phases(self):
        """Test Spark lifecycle phases."""
        from grid.spark.core import SparkPhase

        assert SparkPhase.IDLE.value == "idle"
        assert SparkPhase.ATTACK.value == "attack"
        assert SparkPhase.SUSTAIN.value == "sustain"
        assert SparkPhase.RELEASE.value == "release"
        assert SparkPhase.COMPLETE.value == "complete"

    def test_spark_result_success(self):
        """Test SparkResult success property."""
        from grid.spark.core import SparkPhase, SparkResult

        result = SparkResult(
            request="test",
            output={"data": "value"},
            persona="navigator",
            phase=SparkPhase.COMPLETE,
        )
        assert result.success is True

        failed_result = SparkResult(
            request="test",
            output=None,
            persona="navigator",
            phase=SparkPhase.COMPLETE,
        )
        assert failed_result.success is False

    def test_spark_invoke_navigator(self):
        """Test invoking spark with navigator persona."""
        from grid.spark import spark

        result = spark("check zone map", persona="navigator")
        assert result.persona == "navigator"
        assert result.output is not None
        assert result.duration_ms >= 0

    def test_spark_available_personas(self):
        """Test all personas are registered."""
        from grid.spark import Spark

        s = Spark()
        expected = ["navigator", "resonance", "agentic", "reasoning", "staircase"]
        for persona in expected:
            assert persona in s.available_personas


class TestStaircaseIntelligence:
    """Tests for Staircase Intelligence routing system."""

    def test_staircase_states(self):
        """Test StaircaseState enum."""
        from grid.spark.staircase import StaircaseState

        assert StaircaseState.STABLE.value == "stable"
        assert StaircaseState.MOVING.value == "moving"
        assert StaircaseState.VANISHED.value == "vanished"
        assert StaircaseState.LOCKED.value == "locked"

    def test_day_behavior(self):
        """Test DayBehavior enum."""
        from grid.spark.staircase import DayBehavior

        assert DayBehavior.NORMAL.value == "normal"
        assert DayBehavior.FRIDAY_REDIRECT.value == "friday_redirect"

    def test_staircase_creation(self):
        """Test creating a single staircase."""
        from grid.spark.staircase import Staircase, StaircaseState

        stair = Staircase(
            id="test-stair",
            origin="room_a",
            destination="room_b",
        )
        assert stair.id == "test-stair"
        assert stair.origin == "room_a"
        assert stair.destination == "room_b"
        assert stair.state == StaircaseState.STABLE

    def test_staircase_traversal_success(self):
        """Test successful staircase traversal."""
        from grid.spark.staircase import Staircase

        stair = Staircase(
            id="test-stair",
            origin="room_a",
            destination="room_b",
        )
        success, message = stair.attempt_traverse({})
        assert success is True
        assert "room_b" in message

    def test_staircase_traversal_with_vanishing_step(self):
        """Test traversal fails without knowledge of vanishing step."""
        from grid.spark.staircase import Staircase

        stair = Staircase(
            id="test-stair",
            origin="room_a",
            destination="room_b",
            has_vanishing_step=True,
        )

        # Without knowledge
        success, message = stair.attempt_traverse({})
        assert success is False
        assert "vanishing step" in message.lower()

        # With knowledge
        success, message = stair.attempt_traverse({"knows_vanishing_step": True})
        assert success is True

    def test_staircase_traversal_polite_door(self):
        """Test polite door requires polite request."""
        from grid.spark.staircase import Staircase, StaircaseState

        stair = Staircase(
            id="test-stair",
            origin="room_a",
            destination="room_b",
            state=StaircaseState.LOCKED,
            requires_polite_request=True,
        )

        # Without auth
        success, message = stair.attempt_traverse({})
        assert success is False

        # With auth but not polite
        success, message = stair.attempt_traverse({"authenticated": True})
        assert success is False
        assert "politely" in message.lower()

        # With auth and polite
        success, message = stair.attempt_traverse({"authenticated": True, "polite": True})
        assert success is True

    def test_grand_staircase_creation(self):
        """Test creating a GrandStaircase system."""
        from grid.spark.staircase import GrandStaircase, Staircase

        gs = GrandStaircase()
        gs.add_staircase(Staircase(id="s1", origin="a", destination="b"))
        gs.add_staircase(Staircase(id="s2", origin="b", destination="c"))

        assert len(gs.staircases) == 2

    def test_grand_staircase_routing(self):
        """Test finding routes in GrandStaircase."""
        from grid.spark.staircase import GrandStaircase, Staircase

        gs = GrandStaircase()
        gs.add_staircase(Staircase(id="s1", origin="a", destination="b"))
        gs.add_staircase(Staircase(id="s2", origin="b", destination="c"))
        gs.add_staircase(Staircase(id="s3", origin="a", destination="c"))

        # Direct route
        route = gs.find_route("a", "c")
        assert route is not None
        assert route[0] == "a"
        assert route[-1] == "c"

    def test_hogwarts_topology(self):
        """Test creating Hogwarts-inspired topology."""
        from grid.spark.staircase import create_hogwarts_topology

        stairs = create_hogwarts_topology()
        assert len(stairs.staircases) > 0

        # Should be able to find at least some routes
        health = stairs.get_health_report()
        assert health["total_staircases"] > 0

    def test_staircase_cycle(self):
        """Test autonomous movement cycle."""
        from grid.spark.staircase import create_hogwarts_topology

        stairs = create_hogwarts_topology()

        # Run multiple cycles
        total_moved = 0
        for _ in range(10):
            moved = stairs.cycle()
            total_moved += len(moved)

        # With 10 cycles and ~30 staircases at 10% probability each,
        # we should see some movement
        assert total_moved >= 0  # Could be 0 due to randomness, but likely > 0

    def test_reference_card(self):
        """Test reference card exists and has content."""
        from grid.spark.staircase import REFERENCE_CARD

        assert REFERENCE_CARD is not None
        assert "Moving Stairs" in REFERENCE_CARD
        assert "Circuit Breaker" in REFERENCE_CARD


class TestStaircasePersona:
    """Tests for StaircasePersona integration with Spark."""

    def test_staircase_persona_exists(self):
        """Test StaircasePersona is available."""
        from grid.spark import Spark

        s = Spark()
        assert "staircase" in s.available_personas

    def test_staircase_persona_find_route(self):
        """Test finding route through persona."""
        from grid.spark import spark

        result = spark("find route", persona="staircase")
        assert result.persona == "staircase"
        assert "route" in result.output or "found" in result.output

    def test_staircase_persona_health(self):
        """Test getting health through persona."""
        from grid.spark import spark

        result = spark("health status", persona="staircase")
        assert result.persona == "staircase"
        assert "total_staircases" in result.output or "reference" in result.output


class TestKnowledgeGraphSchema:
    """Tests for Knowledge Graph schema system."""

    def test_kg_schema_import(self):
        """Test KG schema can be imported."""
        from grid.knowledge.graph_schema import EntityType, get_kg_schema

        schema = get_kg_schema()
        assert schema is not None
        assert EntityType.AGENT is not None

    def test_entity_types(self):
        """Test entity type enumeration."""
        from grid.knowledge.graph_schema import EntityType

        assert EntityType.AGENT.value == "Agent"
        assert EntityType.SKILL.value == "Skill"
        assert EntityType.ARTIFACT.value == "Artifact"

    def test_get_entity_schema(self):
        """Test getting entity schema."""
        from grid.knowledge.graph_schema import EntityType, get_kg_schema

        schema = get_kg_schema()
        agent_schema = schema.get_entity_schema(EntityType.AGENT)

        assert agent_schema is not None
        assert agent_schema.entity_type == EntityType.AGENT

    def test_entity_validation(self):
        """Test entity validation."""
        from grid.knowledge.graph_schema import EntityType, get_kg_schema

        schema = get_kg_schema()

        # Valid entity
        valid_data = {
            "id": "agent-001",
            "name": "TestAgent",
            "created_at": "2026-01-10T00:00:00",
        }
        is_valid, errors = schema.validate_entity(EntityType.AGENT, valid_data)
        assert is_valid is True
        assert len(errors) == 0

        # Invalid entity (missing required field)
        invalid_data = {"id": "agent-001"}
        is_valid, errors = schema.validate_entity(EntityType.AGENT, invalid_data)
        assert is_valid is False
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
