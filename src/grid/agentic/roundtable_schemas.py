"""Schemas for the Digital Round Table Protocol (DRTP).

The DRTP is a standalone feature of GRID governed by GRID's autonomy and
structural + environmental intelligence system.  All parties at the table
hold equal standing — a party may be a person, an organisation, a system
component, a data entity, or any object with a stake in the topic.  The
protocol is topic-centric: affiliations are irrelevant, only transparent
reasoning and evidence placed on the table matter.

The final output is a **Magnitudinal Compass** — a calculated, balanced
directional output that encodes the collective reasoning into an actionable
vector for GRID's decision fabric.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PartyKind(StrEnum):
    """What kind of entity sits at the table."""

    PERSON = "person"
    ORGANISATION = "organisation"
    SYSTEM = "system"
    DATA_ENTITY = "data_entity"
    OBJECT = "object"
    CONCEPT = "concept"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class Party(BaseModel):
    """A participant at the round table.

    A party is *anything* with a stake in the topic — a human, a system
    component, an abstract concept, or a data entity.  All parties hold
    **equal standing**; no party is larger or smaller than another.
    """

    name: str = Field(..., description="Party identifier")
    kind: PartyKind = Field(
        default=PartyKind.PERSON,
        description="What kind of entity this party represents",
    )
    title: str = Field(..., description="Role or designation")
    primary_goal: str = Field(
        ..., description="What this party seeks from the discussion"
    )


class PartyRoster(BaseModel):
    """The inferred set of parties for a round-table session.

    The roster size is determined by the topic — GRID's intelligence
    decides how many parties are needed, though the default target is 4.
    """

    roles: list[Party] = Field(
        ...,
        min_length=2,
        description="Parties seated at the round table (minimum 2)",
    )


class DiscussionEntry(BaseModel):
    """A single transparent statement placed on the table."""

    speaker: str = Field(..., description="Name of the speaking party")
    text: str = Field(..., description="Transparent opinion or reasoning")


class MagnitudinalCompass(BaseModel):
    """The calculated directional output of the round table.

    This is the actionable conclusion — a balanced, reasoned vector
    distilled from every party's transparent input.  It can be consumed
    by other GRID subsystems as a decision compass.
    """

    direction: str = Field(
        ..., description="The synthesised directional statement"
    )
    reasoning: str = Field(
        ..., description="How the direction was derived from the discussion"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level of the compass (0.0–1.0)",
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Primary factors that shaped the direction",
    )


class TriadWeights(BaseModel):
    """Snapshot of the GRID triad balance at a point in time.

    Tracks how much the discussion leaned into each dimension.
    A perfectly balanced discussion has roughly equal weights.
    """

    practical: float = Field(default=0.0, ge=0.0, description="R-dimension weight")
    legal: float = Field(default=0.0, ge=0.0, description="Z-dimension weight")
    psychological: float = Field(default=0.0, ge=0.0, description="Ψ-dimension weight")


class RoundTableRequest(BaseModel):
    """Request to initiate a round-table session."""

    topic: str = Field(..., description="The matter to be discussed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "The directive magnitudinal compassing of GRID",
            }
        }
    )


class RoundTableResult(BaseModel):
    """Complete output of a facilitated round-table session.

    Contains the environment, all parties' transparent statements,
    and the resulting magnitudinal compass.
    """

    topic: str = Field(..., description="The discussed topic")
    ambiance: str = Field(
        ..., description="The constructed environment and setting"
    )
    parties: list[Party] = Field(
        ..., description="All parties who participated (equal standing)"
    )
    history: list[DiscussionEntry] = Field(
        default_factory=list,
        description="Ordered transcript of transparent statements",
    )
    compass: MagnitudinalCompass = Field(
        ..., description="The resulting magnitudinal compass"
    )
    triad_weights: TriadWeights = Field(
        default_factory=TriadWeights,
        description="Final GRID triad balance (Practical / Legal / Psychological)",
    )
    environmental_shifts: list[dict] = Field(
        default_factory=list,
        description="Audit trail of atmospheric recalibrations",
    )
    facilitated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 timestamp of facilitation",
    )
