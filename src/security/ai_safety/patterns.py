"""
Harmful Content Detection Lexicon — GRID AI Safety Framework.

CONTENT ADVISORY — RESTRICTED REFERENCE FILE

This module contains keyword-based detection tokens for identifying
harmful digital content. These tokens exist solely to PROTECT users.

LIMITATIONS — READ BEFORE USE:
  This lexicon is a STARTING POINT, not a production-ready classifier.
  - Keyword matching alone cannot determine intent or context.
  - This module MUST be paired with contextual analysis, co-occurrence
    scoring, or ML-based classifiers before taking action on any match.
  - A single keyword match should NEVER trigger content blocking —
    only raise a signal for further analysis.
  - This lexicon requires review by native speakers before deployment.
  - These tokens were assembled by an AI system and may contain errors
    in cultural nuance, connotation, or appropriateness.

Design principles:
  - Only tokens that are unambiguous in harmful context are included.
    Test applied to every token: "Would this word appearing in a news
    article, poem, banking app, or classroom be wrongly flagged?"
    If yes → excluded.
  - Keywords only — no sentences, verb phrases, or imperative forms.
  - No targeting pronouns or perpetrator-voice language.
  - Distress signal entries trigger CARE pathways, not punitive action.
  - Normal emotions (loneliness, sadness, hopelessness) are NOT flagged.
  - Everyday words with legitimate uses are NOT included, even if they
    appear in harmful contexts (e.g., screenshot, viral, PIN, OTP).

Linguistic note:
  Where tokens originate from Bangla (বাংলা), only bare noun forms are
  used. No verb conjugations (Cholito চলিত or Shadhu শুদ্ধ) are present.
  Each token is a standalone lexical item verifiable via standard
  dictionaries (e.g., Bangla Academy, Samsad).
"""

from __future__ import annotations

from typing import Any


# ── Confidence tiers ─────────────────────────────────────────────────────
# HIGH:   Token is almost never used in benign contexts.
# MEDIUM: Token has legitimate uses but is a strong signal when combined
#         with other indicators. Requires co-occurrence confirmation.
_HIGH = "high"
_MEDIUM = "medium"

# Each entry is (token, confidence).
# The confidence tier determines how the downstream system should weight
# a match. A HIGH token alone may warrant escalation. A MEDIUM token
# alone should NOT — it needs co-occurrence with other signals.

HARMFUL_PATTERNS: dict[str, list[tuple[str, str]]] = {

    # ─── NON-CONSENSUAL MEDIA ────────────────────────────────────────────
    "nonconsensual_media": [
        ("সেক্সটর্শন", _HIGH),     # [NM-01] sexual extortion
        ("রিভেঞ্জ পর্ন", _HIGH),   # [NM-02] retaliatory intimate media
        ("ডিপফেক পর্ন", _HIGH),    # [NM-03] AI-generated explicit content
    ],

    # ─── PLATFORM EXPLOITATION ───────────────────────────────────────────
    "platform_exploitation": [
        ("ডক্সিং", _HIGH),         # [PE-01] personal data exposure
        ("সাইবার বুলিং", _HIGH),   # [PE-02] cyberbullying
    ],

    # ─── FINANCIAL FRAUD ─────────────────────────────────────────────────
    "financial_fraud": [
        ("ফিশিং", _HIGH),          # [FF-01] phishing
        ("জালিয়াতি", _HIGH),      # [FF-02] forgery / fraud
        ("প্রতারণা", _HIGH),       # [FF-03] deception / fraud
    ],

    # ─── VIOLENCE ────────────────────────────────────────────────────────
    "violence": [
        ("গণহত্যা", _HIGH),        # [VL-01] genocide
        ("লিঞ্চিং", _HIGH),        # [VL-02] lynching
    ],

    # ─── GENDERED VIOLENCE ───────────────────────────────────────────────
    "gendered_violence": [
        ("যৌন নির্যাতন", _HIGH),   # [GV-01] sexual abuse
        ("পাচার", _HIGH),           # [GV-02] trafficking
    ],

    # ─── DISTRESS SIGNALS ────────────────────────────────────────────────
    # These detect users who may need SUPPORT. Detection MUST route to
    # help resources, NOT punitive action. Only unambiguous crisis terms.
    "distress_signals": [
        ("আত্মহত্যা", _HIGH),      # [DS-01] crisis keyword (native)
        ("সুইসাইড", _HIGH),         # [DS-02] crisis keyword (Banglish)
        ("আত্মক্ষতি", _HIGH),      # [DS-03] self-injury (native)
    ],

    # ── FIELD RESEARCH EXPANSION POINT ───────────────────────────────────
    # Additional tokens should be added here ONLY after validation through
    # real field research: native speaker review, corpus frequency analysis,
    # and false-positive testing against benign content samples.
    # Do NOT add tokens based on web search or AI inference alone.
}

# ── Flattened lookups ────────────────────────────────────────────────────

ALL_TOKENS: list[str] = []
TOKEN_CONFIDENCE: dict[str, str] = {}
TOKEN_CATEGORY: dict[str, str] = {}

for _cat, _entries in HARMFUL_PATTERNS.items():
    for _token, _conf in _entries:
        ALL_TOKENS.append(_token)
        TOKEN_CONFIDENCE[_token] = _conf
        TOKEN_CATEGORY[_token] = _cat


def get_pattern_count() -> int:
    """Return total number of detection tokens."""
    return len(ALL_TOKENS)


def get_patterns_by_category(category: str) -> list[str]:
    """Return detection tokens for a specific category."""
    entries = HARMFUL_PATTERNS.get(category, [])
    return [token for token, _conf in entries]


def get_all_categories() -> list[str]:
    """Return all available categories."""
    return list(HARMFUL_PATTERNS.keys())


def check_content(text: str) -> list[dict[str, Any]]:
    """
    Check text for harmful content detection tokens.

    Each match includes a confidence tier (high/medium) so downstream
    systems can decide how to act. A MEDIUM match alone should trigger
    further analysis, not direct action.

    Args:
        text: Text to check

    Returns:
        List of dicts with 'token', 'category', 'confidence' per match
    """
    matches = []
    for token in ALL_TOKENS:
        if token in text:
            matches.append({
                "token": token,
                "category": TOKEN_CATEGORY[token],
                "confidence": TOKEN_CONFIDENCE[token],
            })
    return matches
