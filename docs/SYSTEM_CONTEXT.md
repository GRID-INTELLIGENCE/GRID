# System Context: Grid/Circuits Research Platform

**Version:** 2.0 (Earth-grounded structure)
**Predecessor:** Atmosphere/Echoes (Air-element exploratory phase)
**Primary Research Domain:** Information propagation dynamics and sensory coherence states

---

## Core Research Questions

### 1. Information as Environmental Force
How does information, once released into a system, influence nearby circumstances and entities? Not metaphorically—**measurably**. Information creates state changes in networks the same way pressure waves propagate through physical media.

### 2. Influence Vectors
In what aspects and magnitudes can information exert influence? This platform models:
- **Direction** (polarity: supportive ↔ adversarial)
- **Magnitude** (intensity of influence)
- **Trajectory** (improving, declining, stable)
- **Propagation pathways** (relationships as influence channels)

### 3. Sensory Goldilocks Zone
The state where five primary sensory channels (sight, sound, touch, taste, smell) achieve coherence—neither overstimulated nor understimulated. Goals:
- Precisely define this state
- Optimize by mitigating perceptual risks
- Identify practical daily-life scenarios manifesting this coherence

### 4. Zoological & Psychological Patterns (Secondary Lens)
- **Zoology:** Different sensory configurations reveal alternative equilibrium states
- **Psychology:** How information creates perceptual/emotional states in humans
- Both inform the primary research but are not the central focus

---

## Architectural Model

### Entities = Information Nodes
Not just "things mentioned in text." Entities are **accumulation points** where information concentrates and from which it radiates influence.

### Relationships = Influence Vectors
Not social graphs. Each relationship represents:
- An active or potential **pathway for information flow**
- A **directional force** with measurable polarity
- A **dynamic state** that changes as information accumulates

Example relationship features:
```
polarity_score: -1.0 to +1.0  # Direction of influence
confidence: 0.0 to 1.0        # Measurement certainty
contextual_features:          # Multi-dimensional state
  - emotional_state           # Feeling-based perception
  - power_asymmetry           # Spatial/dominance dynamics
  - risk_level                # Threat detection signal
  - trajectory                # Temporal change direction
```

### Patterns = Resonance Signatures
Recurring behaviors that indicate:
- Stable information flow states
- Deviation events (pattern breaks)
- Emergent coherence or dissonance

### Events = Information Packets
Discrete units of information entering the system. Each event:
- Originates from a source
- Carries payload (text, metadata, timestamp)
- Triggers entity extraction and relationship analysis
- Contributes to pattern detection

---

## System Components

### `grid/` - Foundational Intelligence Layer
Core programs that extract meaning from information:
- **`programs/ner_service.py`** - Entity extraction (identify information nodes)
- **`programs/relationship_analyzer.py`** - Influence vector analysis
- **`pattern/engine.py`** - Pattern recognition and deviation detection
- **`services/retrieval_service.py`** - Historical context (RAG)

### `circuits/` - API Surface Layer
Exposes research capabilities as composable services:
- **`circuits/main.py`** - FastAPI application
- **`circuits/perf_benchmark.py`** - Performance measurement tools
- Endpoints structure information flow analysis as HTTP operations

---

## Why Performance Matters

Information propagates at **perceptual speed**. Human sensory processing operates in milliseconds. If analysis latency exceeds perception latency, the system studies **echoes, not waves**.

Target: Sub-millisecond relationship analysis for real-time information influence tracking.

Performance optimizations support:
- Real-time event stream processing
- Multi-document concurrent analysis
- Historical context retrieval without blocking
- Pattern detection at scale

---

## Research Philosophy

### Evidence-Grounded
Every judgment ties to traceable evidence. No speculation without source attribution.

```python
result = {
    "polarity_score": 0.65,
    "polarity_label": "cooperative",
    "explanation": "Based on 12 interactions...",
    "top_evidence": [...]  # Specific events/patterns
}
```

### Transparent Reasoning
The system shows its work. Contextual features reveal **how** conclusions were reached:
- Which signals contributed (cooperation_count, conflict_count, etc.)
- Feature weights applied
- Confidence calculation basis

### Composable Intelligence
Services are modular. Relationship analysis can run with or without:
- Historical context (RAG)
- Event streams
- Pattern detection
Each component adds dimensionality without hard dependencies.

---

## Evolutionary Path

### Atmosphere/Echoes (Air Phase)
- Formless exploration of information resonance
- Studied propagation without structural capture
- Insights: information **does** create measurable influence, but ephemeral models can't pin it down

### Grid/Circuits (Earth Phase - Current)
- Grounded structure for systematic measurement
- Grid = substrate for information flow
- Circuits = defined pathways for influence propagation
- Persistent storage, traceable analysis, repeatable experiments

### Future Direction
Convergence toward **sensory coherence modeling**:
- Multi-modal information processing (not just text)
- Real-time state detection (when systems enter/exit Goldilocks zone)
- Predictive influence modeling (given information X, predict state change Y)

---

## Key Distinctions

### This is NOT:
- A social network analysis tool
- A sentiment analysis API
- A chatbot or conversational AI
- A knowledge graph database

### This IS:
- Research infrastructure for **information as force**
- A platform to study **how communication shapes system states**
- Tools to identify **sensory/perceptual coherence conditions**
- Evidence-grounded **influence dynamics modeling**

---

## Operational Context

### For Claude Opus 4.x
When analyzing this codebase:
1. Entities are **information nodes**, not just text spans
2. Relationships encode **influence vectors** with direction and magnitude
3. Performance optimization serves **real-time propagation tracking**
4. The goal is finding **sensory Goldilocks zones**, not maximizing accuracy metrics
5. Evidence trails matter—every judgment must be traceable

### For Claude 3.5 Sonnet
Optimize articulation by recognizing:
- `RelationshipAnalyzer` isn't scoring social ties—it's measuring **information influence**
- `contextual_features` aren't ML features—they're **perceptual state dimensions**
- Pattern detection seeks **resonance signatures**, not statistical correlations
- The fast path (empty events/patterns) handles **fresh information arrival** before context builds
- Singleton services reduce latency because **information doesn't wait for initialization**

---

## Research Outputs

### Immediate (Current Capabilities)
- Real-time entity extraction from information streams
- Directional influence analysis between entities
- Pattern deviation detection
- Evidence-backed relationship judgments

### Near-Term (Optimization Focus)
- Sub-millisecond relationship analysis at scale
- Multi-document concurrent processing
- Historical context integration without latency penalty
- Perceptual state classification (Goldilocks zone detection)

### Long-Term (Research Horizon)
- Multi-sensory information modeling (beyond text)
- Predictive influence dynamics
- Optimal communication pathway recommendation
- Cross-species sensory coherence comparison (zoological lens)

---

## Practical Application Scenarios

Information propagation analysis applies to:
- **Crisis monitoring** - How information flows during high-stakes events
- **Organizational dynamics** - Communication patterns that create team states
- **Intelligence analysis** - Tracking influence between geopolitical actors
- **Market signals** - Information cascades affecting economic actors
- **Daily life optimization** - Identifying communication patterns that create perceptual coherence

---

## Final Note

This platform studies **the physics of information**—not as metaphor, but as measurable phenomenon. Information propagates. It influences. It creates states. This system captures, measures, and reasons about those dynamics with evidence and transparency.

The air phase taught us information moves. The earth phase lets us track where it goes and what it does when it arrives.
