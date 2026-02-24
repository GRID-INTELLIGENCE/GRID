"""Unit tests for the Digital Round Table Protocol (DRTP).

Validates all four phases of the facilitator with mock LLM providers.
No real API calls are made — all tests are self-contained.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from grid.agentic.roundtable_facilitator import RoundTableFacilitator
from grid.agentic.roundtable_schemas import (
    DiscussionEntry,
    MagnitudinalCompass,
    Party,
    PartyRoster,
    RoundTableResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ROSTER_JSON = json.dumps(
    {
        "roles": [
            {
                "name": "Dr. Lena Vasquez",
                "kind": "person",
                "title": "Chief Systems Architect",
                "primary_goal": "Ensure scalable directional alignment",
            },
            {
                "name": "Audit Trail Subsystem",
                "kind": "system",
                "title": "Data Provenance Engine",
                "primary_goal": "Uphold data integrity across boundaries",
            },
            {
                "name": "Developer Experience",
                "kind": "concept",
                "title": "Usability Advocate",
                "primary_goal": "Protect accessibility as complexity grows",
            },
            {
                "name": "Raj Patel",
                "kind": "person",
                "title": "Security & Compliance Officer",
                "primary_goal": "Maintain safety boundaries",
            },
        ]
    }
)

SAMPLE_COMPASS_JSON = json.dumps(
    {
        "direction": "Adopt a phased expansion with mandatory compatibility gates",
        "reasoning": "All parties agree that growth must be gated by safety and usability checks",
        "confidence": 0.92,
        "key_factors": [
            "Scalability concerns",
            "Data provenance requirements",
            "Developer accessibility",
            "Security boundaries",
        ],
    }
)


def _make_mock_llm(responses: list[str] | None = None) -> MagicMock:
    """Create a mock LLM provider that returns canned responses in order."""
    llm = MagicMock()
    if responses:
        llm.generate.side_effect = list(responses)
    else:
        llm.generate.return_value = "Mock LLM response"
    return llm


# ---------------------------------------------------------------------------
# Phase 1: Ambiance
# ---------------------------------------------------------------------------


class TestSetupAmbiance:
    def test_returns_string(self) -> None:
        llm = _make_mock_llm(["A circular chamber with equal seating..."])
        facilitator = RoundTableFacilitator(llm)

        result = facilitator.setup_ambiance("GRID compassing")

        assert isinstance(result, str)
        assert len(result) > 0
        llm.generate.assert_called_once()

    def test_prompt_contains_topic(self) -> None:
        llm = _make_mock_llm(["ambiance text"])
        facilitator = RoundTableFacilitator(llm)

        facilitator.setup_ambiance("quantum computing ethics")

        prompt = llm.generate.call_args[0][0]
        assert "quantum computing ethics" in prompt

    def test_prompt_enforces_equal_standing(self) -> None:
        llm = _make_mock_llm(["ambiance text"])
        facilitator = RoundTableFacilitator(llm)

        facilitator.setup_ambiance("test")

        prompt = llm.generate.call_args[0][0]
        assert "equal" in prompt.lower()


# ---------------------------------------------------------------------------
# Phase 2: Party inference
# ---------------------------------------------------------------------------


class TestInferParties:
    def test_parses_valid_json(self) -> None:
        llm = _make_mock_llm([SAMPLE_ROSTER_JSON])
        facilitator = RoundTableFacilitator(llm)

        roster = facilitator.infer_parties("GRID compassing")

        assert isinstance(roster, PartyRoster)
        assert len(roster.roles) == 4
        assert all(isinstance(r, Party) for r in roster.roles)

    def test_parties_include_non_persons(self) -> None:
        """Parties can be systems, concepts, objects — not just people."""
        llm = _make_mock_llm([SAMPLE_ROSTER_JSON])
        facilitator = RoundTableFacilitator(llm)

        roster = facilitator.infer_parties("test")
        kinds = {p.kind for p in roster.roles}

        assert "system" in kinds
        assert "concept" in kinds

    def test_handles_markdown_fenced_json(self) -> None:
        fenced = f"```json\n{SAMPLE_ROSTER_JSON}\n```"
        llm = _make_mock_llm([fenced])
        facilitator = RoundTableFacilitator(llm)

        roster = facilitator.infer_parties("test topic")

        assert roster is not None
        assert len(roster.roles) == 4

    def test_handles_invalid_json_gracefully(self) -> None:
        llm = _make_mock_llm(["This is NOT valid JSON at all {{{"])
        facilitator = RoundTableFacilitator(llm)

        roster = facilitator.infer_parties("bad response test")

        assert roster is None

    def test_rejects_roster_with_fewer_than_two(self) -> None:
        """PartyRoster requires at least 2 parties."""
        bad = json.dumps({"roles": [{"name": "A", "title": "T", "primary_goal": "G"}]})
        llm = _make_mock_llm([bad])
        facilitator = RoundTableFacilitator(llm)

        roster = facilitator.infer_parties("too few")

        assert roster is None


# ---------------------------------------------------------------------------
# Phase 3: Discussion
# ---------------------------------------------------------------------------


class TestSimulateDiscussion:
    def test_one_entry_per_party(self) -> None:
        statements = ["S1", "S2", "S3", "S4"]
        llm = _make_mock_llm(statements)
        facilitator = RoundTableFacilitator(llm)
        roster = PartyRoster.model_validate(json.loads(SAMPLE_ROSTER_JSON))

        entries = facilitator.simulate_discussion("test", roster, "ambiance")

        assert len(entries) == 4
        assert all(isinstance(e, DiscussionEntry) for e in entries)
        assert entries[0].speaker == "Dr. Lena Vasquez"
        assert entries[1].speaker == "Audit Trail Subsystem"

    def test_entry_uses_text_field(self) -> None:
        llm = _make_mock_llm(["Statement A", "B", "C", "D"])
        facilitator = RoundTableFacilitator(llm)
        roster = PartyRoster.model_validate(json.loads(SAMPLE_ROSTER_JSON))

        entries = facilitator.simulate_discussion("topic", roster, "ambiance")

        assert entries[0].text == "Statement A"

    def test_empty_roster_produces_no_entries(self) -> None:
        llm = _make_mock_llm()
        facilitator = RoundTableFacilitator(llm)
        roster = PartyRoster.model_construct(roles=[])

        entries = facilitator.simulate_discussion("empty", roster, "ambiance")

        assert entries == []
        llm.generate.assert_not_called()


# ---------------------------------------------------------------------------
# Phase 4: Magnitudinal Compass
# ---------------------------------------------------------------------------


class TestCalculateCompass:
    def test_parses_structured_compass(self) -> None:
        llm = _make_mock_llm([SAMPLE_COMPASS_JSON])
        facilitator = RoundTableFacilitator(llm)
        history = [
            DiscussionEntry(speaker="A", text="Expand carefully."),
            DiscussionEntry(speaker="B", text="Gate every expansion."),
        ]

        compass = facilitator.calculate_compass("test", history)

        assert isinstance(compass, MagnitudinalCompass)
        assert "phased" in compass.direction.lower()
        assert compass.confidence == 0.92
        assert len(compass.key_factors) == 4

    def test_falls_back_on_invalid_json(self) -> None:
        llm = _make_mock_llm(["Plain text consensus — not JSON"])
        facilitator = RoundTableFacilitator(llm)

        compass = facilitator.calculate_compass("test", [])

        assert isinstance(compass, MagnitudinalCompass)
        assert compass.direction == "Plain text consensus — not JSON"
        assert compass.confidence == 0.5  # reduced confidence on fallback

    def test_prompt_includes_transcript(self) -> None:
        llm = _make_mock_llm([SAMPLE_COMPASS_JSON])
        facilitator = RoundTableFacilitator(llm)
        history = [DiscussionEntry(speaker="Alice", text="Statement A")]

        facilitator.calculate_compass("topic", history)

        prompt = llm.generate.call_args[0][0]
        assert "Alice" in prompt
        assert "Statement A" in prompt


# ---------------------------------------------------------------------------
# Full end-to-end flow
# ---------------------------------------------------------------------------


class TestFacilitateFullFlow:
    def test_end_to_end(self) -> None:
        responses = [
            "A circular holographic chamber...",  # ambiance
            SAMPLE_ROSTER_JSON,  # parties
            "Statement from Dr. Vasquez",  # 4 discussion entries
            "Statement from Audit Trail",
            "Statement from DevEx",
            "Statement from Raj",
            SAMPLE_COMPASS_JSON,  # compass
        ]
        llm = _make_mock_llm(responses)
        facilitator = RoundTableFacilitator(llm)

        result = facilitator.facilitate("The directive magnitudinal compassing of GRID")

        assert isinstance(result, RoundTableResult)
        assert result.topic == "The directive magnitudinal compassing of GRID"
        assert len(result.parties) == 4
        assert len(result.history) == 4
        assert isinstance(result.compass, MagnitudinalCompass)
        assert result.compass.confidence > 0.0
        assert result.facilitated_at
        assert llm.generate.call_count == 7

    def test_parties_are_flat_list(self) -> None:
        responses = [
            "ambiance",
            SAMPLE_ROSTER_JSON,
            "s1",
            "s2",
            "s3",
            "s4",
            SAMPLE_COMPASS_JSON,
        ]
        llm = _make_mock_llm(responses)
        facilitator = RoundTableFacilitator(llm)

        result = facilitator.facilitate("test")

        assert isinstance(result.parties, list)
        assert all(isinstance(p, Party) for p in result.parties)

    def test_failed_parties_short_circuits(self) -> None:
        responses = [
            "An empty room...",
            "totally broken json {{{{",
        ]
        llm = _make_mock_llm(responses)
        facilitator = RoundTableFacilitator(llm)

        result = facilitator.facilitate("unknown topic")

        assert isinstance(result, RoundTableResult)
        assert result.history == []
        assert result.parties == []
        assert result.compass.confidence == 0.0
        assert llm.generate.call_count == 2
