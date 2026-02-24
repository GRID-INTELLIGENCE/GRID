"""Digital Round Table Protocol (DRTP) — Facilitator.

A standalone GRID feature governed by GRID's autonomy and structural +
environmental intelligence system.  The facilitator constructs a disciplined,
soulful environment where all parties hold equal standing — regardless of
whether a party is a person, a system, an object, or a concept.

The discussion is **topic-centric**: affiliations are stripped away so that
only transparent opinions and reasoning are placed on the table.  The
resulting output is a **Magnitudinal Compass** — a well-reasoned, calculated,
balanced directional vector for GRID's decision fabric.

Design heritage: modern adaptation of the Great Hall module, now fully
standalone and integral to GRID's intelligence layer.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from .grid_environment import GridEnvironment
from .roundtable_schemas import (
    DiscussionEntry,
    MagnitudinalCompass,
    Party,
    PartyRoster,
    RoundTableResult,
    TriadWeights,
)

if TYPE_CHECKING:
    from tools.rag.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_AMBIANCE_PROMPT = (
    "You are GRID's environmental intelligence system constructing the "
    "setting for a round-table discussion.\n\n"
    "Topic: '{topic}'\n\n"
    "Design a disciplined yet soulful digital environment for this "
    "discussion.  Describe the lighting, spatial arrangement, and overall "
    "mood.  The space must embody these principles:\n"
    "- Every seat is equal — no head of table, no hierarchy\n"
    "- The environment encourages transparency and honest reasoning\n"
    "- The mood is focused, deliberate, and respectful\n\n"
    "Keep it to two concise paragraphs."
)

_PARTY_PROMPT = (
    "You are GRID's structural intelligence system.\n\n"
    "Topic: {topic}\n\n"
    "Identify 4 diverse parties who must be at this round table.  A party "
    "can be a person, an organisation, a system component, a data entity, "
    "an object, or even an abstract concept — whatever is most relevant to "
    "the topic.  All parties hold EQUAL standing.\n\n"
    "Return ONLY a JSON object with a list of 'roles', where each role has:\n"
    '- "name" (string): party identifier\n'
    '- "kind" (string): one of "person", "organisation", "system", '
    '"data_entity", "object", "concept"\n'
    '- "title" (string): role or designation\n'
    '- "primary_goal" (string): what this party seeks from the discussion\n\n'
    "Do NOT include any text outside the JSON object."
)

_OPENING_STATEMENT_PROMPT = (
    "You are {name}, a {kind} serving as {title}.\n"
    "Your goal: {goal}\n"
    "Topic: {topic}\n"
    "Setting: {ambiance}\n\n"
    "Rules of the round table:\n"
    "- You hold equal standing with every other party\n"
    "- Focus on the topic, not on affiliations\n"
    "- Place transparent opinions and reasoning on the table\n\n"
    "Give your opening statement.  Be direct, substantive, and under "
    "200 words."
)

_COMPASS_PROMPT = (
    "You are GRID's autonomy system acting as a neutral moderator.\n\n"
    "Topic: '{topic}'\n\n"
    "Below is the full transcript of transparent statements from the "
    "round table:\n\n"
    "{transcript}\n\n"
    "Synthesise a Magnitudinal Compass — a fair, balanced, actionable "
    "directional output.  Consider the weight of every party's reasoning "
    "equally.\n\n"
    "Return ONLY a JSON object with:\n"
    '- "direction" (string): the synthesised directional statement\n'
    '- "reasoning" (string): how this direction was derived\n'
    '- "confidence" (float 0.0-1.0): confidence in this compass heading\n'
    '- "key_factors" (list of strings): primary factors that shaped it\n\n'
    "Do NOT include any text outside the JSON object."
)


class RoundTableFacilitator:
    """Facilitates a DRTP session — governed by GRID's autonomy system.

    The facilitator chains four phases:
    1. **Ambiance** — construct the environment
    2. **Parties** — infer who/what belongs at the table
    3. **Discussion** — collect transparent statements
    4. **Compass** — calculate the magnitudinal compass

    Example::

        from tools.rag.llm.gemini import GeminiLLM

        llm = GeminiLLM(model="gemini-2.5-flash-preview-09-2025")
        facilitator = RoundTableFacilitator(llm)
        result = facilitator.facilitate("GRID's directive compass")
        print(result.compass.direction)
    """

    def __init__(
        self,
        llm: BaseLLMProvider,
        environment: GridEnvironment | None = None,
    ) -> None:
        self._llm = llm
        self._env = environment or GridEnvironment()

    # ------------------------------------------------------------------
    # Phase 1: Ambiance
    # ------------------------------------------------------------------

    def setup_ambiance(self, topic: str) -> str:
        """Construct the round-table environment.

        The ambiance enforces equal standing and topic-centric focus.
        """
        prompt = _AMBIANCE_PROMPT.format(topic=topic)
        result = self._llm.generate(prompt)
        logger.info("Ambiance constructed for topic: %s", topic)
        return result

    # ------------------------------------------------------------------
    # Phase 2: Party inference
    # ------------------------------------------------------------------

    def infer_parties(self, topic: str) -> PartyRoster | None:
        """Infer which parties belong at this round table.

        Parties can be persons, systems, objects, concepts — anything
        with a stake in the topic.

        Returns:
            A ``PartyRoster`` or ``None`` if inference fails.
        """
        prompt = _PARTY_PROMPT.format(topic=topic)
        raw = self._llm.generate(prompt)
        return self._parse_roster(raw)

    @staticmethod
    def _parse_roster(raw: str) -> PartyRoster | None:
        """Parse LLM JSON into a ``PartyRoster``.

        Handles markdown fences and malformed output gracefully.
        """
        text = raw.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(line for line in lines if not line.strip().startswith("```"))

        try:
            data = json.loads(text)
            roles = [
                Party(
                    name=r.get("name", "Unknown"),
                    kind=r.get("kind", "person"),
                    title=r.get("title", "Participant"),
                    primary_goal=r.get("primary_goal", "Contribute"),
                )
                for r in data.get("roles", [])
            ]
            return PartyRoster(roles=roles)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Failed to parse party JSON: %s", exc)
            return None
        except Exception as exc:
            # Pydantic validation (e.g. fewer than 2 parties)
            logger.warning("Party roster validation failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Phase 3: Discussion
    # ------------------------------------------------------------------

    def simulate_discussion(
        self,
        topic: str,
        parties: PartyRoster,
        ambiance: str,
    ) -> list[DiscussionEntry]:
        """Collect transparent statements from every party.

        Each party speaks with equal standing;  focus is on the topic,
        not on affiliations.
        """
        entries: list[DiscussionEntry] = []
        for party in parties.roles:
            # Inject environmental nudge into prompt if engine shifted
            env_payload = self._env._generate_api_output()
            nudge = env_payload["system_instruction"]

            prompt = _OPENING_STATEMENT_PROMPT.format(
                name=party.name,
                kind=party.kind.value,
                title=party.title,
                goal=party.primary_goal,
                topic=topic,
                ambiance=ambiance,
            )
            # Prepend environmental constraint if non-default
            if self._env.get_shifts():
                prompt = f"{nudge}\n\n{prompt}"

            text = self._llm.generate(prompt)
            entries.append(DiscussionEntry(speaker=party.name, text=text))

            # Feed statement into the homeostatic sensor
            self._env.process_wave(text)
            logger.debug("Statement collected from %s", party.name)
        return entries

    # ------------------------------------------------------------------
    # Phase 4: Magnitudinal Compass
    # ------------------------------------------------------------------

    def calculate_compass(
        self,
        topic: str,
        history: list[DiscussionEntry],
    ) -> MagnitudinalCompass:
        """Calculate the magnitudinal compass from the discussion.

        Weighs every party's reasoning equally to produce a fair,
        balanced directional output.
        """
        transcript = "\n\n".join(f"**{entry.speaker}**: {entry.text}" for entry in history)
        prompt = _COMPASS_PROMPT.format(topic=topic, transcript=transcript)
        raw = self._llm.generate(prompt)
        return self._parse_compass(raw)

    @staticmethod
    def _parse_compass(raw: str) -> MagnitudinalCompass:
        """Parse LLM JSON into a ``MagnitudinalCompass``.

        Falls back to a plain-text compass on parse failure.
        """
        text = raw.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(line for line in lines if not line.strip().startswith("```"))

        try:
            data = json.loads(text)
            return MagnitudinalCompass(
                direction=data.get("direction", text),
                reasoning=data.get("reasoning", "Derived from discussion"),
                confidence=float(data.get("confidence", 1.0)),
                key_factors=data.get("key_factors", []),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            # Graceful fallback — use raw text as direction
            return MagnitudinalCompass(
                direction=text,
                reasoning="Raw synthesis (structured parsing failed)",
                confidence=0.5,
                key_factors=[],
            )

    # ------------------------------------------------------------------
    # Top-level orchestrator
    # ------------------------------------------------------------------

    def facilitate(self, topic: str) -> RoundTableResult:
        """Run the full DRTP session.

        Chains: ambiance → parties → discussion → compass.

        Args:
            topic: The matter to be discussed.

        Returns:
            A complete ``RoundTableResult`` with magnitudinal compass.
        """
        logger.info("=== Round Table Initiated: %s ===", topic)

        # Reset environment for clean session
        self._env.reset()

        ambiance = self.setup_ambiance(topic)
        roster = self.infer_parties(topic)

        if roster is None:
            logger.warning("No parties inferred — aborting session.")
            return RoundTableResult(
                topic=topic,
                ambiance=ambiance,
                parties=[],
                history=[],
                compass=MagnitudinalCompass(
                    direction="No direction — parties could not be inferred",
                    reasoning="The round table could not be convened",
                    confidence=0.0,
                    key_factors=[],
                ),
            )

        history = self.simulate_discussion(topic, roster, ambiance)
        compass = self.calculate_compass(topic, history)

        # Capture final environmental state
        weights = self._env.get_weights()
        triad = TriadWeights(
            practical=weights.get("practical", 0.0),
            legal=weights.get("legal", 0.0),
            psychological=weights.get("psychological", 0.0),
        )
        shifts = [
            {
                "trigger": s.trigger,
                "dominant": s.dominant_dimension,
                "temperature": s.temperature,
                "nudge": s.nudge,
            }
            for s in self._env.get_shifts()
        ]

        logger.info("=== Round Table Complete: %s ===", topic)
        return RoundTableResult(
            topic=topic,
            ambiance=ambiance,
            parties=roster.roles,
            history=history,
            compass=compass,
            triad_weights=triad,
            environmental_shifts=shifts,
        )
