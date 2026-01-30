www# Relationship Analyzer Design Document

## Overview

The Relationship Analyzer is a service that computes relationship judgments (friend/foe/neutral) for entity relationships by analyzing contextual features, patterns, and historical data.

## Output Format

### Relationship Judgment Response

```python
{
    "polarity_score": float,      # Numeric score from -1.0 (adversarial) to +1.0 (supportive)
    "polarity_label": str,         # Categorical label: supportive, cooperative, neutral, competitive, adversarial, manipulative, ambiguous
    "confidence": float,           # Confidence score from 0.0 to 1.0
    "explanation": str,            # Human-readable explanation of the judgment
    "top_evidence": [              # List of key evidence items
        {
            "type": str,           # "pattern", "history", "emotion", "trigger", etc.
            "description": str,    # Description of the evidence
            "weight": float        # How much this evidence contributed to the judgment
        }
    ],
    "contextual_features": {       # Extracted contextual features
        "trigger_event": str | None,
        "emotional_state": str | None,
        "relationship_history": dict,
        "risk_level": str,
        "stance_change": str,
        "power_asymmetry": str,
        "prior_conflict": dict
    },
    "judged_at": datetime,
    "judgment_version": str        # Version of judgment logic used
}
```

### Example Output

```json
{
    "polarity_score": -0.65,
    "polarity_label": "adversarial",
    "confidence": 0.85,
    "explanation": "Rapidly deteriorating relationship with escalating conflicts, trust broken, defensive and angry interactions, high risk of termination.",
    "top_evidence": [
        {
            "type": "history",
            "description": "8 conflicts in 10 interactions, all recent",
            "weight": 0.35
        },
        {
            "type": "pattern",
            "description": "CAUSE_EFFECT pattern: pricing changes → disputes → escalation",
            "weight": 0.25
        },
        {
            "type": "emotion",
            "description": "Angry and defensive emotional states detected",
            "weight": 0.20
        },
        {
            "type": "stance_change",
            "description": "Sudden negative shift from initial cooperation",
            "weight": 0.20
        }
    ],
    "contextual_features": {
        "trigger_event": null,
        "emotional_state": "angry",
        "relationship_history": {
            "interaction_count": 10,
            "cooperation_count": 2,
            "conflict_count": 8,
            "relationship_age_days": 180,
            "trajectory": "declining"
        },
        "risk_level": "high",
        "stance_change": "sudden_negative",
        "power_asymmetry": "symmetric",
        "prior_conflict": {
            "has_conflict": true,
            "conflict_count": 8,
            "last_conflict_days_ago": 3,
            "conflict_severity": "high"
        }
    },
    "judged_at": "2025-01-15T10:30:00Z",
    "judgment_version": "1.0"
}
```

## Backend Approach

### Rule/Model-Driven (Features + Classifier)

The system uses a **rule-based approach** with feature extraction and weighted scoring:

1. **Feature Extraction**: Extract contextual features from entities, relationships, events, and patterns
2. **Feature Weighting**: Apply configurable weights to each feature type
3. **Score Computation**: Compute numeric polarity score using weighted feature combination
4. **Label Classification**: Map numeric score to categorical label using thresholds
5. **Confidence Calculation**: Compute confidence based on evidence strength and consistency
6. **Explanation Generation**: Generate human-readable explanation citing key evidence

### Why Rule-Based (Not Pure LLM)?

- **Deterministic**: Same inputs produce same outputs (important for testing and debugging)
- **Explainable**: Clear rules make it easy to understand why a judgment was made
- **Fast**: No API calls, works offline
- **Tunable**: Feature weights can be adjusted based on domain knowledge
- **Testable**: Can test with labeled examples and verify correctness

### Future: Hybrid Mode

The design allows for future addition of LLM-based explanations:
- Rules compute the core judgment (score, label, confidence)
- LLM generates richer explanations and identifies nuanced evidence
- Best of both worlds: deterministic judgment + rich explanations

## Integration Points

### Pipeline Position

```
Input → NER → Entity Extraction → Relationship Extraction → [Relationship Analyzer] → Scenario Analyzer → Output
```

The Relationship Analyzer sits **after** NER and relationship extraction, but **before** scenario analysis, so that scenario analysis can use relationship judgments.

### Data Flow

1. **Input**:
   - `EntityRelationship` object
   - Related `Entity` objects (source and target)
   - Related `Event` objects (for context)
   - `PatternMatch` objects (from pattern engine)

2. **Processing**:
   - Extract contextual features
   - Query historical data (prior interactions, conflicts)
   - Compute polarity score
   - Classify label
   - Calculate confidence
   - Generate explanation and evidence

3. **Output**:
   - Update `EntityRelationship` with judgment fields
   - Store judgment in database
   - Publish `RelationshipJudgedEvent` to EventBus
   - Return judgment response

## Storage

### EntityRelationship Model Extensions

Add fields to existing `EntityRelationship` model:
- `polarity_score`: Float (nullable)
- `polarity_label`: String (nullable)
- `judgment_metadata`: JSON (stores explanation, evidence, contextual_features)
- `judged_at`: DateTime (nullable)
- `judgment_version`: String (nullable)

### RelationshipJudgment Model (Optional)

Separate table for judgment history:
- Allows tracking how judgments change over time
- Useful for analyzing relationship evolution
- Can be added later if needed

## API Endpoints

### POST /ner/relationships/analyze
Analyze a specific relationship and return judgment.

**Request:**
```json
{
    "relationship_id": "uuid",
    "include_history": true
}
```

**Response:** RelationshipJudgmentResponse

### GET /ner/relationships/{id}/judgment
Get current judgment for a relationship.

**Response:** RelationshipJudgmentResponse

### POST /ner/relationships/batch-analyze
Analyze multiple relationships.

**Request:**
```json
{
    "relationship_ids": ["uuid1", "uuid2", ...],
    "include_history": false
}
```

**Response:** List[RelationshipJudgmentResponse]

### GET /ner/relationships (Updated)
Add optional `include_judgment` query parameter to include judgment fields in response.

## Configuration

### RelationshipAnalyzerSettings

```python
class RelationshipAnalyzerSettings(BaseSettings):
    enable_judgment: bool = True
    confidence_threshold: float = 0.6  # Minimum confidence to return judgment
    use_historical_context: bool = True
    judgment_version: str = "1.0"

    # Feature weights (sum should be ~1.0)
    feature_weights: Dict[str, float] = {
        "relationship_history": 0.30,
        "pattern_signals": 0.25,
        "emotional_state": 0.15,
        "stance_change": 0.15,
        "power_asymmetry": 0.10,
        "risk_level": 0.05
    }

    # Score thresholds for label classification
    label_thresholds: Dict[str, float] = {
        "supportive": 0.7,
        "cooperative": 0.3,
        "neutral": 0.2,
        "competitive": -0.2,
        "adversarial": -0.5,
        "manipulative": -0.7
    }
```

## Algorithm Overview

### 1. Feature Extraction

For each contextual feature (see `context_features.md`):
- Extract from text using NER/pattern matching
- Query database for historical data
- Compute derived features (e.g., trajectory from history)

### 2. Score Computation

```python
score = 0.0

# Relationship history contribution
history_score = compute_history_score(relationship_history)
score += history_score * weights["relationship_history"]

# Pattern signals contribution
pattern_score = compute_pattern_score(patterns)
score += pattern_score * weights["pattern_signals"]

# Emotional state contribution
emotion_score = compute_emotion_score(emotional_state)
score += emotion_score * weights["emotional_state"]

# Stance change contribution
stance_score = compute_stance_score(stance_change)
score += stance_score * weights["stance_change"]

# Power asymmetry contribution (only if negative)
if power_asymmetry == "extreme_asymmetry" and negative_outcomes:
    score -= weights["power_asymmetry"]

# Risk level contribution (only if high risk + negative patterns)
if risk_level == "high" and negative_patterns:
    score -= weights["risk_level"]

# Clamp to [-1.0, +1.0]
score = max(-1.0, min(1.0, score))
```

### 2.1 Cognition Pattern Scoring (9-Pattern Stack)

Pattern signals come from the 9 cognition patterns defined in `we_definition.md` / `cognition_grid.py`.
They are combined in `RelationshipAnalyzer._compute_pattern_score` as follows:

- **Stability / continuity patterns (generally positive)**
  - **Repetition & Habit** (`REPETITION_HABIT`)
    - Contribution: `+0.4 * confidence`
    - Intuition: strong, repeated routines between entities signal a more stable relationship.
  - **Natural Rhythms** (`NATURAL_RHYTHMS`)
    - Contribution: `+0.35 * confidence`
    - Intuition: periodic, organic cycles around the relationship support stability.
  - **Temporal Patterns** (`TEMPORAL_PATTERNS`)
    - Contribution: `+0.3 * confidence`
    - Intuition: regular timing/sequence patterns reinforce predictability.

- **Context / geometric patterns (lighter positive influence)**
  - **Spatial Relationships** (`SPATIAL_RELATIONSHIPS`)
    - Contribution: `+0.2 * confidence`
  - **Flow & Motion** (`FLOW_MOTION`)
    - Contribution: `+0.2 * confidence`
  - **Color & Light** (`COLOR_LIGHT`)
    - Contribution: `+0.15 * confidence`
  - Intuition: these patterns describe how the relationship is laid out in space, movement, and visual salience.
    They gently bias polarity when consistent with other positive signals but are not dominant on their own.

- **Tension / risk patterns (negative bias)**
  - **Deviation & Surprise** (`DEVIATION_SURPRISE`)
    - Contribution: `-0.4 * confidence`
    - Intuition: strong anomalies and pattern violations increase perceived tension and risk.
  - **Cause & Effect** (`CAUSE_EFFECT`)
    - Contribution: `-0.25 * confidence` (by default)
    - Intuition: dense or high-confidence causal chains are treated as potentially risky/entangling when we
      do not yet inspect the valence of specific outcomes.

- **Combination patterns (amplifier, not standalone)**
  - **Combination Patterns** (`COMBINATION_PATTERNS`)
    - First, a **base score** is computed from all patterns *except* `COMBINATION_PATTERNS`.
    - If the base score is non-zero and any `COMBINATION_PATTERNS` are present, an amplifier term is added:
      - `combo_contribution = 0.2 * avg_combo_confidence * sign(base_score)`
    - Intuition: when multiple patterns overlap coherently, they amplify the existing direction (more cooperative
      if already positive, more adversarial if already negative) instead of acting as an independent positive.

Implementation details:

- Each pattern contributes a **per-pattern score** based on its role and confidence.
- Only patterns with non-zero contribution are counted as **contributors**.
- The base pattern score is the average of contributor contributions:

  ```python
  if base_contributor_count > 0:
      base_score_without_combo = base_score_without_combo / base_contributor_count
  ```

- `COMBINATION_PATTERNS` are then applied as an optional amplifier on top of this base score.
- The final `pattern_score` is clamped to `[-1.0, +1.0]` and then weighted by
  `feature_weights["pattern_signals"]` (default `0.25`) inside `_compute_polarity_score`.

This design keeps relationship history as the dominant driver of polarity, while the 9-pattern stack
acts as a geometric/modulating signal that nudges judgments in explainable ways.

#### 2.1.1 Pattern → Score Cheat Sheet

| Pattern Code              | Name                   | Role                          | Contribution Formula           |
|---------------------------|------------------------|-------------------------------|--------------------------------|
| `REPETITION_HABIT`       | Repetition & Habit     | Stability / continuity (+)    | `+0.4 * confidence`            |
| `NATURAL_RHYTHMS`        | Natural Rhythms        | Stability / continuity (+)    | `+0.35 * confidence`           |
| `TEMPORAL_PATTERNS`      | Temporal Patterns      | Stability / continuity (+)    | `+0.3 * confidence`            |
| `SPATIAL_RELATIONSHIPS`  | Spatial Relationships  | Context / geometric (+ light) | `+0.2 * confidence`            |
| `FLOW_MOTION`            | Flow & Motion          | Context / geometric (+ light) | `+0.2 * confidence`            |
| `COLOR_LIGHT`            | Color & Light          | Context / geometric (+ light) | `+0.15 * confidence`           |
| `DEVIATION_SURPRISE`     | Deviation & Surprise   | Tension / risk (−)            | `-0.4 * confidence`            |
| `CAUSE_EFFECT`           | Cause & Effect         | Tension / risk (−, by default)| `-0.25 * confidence`           |
| `COMBINATION_PATTERNS`   | Combination Patterns   | Amplifier (follows net sign)  | `+0.2 * avg_combo_conf * sign(base_score)` |

Use this table when tuning or debugging judgments: if a relationship’s polarity seems off, inspect
which patterns fired, their confidences, and how they combine via the formulas above.

### 3. Label Classification

```python
def classify_label(score: float, thresholds: Dict[str, float]) -> str:
    if score >= thresholds["supportive"]:
        return "supportive"
    elif score >= thresholds["cooperative"]:
        return "cooperative"
    elif score >= thresholds["neutral"]:
        return "neutral"
    elif score >= thresholds["competitive"]:
        return "competitive"
    elif score >= thresholds["adversarial"]:
        return "adversarial"
    elif score >= thresholds["manipulative"]:
        return "manipulative"
    else:
        return "ambiguous"  # Very negative or contradictory
```

### 4. Confidence Calculation

```python
confidence = 0.0

# Base confidence from evidence strength
if interaction_count >= 10:
    confidence += 0.3
elif interaction_count >= 5:
    confidence += 0.2
else:
    confidence += 0.1

# Pattern strength
if strong_patterns_detected:
    confidence += 0.3
elif some_patterns_detected:
    confidence += 0.15

# Signal consistency
if signals_consistent:
    confidence += 0.2
elif some_contradiction:
    confidence += 0.1

# Historical data availability
if historical_data_available:
    confidence += 0.2

confidence = min(1.0, confidence)
```

### 5. Explanation Generation

Generate explanation by:
1. Identify top 3-5 evidence items (by weight)
2. Format each evidence item as a sentence
3. Combine into coherent explanation
4. Include overall judgment summary

## Testing Strategy

1. **Unit Tests**: Test each feature extraction function, score computation, label classification
2. **Integration Tests**: Test full pipeline with labeled examples from `relationship_judgment.md`
3. **Validation Tests**: Verify judgments match expected labels for provided examples
4. **Edge Cases**: Test with minimal data, contradictory signals, extreme values

## Future Enhancements

1. **LLM Explanations**: Add optional LLM-based explanation generation for richer narratives
2. **Machine Learning**: Train classifier on labeled examples to improve accuracy
3. **Temporal Analysis**: Track relationship evolution over time with judgment history
4. **Confidence Calibration**: Improve confidence scoring based on validation results
5. **Domain Adaptation**: Allow domain-specific feature weights and thresholds
