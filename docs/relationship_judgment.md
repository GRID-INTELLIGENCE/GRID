# Relationship Judgment Guidelines

This document defines the criteria and examples for judging entity relationships as friend/foe/neutral and related categories.

## Relationship Polarity Labels

### supportive (+0.7 to +1.0)
**Definition:** Entities actively support each other's goals, with alignment of interests and positive reinforcement.

**Criteria:**
- Explicit statements of support or partnership
- Shared goals and aligned strategies
- Positive reinforcement patterns (one entity's success benefits the other)
- Long-term cooperation with increasing trust
- Mutual benefit evident in interactions

**Evidence signals:**
- Pattern: COMBINATION_PATTERNS with positive relationship types
- High cooperation_count relative to conflict_count
- Positive stance_change or stable positive trajectory
- Low risk_level despite high interaction frequency

**Example:**
```
Entities: NovaCore & GreenCapital
Relations: "strategic_partner", "mutual_benefit", "aligned_interests"
History: 20+ cooperative interactions over 2 years, 0 conflicts
Patterns: SPATIAL_RELATIONSHIPS (same markets), TEMPORAL_PATTERNS (coordinated timing)
Judgment: supportive (score: +0.85)
Explanation: "Long-term strategic partnership with aligned interests, consistent cooperation, and mutual benefit patterns."
```

### cooperative (+0.3 to +0.7)
**Definition:** Entities work together effectively, with generally positive interactions but less deep alignment than supportive.

**Criteria:**
- Regular collaboration and joint activities
- More cooperation than conflict
- Positive or neutral emotional tone
- Functional working relationship
- May have occasional disagreements but resolve them

**Evidence signals:**
- Pattern: CAUSE_EFFECT with positive outcomes
- cooperation_count > conflict_count
- Stable or improving trajectory
- Medium to low risk_level

**Example:**
```
Entities: Vendor X & Company Y
Relations: "supplier", "contractual", "service_provider"
History: 12 interactions, 8 cooperative, 2 minor conflicts (pricing), resolved
Patterns: TEMPORAL_PATTERNS (regular delivery cycles)
Judgment: cooperative (score: +0.55)
Explanation: "Functional supplier relationship with regular cooperation, occasional pricing disputes resolved amicably."
```

### neutral (0.0 ± 0.2)
**Definition:** Entities interact without clear positive or negative valence, or interactions are too limited to judge.

**Criteria:**
- Minimal interaction history
- No clear pattern of cooperation or conflict
- Transactional or purely informational interactions
- Neutral emotional tone
- No significant alignment or opposition

**Evidence signals:**
- Low interaction_count
- No strong patterns detected
- Neutral or absent emotional_state
- Low risk_level

**Example:**
```
Entities: Company A & Company B
Relations: "mentioned_together", "industry_peer"
History: 3 interactions, all informational (news mentions together)
Patterns: None significant
Judgment: neutral (score: +0.05)
Explanation: "Limited interaction history, primarily informational mentions with no clear cooperative or adversarial pattern."
```

### competitive (-0.2 to -0.3)
**Definition:** Entities are in competition but maintain professional boundaries, not actively hostile.

**Criteria:**
- Competing for same resources, markets, or opportunities
- Professional competition without personal animosity
- May cooperate on some matters while competing on others
- Respectful competition, not destructive

**Evidence signals:**
- Pattern: SPATIAL_RELATIONSHIPS (same markets) + negative sentiment
- Some conflict_count but not dominant
- Neutral to slightly negative emotional_state
- Medium risk_level

**Example:**
```
Entities: TechCorp & RivalTech
Relations: "competitor", "market_rival", "occasional_partnership"
History: 15 interactions, 5 competitive, 3 cooperative (standards), 7 neutral
Patterns: SPATIAL_RELATIONSHIPS (overlapping markets)
Judgment: competitive (score: -0.25)
Explanation: "Market competitors with professional rivalry, occasional cooperation on industry standards, respectful competition."
```

### adversarial (-0.5 to -0.8)
**Definition:** Entities have conflicting interests with active opposition, though not necessarily malicious.

**Criteria:**
- Clear opposition of interests
- Conflict_count significant relative to cooperation
- Negative emotional tone (angry, defensive, anxious)
- Escalating or volatile trajectory
- High risk_level

**Evidence signals:**
- Pattern: CAUSE_EFFECT with negative outcomes, DEVIATION_SURPRISE (unexpected conflicts)
- conflict_count > cooperation_count or recent negative_shift
- Negative emotional_state
- High risk_level

**Example:**
```
Entities: Vendor X & CFO
Relations: "contract_dispute", "pricing_conflict", "escalation"
History: 8 interactions, 1 initial cooperation, 7 conflicts (pricing, delivery)
Patterns: DEVIATION_SURPRISE (sudden conflict escalation), CAUSE_EFFECT (pricing changes → disputes)
Emotional state: "anxious", "defensive"
Judgment: adversarial (score: -0.65)
Explanation: "Repeated escalations over pricing and delivery, trust eroded, defensive interactions, high conflict-to-cooperation ratio."
```

### manipulative (-0.7 to -0.9)
**Definition:** One entity exploits or manipulates the other, with asymmetric benefit and potential harm.

**Criteria:**
- Extreme power_asymmetry exploited
- One-sided benefit patterns
- Hidden agendas or deceptive behavior
- Target entity at significant disadvantage
- High risk_level, especially for target

**Evidence signals:**
- Pattern: COMBINATION_PATTERNS with suspicious combinations
- Extreme power_asymmetry + negative outcomes for weaker party
- DEVIATION_SURPRISE (unexpected negative outcomes)
- High risk_level for one party

**Example:**
```
Entities: LargeCorp & SmallVendor
Relations: "contractor", "vendor", "unfavorable_terms"
History: 10 interactions, all favor LargeCorp, SmallVendor complaints ignored
Patterns: COMBINATION_PATTERNS (money + power asymmetry), DEVIATION_SURPRISE (unexpected contract changes)
Power asymmetry: "extreme_asymmetry" (target_dominant = LargeCorp)
Risk level: "high" (for SmallVendor)
Judgment: manipulative (score: -0.80)
Explanation: "Extreme power asymmetry exploited, one-sided benefit, SmallVendor complaints ignored, high risk for weaker party."
```

### ambiguous (-0.2 to +0.2)
**Definition:** Relationship is unclear, contradictory, or rapidly changing, making judgment uncertain.

**Criteria:**
- Contradictory signals (both positive and negative patterns)
- Volatile trajectory with frequent shifts
- Insufficient information
- Mixed emotional states
- Unclear alignment or opposition

**Evidence signals:**
- Pattern: Multiple conflicting patterns
- Volatile stance_change
- Mixed emotional_state
- Low confidence due to contradictory evidence

**Example:**
```
Entities: Company A & Company B
Relations: "partnership", "dispute", "negotiation"
History: 6 interactions, 3 positive, 2 negative, 1 neutral, rapid shifts
Patterns: CAUSE_EFFECT (positive), DEVIATION_SURPRISE (negative), conflicting signals
Stance change: "volatile"
Judgment: ambiguous (score: +0.10, confidence: 0.4)
Explanation: "Contradictory signals with volatile pattern, both cooperative and adversarial elements, relationship direction unclear."
```

## Numeric Score Mapping

| Label | Score Range | Typical Score |
|-------|-------------|---------------|
| supportive | +0.7 to +1.0 | +0.85 |
| cooperative | +0.3 to +0.7 | +0.55 |
| neutral | -0.2 to +0.2 | 0.0 |
| competitive | -0.2 to -0.3 | -0.25 |
| adversarial | -0.5 to -0.8 | -0.65 |
| manipulative | -0.7 to -0.9 | -0.80 |
| ambiguous | -0.2 to +0.2 | 0.0 (low confidence) |

## Judgment Criteria Summary

When judging a relationship, consider:

1. **Historical pattern** (relationship_history): More cooperation → positive, more conflict → negative
2. **Recent trajectory** (stance_change): Improving → positive, declining → negative
3. **Emotional tone** (emotional_state): Positive emotions → positive, negative → negative
4. **Pattern signals**: CAUSE_EFFECT, COMBINATION_PATTERNS, DEVIATION_SURPRISE inform judgment
5. **Power dynamics** (power_asymmetry): Extreme asymmetry + negative outcomes → manipulative
6. **Risk level**: High risk + negative patterns → more negative judgment
7. **Trigger events**: Crisis/conflict triggers can shift judgment temporarily

## Confidence Scoring

Confidence (0.0 to 1.0) depends on:

- **High confidence (0.8-1.0)**: Clear, consistent signals, sufficient history, strong patterns
- **Medium confidence (0.5-0.8)**: Some signals present, moderate history, some patterns
- **Low confidence (0.0-0.5)**: Contradictory signals, limited history, ambiguous patterns

Low confidence may result in "ambiguous" label even if score suggests a direction.

## Labeled Examples

### Example 1: Long-term Partnership
```
Text: "NovaCore and GreenCapital have maintained a strategic partnership for over 5 years,
       with 50+ joint initiatives, shared market expansion, and mutual technology licensing."

Entities: NovaCore (ORG), GreenCapital (ORG)
Relations: "strategic_partner", "joint_initiative", "technology_license"
History: 50+ interactions, all cooperative, 5 years
Patterns: SPATIAL_RELATIONSHIPS, TEMPORAL_PATTERNS, COMBINATION_PATTERNS
Emotional state: "calm", "excited"
Risk level: "low"
Power asymmetry: "symmetric"

Judgment: supportive (score: +0.90, confidence: 0.95)
Explanation: "Long-term strategic partnership with extensive cooperation history,
              aligned interests, mutual benefit, and stable positive trajectory."
```

### Example 2: Supplier Relationship with Disputes
```
Text: "Vendor X has been supplying components to Company Y for 2 years.
       Recent pricing negotiations became tense, with the CFO expressing frustration
       over repeated cost increases. However, delivery quality remains good."

Entities: Vendor X (ORG), Company Y (ORG), CFO (PERSON)
Relations: "supplier", "pricing_negotiation", "delivery"
History: 24 interactions, 18 cooperative (delivery), 4 conflicts (pricing), 2 neutral
Recent: 3 pricing conflicts in last 2 months
Patterns: CAUSE_EFFECT (pricing changes → disputes), TEMPORAL_PATTERNS (regular delivery)
Emotional state: "frustrated" (CFO), "defensive" (Vendor X)
Stance change: "negative_shift"
Risk level: "medium"

Judgment: cooperative (score: +0.40, confidence: 0.75)
Explanation: "Functional supplier relationship with good delivery track record,
              but recent pricing disputes and negative shift in tone reduce positive score."
```

### Example 3: Market Competitors
```
Text: "TechCorp and RivalTech compete aggressively in the enterprise software market,
       but have collaborated on industry standards and occasionally partner on large deals."

Entities: TechCorp (ORG), RivalTech (ORG)
Relations: "competitor", "market_rival", "standards_collaboration", "occasional_partnership"
History: 30 interactions, 12 competitive, 8 cooperative (standards), 10 neutral
Patterns: SPATIAL_RELATIONSHIPS (same markets), COMBINATION_PATTERNS (compete + cooperate)
Emotional state: "competitive" (neutral professional)
Risk level: "medium"
Power asymmetry: "symmetric"

Judgment: competitive (score: -0.20, confidence: 0.80)
Explanation: "Professional market competition with occasional cooperation on industry matters,
              balanced competitive and cooperative elements, respectful rivalry."
```

### Example 4: Escalating Conflict
```
Text: "The relationship between Vendor X and the CFO has deteriorated significantly.
       After initial successful deliveries, repeated pricing disputes escalated to
       contract renegotiations. The CFO threatened to switch vendors, and Vendor X
       accused the company of unfair negotiation tactics."

Entities: Vendor X (ORG), CFO (PERSON)
Relations: "vendor", "pricing_dispute", "contract_renegotiation", "threat", "accusation"
History: 10 interactions, 2 initial cooperation, 8 conflicts (escalating)
Recent: All 5 recent interactions are conflicts
Patterns: CAUSE_EFFECT (pricing → disputes → escalation), DEVIATION_SURPRISE (sudden deterioration)
Emotional state: "angry", "defensive"
Stance change: "sudden_negative"
Risk level: "high"
Prior conflict: has_conflict=true, conflict_count=8, last_conflict_days_ago=3

Judgment: adversarial (score: -0.75, confidence: 0.90)
Explanation: "Rapidly deteriorating relationship with escalating conflicts,
              trust broken, defensive and angry interactions, high risk of termination."
```

### Example 5: Power Imbalance Exploitation
```
Text: "LargeCorp forced SmallVendor to accept unfavorable contract terms,
       including extended payment terms and liability shifts. SmallVendor's
       complaints were ignored, and the contract was presented as 'take it or leave it.'"

Entities: LargeCorp (ORG), SmallVendor (ORG)
Relations: "contractor", "unfavorable_terms", "forced_agreement"
History: 8 interactions, all favor LargeCorp, SmallVendor concerns dismissed
Patterns: COMBINATION_PATTERNS (money + power), DEVIATION_SURPRISE (unexpected terms)
Emotional state: "defensive" (SmallVendor), "opportunistic" (LargeCorp)
Power asymmetry: "extreme_asymmetry" (target_dominant = LargeCorp)
Risk level: "high" (for SmallVendor)
Prior conflict: has_conflict=true (one-sided)

Judgment: manipulative (score: -0.85, confidence: 0.85)
Explanation: "Extreme power asymmetry exploited, one-sided benefit,
              SmallVendor's concerns ignored, high risk for weaker party,
              forced agreement pattern."
```

### Example 6: Ambiguous New Relationship
```
Text: "Company A and Company B announced a partnership, but details are unclear.
       Some sources suggest it's a strategic alliance, while others indicate
       it may be a temporary arrangement or even a competitive move."

Entities: Company A (ORG), Company B (ORG)
Relations: "partnership", "strategic_alliance", "unclear_terms"
History: 2 interactions (announcement, speculation)
Patterns: None significant (too new)
Emotional state: Unclear
Risk level: "medium" (uncertainty)
Information: Limited, contradictory signals

Judgment: ambiguous (score: +0.10, confidence: 0.30)
Explanation: "Very limited interaction history, contradictory information,
              unclear relationship nature, insufficient evidence for clear judgment."
```

## Implementation Notes

- These examples should be used as test cases for the RelationshipAnalyzer
- Judgment logic should weight features according to these criteria
- Confidence should reflect the strength and consistency of evidence
- Explanations should cite specific features and evidence that led to the judgment
