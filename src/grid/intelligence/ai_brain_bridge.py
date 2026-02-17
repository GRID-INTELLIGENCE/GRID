"""
AI Brain Bridge Service - Phase 2 Implementation
Connects Knowledge Graph to Navigation with Spatial Reasoning
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import networkx as nx

from ..knowledge import PersistentJSONKnowledgeStore
from ..knowledge.graph_schema import EntityType
from ..knowledge.graph_store import Entity
from .brain import AIBrain

logger = logging.getLogger(__name__)


class NodeType(StrEnum):
    ENTITY = "entity"
    EVENT = "event"
    PATTERN = "pattern"
    SOUND = "sound"
    GEOMETRY = "geometry"
    SPATIAL = "spatial"
    NAVIGATION = "navigation"


class RelationType(StrEnum):
    CAUSES = "causes"
    ENHANCES = "enhances"
    INHIBITS = "inhibits"
    CONTAINS = "contains"
    CONNECTS_TO = "connects_to"
    SPATIAL_NEAR = "spatial_near"
    TEMPORAL_BEFORE = "temporal_before"


@dataclass
class KnowledgeNode:
    id: str
    type: NodeType
    attributes: dict[str, Any]
    relationships: list["Relationship"]
    confidence: float
    last_updated: datetime
    spatial_coords: tuple[float, float, float] | None = None


@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: RelationType
    strength: float
    context_tags: list[str]


@dataclass
class SpatialPattern:
    coordinates: list[tuple[float, float]]
    relationships: list[str]
    confidence: float
    pattern_type: str


@dataclass
class NavigationEnhancement:
    path_suggestions: list[list[tuple[float, float]]]
    spatial_insights: dict[str, Any]
    confidence_scores: list[float]
    reasoning_explanation: str


class KnowledgeGraphBridge:
    """Bridge between AI Brain and Navigation System"""

    def __init__(self, ai_brain: AIBrain) -> None:
        self.ai_brain = ai_brain
        self.graph = nx.DiGraph()
        self.spatial_index: dict[str, tuple[float, float]] = {}
        self.pattern_cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self.store = PersistentJSONKnowledgeStore(Path("dev/navigation_graph.json"))
        self._load_from_store()

    def _load_from_store(self) -> None:
        """Load persistent navigation nodes into memory"""
        self.store.connect()
        stats = self.store.get_graph_statistics()
        logger.info(f"Loading {stats['total_entities']} nodes from persistent store")

        for entity_id, entity in self.store.entities.items():
            if entity.entity_type == EntityType.CONTEXT or entity.entity_id.startswith("nav_"):
                # Hydrate spatial index and graph
                props = entity.properties
                coords = props.get("coords")
                if coords:
                    self.spatial_index[entity_id] = tuple(coords[:2])

                node = KnowledgeNode(
                    id=entity_id,
                    type=NodeType.NAVIGATION,
                    attributes=props.get("attributes", {}),
                    relationships=[],
                    confidence=props.get("confidence", 1.0),
                    last_updated=entity.updated_at,
                    spatial_coords=tuple(coords) if coords else None,
                )
                self.graph.add_node(entity_id, **node.__dict__)

    async def add_navigation_node(
        self, coords: tuple[float, float], nav_data: dict[str, Any], confidence: float = 1.0
    ) -> str:
        """Add navigation-related node to knowledge graph"""
        async with self._lock:
            node_id = f"nav_{coords[0]}_{coords[1]}"
            node = KnowledgeNode(
                id=node_id,
                type=NodeType.NAVIGATION,
                attributes=nav_data,
                relationships=[],
                confidence=confidence,
                last_updated=datetime.now(UTC),
                spatial_coords=(*coords, 0.0),  # Default z=0
            )

            self.graph.add_node(node_id, **node.__dict__)
            self.spatial_index[node_id] = coords

            # Persist to JSON store
            entity = Entity(
                entity_id=node_id,
                entity_type=EntityType.CONTEXT,  # Using Context for navigation points
                properties={
                    "id": node_id,
                    "name": f"Navigation Point at {coords}",
                    "coords": (*coords, 0.0),
                    "attributes": nav_data,
                    "confidence": confidence,
                },
                created_at=node.last_updated,
                updated_at=node.last_updated,
            )
            self.store.store_entity(entity)

            return node_id

    async def analyze_spatial_patterns(self, region: tuple[float, float, float, float]) -> list[SpatialPattern]:
        """Analyze spatial patterns in a given region"""
        x1, y1, x2, y2 = region

        # Find nodes in region
        region_nodes = []
        for node_id, coords in self.spatial_index.items():
            if x1 <= coords[0] <= x2 and y1 <= coords[1] <= y2:
                region_nodes.append(node_id)

        patterns: list[SpatialPattern] = []

        # Pattern 1: Clustering detection
        if len(region_nodes) >= 3:
            clusters = self._detect_clusters(region_nodes)
            for cluster in clusters:
                pattern = SpatialPattern(
                    coordinates=[self.spatial_index[nid] for nid in cluster],
                    relationships=self._get_relationships(cluster),
                    confidence=self._calculate_pattern_confidence(cluster),
                    pattern_type="cluster",
                )
                patterns.append(pattern)

        # Pattern 2: Path detection
        paths = self._detect_paths(region_nodes)
        for path in paths:
            pattern = SpatialPattern(
                coordinates=[self.spatial_index[nid] for nid in path],
                relationships=self._get_relationships(path),
                confidence=self._calculate_pattern_confidence(path),
                pattern_type="path",
            )
            patterns.append(pattern)

        return patterns

    async def enhance_navigation_with_ai(
        self, current_position: tuple[float, float], target_position: tuple[float, float], context: dict[str, Any]
    ) -> NavigationEnhancement:
        """Enhance navigation using AI reasoning"""

        # Get spatial patterns in relevant area
        region = (
            min(current_position[0], target_position[0]) - 5,
            min(current_position[1], target_position[1]) - 5,
            max(current_position[0], target_position[0]) + 5,
            max(current_position[1], target_position[1]) + 5,
        )

        patterns = await self.analyze_spatial_patterns(region)

        # Generate AI-enhanced path suggestions
        base_path = self._calculate_base_path(current_position, target_position)
        enhanced_paths: list[list[tuple[float, float]]] = []

        for pattern in patterns:
            if pattern.pattern_type == "path" and pattern.confidence > 0.7:
                # Use known high-confidence paths
                enhanced_path = self._integrate_pattern_with_path(base_path, pattern)
                enhanced_paths.append(enhanced_path)

        # If no good patterns found, use spatial reasoning
        if not enhanced_paths:
            enhanced_paths = [self._apply_spatial_reasoning(base_path, context)]

        # Calculate confidence scores
        confidence_scores: list[float] = []
        for path in enhanced_paths:
            confidence = self._calculate_path_confidence(path, patterns, context)
            confidence_scores.append(confidence)

        # Generate reasoning explanation
        explanation = self._generate_reasoning_explanation(patterns, enhanced_paths, context)

        return NavigationEnhancement(
            path_suggestions=enhanced_paths,
            spatial_insights={"patterns_detected": len(patterns), "region": region},
            confidence_scores=confidence_scores,
            reasoning_explanation=explanation,
        )

    def _detect_clusters(self, nodes: list[str]) -> list[list[str]]:
        """Detect clusters of nodes using spatial proximity"""
        clusters: list[list[str]] = []
        visited = set()

        for node_id in nodes:
            if node_id in visited:
                continue

            cluster = [node_id]
            visited.add(node_id)
            node_coords = self.spatial_index[node_id]

            # Find nearby nodes
            for other_id in nodes:
                if other_id in visited:
                    continue

                other_coords = self.spatial_index[other_id]
                distance = ((node_coords[0] - other_coords[0]) ** 2 + (node_coords[1] - other_coords[1]) ** 2) ** 0.5

                if distance < 3.0:  # Cluster threshold
                    cluster.append(other_id)
                    visited.add(other_id)

            if len(cluster) >= 2:
                clusters.append(cluster)

        return clusters

    def _detect_paths(self, nodes: list[str]) -> list[list[str]]:
        """Detect linear paths through nodes"""
        paths: list[list[str]] = []

        # Simple path detection: find sequences of connected nodes
        for start_node in nodes:
            path = [start_node]
            current = start_node
            visited = {start_node}

            while True:
                neighbors = self._get_spatial_neighbors(current, visited, nodes)
                if not neighbors:
                    break

                # Choose the most aligned neighbor
                next_node = self._choose_path_direction(current, neighbors, path)
                if next_node is None:
                    break

                path.append(next_node)
                visited.add(next_node)
                current = next_node

            if len(path) >= 3:
                paths.append(path)

        return paths

    def _get_spatial_neighbors(self, node: str, visited: set, candidates: list[str]) -> list[str]:
        """Get unvisited spatial neighbors of a node"""
        node_coords = self.spatial_index[node]
        neighbors: list[str] = []

        for candidate in candidates:
            if candidate in visited:
                continue

            cand_coords = self.spatial_index[candidate]
            distance = ((node_coords[0] - cand_coords[0]) ** 2 + (node_coords[1] - cand_coords[1]) ** 2) ** 0.5

            if distance < 2.0:  # Neighbor threshold
                neighbors.append(candidate)

        return neighbors

    def _choose_path_direction(self, current: str, neighbors: list[str], path: list[str]) -> str | None:
        """Choose the best next node for path continuation"""
        if len(path) == 1:
            return neighbors[0] if neighbors else None

        # Calculate path direction
        if len(path) >= 2:
            prev_coords = self.spatial_index[path[-2]]
            curr_coords = self.spatial_index[current]
            direction = (curr_coords[0] - prev_coords[0], curr_coords[1] - prev_coords[1])

            # Choose neighbor that best continues direction
            best_neighbor = None
            best_alignment = -1

            for neighbor in neighbors:
                next_coords = self.spatial_index[neighbor]
                next_direction = (next_coords[0] - curr_coords[0], next_coords[1] - curr_coords[1])

                # Calculate alignment (dot product normalized)
                alignment = direction[0] * next_direction[0] + direction[1] * next_direction[1]
                alignment /= (direction[0] ** 2 + direction[1] ** 2) ** 0.5 * (
                    next_direction[0] ** 2 + next_direction[1] ** 2
                ) ** 0.5 + 0.001

                if alignment > best_alignment:
                    best_alignment = alignment
                    best_neighbor = neighbor

            return best_neighbor

        return neighbors[0] if neighbors else None

    def _calculate_base_path(self, start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
        """Calculate basic straight-line path"""
        # Simple straight line path with intermediate points
        distance = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        steps = max(int(distance / 0.5), 2)  # Point every 0.5 units

        path: list[tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            path.append((x, y))

        return path

    def _integrate_pattern_with_path(
        self, base_path: list[tuple[float, float]], pattern: SpatialPattern
    ) -> list[tuple[float, float]]:
        """Integrate a known pattern into the base path"""
        # For now, return pattern coordinates if they connect start to end
        # In future, implement more sophisticated path integration
        return pattern.coordinates

    def _apply_spatial_reasoning(
        self, base_path: list[tuple[float, float]], context: dict[str, Any]
    ) -> list[tuple[float, float]]:
        """Apply spatial reasoning to enhance base path"""
        enhanced_path: list[tuple[float, float]] = []

        for point in base_path:
            # Add some spatial reasoning-based modifications
            # For now, keep the base path but this is where enhancement logic goes
            enhanced_path.append(point)

        return enhanced_path

    def _calculate_path_confidence(
        self, path: list[tuple[float, float]], patterns: list[SpatialPattern], context: dict[str, Any]
    ) -> float:
        """Calculate confidence score for a path"""
        base_confidence = 0.5  # Base confidence

        # Boost confidence if path aligns with known patterns
        for pattern in patterns:
            if pattern.confidence > 0.7:
                base_confidence += 0.2

        # Consider context factors
        if context.get("visibility", "good") == "good":
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _generate_reasoning_explanation(
        self, patterns: list[SpatialPattern], paths: list[list[tuple[float, float]]], context: dict[str, Any]
    ) -> str:
        """Generate explanation for the navigation enhancement"""
        explanation_parts = []

        if patterns:
            explanation_parts.append(f"Detected {len(patterns)} spatial patterns in region")

        if paths:
            explanation_parts.append(f"Generated {len(paths)} enhanced path options")

        if context:
            explanation_parts.append(f"Considered context: {list(context.keys())}")

        return "; ".join(explanation_parts) if explanation_parts else "Base navigation with AI enhancement"

    def _get_relationships(self, nodes: list[str]) -> list[str]:
        """Get relationships between nodes"""
        relationships: list[str] = []
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1 :]:
                if self.graph.has_edge(node1, node2):
                    relationships.append(f"{node1}->{node2}")
                elif self.graph.has_edge(node2, node1):
                    relationships.append(f"{node2}->{node1}")
        return relationships

    def _calculate_pattern_confidence(self, nodes: list[str]) -> float:
        """Calculate confidence score for a pattern"""
        if not nodes:
            return 0.0

        confidences: list[float] = []
        for node_id in nodes:
            if node_id in self.graph.nodes:
                node_data = self.graph.nodes[node_id]
                confidences.append(node_data.get("confidence", 0.5))

        return sum(confidences) / len(confidences) if confidences else 0.5


class AIBrainIntegration:
    """Main integration class for AI Brain with GRID systems"""

    def __init__(self) -> None:
        self.ai_brain = AIBrain()
        self.knowledge_bridge = KnowledgeGraphBridge(self.ai_brain)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the AI Brain integration"""
        if self._initialized:
            return

        # Create AI Brain session for navigation (stored for potential future use)
        _session = self.ai_brain.create_session(
            user_context={"purpose": "navigation_enhancement"},
            capabilities=["spatial_reasoning", "pattern_recognition", "path_optimization"],
        )

        self._initialized = True

    async def enhance_navigation(
        self,
        current_position: tuple[float, float],
        target_position: tuple[float, float],
        context: dict[str, Any] | None = None,
    ) -> NavigationEnhancement:
        """Main interface for navigation enhancement"""
        if not self._initialized:
            await self.initialize()

        context = context or {}
        return await self.knowledge_bridge.enhance_navigation_with_ai(current_position, target_position, context)

    async def add_navigation_data(self, coords: tuple[float, float], nav_data: dict[str, Any]) -> str:
        """Add navigation data to the knowledge graph"""
        if not self._initialized:
            await self.initialize()

        return await self.knowledge_bridge.add_navigation_node(coords, nav_data)
