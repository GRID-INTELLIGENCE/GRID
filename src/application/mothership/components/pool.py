"""
Component Pool Architecture for Dynamic Scaling
===============================================

Implements watch-like mechanism for precise component coordination
and dynamic resource allocation based on demand.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ComponentState(StrEnum):
    """Component lifecycle states."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    RECOVERING = "recovering"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


class ComponentType(StrEnum):
    """Types of components in the pool."""

    PROCESSOR = "processor"
    VALIDATOR = "validator"
    TRANSFORMER = "transformer"
    AGGREGATOR = "aggregator"
    MONITOR = "monitor"
    CUSTOM = "custom"


@dataclass
class ComponentMetrics:
    """Performance metrics for components."""

    component_id: str
    component_type: ComponentType
    state: ComponentState
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_processing_time: float = 0.0
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_operations == 0:
            return 1.0
        return self.successful_operations / self.total_operations

    @property
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        state_weight = {
            ComponentState.ACTIVE: 1.0,
            ComponentState.IDLE: 0.8,
            ComponentState.BUSY: 0.6,
            ComponentState.RECOVERING: 0.3,
            ComponentState.INITIALIZING: 0.4,
            ComponentState.SHUTTING_DOWN: 0.1,
            ComponentState.TERMINATED: 0.0,
        }

        state_score = state_weight.get(self.state, 0.0)
        success_score = self.success_rate
        speed_score = 1.0 / (1.0 + self.avg_processing_time)

        return (state_score + success_score + speed_score) / 3.0

    def update_operation(self, success: bool, processing_time: float):
        """Update operation metrics."""
        self.total_operations += 1
        self.last_activity = datetime.now(UTC)

        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1

        # Update average processing time
        self.avg_processing_time = (
            self.avg_processing_time * (self.total_operations - 1) + processing_time
        ) / self.total_operations

        # Update error rate
        self.error_rate = self.failed_operations / self.total_operations


class Component:
    """Base component class for the pool."""

    def __init__(self, component_id: str, component_type: ComponentType):
        self.component_id = component_id
        self.component_type = component_type
        self.state = ComponentState.INITIALIZING
        self.metrics = ComponentMetrics(
            component_id=component_id, component_type=component_type, state=ComponentState.INITIALIZING
        )
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize the component."""
        async with self._lock:
            try:
                await self._on_initialize()
                self.state = ComponentState.IDLE
                self.metrics.state = ComponentState.IDLE
                logger.info(f"Component {self.component_id} initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize component {self.component_id}: {e}")
                self.state = ComponentState.TERMINATED
                self.metrics.state = ComponentState.TERMINATED
                return False

    async def process(self, data: Any) -> Any:
        """Process data through the component."""
        async with self._lock:
            if self.state not in [ComponentState.IDLE, ComponentState.ACTIVE]:
                raise RuntimeError(f"Component {self.component_id} is not available for processing")

            self.state = ComponentState.BUSY
            self.metrics.state = ComponentState.BUSY

        start_time = time.time()
        try:
            result = await self._on_process(data)
            processing_time = time.time() - start_time

            async with self._lock:
                self.state = ComponentState.ACTIVE
                self.metrics.state = ComponentState.ACTIVE
                self.metrics.update_operation(True, processing_time)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Component {self.component_id} processing failed: {e}")

            async with self._lock:
                self.state = ComponentState.RECOVERING
                self.metrics.state = ComponentState.RECOVERING
                self.metrics.update_operation(False, processing_time)

            raise e

    async def shutdown(self):
        """Shutdown the component."""
        async with self._lock:
            self.state = ComponentState.SHUTTING_DOWN
            self.metrics.state = ComponentState.SHUTTING_DOWN

            try:
                await self._on_shutdown()
                self.state = ComponentState.TERMINATED
                self.metrics.state = ComponentState.TERMINATED
                logger.info(f"Component {self.component_id} shutdown successfully")
            except Exception as e:
                logger.error(f"Error during component {self.component_id} shutdown: {e}")

    async def _on_initialize(self):
        """Override for component-specific initialization."""
        await asyncio.sleep(0.01)  # Simulate initialization

    async def _on_process(self, data: Any) -> Any:
        """Override for component-specific processing."""
        await asyncio.sleep(0.05)  # Simulate processing
        return f"processed_by_{self.component_id}"

    async def _on_shutdown(self):
        """Override for component-specific cleanup."""
        await asyncio.sleep(0.01)  # Simulate cleanup


class ProcessorComponent(Component):
    """Data processing component."""

    def __init__(self, component_id: str):
        super().__init__(component_id, ComponentType.PROCESSOR)

    async def _on_process(self, data: Any) -> Any:
        """Process data with transformation."""
        await asyncio.sleep(0.05)
        return {
            "original": data,
            "processed": True,
            "processor": self.component_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class ValidatorComponent(Component):
    """Data validation component."""

    def __init__(self, component_id: str):
        super().__init__(component_id, ComponentType.VALIDATOR)

    async def _on_process(self, data: Any) -> Any:
        """Validate data structure and content."""
        await asyncio.sleep(0.02)

        # Simple validation logic
        is_valid = isinstance(data, dict) and "data" in data

        return {"valid": is_valid, "validator": self.component_id, "validated_at": datetime.now(UTC).isoformat()}


class ComponentPool:
    """
    Dynamic component pool with watch-like precision coordination.

    Features:
    - Dynamic scaling based on demand
    - Component health monitoring
    - Automatic recovery and replacement
    - Load balancing across components
    """

    def __init__(self, min_components: int = 2, max_components: int = 20):
        self.min_components = min_components
        self.max_components = max_components
        self.components: dict[str, Component] = {}
        self.component_types: dict[ComponentType, list[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._monitoring_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False

    async def initialize(self):
        """Initialize the component pool."""
        if self._initialized:
            return

        # Create minimum components
        for i in range(self.min_components):
            component_type = ComponentType.PROCESSOR if i % 2 == 0 else ComponentType.VALIDATOR
            await self._add_component(component_type)

        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitor_components())

        self._initialized = True
        logger.info(f"ComponentPool initialized with {len(self.components)} components")

    async def get_component(self, component_type: ComponentType | None = None) -> Component | None:
        """Get best available component of specified type."""
        async with self._lock:
            candidates = []

            if component_type:
                candidates = [
                    comp
                    for comp_id, comp in self.components.items()
                    if comp.component_type == component_type and comp.state == ComponentState.IDLE
                ]
            else:
                candidates = [comp for comp_id, comp in self.components.items() if comp.state == ComponentState.IDLE]

            if not candidates:
                # Try to scale up
                await self._scale_up_if_needed(component_type)

                # Retry after scaling
                if component_type:
                    candidates = [
                        comp
                        for comp_id, comp in self.components.items()
                        if comp.component_type == component_type and comp.state == ComponentState.IDLE
                    ]
                else:
                    candidates = [
                        comp for comp_id, comp in self.components.items() if comp.state == ComponentState.IDLE
                    ]

            if not candidates:
                return None

            # Select component with highest efficiency score
            best_component = max(candidates, key=lambda c: c.metrics.efficiency_score)
            return best_component

    async def process_with_component(self, data: Any, component_type: ComponentType | None = None) -> Any:
        """Process data using best available component."""
        component = await self.get_component(component_type)

        if not component:
            raise RuntimeError("No available components for processing")

        return await component.process(data)

    async def _add_component(self, component_type: ComponentType) -> str:
        """Add a new component to the pool."""
        component_id = f"{component_type.value}_{len(self.components)}"

        if component_type == ComponentType.PROCESSOR:
            component = ProcessorComponent(component_id)
        elif component_type == ComponentType.VALIDATOR:
            component = ValidatorComponent(component_id)
        else:
            component = Component(component_id, component_type)

        # Initialize component
        if await component.initialize():
            async with self._lock:
                self.components[component_id] = component
                self.component_types[component_type].append(component_id)

            logger.info(f"Added component {component_id} of type {component_type.value}")
            return component_id
        else:
            logger.error(f"Failed to initialize component {component_id}")
            raise RuntimeError(f"Component initialization failed: {component_id}")

    async def _scale_up_if_needed(self, component_type: ComponentType | None = None):
        """Scale up component pool if needed."""
        current_count = len(self.components)

        if current_count >= self.max_components:
            return

        # Check if we need more components of specific type
        if component_type:
            type_count = len(self.component_types[component_type])
            if type_count < self.min_components:
                await self._add_component(component_type)
        else:
            # Add general component
            await self._add_component(ComponentType.PROCESSOR)

    async def _monitor_components(self):
        """Monitor component health and performance."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_component_health()
                await self._optimize_pool()
                await asyncio.sleep(30)  # Increased from 5s to 30s for lower overhead
            except Exception as e:
                logger.error(f"Component monitoring error: {e}")
                await asyncio.sleep(5)

    async def _check_component_health(self):
        """Check health of all components and recover if needed."""
        async with self._lock:
            for component_id, component in list(self.components.items()):
                # Check for stuck components
                if component.state == ComponentState.RECOVERING:
                    # Try to recover
                    if await component.initialize():
                        logger.info(f"Recovered component {component_id}")
                    else:
                        # Remove failed component
                        await self._remove_component(component_id)

                # Check for idle components that can be terminated
                elif component.state == ComponentState.IDLE and len(self.components) > self.min_components:
                    idle_time = (datetime.now(UTC) - component.metrics.last_activity).total_seconds()
                    if idle_time > 60:  # Idle for more than 1 minute
                        await self._remove_component(component_id)

    async def _optimize_pool(self):
        """Optimize component pool based on load and performance."""
        async with self._lock:
            # Calculate overall pool efficiency
            if not self.components:
                return

            total_efficiency = sum(comp.metrics.efficiency_score for comp in self.components.values())
            avg_efficiency = total_efficiency / len(self.components)

            # Scale down if efficiency is high and we have excess components
            if avg_efficiency > 0.8 and len(self.components) > self.min_components:
                idle_components = [comp for comp in self.components.values() if comp.state == ComponentState.IDLE]

                if idle_components:
                    await self._remove_component(idle_components[0].component_id)

    async def _remove_component(self, component_id: str):
        """Remove a component from the pool."""
        if component_id not in self.components:
            return

        component = self.components[component_id]
        await component.shutdown()

        # Remove from tracking
        self.component_types[component.component_type].remove(component_id)
        del self.components[component_id]

        logger.info(f"Removed component {component_id}")

    async def shutdown(self):
        """Shutdown the component pool."""
        self._shutdown_event.set()

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Shutdown all components
        async with self._lock:
            for component in list(self.components.values()):
                await component.shutdown()

            self.components.clear()
            self.component_types.clear()

        logger.info("ComponentPool shutdown complete")

    def get_pool_stats(self) -> dict[str, Any]:
        """Get comprehensive pool statistics."""
        stats = {
            "total_components": len(self.components),
            "component_types": {
                comp_type.value: len(component_ids) for comp_type, component_ids in self.component_types.items()
            },
            "components": {},
        }

        for component_id, component in self.components.items():
            stats["components"][component_id] = {
                "type": component.component_type.value,
                "state": component.state.value,
                "efficiency_score": component.metrics.efficiency_score,
                "success_rate": component.metrics.success_rate,
                "total_operations": component.metrics.total_operations,
                "avg_processing_time": component.metrics.avg_processing_time,
            }

        return stats


# Singleton instance
_pool: ComponentPool | None = None


def get_component_pool() -> ComponentPool:
    """Get the singleton ComponentPool instance."""
    global _pool
    if _pool is None:
        _pool = ComponentPool()
    return _pool
