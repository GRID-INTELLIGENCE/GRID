"""
Staircase Intelligence - Autonomous Routing System Inspired by Hogwarts

From J.K. Rowling's description of Hogwarts:
- 142 staircases with different behaviors
- Some lead somewhere different on a Friday (time-aware routing)
- Vanishing steps you must remember to jump (trap detection)
- Doors that require specific interactions (authentication)
- Everything seemed to move around (dynamic topology)

This module implements a "living architecture" routing system
where paths can autonomously reconfigure based on:
- Time/schedule
- Load balancing
- Security conditions
- User context

Analogies:
- Moving stairs = Dynamic route tables
- Vanishing steps = Circuit breakers / traps
- Polite doors = Authentication gates
- Everything moves = Eventual consistency
"""

from __future__ import annotations

import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class StaircaseState(str, Enum):
    """State of a staircase/route."""

    STABLE = "stable"  # Fixed route
    MOVING = "moving"  # Currently reconfiguring
    VANISHED = "vanished"  # Temporarily unavailable (circuit breaker open)
    LOCKED = "locked"  # Requires authentication


class DayBehavior(str, Enum):
    """Special behaviors on certain days (like Friday staircases)."""

    NORMAL = "normal"
    FRIDAY_REDIRECT = "friday_redirect"
    WEEKEND_MAINTENANCE = "weekend_maintenance"
    NIGHT_LOCKDOWN = "night_lockdown"


@dataclass
class Staircase:
    """A single staircase (route) in the system."""

    id: str
    origin: str
    destination: str
    state: StaircaseState = StaircaseState.STABLE
    day_behavior: DayBehavior = DayBehavior.NORMAL
    has_vanishing_step: bool = False
    requires_polite_request: bool = False
    last_moved: datetime = field(default_factory=datetime.now)
    move_probability: float = 0.1  # Chance of moving each cycle

    def get_effective_destination(self) -> str:
        """Get current destination considering state and time."""
        now = datetime.now()

        # Friday redirect behavior
        if self.day_behavior == DayBehavior.FRIDAY_REDIRECT and now.weekday() == 4:
            return f"{self.destination}_friday_alternate"

        # Night lockdown
        if self.day_behavior == DayBehavior.NIGHT_LOCKDOWN and now.hour >= 22:
            return "restricted_area"

        return self.destination

    def attempt_traverse(self, user_context: dict[str, Any]) -> tuple[bool, str]:
        """Attempt to traverse this staircase.

        Returns:
            (success, message)
        """
        # Check if vanished (circuit breaker)
        if self.state == StaircaseState.VANISHED:
            return False, "Route temporarily unavailable (circuit open)"

        # Check if locked (authentication)
        if self.state == StaircaseState.LOCKED:
            if not user_context.get("authenticated"):
                return False, "Authentication required"
            if self.requires_polite_request and not user_context.get("polite"):
                return False, "Please ask politely (include 'please' in request)"

        # Check for vanishing step (trap)
        if self.has_vanishing_step:
            if not user_context.get("knows_vanishing_step"):
                return False, "Fell through vanishing step! Remember to jump next time."

        # Check if moving
        if self.state == StaircaseState.MOVING:
            return False, "Staircase is currently moving, please wait"

        return True, f"Traversed to {self.get_effective_destination()}"

    def maybe_move(self) -> bool:
        """Possibly move the staircase to a new destination."""
        if random.random() < self.move_probability:
            self.state = StaircaseState.MOVING
            self.last_moved = datetime.now()
            return True
        return False


@dataclass
class GrandStaircase:
    """
    The Grand Staircase - A self-organizing routing system.

    Inspired by Hogwarts' 142 staircases that move autonomously,
    creating a living, adaptive network architecture.
    """

    staircases: dict[str, Staircase] = field(default_factory=dict)
    route_cache: dict[str, list[str]] = field(default_factory=dict)
    movement_log: list[dict[str, Any]] = field(default_factory=list)

    def add_staircase(self, staircase: Staircase) -> None:
        """Add a staircase to the system."""
        self.staircases[staircase.id] = staircase

    def find_route(self, origin: str, destination: str) -> list[str] | None:
        """Find a route from origin to destination.

        Uses BFS with awareness of staircase states.
        """
        cache_key = f"{origin}:{destination}"

        # Check cache (but invalidate if staircases moved)
        if cache_key in self.route_cache:
            if self._validate_cached_route(self.route_cache[cache_key]):
                return self.route_cache[cache_key]

        # BFS for path
        visited = set()
        queue = deque([(origin, [origin])])

        while queue:
            current, path = queue.popleft()

            if current in visited:
                continue
            visited.add(current)

            if current == destination:
                self.route_cache[cache_key] = path
                return path

            # Find connected staircases
            for _stair_id, stair in self.staircases.items():
                if stair.origin == current and stair.state != StaircaseState.VANISHED:
                    effective_dest = stair.get_effective_destination()
                    if effective_dest not in visited:
                        queue.append((effective_dest, path + [effective_dest]))

        return None

    def _validate_cached_route(self, route: list[str]) -> bool:
        """Check if a cached route is still valid."""
        for i in range(len(route) - 1):
            origin, dest = route[i], route[i + 1]
            # Find staircase connecting these
            valid = any(
                s.origin == origin
                and s.get_effective_destination() == dest
                and s.state not in (StaircaseState.VANISHED, StaircaseState.MOVING)
                for s in self.staircases.values()
            )
            if not valid:
                return False
        return True

    def cycle(self) -> list[str]:
        """Run one cycle of autonomous movement.

        This is the "magic" - staircases decide to move on their own.

        Returns:
            List of staircase IDs that moved
        """
        moved = []

        for stair_id, stair in self.staircases.items():
            if stair.maybe_move():
                moved.append(stair_id)
                # Randomly reassign destination
                all_destinations = list(set(s.destination for s in self.staircases.values()))
                new_dest = random.choice(all_destinations)

                self.movement_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "staircase_id": stair_id,
                        "old_destination": stair.destination,
                        "new_destination": new_dest,
                    }
                )

                stair.destination = new_dest

                # After moving, become stable again
                stair.state = StaircaseState.STABLE

        # Invalidate all route caches if anything moved
        if moved:
            self.route_cache.clear()

        return moved

    def get_health_report(self) -> dict[str, Any]:
        """Get system health report."""
        states = {}
        for state in StaircaseState:
            states[state.value] = sum(1 for s in self.staircases.values() if s.state == state)

        return {
            "total_staircases": len(self.staircases),
            "states": states,
            "cached_routes": len(self.route_cache),
            "recent_movements": len(self.movement_log),
        }


class StaircaseAPI:
    """
    HTTP-based staircase routing with requests library.

    Demonstrates using requests for distributed staircase intelligence.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "StaircaseIntelligence/1.0",
                "X-Polite": "please",  # Always be polite like Hogwarts doors require
            }
        )

    def check_route_health(self, route_id: str) -> dict[str, Any]:
        """Check if a route is available (circuit breaker pattern)."""
        try:
            response = self.session.get(
                f"{self.base_url}/routes/{route_id}/health",
                timeout=5,
            )
            return {
                "available": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": response.elapsed.total_seconds() * 1000,
            }
        except requests.RequestException as e:
            return {
                "available": False,
                "error": str(e),
                "circuit": "open",  # Vanishing step - circuit breaker triggered
            }

    def discover_routes(self, origin: str) -> list[dict[str, Any]]:
        """Discover available routes from an origin (like stairs moving)."""
        try:
            response = self.session.get(
                f"{self.base_url}/routes/discover",
                params={"origin": origin},
                timeout=10,
            )
            if response.status_code == 200:
                return response.model_dump_json()
        except requests.RequestException:
            pass
        return []

    def traverse_politely(self, route_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Traverse a route with polite request (authentication pattern)."""
        # Add "please" to demonstrate polite door pattern
        payload["please"] = True

        try:
            response = self.session.post(
                f"{self.base_url}/routes/{route_id}/traverse",
                json=payload,
                timeout=30,
            )
            return {
                "success": response.status_code == 200,
                "response": response.model_dump_json() if response.content else {},
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }


def create_hogwarts_topology() -> GrandStaircase:
    """Create a sample Hogwarts-inspired topology."""
    staircase = GrandStaircase()

    # Famous locations
    locations = [
        "great_hall",
        "gryffindor_tower",
        "slytherin_dungeon",
        "ravenclaw_tower",
        "hufflepuff_basement",
        "library",
        "astronomy_tower",
        "owlery",
        "hospital_wing",
        "room_of_requirement",
        "headmaster_office",
    ]

    # Create staircases (routes) between locations
    for i, origin in enumerate(locations):
        for j, dest in enumerate(locations):
            if i != j and random.random() < 0.3:  # 30% connectivity
                stair_id = f"stair_{origin}_{dest}"
                staircase.add_staircase(
                    Staircase(
                        id=stair_id,
                        origin=origin,
                        destination=dest,
                        has_vanishing_step=random.random() < 0.15,  # 15% have traps
                        requires_polite_request=random.random() < 0.1,  # 10% need politeness
                        day_behavior=random.choice(list(DayBehavior)),
                        move_probability=random.uniform(0.05, 0.2),
                    )
                )

    return staircase


# Reference card for I/O processes
REFERENCE_CARD = """
╔══════════════════════════════════════════════════════════════════╗
║           STAIRCASE INTELLIGENCE - REFERENCE CARD                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ANALOGIES: Literature → Software                                ║
║  ─────────────────────────────────────────────────────────────── ║
║  Moving Stairs      → Dynamic Route Tables                       ║
║  Vanishing Steps    → Circuit Breakers / Traps                   ║
║  Polite Doors       → Authentication Gates                       ║
║  Friday Redirect    → Time-Based Routing                         ║
║  142 Staircases     → Distributed Microservices                  ║
║  "Everything Moves" → Eventual Consistency                       ║
║                                                                  ║
║  STATES                                                          ║
║  ─────────────────────────────────────────────────────────────── ║
║  STABLE   → Route available and fixed                            ║
║  MOVING   → Route reconfiguring (retry later)                    ║
║  VANISHED → Circuit open (fallback required)                     ║
║  LOCKED   → Authentication required                              ║
║                                                                  ║
║  PATTERNS                                                        ║
║  ─────────────────────────────────────────────────────────────── ║
║  Local:  GrandStaircase() → In-memory routing with BFS           ║
║  Cloud:  StaircaseAPI()   → HTTP-based with requests             ║
║                                                                  ║
║  USAGE                                                           ║
║  ─────────────────────────────────────────────────────────────── ║
║  from grid.spark.staircase import GrandStaircase                 ║
║  stairs = create_hogwarts_topology()                             ║
║  route = stairs.find_route("great_hall", "library")              ║
║  moved = stairs.cycle()  # Autonomous movement                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


def print_reference_card():
    """Print the reference card."""
    print(REFERENCE_CARD)


__all__ = [
    "StaircaseState",
    "DayBehavior",
    "Staircase",
    "GrandStaircase",
    "StaircaseAPI",
    "create_hogwarts_topology",
    "print_reference_card",
    "REFERENCE_CARD",
]
