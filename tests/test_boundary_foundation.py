"""
Boundary Foundation Tests - Phase 1 of Safety Implementation.

Tests for BoundaryContract and Ring Decorators to validate
the foundational safety boundary system.
"""

import pytest

from grid.safety.boundary_contract import (
    BoundaryContract,
    OwnerType,
    PermissionScope,
    create_contract,
)
from grid.safety.ring_decorators import (
    PrivilegeRing,
    require_ring,
    ring0_protect,
    ring1_mutate,
    ring2_validate,
    ring3_input,
)


class TestBoundaryContract:
    """Tests for BoundaryContract dataclass."""

    def test_contract_creation(self):
        """BoundaryContract should be created with required fields."""
        contract = BoundaryContract(
            owner=OwnerType.ENGINE,
            permissions={PermissionScope.READ, PermissionScope.WRITE},
        )

        assert contract.owner == OwnerType.ENGINE
        assert PermissionScope.READ in contract.permissions
        assert PermissionScope.WRITE in contract.permissions
        assert contract.created_at is not None

    def test_factory_function(self):
        """create_contract factory should create valid contracts."""
        contract = create_contract(
            owner=OwnerType.GUARDIAN,
            permissions={PermissionScope.EXECUTE},
            resource_id="test-resource-001",
            gradient=0.5,
        )

        assert contract.owner == OwnerType.GUARDIAN
        assert contract.resource_id == "test-resource-001"
        assert contract.boundary_gradient == 0.5

    def test_ownership_transfer(self):
        """Ownership transfer should update owner and record history."""
        contract = create_contract(
            owner=OwnerType.USER,
            permissions={PermissionScope.READ},
        )

        contract.transfer_ownership(OwnerType.ENGINE)

        assert contract.owner == OwnerType.ENGINE
        assert len(contract.owner_transfer_history) == 1
        assert contract.owner_transfer_history[0][1] == OwnerType.ENGINE

    def test_permission_check(self):
        """has_permission should correctly check permissions."""
        contract = create_contract(
            owner=OwnerType.SYSTEM,
            permissions={PermissionScope.READ},
        )

        assert contract.has_permission(PermissionScope.READ) is True
        assert contract.has_permission(PermissionScope.WRITE) is False

    def test_permission_grant_revoke(self):
        """Permissions should be grantable and revokable."""
        contract = create_contract(
            owner=OwnerType.OVERWATCH,
            permissions={PermissionScope.READ},
        )

        contract.grant_permission(PermissionScope.MUTATE)
        assert contract.has_permission(PermissionScope.MUTATE) is True

        contract.revoke_permission(PermissionScope.READ)
        assert contract.has_permission(PermissionScope.READ) is False

    def test_value_validation(self):
        """validate_value should check min/max constraints."""
        contract = BoundaryContract(
            owner=OwnerType.ENGINE,
            permissions={PermissionScope.READ},
            min_value=0.0,
            max_value=1.0,
        )

        assert contract.validate_value(0.5) is True
        assert contract.validate_value(-0.1) is False
        assert contract.validate_value(1.1) is False

    def test_boundary_detection(self):
        """is_at_boundary should detect gradient boundaries."""
        contract = create_contract(
            owner=OwnerType.ENGINE,
            permissions={PermissionScope.READ},
        )

        # Boundaries are at 0.3, 0.6, 0.8, 1.0
        assert contract.is_at_boundary(0.3) is True
        assert contract.is_at_boundary(0.31) is True  # Within tolerance
        assert contract.is_at_boundary(0.5) is False
        assert contract.is_at_boundary(0.6) is True
        assert contract.is_at_boundary(0.8) is True

    def test_to_dict_serialization(self):
        """to_dict should serialize contract correctly."""
        contract = create_contract(
            owner=OwnerType.GUARDIAN,
            permissions={PermissionScope.READ, PermissionScope.EXECUTE},
            resource_id="test-123",
            gradient=0.3,
        )

        data = contract.to_dict()

        assert data["owner"] == "guardian"
        assert "read" in data["permissions"]
        assert "execute" in data["permissions"]
        assert data["resource_id"] == "test-123"
        assert data["boundary_gradient"] == 0.3


class TestOwnerTypes:
    """Tests for OwnerType enum completeness."""

    def test_all_owner_types_defined(self):
        """All expected owner types should exist."""
        expected = ["ENGINE", "OVERWATCH", "DYNAMICS", "GUARDIAN", "USER", "SYSTEM"]
        for name in expected:
            assert hasattr(OwnerType, name), f"Missing OwnerType: {name}"


class TestPermissionScopes:
    """Tests for PermissionScope enum completeness."""

    def test_all_permission_scopes_defined(self):
        """All expected permission scopes should exist."""
        expected = ["READ", "WRITE", "MUTATE", "EXECUTE"]
        for name in expected:
            assert hasattr(PermissionScope, name), f"Missing PermissionScope: {name}"


class TestPrivilegeRings:
    """Tests for PrivilegeRing enum and ring decorators."""

    def test_ring_ordering(self):
        """Privilege rings should have correct ordering (lower = more privileged)."""
        assert PrivilegeRing.RING_0 < PrivilegeRing.RING_1
        assert PrivilegeRing.RING_1 < PrivilegeRing.RING_2
        assert PrivilegeRing.RING_2 < PrivilegeRing.RING_3

    def test_ring3_input_decorator(self):
        """ring3_input decorator should wrap function and set ring."""
        from grid.tracing.action_trace import TraceOrigin

        @ring3_input(trace_origin=TraceOrigin.API_REQUEST)
        def sample_input_handler(data: str) -> str:
            return f"processed: {data}"

        result = sample_input_handler("test")
        assert result == "processed: test"

    def test_ring2_validate_decorator(self):
        """ring2_validate decorator should wrap function correctly."""

        @ring2_validate()
        def sample_validator(value: int) -> bool:
            return value > 0

        result = sample_validator(5)
        assert result is True

    def test_ring1_mutate_decorator(self):
        """ring1_mutate decorator should wrap function correctly."""

        @ring1_mutate(safety_critical=True)
        def sample_mutation(data: dict) -> dict:
            data["modified"] = True
            return data

        result = sample_mutation({"value": 1})
        assert result["modified"] is True

    def test_ring0_protect_decorator(self):
        """ring0_protect decorator should wrap function correctly."""

        @ring0_protect
        def sample_guardian_op() -> str:
            return "guardian operation complete"

        result = sample_guardian_op()
        assert result == "guardian operation complete"

    def test_require_ring_blocks_unprivileged(self):
        """require_ring should raise when called from insufficient privilege."""

        @require_ring(PrivilegeRing.RING_0)
        def privileged_function() -> str:
            return "secret"

        # Default ring is RING_3, which is less privileged than RING_0
        with pytest.raises(PermissionError):
            privileged_function()

    def test_nested_ring_decorators(self):
        """Nested ring decorators should properly manage ring transitions."""

        call_order = []

        @ring0_protect
        def outer_function() -> str:
            call_order.append("outer")
            inner_result = inner_function()
            return f"outer + {inner_result}"

        @ring1_mutate()
        def inner_function() -> str:
            call_order.append("inner")
            return "inner"

        result = outer_function()
        assert result == "outer + inner"
        assert call_order == ["outer", "inner"]


class TestBoundaryIntegration:
    """Integration tests for boundary contracts and ring decorators."""

    def test_contract_with_ring_transition(self):
        """BoundaryContract should work across ring transitions."""
        contract = create_contract(
            owner=OwnerType.ENGINE,
            permissions={PermissionScope.READ, PermissionScope.MUTATE},
            resource_id="game-state",
            gradient=0.5,
        )

        @ring1_mutate(safety_critical=True)
        def mutate_with_contract(c: BoundaryContract) -> bool:
            if c.has_permission(PermissionScope.MUTATE):
                c.boundary_gradient = 0.6
                return True
            return False

        result = mutate_with_contract(contract)
        assert result is True
        assert contract.boundary_gradient == 0.6

    def test_ownership_transfer_in_ring0(self):
        """Ownership transfer should work within Ring 0 operations."""
        contract = create_contract(
            owner=OwnerType.USER,
            permissions={PermissionScope.READ},
        )

        @ring0_protect
        def guardian_takeover(c: BoundaryContract) -> None:
            c.transfer_ownership(OwnerType.GUARDIAN)
            c.grant_permission(PermissionScope.EXECUTE)

        guardian_takeover(contract)

        assert contract.owner == OwnerType.GUARDIAN
        assert contract.has_permission(PermissionScope.EXECUTE)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
