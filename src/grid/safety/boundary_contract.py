"""
Boundary Contract - Ownership and Permission Scopes for Safety Boundaries.

This module defines the `BoundaryContract` dataclass for formalizing data
ownership and permission scopes between system layers. Inspired by OS-level
capability systems (seL4, Fuchsia) and Rust's ownership model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PermissionScope(str, Enum):
    """Permission scopes for boundary contracts."""

    READ = "read"
    WRITE = "write"
    MUTATE = "mutate"
    EXECUTE = "execute"


class OwnerType(str, Enum):
    """Types of owners in the safety system."""

    ENGINE = "engine"
    OVERWATCH = "overwatch"
    DYNAMICS = "dynamics"
    GUARDIAN = "guardian"
    USER = "user"
    SYSTEM = "system"


@dataclass
class BoundaryContract:
    """
    A contract that formalizes ownership and permissions for data crossing boundaries.

    Attributes:
        owner: The current owner of the resource.
        permissions: Set of allowed operations on the resource.
        created_at: Timestamp when the contract was created.
        owner_transfer_history: List of (timestamp, new_owner) tuples for audit.
        min_value: Optional minimum value constraint (for numeric resources).
        max_value: Optional maximum value constraint (for numeric resources).
        resource_id: Unique identifier for the resource being contracted.
        boundary_gradient: Position in the safety gradient (0.0-1.0).
    """

    owner: OwnerType
    permissions: set[PermissionScope]
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    owner_transfer_history: list[tuple[float, OwnerType]] = field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None
    resource_id: str | None = None
    boundary_gradient: float = 0.0

    def transfer_ownership(self, new_owner: OwnerType) -> None:
        """
        Transfer ownership of the resource to a new owner.

        Args:
            new_owner: The new owner of the resource.
        """
        timestamp = datetime.now().timestamp()
        self.owner_transfer_history.append((timestamp, new_owner))
        self.owner = new_owner

    def has_permission(self, scope: PermissionScope) -> bool:
        """
        Check if the contract has a specific permission.

        Args:
            scope: The permission to check.

        Returns:
            True if the permission is granted.
        """
        return scope in self.permissions

    def grant_permission(self, scope: PermissionScope) -> None:
        """Grant a new permission to the contract."""
        self.permissions.add(scope)

    def revoke_permission(self, scope: PermissionScope) -> None:
        """Revoke a permission from the contract."""
        self.permissions.discard(scope)

    def validate_value(self, value: float) -> bool:
        """
        Validate a value against the contract's constraints.

        Args:
            value: The value to validate.

        Returns:
            True if the value is within constraints.
        """
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def is_at_boundary(self, gradient: float, tolerance: float = 0.05) -> bool:
        """
        Check if the current gradient is at a boundary transition.

        Boundaries are defined at 0.3, 0.6, 0.8, 1.0.

        Args:
            gradient: The current gradient position.
            tolerance: Tolerance for boundary detection.

        Returns:
            True if at a boundary.
        """
        boundaries = [0.3, 0.6, 0.8, 1.0]
        return any(abs(gradient - b) < tolerance for b in boundaries)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract to a dictionary."""
        return {
            "owner": self.owner.value,
            "permissions": [p.value for p in self.permissions],
            "created_at": self.created_at,
            "owner_transfer_history": [(ts, owner.value) for ts, owner in self.owner_transfer_history],
            "min_value": self.min_value,
            "max_value": self.max_value,
            "resource_id": self.resource_id,
            "boundary_gradient": self.boundary_gradient,
        }


class BoundaryViolationError(Exception):
    """Raised when a boundary contract is violated."""

    def __init__(self, message: str, contract: BoundaryContract):
        super().__init__(message)
        self.contract = contract


def create_contract(
    owner: OwnerType,
    permissions: set[PermissionScope],
    resource_id: str | None = None,
    gradient: float = 0.0,
) -> BoundaryContract:
    """
    Factory function to create a new BoundaryContract.

    Args:
        owner: The owner of the resource.
        permissions: Set of permissions for the resource.
        resource_id: Optional unique identifier.
        gradient: Position in the safety gradient.

    Returns:
        A new BoundaryContract instance.
    """
    return BoundaryContract(
        owner=owner,
        permissions=permissions,
        resource_id=resource_id,
        boundary_gradient=gradient,
    )
