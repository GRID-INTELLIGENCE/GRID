"""
Component Pool Architecture
==========================

Dynamic component management with watch-like precision coordination.
"""

from .pool import (
    Component,
    ComponentPool,
    ComponentState,
    ComponentType,
    ProcessorComponent,
    ValidatorComponent,
    get_component_pool,
)

__all__ = [
    "ComponentPool",
    "get_component_pool",
    "Component",
    "ComponentState",
    "ComponentType",
    "ProcessorComponent",
    "ValidatorComponent"
]
