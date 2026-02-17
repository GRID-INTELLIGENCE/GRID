"""Environment Wheel - Visual representation of agent movement through GRID's environment."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = None  # Will be set after import


class WheelZone(StrEnum):
    """Zones/sectors of the environment wheel."""

    CORE = "core"  # grid/ - Core intelligence layer
    COGNITIVE = "cognitive"  # light_of_the_seven/ - Cognitive layer
    APPLICATION = "application"  # application/ - Application layer
    TOOLS = "tools"  # tools/ - Tools and utilities
    ARENA = "arena"  # Arena/ - Arena simulation
    AGENTIC = "agentic"  # grid/agentic/ - Agentic system
    INTERFACES = "interfaces"  # grid/interfaces/ - Interface layer
    CANVAS = "canvas"  # application/canvas/ - Canvas routing


class AgentPosition:
    """Position of an agent on the wheel."""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        zone: WheelZone,
        angle: float = 0.0,
        radius: float = 0.5,
        velocity: float = 0.0,
    ):
        """Initialize agent position.

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            zone: Current zone on the wheel
            angle: Angle in radians (0 to 2π)
            radius: Distance from center (0.0 to 1.0)
            velocity: Angular velocity (radians per update)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.zone = zone
        self.angle = angle
        self.radius = radius
        self.velocity = velocity
        self.trail: list[tuple[float, float]] = []  # Position history
        self.last_update = time.time()
        self.metadata: dict[str, Any] = {}

    def update(
        self,
        delta_time: float,
        target_zone: WheelZone | None = None,
        target_angle: float | None = None,
    ) -> None:
        """Update agent position on the wheel.

        Args:
            delta_time: Time since last update
            target_zone: Optional target zone to move towards
            target_angle: Optional target angle to rotate towards
        """
        if target_zone and target_zone != self.zone:
            # Move towards target zone
            target_angle_for_zone = self._zone_to_angle(target_zone)
            self._rotate_towards(target_angle_for_zone, delta_time)
        elif target_angle is not None:
            # Rotate towards target angle
            self._rotate_towards(target_angle, delta_time)
        else:
            # Continue with current velocity
            self.angle = (self.angle + self.velocity * delta_time) % (2 * math.pi)

        # Record position in trail
        x, y = self._polar_to_cartesian()
        self.trail.append((x, y))

        # Limit trail length
        if len(self.trail) > 50:
            self.trail = self.trail[-50:]

        self.last_update = time.time()

    def _rotate_towards(self, target_angle: float, delta_time: float) -> None:
        """Rotate towards target angle with smooth interpolation."""
        # Normalize angles
        angle_diff = (target_angle - self.angle) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi

        # Smooth interpolation
        rotation_speed = 2.0  # radians per second
        max_rotation = rotation_speed * delta_time

        if abs(angle_diff) < max_rotation:
            self.angle = target_angle
        else:
            self.angle = (self.angle + math.copysign(max_rotation, angle_diff)) % (2 * math.pi)

    def _zone_to_angle(self, zone: WheelZone) -> float:
        """Convert zone to angle on wheel."""
        zone_angles = {
            WheelZone.CORE: 0.0,
            WheelZone.COGNITIVE: math.pi / 4,
            WheelZone.APPLICATION: math.pi / 2,
            WheelZone.TOOLS: 3 * math.pi / 4,
            WheelZone.ARENA: math.pi,
            WheelZone.AGENTIC: 5 * math.pi / 4,
            WheelZone.INTERFACES: 3 * math.pi / 2,
            WheelZone.CANVAS: 7 * math.pi / 4,
        }
        return zone_angles.get(zone, 0.0)

    def _polar_to_cartesian(self) -> tuple[float, float]:
        """Convert polar coordinates to cartesian."""
        x = self.radius * math.cos(self.angle)
        y = self.radius * math.sin(self.angle)
        return (x, y)

    def get_position(self) -> dict[str, Any]:
        """Get current position as dictionary."""
        x, y = self._polar_to_cartesian()
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "zone": self.zone.value,
            "angle": self.angle,
            "angle_degrees": math.degrees(self.angle),
            "radius": self.radius,
            "x": x,
            "y": y,
            "velocity": self.velocity,
            "trail_length": len(self.trail),
            "metadata": self.metadata,
        }


@dataclass
class WheelState:
    """State of the environment wheel."""

    rotation_angle: float = 0.0  # Overall wheel rotation
    rotation_velocity: float = 0.0  # Rotation speed
    agents: dict[str, AgentPosition] = field(default_factory=dict)
    zones: dict[WheelZone, dict[str, Any]] = field(default_factory=dict)
    last_update: float = field(default_factory=time.time)
    update_count: int = 0

    def __post_init__(self) -> None:
        """Initialize zone states."""
        for zone in WheelZone:
            self.zones[zone] = {
                "agent_count": 0,
                "activity_level": 0.0,
                "last_activity": None,
                "metadata": {},
            }


class EnvironmentWheel:
    """
    Spinning wheel visualization of the GRID environment.

    Represents the movement of agents through different zones/layers
    of the GRID system as a spinning wheel that can be seen and perceived.
    The wheel continuously rotates, and agents move between zones,
    creating a visual representation of the system's dynamic state.
    """

    def __init__(
        self,
        rotation_speed: float = 0.1,  # Base rotation speed (radians per update)
        auto_rotate: bool = True,
    ):
        """Initialize environment wheel.

        Args:
            rotation_speed: Base rotation speed of the wheel
            auto_rotate: Whether to auto-rotate the wheel
        """
        self.rotation_speed = rotation_speed
        self.auto_rotate = auto_rotate
        self.state = WheelState()
        self._zone_activity_decay = 0.95  # Activity decay per update

    def spin(self, delta_time: float | None = None) -> WheelState:
        """Spin the wheel, updating all positions and state.

        Args:
            delta_time: Optional delta time, otherwise calculated from last update

        Returns:
            Updated wheel state
        """
        current_time = time.time()

        if delta_time is None:
            delta_time = current_time - self.state.last_update
        else:
            delta_time = max(0.0, min(delta_time, 1.0))  # Clamp to reasonable range

        # Update overall rotation
        if self.auto_rotate:
            self.state.rotation_angle = (self.state.rotation_angle + self.rotation_speed * delta_time) % (2 * math.pi)
            self.state.rotation_velocity = self.rotation_speed

        # Update agent positions
        for agent in self.state.agents.values():
            agent.update(delta_time)

        # Decay zone activity
        for zone_data in self.state.zones.values():
            zone_data["activity_level"] *= self._zone_activity_decay

        # Update zone agent counts
        self._update_zone_counts()

        self.state.last_update = current_time
        self.state.update_count += 1

        return self.state

    def add_agent(
        self,
        agent_id: str,
        agent_name: str,
        zone: WheelZone,
        radius: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentPosition:
        """Add an agent to the wheel.

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable name
            zone: Initial zone
            radius: Optional radius (default: random based on zone)
            metadata: Optional metadata

        Returns:
            Created AgentPosition
        """
        if radius is None:
            # Vary radius slightly per zone for visual interest
            base_radius = 0.5
            zone_variation = hash(zone.value) % 100 / 1000.0  # Small variation
            radius = base_radius + zone_variation

        angle = self._zone_to_angle(zone)

        agent = AgentPosition(
            agent_id=agent_id,
            agent_name=agent_name,
            zone=zone,
            angle=angle,
            radius=radius,
            velocity=0.1 + (hash(agent_id) % 50) / 500.0,  # Varied velocity
        )

        if metadata:
            agent.metadata = metadata

        self.state.agents[agent_id] = agent

        # Update zone activity
        self.state.zones[zone]["agent_count"] += 1
        self.state.zones[zone]["activity_level"] = min(1.0, self.state.zones[zone]["activity_level"] + 0.2)
        self.state.zones[zone]["last_activity"] = datetime.now().isoformat()

        return agent

    def move_agent(
        self,
        agent_id: str,
        target_zone: WheelZone,
        speed: float | None = None,
    ) -> bool:
        """Move an agent to a target zone.

        Args:
            agent_id: Agent identifier
            target_zone: Target zone to move to
            speed: Optional movement speed multiplier

        Returns:
            True if agent found and movement initiated
        """
        if agent_id not in self.state.agents:
            return False

        agent = self.state.agents[agent_id]

        # Update agent velocity for movement
        if speed is not None:
            agent.velocity = speed

        # Mark zone change
        old_zone = agent.zone
        agent.zone = target_zone

        # Update zone activities
        if old_zone in self.state.zones:
            self.state.zones[old_zone]["agent_count"] = max(0, self.state.zones[old_zone]["agent_count"] - 1)

        self.state.zones[target_zone]["agent_count"] += 1
        self.state.zones[target_zone]["activity_level"] = min(
            1.0, self.state.zones[target_zone]["activity_level"] + 0.3
        )
        self.state.zones[target_zone]["last_activity"] = datetime.now().isoformat()

        return True

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the wheel.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was removed
        """
        if agent_id not in self.state.agents:
            return False

        agent = self.state.agents[agent_id]
        zone = agent.zone

        # Update zone count
        if zone in self.state.zones:
            self.state.zones[zone]["agent_count"] = max(0, self.state.zones[zone]["agent_count"] - 1)

        del self.state.agents[agent_id]
        return True

    def get_visualization(self) -> dict[str, Any]:
        """Get visualization data of the wheel state.

        Returns:
            Dictionary with visualization data
        """
        self.spin()  # Update state

        agents_data = []
        for agent in self.state.agents.values():
            pos = agent.get_position()
            # Apply wheel rotation to agent positions
            pos["visual_angle"] = (pos["angle"] + self.state.rotation_angle) % (2 * math.pi)
            pos["visual_x"] = pos["radius"] * math.cos(pos["visual_angle"])
            pos["visual_y"] = pos["radius"] * math.sin(pos["visual_angle"])
            agents_data.append(pos)

        zones_data = {}
        for zone, data in self.state.zones.items():
            angle = self._zone_to_angle(zone)
            zones_data[zone.value] = {
                **data,
                "angle": angle,
                "angle_degrees": math.degrees(angle),
                "visual_angle": (angle + self.state.rotation_angle) % (2 * math.pi),
            }

        return {
            "rotation_angle": self.state.rotation_angle,
            "rotation_angle_degrees": math.degrees(self.state.rotation_angle),
            "rotation_velocity": self.state.rotation_velocity,
            "agents": agents_data,
            "zones": zones_data,
            "total_agents": len(self.state.agents),
            "update_count": self.state.update_count,
            "last_update": datetime.fromtimestamp(self.state.last_update).isoformat(),
        }

    def get_text_visualization(self, width: int = 60, height: int = 30) -> str:
        """Get ASCII text visualization of the wheel.

        Args:
            width: Width of visualization in characters
            height: Height of visualization in characters

        Returns:
            ASCII art string
        """
        self.spin()

        # Create character grid
        grid = [[" " for _ in range(width)] for _ in range(height)]

        center_x, center_y = width // 2, height // 2
        max_radius = min(center_x, center_y) - 2

        # Draw wheel zones (sectors)
        len(WheelZone)
        for _i, zone in enumerate(WheelZone):
            angle = self._zone_to_angle(zone) + self.state.rotation_angle
            # Draw zone label at edge
            label_x = int(center_x + max_radius * 0.8 * math.cos(angle))
            label_y = int(center_y + max_radius * 0.8 * math.sin(angle))
            if 0 <= label_x < width and 0 <= label_y < height:
                zone_char = zone.value[0].upper()
                grid[label_y][label_x] = zone_char

        # Draw agents
        for agent in self.state.agents.values():
            pos = agent.get_position()
            # Calculate visual angle with wheel rotation (pos doesn't have visual_angle)
            visual_angle = (pos["angle"] + self.state.rotation_angle) % (2 * math.pi)
            x = int(center_x + pos["radius"] * max_radius * math.cos(visual_angle))
            y = int(center_y + pos["radius"] * max_radius * math.sin(visual_angle))

            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "*"  # Agent marker

        # Draw center
        grid[center_y][center_x] = "O"

        # Build output string
        lines = []
        lines.append(f"Environment Wheel - Rotation: {math.degrees(self.state.rotation_angle):.1f} deg")
        lines.append(f"Agents: {len(self.state.agents)} | Updates: {self.state.update_count}")
        lines.append("-" * width)

        lines.extend("".join(row) for row in grid)

        lines.append("-" * width)

        # Zone activity summary
        active_zones = [
            (zone.value, data["agent_count"], data["activity_level"])
            for zone, data in self.state.zones.items()
            if data["agent_count"] > 0 or data["activity_level"] > 0.1
        ]
        if active_zones:
            lines.append("Active Zones:")
            for zone_name, count, activity in sorted(active_zones, key=lambda x: x[2], reverse=True)[:5]:
                lines.append(f"  {zone_name}: {count} agents, activity {activity:.2f}")

        return "\n".join(lines)

    def _zone_to_angle(self, zone: WheelZone) -> float:
        """Convert zone to base angle."""
        zone_angles = {
            WheelZone.CORE: 0.0,
            WheelZone.COGNITIVE: math.pi / 4,
            WheelZone.APPLICATION: math.pi / 2,
            WheelZone.TOOLS: 3 * math.pi / 4,
            WheelZone.ARENA: math.pi,
            WheelZone.AGENTIC: 5 * math.pi / 4,
            WheelZone.INTERFACES: 3 * math.pi / 2,
            WheelZone.CANVAS: 7 * math.pi / 4,
        }
        return zone_angles.get(zone, 0.0)

    def _update_zone_counts(self) -> None:
        """Update zone agent counts based on current positions."""
        # Reset counts
        for zone_data in self.state.zones.values():
            zone_data["agent_count"] = 0

        # Count agents in each zone
        for agent in self.state.agents.values():
            if agent.zone in self.state.zones:
                self.state.zones[agent.zone]["agent_count"] += 1
