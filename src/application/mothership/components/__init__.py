"""
Component Pool Architecture
==========================

Dynamic component management with watch-like precision coordination.
"""

from .pool import (
    ComponentPool, 
    get_component_pool,
    Component,
    ComponentState,
    ComponentType,
    ProcessorComponent,
    ValidatorComponent
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