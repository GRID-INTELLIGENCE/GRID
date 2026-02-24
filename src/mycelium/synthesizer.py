"""
Synthesizer — Pattern recognition and complexity-to-simplicity engine.

Mission 2 of Mycelium: generalize keywords and highlights within a topic
that support explaining any complex information to any level of expertise.

This is the core engine. It takes text (documents, data, complex info)
and produces SynthesisResults — gists, highlights, layered explanations.

No external AI/LLM dependency. Uses statistical NLP heuristics:
  - Sentence scoring (position, keyword density, length)
  - Keyword extraction (TF-based with domain awareness)
  - Pattern recognition (structure, repetition, deviation)
  - Adaptive compression (persona-aware depth control)

Inspired by:
  - GRID's PatternRecognizer (recognize → analyze → recommend)
  - GRID's QueryCache (context hashing for staleness detection)
  - Mycelium's cave-symbol principle (compress meaning, not just length)
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass

from mycelium.core import (
    Depth,
    Highlight,
    HighlightPriority,
    PersonaProfile,
    SynthesisResult,
)

logger = logging.getLogger(__name__)

# Common English stop words — not worth highlighting
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "need", "must",
        "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
        "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
        "our", "their", "what", "which", "who", "whom", "where", "when", "why",
        "how", "all", "each", "every", "both", "few", "more", "most", "other",
        "some", "such", "no", "not", "only", "own", "same", "so", "than",
        "too", "very", "just", "about", "above", "after", "again", "also",
        "any", "because", "before", "between", "during", "if", "into", "then",
        "there", "through", "under", "until", "up", "while", "as", "over",
        "here", "out", "even", "new", "like", "well", "back", "way",
        "get", "got", "make", "made", "still", "much", "many", "since",
    }
)


@dataclass
class _SentenceScore:
    """Internal: a sentence with its computed relevance score."""

    text: str
    index: int
    score: float
    word_count: int
    keyword_density: float


class Synthesizer:
    """Pattern-recognizing text synthesizer.

    Takes complex text and produces accessible output adapted to the user's
    persona. Zero external dependencies. Pure Python heuristics.
    """

    def __init__(self, persona: PersonaProfile | None = None) -> None:
        self._persona = persona or PersonaProfile()

    @property
    def persona(self) -> PersonaProfile:
        return self._persona

    @persona.setter
    def persona(self, value: PersonaProfile) -> None:
        self._persona = value

    def synthesize(
        self,
        text: str,
        depth: Depth | None = None,
        max_highlights: int = 10,
    ) -> SynthesisResult:
        """Main entry point. Synthesize complex text into accessible output.

        Args:
            text: The source text to synthesize.
            depth: Override depth (otherwise uses persona's effective depth).
            max_highlights: Maximum number of keywords/highlights to extract.

        Returns:
            SynthesisResult with gist, highlights, summary, explanation, analogy.
        """
        if not text or not text.strip():
            return SynthesisResult(
                gist="(empty input)",
                source_length=0,
                compression_ratio=0.0,
            )

        effective_depth = depth or self._persona.effective_depth()
        sentences = self._split_sentences(text)
        words = self._tokenize(text)
        keywords = self._extract_keywords(words, max_highlights)
        highlights = self._build_highlights(keywords, text)
        scored_sentences = self._score_sentences(sentences, keywords)

        # Build layered output based on depth
        gist = self._build_gist(scored_sentences)
        summary = self._build_summary(scored_sentences, effective_depth)
        explanation = self._build_explanation(
            scored_sentences, highlights, effective_depth
        )
        analogy = self._build_analogy(keywords, effective_depth)
        patterns = self._detect_text_patterns(sentences, words)

        source_len = len(text)
        gist_len = len(gist)
        ratio = gist_len / source_len if source_len > 0 else 0.0

        return SynthesisResult(
            gist=gist,
            highlights=highlights,
            summary=summary,
            explanation=explanation,
            analogy=analogy,
            source_length=source_len,
            compression_ratio=ratio,
            depth_used=effective_depth,
            patterns_applied=patterns,
        )

    def extract_keywords(self, text: str, top_n: int = 10) -> list[Highlight]:
        """Extract keywords/highlights from text. Standalone utility."""
        words = self._tokenize(text)
        keywords = self._extract_keywords(words, top_n)
        return self._build_highlights(keywords, text)

    def summarize(self, text: str, sentence_count: int = 3) -> str:
        """Extract the N most important sentences. Standalone utility."""
        sentences = self._split_sentences(text)
        if len(sentences) <= sentence_count:
            return text

        words = self._tokenize(text)
        keywords = self._extract_keywords(words, 10)
        scored = self._score_sentences(sentences, keywords)
        top = sorted(scored, key=lambda s: s.score, reverse=True)[:sentence_count]
        # Preserve original order
        top.sort(key=lambda s: s.index)
        return " ".join(s.text for s in top)

    def simplify(self, text: str) -> str:
        """Reduce text to its absolute simplest form. ELI5 mode."""
        sentences = self._split_sentences(text)
        words = self._tokenize(text)
        keywords = self._extract_keywords(words, 5)
        scored = self._score_sentences(sentences, keywords)

        if not scored:
            return text[:200] if len(text) > 200 else text

        best = max(scored, key=lambda s: s.score)
        keyword_str = ", ".join(kw for kw, _ in keywords[:3])

        if self._persona.expertise in ("child", "beginner"):
            return f"{best.text} (Key ideas: {keyword_str})"
        return best.text

    # --- Sentence processing ---

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences. Handles common abbreviations."""
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())
        # Split on sentence-ending punctuation followed by space + uppercase
        raw = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        # Filter empty and very short fragments
        return [s.strip() for s in raw if len(s.strip()) > 10]

    def _score_sentences(
        self,
        sentences: list[str],
        keywords: list[tuple[str, int]],
    ) -> list[_SentenceScore]:
        """Score each sentence by relevance using multiple heuristics."""
        if not sentences:
            return []

        keyword_set = {kw.lower() for kw, _ in keywords}
        total = len(sentences)
        scored: list[_SentenceScore] = []

        for i, sentence in enumerate(sentences):
            words = self._tokenize(sentence)
            word_count = len(words)

            if word_count == 0:
                continue

            # 1. Position score: first and last sentences are usually important
            position_score = 0.0
            if i == 0:
                position_score = 1.0
            elif i == total - 1:
                position_score = 0.7
            elif i < total * 0.2:
                position_score = 0.5
            else:
                position_score = 0.2

            # 2. Keyword density: fraction of words that are keywords
            kw_count = sum(1 for w in words if w in keyword_set)
            keyword_density = kw_count / word_count if word_count > 0 else 0.0

            # 3. Length score: prefer medium-length sentences (not too short, not too long)
            length_score = 0.0
            if 10 <= word_count <= 30:
                length_score = 1.0
            elif word_count < 10:
                length_score = word_count / 10
            else:
                length_score = max(0.3, 1.0 - (word_count - 30) / 50)

            # 4. Signal words: sentences with definitions, conclusions, key transitions
            signal_score = 0.0
            lower_sent = sentence.lower()
            signal_phrases = [
                "in summary", "in conclusion", "the key", "most important",
                "this means", "in other words", "the main", "essentially",
                "the result", "therefore", "this shows", "defined as",
                "for example", "specifically", "the purpose", "the goal",
            ]
            for phrase in signal_phrases:
                if phrase in lower_sent:
                    signal_score = 0.8
                    break

            # Composite score
            score = (
                position_score * 0.25
                + keyword_density * 0.35
                + length_score * 0.15
                + signal_score * 0.25
            )

            scored.append(
                _SentenceScore(
                    text=sentence,
                    index=i,
                    score=score,
                    word_count=word_count,
                    keyword_density=keyword_density,
                )
            )

        return scored

    # --- Keyword extraction ---

    def _extract_keywords(
        self, words: list[str], top_n: int = 10
    ) -> list[tuple[str, int]]:
        """Extract top keywords by term frequency, excluding stop words."""
        # Filter stop words and very short words
        meaningful = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
        counts = Counter(meaningful)

        # Boost multi-occurrence words (they're more likely to be topical)
        boosted: dict[str, float] = {}
        for word, count in counts.items():
            boost = 1.0
            # Longer words tend to be more specific/meaningful
            if len(word) > 8:
                boost = 1.3
            elif len(word) > 5:
                boost = 1.1
            boosted[word] = count * boost

        sorted_kw = sorted(boosted.items(), key=lambda x: x[1], reverse=True)
        return [(word, int(score)) for word, score in sorted_kw[:top_n]]

    def _build_highlights(
        self, keywords: list[tuple[str, int]], source_text: str
    ) -> list[Highlight]:
        """Convert extracted keywords into Highlight objects with context."""
        highlights: list[Highlight] = []
        lower_source = source_text.lower()

        for rank, (word, score) in enumerate(keywords):
            # Find first occurrence position
            pos = lower_source.find(word.lower())

            # Extract surrounding context (±40 chars)
            context = ""
            if pos >= 0:
                start = max(0, pos - 40)
                end = min(len(source_text), pos + len(word) + 40)
                context = source_text[start:end].strip()
                if start > 0:
                    context = "..." + context
                if end < len(source_text):
                    context = context + "..."

            # Assign priority based on rank
            if rank < 3:
                priority = HighlightPriority.CRITICAL
            elif rank < 6:
                priority = HighlightPriority.HIGH
            elif rank < 8:
                priority = HighlightPriority.MEDIUM
            else:
                priority = HighlightPriority.LOW

            # Categorize keyword
            category = self._categorize_keyword(word)

            highlights.append(
                Highlight(
                    text=word,
                    priority=priority,
                    context=context,
                    category=category,
                    position=max(pos, 0),
                )
            )

        return highlights

    # --- Output builders ---

    def _build_gist(self, scored: list[_SentenceScore]) -> str:
        """Build the single most important sentence — the gist."""
        if not scored:
            return "(no content to summarize)"
        best = max(scored, key=lambda s: s.score)
        return best.text

    def _build_summary(
        self, scored: list[_SentenceScore], depth: Depth
    ) -> str:
        """Build a multi-sentence summary. Length depends on depth."""
        if not scored:
            return ""

        match depth:
            case Depth.ESPRESSO:
                n = min(2, len(scored))
            case Depth.AMERICANO:
                n = min(4, len(scored))
            case Depth.COLD_BREW:
                n = min(7, len(scored))

        top = sorted(scored, key=lambda s: s.score, reverse=True)[:n]
        top.sort(key=lambda s: s.index)  # preserve order
        return " ".join(s.text for s in top)

    def _build_explanation(
        self,
        scored: list[_SentenceScore],
        highlights: list[Highlight],
        depth: Depth,
    ) -> str:
        """Build an accessible explanation. Adapts to persona."""
        if not scored or depth == Depth.ESPRESSO:
            return ""

        parts: list[str] = []

        # Lead with key concepts
        critical_kw = [h.text for h in highlights if h.priority == HighlightPriority.CRITICAL]
        if critical_kw:
            parts.append(f"Key concepts: {', '.join(critical_kw)}.")

        # Add top sentences
        match depth:
            case Depth.AMERICANO:
                n = min(5, len(scored))
            case Depth.COLD_BREW:
                n = min(10, len(scored))
            case _:
                n = 3

        top = sorted(scored, key=lambda s: s.score, reverse=True)[:n]
        top.sort(key=lambda s: s.index)

        parts.extend(s.text for s in top)

        return " ".join(parts)

    def _build_analogy(
        self, keywords: list[tuple[str, int]], depth: Depth
    ) -> str:
        """Generate a simple analogy if possible. Uses geometric metaphors."""
        if depth == Depth.ESPRESSO or not keywords:
            return ""

        top_word = keywords[0][0] if keywords else ""
        kw_count = len(keywords)

        # Simple structural analogies based on keyword patterns
        if kw_count <= 3:
            return (
                f"Think of this like a triangle with three corners: "
                f"each keyword ({', '.join(k for k, _ in keywords[:3])}) "
                f"is one corner that holds the whole idea together."
            )
        elif kw_count <= 6:
            return (
                f"Picture a web with '{top_word}' at the center. "
                f"The other concepts connect to it like threads — "
                f"pull one and the others move too."
            )
        else:
            return (
                f"This topic is like a forest. '{top_word}' is the tallest tree "
                f"— the most visible idea. The other keywords are the surrounding "
                f"trees. Together they form the landscape of the subject."
            )

    # --- Pattern detection ---

    def _detect_text_patterns(
        self, sentences: list[str], words: list[str]
    ) -> list[str]:
        """Detect structural patterns in the text. Returns pattern names."""
        patterns: list[str] = []

        # Repetition: same words appearing frequently
        counts = Counter(w for w in words if w not in _STOP_WORDS and len(w) > 3)
        if counts and counts.most_common(1)[0][1] >= 3:
            patterns.append("repetition")

        # Rhythm: sentences of similar length (low variance)
        if len(sentences) >= 3:
            lengths = [len(s.split()) for s in sentences]
            mean_len = sum(lengths) / len(lengths)
            if mean_len > 0:
                variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
                cv = math.sqrt(variance) / mean_len if mean_len > 0 else 0
                if cv < 0.3:
                    patterns.append("rhythm")

        # Flow: text follows a logical progression (heuristic: connective words)
        connectives = {"therefore", "thus", "consequently", "because", "since",
                       "however", "moreover", "furthermore", "finally", "then",
                       "while", "when", "during", "through", "rather",
                       "described", "given", "following", "where"}
        connective_count = sum(1 for w in words if w in connectives)
        if connective_count >= 2:
            patterns.append("flow")

        # Deviation: presence of contrast/exception words
        contrasts = {"however", "but", "although", "despite", "except",
                     "unlike", "whereas", "nevertheless", "conversely"}
        contrast_count = sum(1 for w in words if w in contrasts)
        if contrast_count >= 2:
            patterns.append("deviation")

        # Spatial: structural/organizational language
        spatial_words = {"structure", "layer", "component", "architecture",
                         "framework", "hierarchy", "module", "system", "network"}
        spatial_count = sum(1 for w in words if w in spatial_words)
        if spatial_count >= 2:
            patterns.append("spatial")

        # Cause: causal language
        causal = {"causes", "leads", "results", "produces", "triggers",
                  "enables", "prevents", "affects", "influences", "determines"}
        causal_count = sum(1 for w in words if w in causal)
        if causal_count >= 2:
            patterns.append("cause")

        return patterns

    # --- Utilities ---

    @staticmethod
    def _categorize_keyword(word: str) -> str:
        """Heuristic keyword categorization."""
        lower = word.lower()

        # Check if it looks like an action (verbs often end in -ing, -tion, -ment)
        if lower.endswith(("ing", "tion", "ment", "ance", "ence")):
            return "action"
        # Check if it might be a concept (abstract nouns often end in -ity, -ism, -ness)
        if lower.endswith(("ity", "ism", "ness", "ology", "ance")):
            return "concept"
        # Check if capitalized (proper nouns, names)
        if word[0].isupper() and len(word) > 1:
            return "name"
        return "concept"

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple word tokenizer."""
        return [w.lower() for w in re.findall(r"[a-zA-Z]+", text) if len(w) > 1]
