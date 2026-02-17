"""Cognitive Unit: The smallest "honest slice" of attention.

As documented in docs/research/k1_cognitive_vectors.md

The Cognitive Unit represents a synchronized slice across all senses/inputs at a
specific moment in time. It's the fundamental unit for K1 geometric cognitive
vector analysis.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VisionComponent:
    """Visual component of a cognitive unit.

    Represents visual information through hue, luminance, and saturation.
    """

    hue: float = 0.0  # 0-1, color wheel position
    luminance: float = 0.5  # 0-1, brightness
    saturation: float = 0.5  # 0-1, color intensity

    def to_vector(self) -> np.ndarray:
        """Convert to 3D vector."""
        return np.array([self.hue, self.luminance, self.saturation], dtype=np.float32)


@dataclass
class SoundComponent:
    """Audio component of a cognitive unit.

    Represents auditory information through mel (pitch) and amplitude.
    """

    mel: float = 0.0  # 0-1, normalized mel frequency
    amplitude: float = 0.5  # 0-1, volume/intensity

    def to_vector(self) -> np.ndarray:
        """Convert to 2D vector."""
        return np.array([self.mel, self.amplitude], dtype=np.float32)


@dataclass
class LocomotionComponent:
    """Locomotion/movement component of a cognitive unit.

    Represents movement direction and speed through heading and velocity.
    """

    heading: float = 0.0  # 0-1, normalized heading (0-2π mapped to 0-1)
    speed: float = 0.0  # 0-1, normalized speed

    def to_vector(self) -> np.ndarray:
        """Convert to 2D vector."""
        return np.array([self.heading, self.speed], dtype=np.float32)


@dataclass
class CognitiveUnit:
    """A synchronized slice across senses/inputs.

    The Cognitive Unit is the fundamental unit for K1 analysis. It represents
    a momentary state of cognitive experience across multiple modalities.
    """

    # Multimodal components
    vision: VisionComponent = field(default_factory=VisionComponent)
    sound: SoundComponent = field(default_factory=SoundComponent)
    locomotion: LocomotionComponent = field(default_factory=LocomotionComponent)

    # Identification
    timestamp: datetime = field(default_factory=datetime.now)
    source_id: str = ""  # Origin of this cognitive unit
    window_id: str = ""  # Window/glimpse this unit belongs to

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_vector(self, vector_size: int = 32) -> np.ndarray:
        """Convert to fixed-length vector.

        Args:
            vector_size: Size of output vector (must be >= 7)

        Returns:
            Fixed-length numpy array representation
        """
        if vector_size < 7:
            raise ValueError("Vector size must be at least 7 for all components")

        # Concatenate component vectors
        components = np.concatenate(
            [
                self.vision.to_vector(),
                self.sound.to_vector(),
                self.locomotion.to_vector(),
            ]
        )

        # Pad or truncate to desired size
        if len(components) > vector_size:
            return components[:vector_size]
        else:
            result = np.zeros(vector_size, dtype=np.float32)
            result[: len(components)] = components
            return result

    def serialize(self) -> dict[str, Any]:
        """Serialize for storage/transmission.

        Returns:
            Dictionary representation
        """
        return {
            "vision": {
                "hue": self.vision.hue,
                "luminance": self.vision.luminance,
                "saturation": self.vision.saturation,
            },
            "sound": {
                "mel": self.sound.mel,
                "amplitude": self.sound.amplitude,
            },
            "locomotion": {
                "heading": self.locomotion.heading,
                "speed": self.locomotion.speed,
            },
            "timestamp": self.timestamp.isoformat(),
            "source_id": self.source_id,
            "window_id": self.window_id,
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> CognitiveUnit:
        """Deserialize from storage/transmission.

        Args:
            data: Dictionary representation

        Returns:
            CognitiveUnit instance
        """
        vision_data = data.get("vision", {})
        sound_data = data.get("sound", {})
        locomotion_data = data.get("locomotion", {})

        return cls(
            vision=VisionComponent(
                hue=vision_data.get("hue", 0.0),
                luminance=vision_data.get("luminance", 0.5),
                saturation=vision_data.get("saturation", 0.5),
            ),
            sound=SoundComponent(
                mel=sound_data.get("mel", 0.0),
                amplitude=sound_data.get("amplitude", 0.5),
            ),
            locomotion=LocomotionComponent(
                heading=locomotion_data.get("heading", 0.0),
                speed=locomotion_data.get("speed", 0.0),
            ),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            source_id=data.get("source_id", ""),
            window_id=data.get("window_id", ""),
            metadata=data.get("metadata", {}),
        )

    def distance_to(self, other: CognitiveUnit) -> float:
        """Calculate Euclidean distance to another unit.

        Args:
            other: Another cognitive unit

        Returns:
            Distance between units
        """
        v1 = self.to_vector()
        v2 = other.to_vector()
        return float(np.linalg.norm(v1 - v2))

    def similarity_to(self, other: CognitiveUnit) -> float:
        """Calculate cosine similarity to another unit.

        Args:
            other: Another cognitive unit

        Returns:
            Similarity score (0-1, 1 = identical)
        """
        v1 = self.to_vector()
        v2 = other.to_vector()

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


@dataclass
class CognitiveVector:
    """Geometric representation of a sequence of cognitive units.

    A CognitiveVector represents a trajectory through the cognitive space,
    capturing the evolution of cognitive state over time.
    """

    units: list[CognitiveUnit] = field(default_factory=list)

    # Computed properties
    _length: float | None = None
    _displacement: float | None = None
    _centroid: np.ndarray | None = None

    def add_unit(self, unit: CognitiveUnit) -> None:
        """Add a cognitive unit to this vector.

        Args:
            unit: Cognitive unit to add
        """
        self.units.append(unit)
        # Clear cached properties
        self._length = None
        self._displacement = None
        self._centroid = None

    def length(self) -> float:
        """Calculate total path length.

        Returns:
            Total length of the trajectory
        """
        if self._length is not None:
            return self._length

        if len(self.units) < 2:
            self._length = 0.0
            return self._length

        total = 0.0
        for i in range(1, len(self.units)):
            total += self.units[i].distance_to(self.units[i - 1])

        self._length = total
        return self._length

    def displacement(self) -> float:
        """Calculate net displacement from start to end.

        Returns:
            Net displacement
        """
        if self._displacement is not None:
            return self._displacement

        if len(self.units) < 2:
            self._displacement = 0.0
            return self._displacement

        self._displacement = self.units[-1].distance_to(self.units[0])
        return self._displacement

    def centroid(self) -> np.ndarray:
        """Calculate centroid of all unit vectors.

        Returns:
            Centroid vector
        """
        if self._centroid is not None:
            return self._centroid

        if not self.units:
            self._centroid = np.zeros(32, dtype=np.float32)
            return self._centroid

        vectors = np.array([u.to_vector() for u in self.units])
        self._centroid = np.mean(vectors, axis=0)
        return self._centroid

    def straightness(self) -> float:
        """Calculate how straight the trajectory is.

        Returns:
            Straightness ratio (displacement / length, 0-1)
        """
        length = self.length()
        if length == 0:
            return 1.0

        return self.displacement() / length

    def variance(self) -> float:
        """Calculate variance of positions from centroid.

        Returns:
            Variance measure
        """
        if not self.units:
            return 0.0

        centroid = self.centroid()
        vectors = np.array([u.to_vector() for u in self.units])

        return float(np.mean(np.sum((vectors - centroid) ** 2, axis=1)))

    def to_matrix(self) -> np.ndarray:
        """Convert to matrix for batch processing.

        Returns:
            Matrix with shape (len(units), 32)
        """
        return np.array([u.to_vector() for u in self.units], dtype=np.float32)

    def serialize(self) -> dict[str, Any]:
        """Serialize for storage.

        Returns:
            Dictionary representation
        """
        return {
            "units": [u.serialize() for u in self.units],
            "length": self.length(),
            "displacement": self.displacement(),
            "straightness": self.straightness(),
            "variance": self.variance(),
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> CognitiveVector:
        """Deserialize from storage.

        Args:
            data: Dictionary representation

        Returns:
            CognitiveVector instance
        """
        units = [CognitiveUnit.deserialize(u) for u in data.get("units", [])]
        return cls(units=units)


@dataclass
class Glimpse:
    """A temporal window of cognitive units.

    A Glimpse represents a bounded time slice containing multiple cognitive units.
    Multiple glimpses form a version of cognitive experience.
    """

    window_id: str
    units: list[CognitiveUnit] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    def __post_init__(self):
        """Initialize timestamps based on units."""
        if self.units and not self.start_time:
            self.start_time = min(u.timestamp for u in self.units)
        if self.units and not self.end_time:
            self.end_time = max(u.timestamp for u in self.units)

    def add_unit(self, unit: CognitiveUnit) -> None:
        """Add a unit to this glimpse.

        Args:
            unit: Cognitive unit to add
        """
        self.units.append(unit)
        unit.window_id = self.window_id

        if self.start_time is None or unit.timestamp < self.start_time:
            self.start_time = unit.timestamp
        if self.end_time is None or unit.timestamp > self.end_time:
            self.end_time = unit.timestamp

    def duration(self) -> float:
        """Get glimpse duration in seconds.

        Returns:
            Duration in seconds
        """
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_vector(self) -> CognitiveVector:
        """Convert glimpse to cognitive vector.

        Returns:
            CognitiveVector representation
        """
        return CognitiveVector(units=self.units.copy())


class CognitiveUnitFactory:
    """Factory for creating cognitive units from various inputs."""

    @staticmethod
    def from_sensor_data(
        vision_data: dict[str, float] | None = None,
        sound_data: dict[str, float] | None = None,
        locomotion_data: dict[str, float] | None = None,
        source_id: str = "",
        window_id: str = "",
    ) -> CognitiveUnit:
        """Create a cognitive unit from sensor data.

        Args:
            vision_data: Optional vision component data (hue, luminance, saturation)
            sound_data: Optional sound component data (mel, amplitude)
            locomotion_data: Optional locomotion component data (heading, speed)
            source_id: Origin of this unit
            window_id: Window this unit belongs to

        Returns:
            CognitiveUnit instance
        """
        vision_data = vision_data or {}
        sound_data = sound_data or {}
        locomotion_data = locomotion_data or {}

        return CognitiveUnit(
            vision=VisionComponent(
                hue=vision_data.get("hue", 0.0),
                luminance=vision_data.get("luminance", 0.5),
                saturation=vision_data.get("saturation", 0.5),
            ),
            sound=SoundComponent(
                mel=sound_data.get("mel", 0.0),
                amplitude=sound_data.get("amplitude", 0.5),
            ),
            locomotion=LocomotionComponent(
                heading=locomotion_data.get("heading", 0.0),
                speed=locomotion_data.get("speed", 0.0),
            ),
            source_id=source_id,
            window_id=window_id,
        )

    @staticmethod
    def from_array(array: np.ndarray, source_id: str = "", window_id: str = "") -> CognitiveUnit:
        """Create a cognitive unit from a numpy array.

        Args:
            array: Input array (must have at least 7 elements)
            source_id: Origin of this unit
            window_id: Window this unit belongs to

        Returns:
            CognitiveUnit instance
        """
        if len(array) < 7:
            raise ValueError("Array must have at least 7 elements")

        return CognitiveUnit(
            vision=VisionComponent(hue=float(array[0]), luminance=float(array[1]), saturation=float(array[2])),
            sound=SoundComponent(mel=float(array[3]), amplitude=float(array[4])),
            locomotion=LocomotionComponent(heading=float(array[5]), speed=float(array[6])),
            source_id=source_id,
            window_id=window_id,
        )

    @staticmethod
    def interpolate(unit1: CognitiveUnit, unit2: CognitiveUnit, alpha: float = 0.5) -> CognitiveUnit:
        """Interpolate between two cognitive units.

        Args:
            unit1: First cognitive unit
            unit2: Second cognitive unit
            alpha: Interpolation factor (0 = unit1, 1 = unit2)

        Returns:
            Interpolated cognitive unit
        """
        alpha = max(0.0, min(1.0, alpha))

        def interp_value(a: float, b: float) -> float:
            return a * (1 - alpha) + b * alpha

        return CognitiveUnit(
            vision=VisionComponent(
                hue=interp_value(unit1.vision.hue, unit2.vision.hue),
                luminance=interp_value(unit1.vision.luminance, unit2.vision.luminance),
                saturation=interp_value(unit1.vision.saturation, unit2.vision.saturation),
            ),
            sound=SoundComponent(
                mel=interp_value(unit1.sound.mel, unit2.sound.mel),
                amplitude=interp_value(unit1.sound.amplitude, unit2.sound.amplitude),
            ),
            locomotion=LocomotionComponent(
                heading=interp_value(unit1.locomotion.heading, unit2.locomotion.heading),
                speed=interp_value(unit1.locomotion.speed, unit2.locomotion.speed),
            ),
            source_id=f"interpolated:{unit1.source_id}:{unit2.source_id}",
            window_id=unit1.window_id or unit2.window_id,
        )


# Utility functions for K1 analysis
def detect_drift_apex(trajectory: list[LocomotionComponent]) -> tuple[float, float]:
    """Detect the furthest point from expected path.

    Args:
        trajectory: List of locomotion components

    Returns:
        Tuple of (drift_magnitude, apex_index)
    """
    if len(trajectory) < 2:
        return 0.0, 0.0

    # Create expected path (straight line from start to end)
    start = trajectory[0]
    end = trajectory[-1]

    # Find point with maximum perpendicular distance
    max_drift = 0.0
    apex_index = 0

    for i, point in enumerate(trajectory):
        # Convert heading to coordinates
        start_x = math.cos(start.heading * 2 * math.pi) * start.speed
        start_y = math.sin(start.heading * 2 * math.pi) * start.speed
        end_x = math.cos(end.heading * 2 * math.pi) * end.speed
        end_y = math.sin(end.heading * 2 * math.pi) * end.speed
        point_x = math.cos(point.heading * 2 * math.pi) * point.speed
        point_y = math.sin(point.heading * 2 * math.pi) * point.speed

        # Calculate perpendicular distance from line
        # Line from (start_x, start_y) to (end_x, end_y)
        dx = end_x - start_x
        dy = end_y - start_y

        if dx == 0 and dy == 0:
            drift = math.sqrt((point_x - start_x) ** 2 + (point_y - start_y) ** 2)
        else:
            # Perpendicular distance formula
            numerator = abs(dy * point_x - dx * point_y + end_x * start_y - end_y * start_x)
            denominator = math.sqrt(dx**2 + dy**2)
            drift = numerator / denominator

        if drift > max_drift:
            max_drift = drift
            apex_index = i

    return max_drift, apex_index


def apply_rdp_simplification(
    points: list[tuple[float, float]],
    epsilon: float = 0.05,
) -> list[tuple[float, float]]:
    """Apply Ramer-Douglas-Peucker simplification to reduce points.

    Args:
        points: List of (x, y) points
        epsilon: Simplification tolerance

    Returns:
        Simplified list of points
    """
    if len(points) <= 2:
        return points.copy()

    # Find the point with maximum distance from line
    start, end = points[0], points[-1]

    def perpendicular_distance(
        point: tuple[float, float], line_start: tuple[float, float], line_end: tuple[float, float]
    ) -> float:
        """Calculate perpendicular distance from point to line."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        return abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / math.sqrt(dx**2 + dy**2)

    # Find point with maximum distance
    max_dist = 0.0
    max_index = 0

    for i in range(1, len(points) - 1):
        dist = perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            max_index = i

    # If max distance is greater than epsilon, recursively simplify
    if max_dist > epsilon:
        left = apply_rdp_simplification(points[: max_index + 1], epsilon)
        right = apply_rdp_simplification(points[max_index:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]
