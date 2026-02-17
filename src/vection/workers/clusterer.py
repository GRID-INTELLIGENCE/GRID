"""Clusterer Worker - Request stream clustering.

A background worker that groups similar events into clusters,
identifying behavioral patterns and common request types.
Clusters emerge from feature similarity without predefined rules.

Clustering Approaches:
- Feature-based: Similar event attributes
- Temporal: Events occurring in bursts
- Session-based: Patterns within sessions
- Cross-session: Patterns across users/sessions
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from vection.schemas.emergence_signal import EmergenceSignal, SignalType

logger = logging.getLogger(__name__)


class ClusterType(str, Enum):
    """Types of clusters detected."""

    FEATURE = "feature"  # Similar features
    TEMPORAL = "temporal"  # Temporal bursts
    SESSION = "session"  # Within-session patterns
    BEHAVIORAL = "behavioral"  # User behavior patterns
    TOPIC = "topic"  # Topic/content similarity


@dataclass
class ClusterMember:
    """A member of a cluster."""

    event_id: str
    timestamp: float
    session_id: str
    features: dict[str, Any]
    distance_to_centroid: float = 0.0


@dataclass
class Cluster:
    """A detected cluster of events."""

    cluster_id: str
    cluster_type: ClusterType
    label: str
    members: list[ClusterMember] = field(default_factory=list)
    centroid: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    stability_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Get cluster size."""
        return len(self.members)

    @property
    def age_seconds(self) -> float:
        """Get cluster age in seconds."""
        return time.time() - self.created_at

    @property
    def staleness_seconds(self) -> float:
        """Get time since last update."""
        return time.time() - self.last_updated

    @property
    def confidence(self) -> float:
        """Calculate cluster confidence based on size and stability."""
        size_factor = min(1.0, math.log1p(self.size) / 3.0)
        stability_factor = self.stability_score
        recency_factor = max(0.0, 1.0 - (self.staleness_seconds / 600.0))
        return size_factor * 0.4 + stability_factor * 0.4 + recency_factor * 0.2

    def add_member(self, member: ClusterMember) -> None:
        """Add a member to the cluster."""
        self.members.append(member)
        self.last_updated = time.time()
        self._update_centroid()
        self._update_stability()

        # Cap members
        if len(self.members) > 100:
            self.members = self.members[-100:]

    def _update_centroid(self) -> None:
        """Update centroid from members."""
        if not self.members:
            return

        # Aggregate feature counts
        feature_counts: dict[str, dict[Any, int]] = defaultdict(lambda: defaultdict(int))
        for member in self.members:
            for key, value in member.features.items():
                feature_counts[key][value] += 1

        # Centroid is most common value for each feature
        self.centroid = {key: max(values.items(), key=lambda x: x[1])[0] for key, values in feature_counts.items()}

    def _update_stability(self) -> None:
        """Update stability score."""
        if len(self.members) < 2:
            self.stability_score = 0.0
            return

        # Calculate average distance to centroid
        total_distance = sum(m.distance_to_centroid for m in self.members)
        avg_distance = total_distance / len(self.members)

        # Lower distance = higher stability (inverse)
        self.stability_score = max(0.0, 1.0 - avg_distance)

    def should_emit(self, min_size: int = 3, min_confidence: float = 0.5) -> bool:
        """Check if cluster should become a signal."""
        return self.size >= min_size and self.confidence >= min_confidence


@dataclass
class EventFeatures:
    """Extracted features from an event."""

    event_id: str
    timestamp: float
    session_id: str
    features: dict[str, Any]
    raw_data: dict[str, Any] = field(default_factory=dict)


class Clusterer:
    """Background worker for request stream clustering.

    Groups similar events into clusters, detecting behavioral
    patterns and common request types without predefined rules.

    Usage:
        clusterer = Clusterer()
        await clusterer.start()
        clusterer.observe(event_data, session_id)
        # ... later ...
        signals = clusterer.get_emitted_signals()
        await clusterer.stop()
    """

    def __init__(
        self,
        min_cluster_size: int = 3,
        confidence_threshold: float = 0.5,
        max_clusters: int = 100,
        similarity_threshold: float = 0.7,
        max_observations: int = 500,
        processing_interval: float = 10.0,
    ) -> None:
        """Initialize the clusterer worker.

        Args:
            min_cluster_size: Minimum members for a valid cluster.
            confidence_threshold: Threshold for emitting signals.
            max_clusters: Maximum clusters to maintain.
            similarity_threshold: Minimum similarity to join cluster.
            max_observations: Maximum observations to retain.
            processing_interval: Seconds between processing runs.
        """
        self._min_cluster_size = min_cluster_size
        self._confidence_threshold = confidence_threshold
        self._max_clusters = max_clusters
        self._similarity_threshold = similarity_threshold
        self._max_observations = max_observations
        self._processing_interval = processing_interval

        self._observations: deque[EventFeatures] = deque(maxlen=max_observations)
        self._clusters: dict[str, Cluster] = {}
        self._emitted_signals: deque[EmergenceSignal] = deque(maxlen=200)
        self._emitted_cluster_ids: set[str] = set()

        self._feature_vocabulary: dict[str, set[Any]] = defaultdict(set)
        self._session_clusters: dict[str, list[str]] = defaultdict(list)

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

        self._total_observations = 0
        self._total_clusters_found = 0
        self._started_at: datetime | None = None
        self._callbacks: list[Callable[[EmergenceSignal], None]] = []

        logger.info(
            f"Clusterer initialized: min_size={min_cluster_size}, "
            f"threshold={confidence_threshold}, similarity={similarity_threshold}"
        )

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def observation_count(self) -> int:
        """Get current observation count."""
        return len(self._observations)

    @property
    def cluster_count(self) -> int:
        """Get current cluster count."""
        return len(self._clusters)

    async def start(self) -> None:
        """Start the clusterer worker."""
        if self._running:
            logger.warning("Clusterer already running")
            return

        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._processing_loop())
        logger.info("Clusterer worker started")

    async def stop(self) -> None:
        """Stop the clusterer worker."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Clusterer worker stopped")

    def observe(
        self,
        event_data: dict[str, Any],
        session_id: str,
        event_id: str | None = None,
    ) -> None:
        """Observe an event for clustering.

        Args:
            event_data: Event data dictionary.
            session_id: Session identifier.
            event_id: Optional event identifier.
        """
        event_id = event_id or self._generate_event_id()
        features = self._extract_features(event_data)

        observation = EventFeatures(
            event_id=event_id,
            timestamp=time.time(),
            session_id=session_id,
            features=features,
            raw_data=event_data,
        )

        self._observations.append(observation)
        self._total_observations += 1

        # Update feature vocabulary
        for key, value in features.items():
            self._feature_vocabulary[key].add(value)

        # Immediate incremental clustering
        self._assign_to_cluster(observation)

        logger.debug(f"Observed event for clustering: {event_id} in session {session_id}")

    def on_cluster(self, callback: Callable[[EmergenceSignal], None]) -> None:
        """Register a callback for new cluster signals.

        Args:
            callback: Function called when cluster is detected.
        """
        self._callbacks.append(callback)

    def get_emitted_signals(self, limit: int = 50) -> list[EmergenceSignal]:
        """Get recently emitted cluster signals.

        Args:
            limit: Maximum signals to return.

        Returns:
            List of EmergenceSignal instances.
        """
        return list(self._emitted_signals)[-limit:]

    def get_clusters(self) -> list[dict[str, Any]]:
        """Get current clusters.

        Returns:
            List of cluster information dictionaries.
        """
        return [
            {
                "cluster_id": c.cluster_id,
                "type": c.cluster_type.value,
                "label": c.label,
                "size": c.size,
                "confidence": round(c.confidence, 3),
                "stability": round(c.stability_score, 3),
                "age_seconds": round(c.age_seconds, 1),
                "centroid": c.centroid,
            }
            for c in self._clusters.values()
        ]

    def get_cluster_by_id(self, cluster_id: str) -> Cluster | None:
        """Get a specific cluster by ID.

        Args:
            cluster_id: Cluster identifier.

        Returns:
            Cluster or None.
        """
        return self._clusters.get(cluster_id)

    def get_session_clusters(self, session_id: str) -> list[str]:
        """Get cluster IDs for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of cluster IDs.
        """
        return self._session_clusters.get(session_id, [])

    def get_stats(self) -> dict[str, Any]:
        """Get clusterer statistics.

        Returns:
            Dictionary with worker statistics.
        """
        return {
            "is_running": self._running,
            "total_observations": self._total_observations,
            "current_observations": len(self._observations),
            "clusters": len(self._clusters),
            "clusters_found": self._total_clusters_found,
            "emitted_signals": len(self._emitted_signals),
            "feature_dimensions": len(self._feature_vocabulary),
            "similarity_threshold": self._similarity_threshold,
            "uptime_seconds": ((datetime.now(timezone.utc) - self._started_at).total_seconds() if self._started_at else 0),
        }

    def reset(self) -> None:
        """Reset clusterer state."""
        self._observations.clear()
        self._clusters.clear()
        self._emitted_signals.clear()
        self._emitted_cluster_ids.clear()
        self._feature_vocabulary.clear()
        self._session_clusters.clear()
        self._total_observations = 0
        self._total_clusters_found = 0
        logger.info("Clusterer reset")

    # =========================================================================
    # Internal Processing
    # =========================================================================

    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                await asyncio.sleep(self._processing_interval)
                await self._process_clusters()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Clusterer processing error: {e}")

    async def _process_clusters(self) -> None:
        """Process and maintain clusters."""
        async with self._lock:
            # Recalculate cluster stability
            for cluster in self._clusters.values():
                cluster._update_stability()

            # Emit qualifying clusters
            await self._emit_clusters()

            # Decay and prune clusters
            await self._decay_clusters()

            # Merge similar clusters
            await self._merge_clusters()

    def _assign_to_cluster(self, observation: EventFeatures) -> None:
        """Assign observation to best-matching cluster or create new.

        Args:
            observation: Event features to cluster.
        """
        best_cluster: Cluster | None = None
        best_similarity = 0.0

        # Find best matching cluster
        for cluster in self._clusters.values():
            similarity = self._calculate_similarity(observation.features, cluster.centroid)
            if similarity > best_similarity and similarity >= self._similarity_threshold:
                best_similarity = similarity
                best_cluster = cluster

        if best_cluster:
            # Add to existing cluster
            member = ClusterMember(
                event_id=observation.event_id,
                timestamp=observation.timestamp,
                session_id=observation.session_id,
                features=observation.features,
                distance_to_centroid=1.0 - best_similarity,
            )
            best_cluster.add_member(member)

            # Track session-cluster association
            if best_cluster.cluster_id not in self._session_clusters[observation.session_id]:
                self._session_clusters[observation.session_id].append(best_cluster.cluster_id)
        else:
            # Create new cluster
            self._create_cluster(observation)

    def _create_cluster(self, observation: EventFeatures) -> Cluster:
        """Create a new cluster from an observation.

        Args:
            observation: Event features for cluster seed.

        Returns:
            New Cluster instance.
        """
        # Enforce max clusters
        if len(self._clusters) >= self._max_clusters:
            self._evict_weakest_cluster()

        cluster_id = self._generate_cluster_id(observation.features)
        label = self._generate_cluster_label(observation.features)
        cluster_type = self._infer_cluster_type(observation.features)

        cluster = Cluster(
            cluster_id=cluster_id,
            cluster_type=cluster_type,
            label=label,
            centroid=observation.features.copy(),
        )

        member = ClusterMember(
            event_id=observation.event_id,
            timestamp=observation.timestamp,
            session_id=observation.session_id,
            features=observation.features,
            distance_to_centroid=0.0,
        )
        cluster.add_member(member)

        self._clusters[cluster_id] = cluster
        self._session_clusters[observation.session_id].append(cluster_id)

        logger.debug(f"Created cluster: {cluster_id} ({label})")
        return cluster

    async def _emit_clusters(self) -> None:
        """Emit qualifying clusters as signals."""
        for cluster in self._clusters.values():
            if cluster.cluster_id in self._emitted_cluster_ids:
                continue

            if cluster.should_emit(self._min_cluster_size, self._confidence_threshold):
                signal = self._create_signal(cluster)
                self._emitted_signals.append(signal)
                self._emitted_cluster_ids.add(cluster.cluster_id)
                self._total_clusters_found += 1

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(signal)
                    except Exception as e:
                        logger.warning(f"Cluster callback error: {e}")

                logger.debug(f"Cluster detected: {cluster.label} (size={cluster.size}, conf={cluster.confidence:.2f})")

    async def _decay_clusters(self) -> None:
        """Decay and remove stale clusters."""
        to_remove = []

        for cluster_id, cluster in self._clusters.items():
            # Remove very stale clusters
            if cluster.staleness_seconds > 3600 and cluster.size < self._min_cluster_size:
                to_remove.append(cluster_id)
            # Remove low-confidence old clusters
            elif cluster.age_seconds > 1800 and cluster.confidence < 0.2:
                to_remove.append(cluster_id)

        for cluster_id in to_remove:
            del self._clusters[cluster_id]
            logger.debug(f"Removed stale cluster: {cluster_id}")

    async def _merge_clusters(self) -> None:
        """Merge highly similar clusters."""
        cluster_list = list(self._clusters.values())
        merged = set()

        for i, cluster_a in enumerate(cluster_list):
            if cluster_a.cluster_id in merged:
                continue

            for cluster_b in cluster_list[i + 1 :]:
                if cluster_b.cluster_id in merged:
                    continue

                similarity = self._calculate_similarity(cluster_a.centroid, cluster_b.centroid)
                if similarity > 0.9:  # Very high similarity threshold for merge
                    # Merge smaller into larger
                    if cluster_a.size >= cluster_b.size:
                        self._merge_into(cluster_b, cluster_a)
                        merged.add(cluster_b.cluster_id)
                    else:
                        self._merge_into(cluster_a, cluster_b)
                        merged.add(cluster_a.cluster_id)

        # Remove merged clusters
        for cluster_id in merged:
            if cluster_id in self._clusters:
                del self._clusters[cluster_id]

    def _merge_into(self, source: Cluster, target: Cluster) -> None:
        """Merge source cluster into target.

        Args:
            source: Cluster to merge from.
            target: Cluster to merge into.
        """
        for member in source.members:
            target.add_member(member)

        logger.debug(f"Merged cluster {source.cluster_id} into {target.cluster_id}")

    def _evict_weakest_cluster(self) -> None:
        """Evict the weakest cluster to make room."""
        if not self._clusters:
            return

        weakest_id = min(
            self._clusters.keys(),
            key=lambda cid: (
                self._clusters[cid].confidence,
                -self._clusters[cid].staleness_seconds,
            ),
        )

        del self._clusters[weakest_id]
        logger.debug(f"Evicted weak cluster: {weakest_id}")

    def _extract_features(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Extract clustering features from event data.

        Args:
            event_data: Event data dictionary.

        Returns:
            Feature dictionary.
        """
        features: dict[str, Any] = {}

        # Key fields to extract
        for key in ("action", "type", "intent", "topic", "category", "domain"):
            if key in event_data and event_data[key]:
                features[key] = str(event_data[key]).lower()

        # Extract keywords from content
        content = event_data.get("content") or event_data.get("query") or ""
        if isinstance(content, str) and content:
            words = [w.lower() for w in content.split() if len(w) > 4 and w.isalpha()]
            if words:
                features["keywords"] = tuple(sorted(words[:5]))

        return features

    def _calculate_similarity(
        self,
        features_a: dict[str, Any],
        features_b: dict[str, Any],
    ) -> float:
        """Calculate similarity between two feature sets.

        Args:
            features_a: First feature set.
            features_b: Second feature set.

        Returns:
            Similarity score (0.0 - 1.0).
        """
        if not features_a or not features_b:
            return 0.0

        all_keys = set(features_a.keys()) | set(features_b.keys())
        if not all_keys:
            return 0.0

        matches = 0
        total = len(all_keys)

        for key in all_keys:
            val_a = features_a.get(key)
            val_b = features_b.get(key)

            if val_a is None or val_b is None:
                continue

            if val_a == val_b:
                matches += 1
            elif isinstance(val_a, tuple) and isinstance(val_b, tuple):
                # Jaccard similarity for keyword tuples
                set_a = set(val_a)
                set_b = set(val_b)
                if set_a or set_b:
                    jaccard = len(set_a & set_b) / len(set_a | set_b)
                    matches += jaccard

        return matches / total if total > 0 else 0.0

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        hash_input = f"{time.time()}:{self._total_observations}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:10]

    def _generate_cluster_id(self, features: dict[str, Any]) -> str:
        """Generate a cluster ID from features."""
        feature_str = str(sorted(features.items()))
        hash_input = f"{feature_str}:{time.time()}"
        return f"cl_{hashlib.md5(hash_input.encode()).hexdigest()[:10]}"

    def _generate_cluster_label(self, features: dict[str, Any]) -> str:
        """Generate a human-readable cluster label."""
        parts = []

        if "action" in features:
            parts.append(f"action:{features['action']}")
        elif "type" in features:
            parts.append(f"type:{features['type']}")

        if "topic" in features:
            parts.append(f"topic:{features['topic']}")
        elif "keywords" in features and features["keywords"]:
            parts.append(f"keywords:{features['keywords'][0]}")

        return " + ".join(parts) if parts else "unknown_cluster"

    def _infer_cluster_type(self, features: dict[str, Any]) -> ClusterType:
        """Infer cluster type from features."""
        if "action" in features or "type" in features:
            return ClusterType.BEHAVIORAL
        if "topic" in features:
            return ClusterType.TOPIC
        if "keywords" in features:
            return ClusterType.FEATURE
        return ClusterType.FEATURE

    def _create_signal(self, cluster: Cluster) -> EmergenceSignal:
        """Create an EmergenceSignal from a cluster."""
        description = f"Cluster detected: {cluster.label} ({cluster.size} members)"

        # Get unique sessions in cluster
        sessions = set(m.session_id for m in cluster.members)

        return EmergenceSignal.create(
            signal_type=SignalType.CLUSTER,
            description=description,
            confidence=cluster.confidence,
            salience=min(0.9, cluster.confidence + 0.1),
            metadata={
                "cluster_type": cluster.cluster_type.value,
                "cluster_id": cluster.cluster_id,
                "size": cluster.size,
                "stability": cluster.stability_score,
                "centroid": cluster.centroid,
                "session_count": len(sessions),
            },
        )


# Module-level singleton
_clusterer: Clusterer | None = None


def get_clusterer() -> Clusterer:
    """Get the global clusterer instance.

    Returns:
        Clusterer singleton.
    """
    global _clusterer
    if _clusterer is None:
        _clusterer = Clusterer()
    return _clusterer
