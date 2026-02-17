"""
Skill: analysis.process_context

Run GRID's full analysis pipeline on text.
Combines entity extraction, pattern detection, relationship analysis, and sentiment.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from .base import SimpleSkill


def _simple_sentiment(text: str) -> str:
    """Simple heuristic sentiment detection."""
    positive_words = {
        "great",
        "excellent",
        "good",
        "amazing",
        "wonderful",
        "fantastic",
        "love",
        "awesome",
        "best",
        "perfect",
        "brilliant",
        "super",
    }
    negative_words = {
        "bad",
        "terrible",
        "horrible",
        "awful",
        "hate",
        "worst",
        "poor",
        "disgusting",
        "useless",
        "broken",
        "fail",
    }

    text_lower = text.lower()
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"


def _process_context(args: Mapping[str, Any]) -> dict[str, Any]:
    """Process text through full GRID analysis pipeline."""
    text = args.get("text")
    if not text:
        return {
            "skill": "analysis.process_context",
            "status": "error",
            "error": "Missing required parameter: 'text'",
        }

    include_sentiment = args.get("include_sentiment", True)
    include_relationships = args.get("include_relationships", True)
    max_entities = int(args.get("max_entities", 50) or 50)

    start_time = time.time()

    try:
        # Stage 1: Entity extraction
        from .patterns_detect_entities import _simple_entity_detection

        entities = _simple_entity_detection(text, ["PERSON", "ORG", "DOMAIN"])[:max_entities]
        stage1_time = time.time()

        # Stage 2: Pattern detection
        import re

        patterns = []
        pattern_map = {
            "feature_impl": r"feature\s+implementation",
            "bug_fix": r"bug\s+fix|fix\s+bug",
            "refactor": r"refactoring|refactor",
            "test_case": r"test\s+case|test",
            "documentation": r"documentation|docs",
        }
        for pattern_name, pattern_re in pattern_map.items():
            matches = list(re.finditer(pattern_re, text, re.IGNORECASE))
            if matches:
                patterns.append(
                    {
                        "pattern": pattern_name,
                        "count": len(matches),
                        "confidence": 0.85,
                    }
                )
        stage2_time = time.time()

        # Stage 3: Sentiment (if requested)
        sentiment = None
        if include_sentiment:
            sentiment = _simple_sentiment(text)
        stage3_time = time.time()

        # Stage 4: Relationships (if requested)
        relationships = []
        if include_relationships and len(entities) > 1:
            # Simple: create relationships between consecutive entities
            relationships.extend(
                    {
                        "source": entities[i]["text"],
                        "target": entities[i + 1]["text"],
                        "type": "RELATED",
                        "confidence": 0.70,
                    }
                for i in range(len(entities) - 1)
            )
        stage4_time = time.time()

        result = {
            "skill": "analysis.process_context",
            "status": "success",
            "text_length": len(text),
            "entities": entities,
            "entity_count": len(entities),
            "patterns": patterns,
            "pattern_count": len(patterns),
        }

        if sentiment is not None:
            result["sentiment"] = sentiment

        if relationships:
            result["relationships"] = relationships
            result["relationship_count"] = len(relationships)

        result["analysis_metadata"] = {
            "duration_ms": int((time.time() - start_time) * 1000),
            "stages_completed": 4,
            "stage_times_ms": {
                "entities": int((stage1_time - start_time) * 1000),
                "patterns": int((stage2_time - stage1_time) * 1000),
                "sentiment": int((stage3_time - stage2_time) * 1000),
                "relationships": int((stage4_time - stage3_time) * 1000),
            },
        }

        return result

    except Exception as e:
        return {
            "skill": "analysis.process_context",
            "status": "error",
            "error": str(e),
        }


# Register skill
analysis_process_context = SimpleSkill(
    id="analysis.process_context",
    name="Full Context Analysis",
    description="Run GRID's complete analysis pipeline on text (entities, patterns, sentiment, relationships)",
    handler=_process_context,
)
