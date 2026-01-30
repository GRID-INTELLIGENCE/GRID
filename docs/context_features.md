# Context Features for Relationship Dynamics

This document defines the contextual features used to analyze relationship dynamics and emotional states in the NER system.

## Overview

Contextual features capture the situational, emotional, and historical context surrounding entity relationships. These features inform relationship judgment (friend/foe/neutral) by providing signals about the nature and state of interactions.

## Feature Definitions

### 1. trigger_event

**Description:** An acute event that precipitates or significantly influences the relationship interaction.

**Types:**
- `earthquake`: Natural disasters, system outages, major disruptions
- `scandal`: Public controversies, ethical violations, reputation damage
- `promotion`: Leadership changes, organizational shifts, new appointments
- `crisis`: Financial crises, market crashes, existential threats
- `opportunity`: New markets, funding rounds, strategic openings
- `conflict`: Disputes, legal actions, competitive threats

**Example:**
```
Text: "After the earthquake disrupted operations, NovaCore and GreenCapital quickly formed a partnership to share resources."
trigger_event: "earthquake"
```

### 2. emotional_state

**Description:** The emotional tone or state explicitly or implicitly present in the interaction context.

**Values:**
- `calm`: Stable, measured, routine interactions
- `anxious`: Uncertainty, concern, worry about outcomes
- `angry`: Hostility, frustration, conflict
- `excited`: Enthusiasm, optimism, positive anticipation
- `defensive`: Protective, guarded, reactive
- `opportunistic`: Strategic, calculated, self-interested
- `high_adrenaline`: Urgent, intense, high-stakes situations

**Example:**
```
Text: "The CFO was visibly anxious during the pricing negotiations with Vendor X."
emotional_state: "anxious"
```

### 3. relationship_history

**Description:** The historical pattern of interactions between entities, including frequency, nature, and trajectory.

**Components:**
- `interaction_count`: Total number of prior interactions
- `cooperation_count`: Number of cooperative interactions
- `conflict_count`: Number of adversarial interactions
- `relationship_age_days`: Days since first interaction
- `trajectory`: `improving`, `declining`, `stable`, `volatile`

**Example:**
```
relationship_history: {
  "interaction_count": 15,
  "cooperation_count": 12,
  "conflict_count": 2,
  "relationship_age_days": 180,
  "trajectory": "improving"
}
```

### 4. risk_level

**Description:** The perceived or calculated risk associated with the relationship or interaction.

**Values:**
- `low`: Minimal risk, stable, predictable
- `medium`: Moderate risk, some uncertainty
- `high`: Significant risk, potential for negative outcomes
- `critical`: Existential risk, major consequences possible

**Factors:**
- Entity types involved (e.g., financial entities + large amounts = higher risk)
- Pattern matches (e.g., DEVIATION_SURPRISE patterns increase risk)
- Historical patterns (e.g., prior conflicts increase risk)
- Context (e.g., crisis situations increase risk)

**Example:**
```
Text: "NovaCore invested $50M in an unproven startup with no track record."
risk_level: "high"
```

### 5. stance_change

**Description:** Detected shifts in relationship stance or tone over time.

**Types:**
- `none`: No significant change detected
- `positive_shift`: Movement toward cooperation/support
- `negative_shift`: Movement toward competition/adversity
- `volatile`: Frequent shifts, unstable pattern
- `sudden_negative`: Abrupt change to adversarial stance

**Detection:**
- Compare recent interactions with historical baseline
- Look for pattern changes (e.g., CAUSE_EFFECT patterns appearing)
- Analyze sentiment trends in relationship metadata

**Example:**
```
Historical: 10 cooperative interactions over 6 months
Recent: 3 adversarial interactions in 2 weeks
stance_change: "sudden_negative"
```

### 6. power_asymmetry

**Description:** The relative power, influence, or resource imbalance between entities.

**Values:**
- `symmetric`: Roughly equal power/resources
- `source_dominant`: Source entity has more power
- `target_dominant`: Target entity has more power
- `extreme_asymmetry`: Very large power differential

**Indicators:**
- Entity types (e.g., Corporation vs Individual)
- Mention frequency (more mentions may indicate dominance)
- Relationship direction (who initiates, who responds)
- Financial amounts or resource scales

**Example:**
```
Text: "The small vendor was forced to accept unfavorable terms from the large corporation."
power_asymmetry: "target_dominant" (target = corporation)
```

### 7. prior_conflict

**Description:** Evidence of historical adversarial interactions or conflicts.

**Components:**
- `has_conflict`: Boolean indicating conflict history
- `conflict_count`: Number of prior conflicts
- `last_conflict_days_ago`: Days since last conflict
- `conflict_severity`: `low`, `medium`, `high`, `critical`
- `conflict_types`: List of conflict types (e.g., ["pricing", "contract", "reputation"])

**Example:**
```
prior_conflict: {
  "has_conflict": true,
  "conflict_count": 3,
  "last_conflict_days_ago": 45,
  "conflict_severity": "medium",
  "conflict_types": ["pricing", "delivery"]
}
```

## Temporal Roles

Contextual features can be categorized by their temporal role:

### background_history
Long-term patterns and historical context that form the baseline for the relationship.

**Examples:**
- `relationship_history`
- `prior_conflict`
- `power_asymmetry` (if stable)

### acute_trigger
Immediate events or states that directly influence the current interaction.

**Examples:**
- `trigger_event`
- `emotional_state`
- `stance_change` (if recent)

### long_term_pattern
Trends and patterns that develop over extended periods.

**Examples:**
- `relationship_history.trajectory`
- `stance_change` (if gradual)
- `risk_level` (if persistent)

## Feature Extraction Guidelines

1. **Extract from text**: Use NER and pattern matching to identify explicit mentions
2. **Infer from patterns**: Use pattern engine outputs (CAUSE_EFFECT, DEVIATION_SURPRISE) as signals
3. **Query history**: Use database queries to compute historical features
4. **Combine signals**: Multiple weak signals can indicate a feature (e.g., multiple negative patterns → negative stance_change)
5. **Temporal context**: Consider time windows (e.g., last 30 days for recent patterns, all history for baseline)

## Usage in Relationship Judgment

These features are combined using weighted rules to compute:
- **Polarity score**: Numeric score from -1.0 (adversarial) to +1.0 (supportive)
- **Polarity label**: Categorical label (supportive, cooperative, neutral, competitive, adversarial, etc.)
- **Confidence**: How certain we are in the judgment
- **Explanation**: Human-readable explanation citing key features

See `relationship_judgment.md` for how these features map to relationship judgments.
