"""
Evidence Extractor for Intelligent RAG Reasoning Layer.

This module extracts structured evidence (facts, claims, code snippets) from
retrieved chunks, maintaining source attribution for chain-of-thought reasoning.

Part of Phase 3: Reasoning Layer
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Classification of evidence types found in chunks."""

    DEFINITION = "definition"  # Defines what something is
    IMPLEMENTATION = "implementation"  # Shows how something works (code)
    EXAMPLE = "example"  # Usage example or demonstration
    REFERENCE = "reference"  # Cross-reference to another location
    CONFIGURATION = "configuration"  # Config values, settings
    ASSERTION = "assertion"  # Claims or statements of fact
    PROCEDURE = "procedure"  # Step-by-step instructions
    METADATA = "metadata"  # File paths, versions, dates
    UNKNOWN = "unknown"


class EvidenceStrength(Enum):
    """How strongly the evidence supports the query."""

    STRONG = "strong"  # Directly answers the query
    MODERATE = "moderate"  # Partially relevant
    WEAK = "weak"  # Tangentially related
    CONTRADICTORY = "contradictory"  # Conflicts with other evidence


@dataclass
class Evidence:
    """A single piece of extracted evidence with full provenance."""

    id: str  # Unique identifier for this evidence
    content: str  # The actual evidence text
    evidence_type: EvidenceType
    strength: EvidenceStrength
    confidence: float  # 0.0 to 1.0

    # Source attribution
    source_chunk_id: str
    source_file: str
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None

    # Context
    surrounding_context: str = ""  # Text around the evidence
    is_code: bool = False
    code_language: Optional[str] = None

    # Relationships
    supports_claims: List[str] = field(default_factory=list)
    contradicts_claims: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)  # Other files/symbols referenced

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.evidence_type.value,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "source": {
                "chunk_id": self.source_chunk_id,
                "file": self.source_file,
                "lines": (f"{self.source_line_start}-{self.source_line_end}" if self.source_line_start else None),
            },
            "is_code": self.is_code,
            "code_language": self.code_language,
            "references": self.references,
        }

    def citation(self) -> str:
        """Generate a citation string for this evidence."""
        if self.source_line_start:
            return f"[{self.source_file}:{self.source_line_start}]"
        return f"[{self.source_file}]"


@dataclass
class EvidenceSet:
    """Collection of evidence extracted from retrieval results."""

    query: str
    evidence: List[Evidence]
    total_chunks_processed: int
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def strong_evidence(self) -> List[Evidence]:
        """Get only strong evidence."""
        return [e for e in self.evidence if e.strength == EvidenceStrength.STRONG]

    @property
    def by_type(self) -> Dict[EvidenceType, List[Evidence]]:
        """Group evidence by type."""
        result: Dict[EvidenceType, List[Evidence]] = {}
        for e in self.evidence:
            if e.evidence_type not in result:
                result[e.evidence_type] = []
            result[e.evidence_type].append(e)
        return result

    @property
    def by_source(self) -> Dict[str, List[Evidence]]:
        """Group evidence by source file."""
        result: Dict[str, List[Evidence]] = {}
        for e in self.evidence:
            if e.source_file not in result:
                result[e.source_file] = []
            result[e.source_file].append(e)
        return result

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence across all evidence."""
        if not self.evidence:
            return 0.0
        return sum(e.confidence for e in self.evidence) / len(self.evidence)

    @property
    def has_contradictions(self) -> bool:
        """Check if there are contradictory evidence pieces."""
        return any(e.strength == EvidenceStrength.CONTRADICTORY for e in self.evidence)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "evidence_count": len(self.evidence),
            "strong_count": len(self.strong_evidence),
            "average_confidence": self.average_confidence,
            "has_contradictions": self.has_contradictions,
            "evidence": [e.to_dict() for e in self.evidence],
            "by_type": {k.value: len(v) for k, v in self.by_type.items()},
            "sources": list(self.by_source.keys()),
        }


class EvidenceExtractor:
    """
    Extracts structured evidence from retrieved chunks.

    This is the first stage of the reasoning layer - it transforms raw
    retrieved text into discrete, attributable facts that can be reasoned over.
    """

    # Patterns for identifying evidence types
    DEFINITION_PATTERNS = [
        r"^#+\s+(?:What is|Definition|Overview)",
        r"(?:is|are)\s+(?:a|an|the)\s+\w+",
        r"^[A-Z][a-z]+\s+(?:is|are)\s+",
        r"refers to",
        r"defined as",
        r"means that",
    ]

    IMPLEMENTATION_PATTERNS = [
        r"```[\w]*\n",  # Code blocks
        r"def\s+\w+\s*\(",  # Python functions
        r"class\s+\w+",  # Class definitions
        r"async\s+def",
        r"@\w+",  # Decorators
        r"import\s+",
        r"from\s+\w+\s+import",
    ]

    EXAMPLE_PATTERNS = [
        r"(?:for\s+)?example",
        r"e\.g\.",
        r"such as",
        r"like this",
        r"here's how",
        r"usage:",
        r"```.*example",
    ]

    PROCEDURE_PATTERNS = [
        r"^\d+\.\s+",  # Numbered lists
        r"^-\s+",  # Bullet points
        r"first,?\s+",
        r"then,?\s+",
        r"finally,?\s+",
        r"step\s+\d+",
        r"how to",
    ]

    REFERENCE_PATTERNS = [
        r"see\s+(?:also\s+)?[`\[]",
        r"refer(?:s|ence)?\s+to",
        r"documented\s+(?:in|at)",
        r"\[.*\]\(.*\)",  # Markdown links
        r"from\s+[\w.]+\s+import",  # Python imports
    ]

    def __init__(self, min_evidence_length: int = 20, max_evidence_length: int = 500):
        """
        Initialize the evidence extractor.

        Args:
            min_evidence_length: Minimum characters for a valid evidence piece
            max_evidence_length: Maximum characters before truncation
        """
        self.min_evidence_length = min_evidence_length
        self.max_evidence_length = max_evidence_length

        # Compile patterns for efficiency
        self._compiled_patterns: Dict[EvidenceType, List[re.Pattern]] = {
            EvidenceType.DEFINITION: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.DEFINITION_PATTERNS],
            EvidenceType.IMPLEMENTATION: [re.compile(p, re.MULTILINE) for p in self.IMPLEMENTATION_PATTERNS],
            EvidenceType.EXAMPLE: [re.compile(p, re.IGNORECASE) for p in self.EXAMPLE_PATTERNS],
            EvidenceType.PROCEDURE: [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.PROCEDURE_PATTERNS],
            EvidenceType.REFERENCE: [re.compile(p, re.IGNORECASE) for p in self.REFERENCE_PATTERNS],
        }

        logger.info("EvidenceExtractor initialized.")

    def extract(
        self,
        query: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        distances: Optional[List[float]] = None,
    ) -> EvidenceSet:
        """
        Extract evidence from retrieved documents.

        Args:
            query: The original query
            documents: List of retrieved document texts
            metadatas: List of metadata dicts for each document
            ids: List of chunk IDs
            distances: Optional similarity distances

        Returns:
            EvidenceSet containing all extracted evidence
        """
        all_evidence: List[Evidence] = []
        query_terms = self._extract_query_terms(query)

        for i, (doc, meta, chunk_id) in enumerate(zip(documents, metadatas, ids)):
            distance = distances[i] if distances else 0.5
            source_file = meta.get("source", meta.get("file_path", "unknown"))

            # Extract evidence pieces from this chunk
            chunk_evidence = self._extract_from_chunk(
                chunk_text=doc,
                chunk_id=chunk_id,
                source_file=source_file,
                metadata=meta,
                query_terms=query_terms,
                base_relevance=1.0 - distance,  # Convert distance to relevance
            )

            all_evidence.extend(chunk_evidence)

        # Deduplicate and merge similar evidence
        deduplicated = self._deduplicate_evidence(all_evidence)

        # Detect contradictions
        self._detect_contradictions(deduplicated)

        # Sort by confidence
        deduplicated.sort(key=lambda e: e.confidence, reverse=True)

        return EvidenceSet(
            query=query,
            evidence=deduplicated,
            total_chunks_processed=len(documents),
            extraction_metadata={
                "query_terms": query_terms,
                "evidence_types_found": list(set(e.evidence_type.value for e in deduplicated)),
            },
        )

    def _extract_from_chunk(
        self,
        chunk_text: str,
        chunk_id: str,
        source_file: str,
        metadata: Dict[str, Any],
        query_terms: List[str],
        base_relevance: float,
    ) -> List[Evidence]:
        """Extract evidence pieces from a single chunk."""
        evidence_list: List[Evidence] = []

        # Split into segments (paragraphs, code blocks, etc.)
        segments = self._segment_chunk(chunk_text)

        for segment_idx, (segment_text, is_code, code_lang) in enumerate(segments):
            if len(segment_text.strip()) < self.min_evidence_length:
                continue

            # Determine evidence type
            evidence_type = self._classify_evidence_type(segment_text, is_code)

            # Calculate relevance to query
            term_overlap = self._calculate_term_overlap(segment_text, query_terms)
            confidence = min(1.0, base_relevance * 0.6 + term_overlap * 0.4)

            # Determine strength based on confidence and type
            strength = self._determine_strength(confidence, evidence_type, term_overlap)

            # Extract references from the segment
            references = self._extract_references(segment_text)

            # Get line numbers if available
            line_start = metadata.get("line_start")
            line_end = metadata.get("line_end")

            # Generate unique ID
            evidence_id = self._generate_evidence_id(chunk_id, segment_idx, segment_text)

            # Truncate if too long
            content = segment_text
            if len(content) > self.max_evidence_length:
                content = content[: self.max_evidence_length] + "..."

            evidence = Evidence(
                id=evidence_id,
                content=content,
                evidence_type=evidence_type,
                strength=strength,
                confidence=confidence,
                source_chunk_id=chunk_id,
                source_file=source_file,
                source_line_start=line_start,
                source_line_end=line_end,
                surrounding_context=chunk_text[:200] if len(chunk_text) > len(segment_text) else "",
                is_code=is_code,
                code_language=code_lang,
                references=references,
            )

            evidence_list.append(evidence)

        return evidence_list

    def _segment_chunk(self, text: str) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Split chunk into segments (prose paragraphs, code blocks).

        Returns list of (text, is_code, language) tuples.
        """
        segments: List[Tuple[str, bool, Optional[str]]] = []

        # Find code blocks first
        code_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        last_end = 0

        for match in code_pattern.finditer(text):
            # Add prose before this code block
            prose = text[last_end : match.start()].strip()
            if prose:
                # Split prose into paragraphs
                for para in prose.split("\n\n"):
                    para = para.strip()
                    if para:
                        segments.append((para, False, None))

            # Add the code block
            lang = match.group(1) or "unknown"
            code = match.group(2).strip()
            if code:
                segments.append((code, True, lang))

            last_end = match.end()

        # Add remaining prose
        remaining = text[last_end:].strip()
        if remaining:
            for para in remaining.split("\n\n"):
                para = para.strip()
                if para:
                    segments.append((para, False, None))

        # If no segments found, treat whole text as one segment
        if not segments:
            # Check if it looks like code
            is_code = self._looks_like_code(text)
            lang = self._detect_language(text) if is_code else None
            segments.append((text.strip(), is_code, lang))

        return segments

    def _looks_like_code(self, text: str) -> bool:
        """Heuristic to detect if text is code."""
        code_indicators = [
            r"def\s+\w+\(",
            r"class\s+\w+",
            r"import\s+",
            r"from\s+\w+\s+import",
            r"if\s+.*:",
            r"for\s+.*:",
            r"return\s+",
            r"self\.",
            r"async\s+def",
            r"await\s+",
            r"\s{4,}",  # Heavy indentation
        ]
        code_score = sum(1 for p in code_indicators if re.search(p, text))
        return code_score >= 2

    def _detect_language(self, text: str) -> str:
        """Detect programming language from code text."""
        if re.search(r"def\s+\w+\(|import\s+|from\s+\w+\s+import|self\.", text):
            return "python"
        if re.search(r"function\s+\w+|const\s+|let\s+|var\s+|=>\s*{", text):
            return "javascript"
        if re.search(r"fn\s+\w+|impl\s+|use\s+\w+::|let\s+mut", text):
            return "rust"
        return "unknown"

    def _classify_evidence_type(self, text: str, is_code: bool) -> EvidenceType:
        """Classify what type of evidence this text represents."""
        if is_code:
            return EvidenceType.IMPLEMENTATION

        # Check patterns in order of specificity
        for evidence_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return evidence_type

        return EvidenceType.ASSERTION

    def _calculate_term_overlap(self, text: str, query_terms: List[str]) -> float:
        """Calculate how many query terms appear in the text."""
        if not query_terms:
            return 0.5

        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term.lower() in text_lower)
        return matches / len(query_terms)

    def _determine_strength(
        self, confidence: float, evidence_type: EvidenceType, term_overlap: float
    ) -> EvidenceStrength:
        """Determine evidence strength based on multiple factors."""
        # High confidence + high term overlap = strong
        if confidence >= 0.7 and term_overlap >= 0.5:
            return EvidenceStrength.STRONG

        # Implementation with good overlap is strong (code evidence)
        if evidence_type == EvidenceType.IMPLEMENTATION and term_overlap >= 0.3:
            return EvidenceStrength.STRONG

        # Moderate confidence or overlap
        if confidence >= 0.4 or term_overlap >= 0.3:
            return EvidenceStrength.MODERATE

        return EvidenceStrength.WEAK

    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract significant terms from query for matching."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "how",
            "does",
            "do",
            "where",
            "can",
            "i",
            "find",
            "in",
            "of",
            "to",
            "for",
            "and",
            "or",
            "this",
            "that",
            "with",
            "from",
            "by",
            "about",
            "are",
            "be",
            "been",
            "being",
        }

        # Tokenize and filter
        words = re.findall(r"\b\w+\b", query.lower())
        terms = [w for w in words if w not in stop_words and len(w) > 2]

        # Also extract quoted terms and backticked code
        quoted = re.findall(r'["`]([^"`]+)["`]', query)
        terms.extend(quoted)

        return list(set(terms))

    def _extract_references(self, text: str) -> List[str]:
        """Extract file paths, symbols, and cross-references from text."""
        references = []

        # Markdown links
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for _, url in md_links:
            if not url.startswith("http"):
                references.append(url)

        # Python imports
        imports = re.findall(r"from\s+([\w.]+)\s+import|import\s+([\w.]+)", text)
        for groups in imports:
            for g in groups:
                if g:
                    references.append(g)

        # File paths (common patterns)
        paths = re.findall(r"[`'\"]([a-zA-Z0-9_/\\.-]+\.\w{1,4})[`'\"]", text)
        references.extend(paths)

        # Backticked symbols
        symbols = re.findall(r"`([A-Za-z_]\w+)`", text)
        references.extend(symbols)

        return list(set(references))

    def _generate_evidence_id(self, chunk_id: str, segment_idx: int, content: str) -> str:
        """Generate a unique ID for an evidence piece."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"ev_{chunk_id}_{segment_idx}_{content_hash}"

    def _deduplicate_evidence(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """Remove duplicate or highly similar evidence pieces."""
        if not evidence_list:
            return []

        # Simple deduplication by content hash
        seen_hashes: set = set()
        unique: List[Evidence] = []

        for ev in evidence_list:
            # Normalize content for comparison
            normalized = " ".join(ev.content.lower().split())
            content_hash = hashlib.md5(normalized.encode()).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(ev)

        return unique

    def _detect_contradictions(self, evidence_list: List[Evidence]) -> None:
        """
        Detect potentially contradictory evidence.

        This is a simple heuristic - real contradiction detection would
        require semantic understanding.
        """
        # Look for negation patterns in similar contexts
        negation_words = {"not", "never", "no", "don't", "doesn't", "cannot", "can't", "won't"}

        for i, ev1 in enumerate(evidence_list):
            ev1_words = set(ev1.content.lower().split())
            ev1_has_negation = bool(ev1_words & negation_words)

            for ev2 in evidence_list[i + 1 :]:
                # Same source file and similar topic?
                if ev1.source_file == ev2.source_file:
                    continue  # Skip same-file comparisons

                ev2_words = set(ev2.content.lower().split())
                ev2_has_negation = bool(ev2_words & negation_words)

                # High word overlap but different negation status
                overlap = len(ev1_words & ev2_words) / max(len(ev1_words), len(ev2_words), 1)
                if overlap > 0.5 and ev1_has_negation != ev2_has_negation:
                    # Mark as potentially contradictory
                    ev1.contradicts_claims.append(ev2.id)
                    ev2.contradicts_claims.append(ev1.id)
                    ev2.strength = EvidenceStrength.CONTRADICTORY


def create_evidence_extractor(min_evidence_length: int = 20, max_evidence_length: int = 500) -> EvidenceExtractor:
    """Factory function for evidence extractor."""
    return EvidenceExtractor(min_evidence_length=min_evidence_length, max_evidence_length=max_evidence_length)


# --- Test harness ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    extractor = EvidenceExtractor()

    # Test with sample retrieved documents
    test_docs = [
        """# GRID Architecture

GRID (Geometric Resonance Intelligence Driver) is a Python-based framework
for exploring complex systems through geometric resonance patterns.

The architecture follows a layered approach:
1. Core layer - fundamental algorithms
2. API layer - external interfaces
3. Database layer - persistence

```python
class GridEngine:
    def __init__(self, config: GridConfig):
        self.config = config
        self.patterns = PatternRegistry()
```

See also `docs/architecture.md` for detailed documentation.""",
        """## Pattern Recognition

The system uses 9 cognition patterns for analysis:
- Flow patterns
- Spatial patterns
- Rhythm patterns

Example usage:

```python
from grid.patterns import FlowPattern

pattern = FlowPattern()
result = pattern.analyze(data)
```

Note: Pattern recognition is NOT a machine learning system.""",
    ]

    test_metas = [
        {"source": "docs/README.md", "line_start": 1, "line_end": 20},
        {"source": "docs/patterns.md", "line_start": 50, "line_end": 75},
    ]

    test_ids = ["chunk_001", "chunk_002"]

    result = extractor.extract(
        query="What is the GRID architecture?",
        documents=test_docs,
        metadatas=test_metas,
        ids=test_ids,
        distances=[0.2, 0.35],
    )

    print("\n" + "=" * 60)
    print("EVIDENCE EXTRACTION TEST".center(60))
    print("=" * 60)

    print(f"\nQuery: '{result.query}'")
    print(f"Total evidence pieces: {len(result.evidence)}")
    print(f"Strong evidence: {len(result.strong_evidence)}")
    print(f"Average confidence: {result.average_confidence:.2%}")
    print(f"Has contradictions: {result.has_contradictions}")

    print("\n--- Evidence by Type ---")
    for etype, evs in result.by_type.items():
        print(f"  {etype.value}: {len(evs)}")

    print("\n--- Top 3 Evidence Pieces ---")
    for ev in result.evidence[:3]:
        print(f"\n[{ev.evidence_type.value.upper()}] {ev.citation()}")
        print(f"  Strength: {ev.strength.value}, Confidence: {ev.confidence:.2%}")
        print(f"  Content: {ev.content[:100]}...")
        if ev.references:
            print(f"  References: {ev.references}")
