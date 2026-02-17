from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import numpy as np


class TemporalRelation(StrEnum):
    """Types of temporal relationships between events/facts."""

    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    OVERLAPS = "overlaps"
    CONTAINS = "contains"
    MEETS = "meets"
    STARTS = "starts"
    FINISHES = "finishes"


class CrossReferenceDomain(StrEnum):
    """Domains for cross-referencing in temporal reasoning."""

    TOPIC = "topic"
    SUBJECT = "subject"
    DOMAIN = "domain"
    PHENOMENON = "phenomenon"
    CONTEXT = "context"
    RELATION = "relation"


@dataclass
class TemporalFact:
    """Represents a single fact with temporal information."""

    subject: str
    predicate: str
    object: str
    timestamp: datetime
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def temporal_distance(self, other: "TemporalFact") -> float:
        """Calculate temporal distance between facts."""
        return abs((self.timestamp - other.timestamp).total_seconds())


@dataclass
class TemporalPath:
    """Represents a temporal path connecting facts through time."""

    facts: list[TemporalFact]
    relations: list[TemporalRelation]
    temporal_weight: float = 1.0
    path_confidence: float = 1.0

    @property
    def duration(self) -> timedelta:
        """Calculate total duration of the temporal path."""
        if len(self.facts) < 2:
            return timedelta(0)
        return self.facts[-1].timestamp - self.facts[0].timestamp

    def validate_temporal_consistency(self) -> bool:
        """Validate temporal consistency of the path."""
        for i in range(len(self.facts) - 1):
            if self.facts[i].timestamp > self.facts[i + 1].timestamp:
                return False
        return True


@dataclass
class CrossReference:
    """Represents cross-reference between temporal elements."""

    source_domain: CrossReferenceDomain
    target_domain: CrossReferenceDomain
    source_entity: str
    target_entity: str
    similarity_score: float
    temporal_alignment: float = 1.0
    contextual_relevance: float = 1.0


@dataclass
class TemporalReasoning:
    """
    Comprehensive temporal reasoning dataclass for neural network decision enhancement.

    Integrates temporal path processing, cross-referencing, and cognitive state management
    to improve decision accuracy in AI systems.
    """

    # Core temporal data
    temporal_facts: list[TemporalFact] = field(default_factory=list)
    temporal_paths: list[TemporalPath] = field(default_factory=list)
    cross_references: list[CrossReference] = field(default_factory=list)

    # Reasoning configuration
    history_window: timedelta = field(default_factory=lambda: timedelta(days=30))
    temporal_decay_factor: float = 0.8
    cross_reference_threshold: float = 0.7
    max_path_length: int = 10

    # Cognitive state tracking
    decision_confidence: float = 0.5
    temporal_consistency_score: float = 1.0
    cross_reference_coverage: float = 0.0

    # Metrics and monitoring
    reasoning_metrics: dict[str, Any] = field(default_factory=dict)
    processing_history: list[dict[str, Any]] = field(default_factory=list)

    def add_temporal_fact(self, fact: TemporalFact) -> None:
        """Add a temporal fact to the reasoning context."""
        self.temporal_facts.append(fact)
        self._update_temporal_consistency()

    def construct_temporal_paths(self, query_subject: str) -> list[TemporalPath]:
        """Construct temporal paths starting from query subject."""
        relevant_facts = [
            f
            for f in self.temporal_facts
            if f.subject == query_subject and datetime.now(UTC) - f.timestamp <= self.history_window
        ]

        paths = []
        for fact in relevant_facts:
            path = self._extend_temporal_path([fact])
            if path and len(path.facts) >= 2:
                paths.append(path)

        self.temporal_paths.extend(paths)
        return paths

    def _extend_temporal_path(self, current_path: list[TemporalFact]) -> TemporalPath | None:
        """Extend temporal path by finding connected facts."""
        if len(current_path) >= self.max_path_length:
            return None

        last_fact = current_path[-1]
        candidates = []

        for fact in self.temporal_facts:
            if fact not in current_path and fact.timestamp > last_fact.timestamp:
                temporal_distance = last_fact.temporal_distance(fact)
                decay_weight = self.temporal_decay_factor**temporal_distance
                candidates.append((fact, decay_weight))

        if not candidates:
            return None

        # Select best candidate based on temporal weight
        best_fact, weight = max(candidates, key=lambda x: x[1])

        extended_path = current_path + [best_fact]
        relation = self._infer_temporal_relation(last_fact, best_fact)

        return TemporalPath(
            facts=extended_path,
            relations=[relation],  # Simplified - would need full relation inference
            temporal_weight=weight,
            path_confidence=0.8,
        )

    def add_cross_reference(self, reference: CrossReference) -> None:
        """Add cross-reference between domains."""
        self.cross_references.append(reference)
        self._update_cross_reference_coverage()

    def perform_cross_referencing(
        self, source_domain: CrossReferenceDomain, target_domain: CrossReferenceDomain
    ) -> list[CrossReference]:
        """Generate cross-references between domains using temporal reasoning."""
        references = []

        # Find entities in source domain
        source_entities = set()
        for fact in self.temporal_facts:
            if source_domain == CrossReferenceDomain.SUBJECT:
                source_entities.add(fact.subject)
            elif source_domain == CrossReferenceDomain.TOPIC:
                source_entities.update(fact.metadata.get("topics", []))

        # Find entities in target domain
        target_entities = set()
        for fact in self.temporal_facts:
            if target_domain == CrossReferenceDomain.SUBJECT:
                target_entities.add(fact.subject)
            elif target_domain == CrossReferenceDomain.TOPIC:
                target_entities.update(fact.metadata.get("topics", []))

        # Generate cross-references based on temporal co-occurrence
        for source in source_entities:
            for target in target_entities:
                if source != target:
                    similarity = self._calculate_temporal_similarity(source, target)
                    if similarity >= self.cross_reference_threshold:
                        reference = CrossReference(
                            source_domain=source_domain,
                            target_domain=target_domain,
                            source_entity=source,
                            target_entity=target,
                            similarity_score=similarity,
                            temporal_alignment=self._calculate_temporal_alignment(source, target),
                        )
                        references.append(reference)
                        self.add_cross_reference(reference)

        return references

    def _calculate_temporal_similarity(self, entity1: str, entity2: str) -> float:
        """Calculate temporal similarity between entities."""
        entity1_timestamps = [
            f.timestamp
            for f in self.temporal_facts
            if entity1 in [f.subject, f.object] or entity1 in f.metadata.get("topics", [])
        ]
        entity2_timestamps = [
            f.timestamp
            for f in self.temporal_facts
            if entity2 in [f.subject, f.object] or entity2 in f.metadata.get("topics", [])
        ]

        if not entity1_timestamps or not entity2_timestamps:
            return 0.0

        # Calculate temporal overlap using Gaussian kernel
        similarities = []
        for t1 in entity1_timestamps:
            for t2 in entity2_timestamps:
                time_diff = abs((t1 - t2).total_seconds()) / (24 * 3600)  # days
                similarity = np.exp(-(time_diff**2) / 2)  # Gaussian decay
                similarities.append(similarity)

        return float(np.mean(similarities)) if similarities else 0.0

    def _calculate_temporal_alignment(self, entity1: str, entity2: str) -> float:
        """Calculate temporal alignment between entities."""
        # Simplified alignment calculation
        entity1_times = [f.timestamp for f in self.temporal_facts if entity1 in [f.subject, f.object]]
        entity2_times = [f.timestamp for f in self.temporal_facts if entity2 in [f.subject, f.object]]

        if not entity1_times or not entity2_times:
            return 0.0

        # Check for temporal patterns (simultaneous, sequential, etc.)
        alignment_score = 0.0
        for t1 in entity1_times:
            closest_t2 = min(entity2_times, key=lambda t2: abs((t1 - t2).total_seconds()))
            time_diff = abs((t1 - closest_t2).total_seconds())
            alignment_score += np.exp(-time_diff / (24 * 3600))  # Exponential decay

        return alignment_score / len(entity1_times)

    def _infer_temporal_relation(self, fact1: TemporalFact, fact2: TemporalFact) -> TemporalRelation:
        """Infer temporal relation between two facts."""
        if fact1.timestamp < fact2.timestamp:
            if (fact2.timestamp - fact1.timestamp) < timedelta(hours=1):
                return TemporalRelation.MEETS
            else:
                return TemporalRelation.BEFORE
        else:
            return TemporalRelation.AFTER

    def _update_temporal_consistency(self) -> None:
        """Update temporal consistency score."""
        if not self.temporal_paths:
            self.temporal_consistency_score = 1.0
            return

        consistent_paths = sum(1 for path in self.temporal_paths if path.validate_temporal_consistency())
        self.temporal_consistency_score = consistent_paths / len(self.temporal_paths)

    def _update_cross_reference_coverage(self) -> None:
        """Update cross-reference coverage metric."""
        if not self.cross_references:
            self.cross_reference_coverage = 0.0
            return

        # Calculate coverage as ratio of cross-referenced entities
        all_entities = set()
        for fact in self.temporal_facts:
            all_entities.add(fact.subject)
            all_entities.add(fact.object)

        referenced_entities = set()
        for ref in self.cross_references:
            referenced_entities.add(ref.source_entity)
            referenced_entities.add(ref.target_entity)

        self.cross_reference_coverage = len(referenced_entities) / len(all_entities) if all_entities else 0.0

    def get_decision_confidence(self, query: str) -> float:
        """Calculate decision confidence based on temporal reasoning."""
        # Base confidence from temporal facts
        relevant_facts = [f for f in self.temporal_facts if query in f.subject or query in f.predicate]

        if not relevant_facts:
            return 0.0

        # Factor in temporal recency, cross-references, and path consistency
        recency_factor = np.mean(
            [np.exp(-abs((f.timestamp - datetime.now(UTC)).total_seconds()) / (24 * 3600)) for f in relevant_facts]
        )

        cross_ref_factor = min(1.0, len(self.cross_references) / 10)  # Scale cross-refs
        consistency_factor = self.temporal_consistency_score

        confidence = recency_factor * 0.4 + cross_ref_factor * 0.3 + consistency_factor * 0.3

        self.decision_confidence = float(confidence)
        return confidence

    def record_processing_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Record processing event for monitoring."""
        event = {
            "timestamp": datetime.now(UTC),
            "event_type": event_type,
            "details": details,
            "metrics": {
                "temporal_facts_count": len(self.temporal_facts),
                "temporal_paths_count": len(self.temporal_paths),
                "cross_references_count": len(self.cross_references),
                "decision_confidence": self.decision_confidence,
                "temporal_consistency_score": self.temporal_consistency_score,
                "cross_reference_coverage": self.cross_reference_coverage,
            },
        }
        self.processing_history.append(event)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "temporal_facts_processed": len(self.temporal_facts),
            "temporal_paths_constructed": len(self.temporal_paths),
            "cross_references_generated": len(self.cross_references),
            "decision_confidence": self.decision_confidence,
            "temporal_consistency_score": self.temporal_consistency_score,
            "cross_reference_coverage": self.cross_reference_coverage,
            "average_path_length": np.mean([len(p.facts) for p in self.temporal_paths]) if self.temporal_paths else 0,
            "processing_events_count": len(self.processing_history),
        }
