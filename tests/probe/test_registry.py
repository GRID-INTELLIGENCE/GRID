"""Tests for grid.probe.registry — EntityRegistry."""

from __future__ import annotations

import pytest

from grid.probe.models import (
    DiscoveryMethod,
    Domain,
    Entity,
    EntityType,
)
from grid.probe.registry import EntityRegistry


def _make_entity(
    eid: str,
    etype: EntityType = EntityType.MIDDLEWARE,
    domain: Domain = Domain.REQUEST_PIPELINE,
    **kwargs: object,
) -> Entity:
    return Entity(
        id=eid,
        label=f"Entity-{eid}",
        type=etype,
        domain=domain,
        source="src/test.py",
        **kwargs,  # type: ignore[arg-type]
    )


class TestEntityRegistry:
    def test_register_new(self) -> None:
        reg = EntityRegistry()
        entity = _make_entity("ent-001")
        assert reg.register(entity) is True
        assert reg.count == 1

    def test_register_duplicate(self) -> None:
        reg = EntityRegistry()
        entity = _make_entity("ent-001")
        reg.register(entity)
        assert reg.register(entity) is False
        assert reg.count == 1

    def test_register_many(self) -> None:
        reg = EntityRegistry()
        entities = [_make_entity(f"ent-{i:03d}") for i in range(5)]
        assert reg.register_many(entities) == 5
        assert reg.count == 5

    def test_register_many_with_duplicates(self) -> None:
        reg = EntityRegistry()
        e1 = _make_entity("ent-001")
        e2 = _make_entity("ent-002")
        reg.register(e1)
        assert reg.register_many([e1, e2]) == 1
        assert reg.count == 2

    def test_get_by_id(self) -> None:
        reg = EntityRegistry()
        entity = _make_entity("ent-001")
        reg.register(entity)
        assert reg.get("ent-001") is entity
        assert reg.get("nonexistent") is None

    def test_get_by_domain(self) -> None:
        reg = EntityRegistry()
        e1 = _make_entity("ent-001", domain=Domain.GOVERNANCE)
        e2 = _make_entity("ent-002", domain=Domain.SECURITY)
        e3 = _make_entity("ent-003", domain=Domain.GOVERNANCE)
        reg.register_many([e1, e2, e3])

        gov = reg.get_by_domain(Domain.GOVERNANCE)
        assert len(gov) == 2
        assert all(e.domain == Domain.GOVERNANCE for e in gov)

        sec = reg.get_by_domain(Domain.SECURITY)
        assert len(sec) == 1

        empty = reg.get_by_domain(Domain.THROTTLING)
        assert empty == []

    def test_get_by_type(self) -> None:
        reg = EntityRegistry()
        e1 = _make_entity("ent-001", etype=EntityType.MIDDLEWARE)
        e2 = _make_entity("ent-002", etype=EntityType.GATE)
        e3 = _make_entity("ent-003", etype=EntityType.MIDDLEWARE)
        reg.register_many([e1, e2, e3])

        mw = reg.get_by_type(EntityType.MIDDLEWARE)
        assert len(mw) == 2

        gates = reg.get_by_type(EntityType.GATE)
        assert len(gates) == 1

    def test_all_entities(self) -> None:
        reg = EntityRegistry()
        entities = [_make_entity(f"ent-{i:03d}") for i in range(3)]
        reg.register_many(entities)
        assert len(reg.all_entities()) == 3

    def test_domains_property(self) -> None:
        reg = EntityRegistry()
        e1 = _make_entity("ent-001", domain=Domain.GOVERNANCE)
        e2 = _make_entity("ent-002", domain=Domain.SECURITY)
        reg.register_many([e1, e2])
        assert set(reg.domains) == {Domain.GOVERNANCE, Domain.SECURITY}

    def test_to_entity_map(self) -> None:
        reg = EntityRegistry()
        entity = _make_entity(
            "ent-001",
            etype=EntityType.GATE,
            domain=Domain.GOVERNANCE,
            class_name="TestGate",
            line_number=10,
            description="A test gate",
            execution_order=1,
            conditional=True,
            condition_flag="enabled",
            critical=True,
            dependencies=("dep-001",),
        )
        reg.register(entity)

        entity_map = reg.to_entity_map()
        assert entity_map["schema_version"] == "probe-entities/1.0"
        assert entity_map["entity_count"] == 1
        assert "ent-001" in entity_map["entities"]
        assert entity_map["entities"]["ent-001"]["label"] == "Entity-ent-001"
        assert entity_map["entities"]["ent-001"]["class_name"] == "TestGate"
        assert entity_map["entities"]["ent-001"]["critical"] is True
        assert entity_map["entities"]["ent-001"]["dependencies"] == ["dep-001"]

        assert "governance" in entity_map["domains"]
        assert entity_map["domains"]["governance"]["entity_count"] == 1

    def test_to_entity_map_empty(self) -> None:
        reg = EntityRegistry()
        entity_map = reg.to_entity_map()
        assert entity_map["entity_count"] == 0
        assert entity_map["entities"] == {}
        assert entity_map["domains"] == {}
