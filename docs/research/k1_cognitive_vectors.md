# Research Plan – Vectorizing Cognitive Patterns for K1 Prerequisites

## Objective & Constraints
- **Objective:** Translate multi-sensory pattern analysis (vision, sound, locomotion) into an actionable structure that can power Kardashev Type 1 (K1) decision systems.
- **Constraints:** Prioritize **simplicity over complexity** and **stability over scale**; every representation should be traceable (Input → Process → Output per R5 in `docs/global_layer.md`).
- **Strategy:** Progress through four phases, each producing concrete artifacts that can be automated in code (baseline conversational input today, `docs/` RAG later).

Think of this plan as a steady breath: bring data in, reshape it, test its balance, then apply it. Each phase should feel learnable to a new analyst who only has this document and the repo.

## Phase 1 – Unified Sensorium (Input)
**Goal:** Normalize color (vision), frequency (sound), and trajectory (locomotion) into one “Cognitive Unit.”

### Cognitive Unit Definition
Let a synchronized slice across the three senses be \( CU_t = (V_t, S_t, L_t) \) where each component already lives in a comparable scale:
- **Vision (V):** Map RGB → perceptual HSV, then normalize hue \(h_t ∈ [0,1]\) and luminance \(l_t ∈ [0,1]\).
- **Sound (S):** Convert raw Hz to perceptual Mel scale \(m_t\) and normalize amplitude \(a_t\).
- **Locomotion (L):** Encode heading as unit vector \( (\cos θ_t, \sin θ_t) \) and speed \(s_t ∈ [0,1]\) using contextual maxima.

The final unit is a fixed vector:
\[
CU_t = [h_t, l_t, m_t, a_t, \cos θ_t, \sin θ_t, s_t]
\]
with metadata `{timestamp, source_id, window_id}` for traceability.

### Input → Process → Output
- **Input:** Raw sensor frames or conversational descriptions tagged with simple tuples `(color, sound, motion)`.
- **Process:** 1) Synchronize timestamps, 2) normalize each modality with contextual bounds, 3) emit `CognitiveUnit` dataclasses.
- **Output:** JSON/ndarray stream of units, ready for pattern engines.

#### Why it matters
- A Cognitive Unit is the smallest “honest slice” of attention. If it is clear, everything downstream can stay simple.
- Keeping the vector fixed-length avoids schema churn when new senses appear later.
- Normalization is where trust is earned; always log the calibration choices beside the data.

### Open Research Tasks
1. Decide sliding-window size (e.g., 120 ms) to retain locomotion cues without overfitting.
2. Define calibration protocol for contextual maxima/minima per session.
3. Implement reference normalizers in `experiments/k1_explore_mode/main.py`.

## Phase 2 – Pattern Vectorization (Transformation)
**Goal:** Convert a sequence of Cognitive Units into the simplest geometric object that predicts behavior.

### Approach
1. **Windowing:** Group contiguous units into “glimpses” (predictive) and “versions” (contextual) tagged in metadata.
2. **Dimensional Reduction:** Use principal axes (e.g., heading vs. speed, hue vs. luminance) to project onto 2–3D latent planes.
3. **Simplification:** Apply Ramer–Douglas–Peucker (RDP) or convex-hull pruning to keep ≤3 key vertices.
4. **Encoding:** Store result as `CognitiveVector = {nodes, dominant_pattern, confidence}` where nodes are ordered waypoints.

### Sidewalk Drift Prototype
- **Data:** Person walking straight, slowly veering right.
- **Algorithm:**
  1. Collect ~30 Cognitive Units (5 s).
  2. Project locomotion components into 2D (heading vs. displacement).
  3. Apply RDP (ε≈0.05) → expect triangle representing start, drift apex, stabilized track.
  4. Tag with `FLOW_MOTION + DEVIATION_SURPRISE` patterns if drift exceeds threshold.
- **Deliverable:** `vectorize_behavior()` function plus serialization for downstream review.

### Practical notes & insights
- A “glimpse” is short and predictive; a “version” is longer and contextual. Tag both so later models know intent.
- When RDP collapses to two points, that is a signal: the behavior was steady. Do not force triangles where none belong.
- Assign cognition patterns early (`FLOW_MOTION`, `DEVIATION_SURPRISE`, `COMBINATION_PATTERNS`) so other systems inherit a labeled stream instead of raw math.
- Document any epsilon tweaks. A future researcher should be able to rerun the triangle with the same knob settings.

## Phase 3 – Structural Stabilization (Architecture)
**Goal:** Stress-test whether the cognitive vectors persist across “versions” (dimensions) with quantum-inspired metrics.

### Stability Metrics
| Metric | Analogy | Definition |
| --- | --- | --- |
| **Coherence Score** | Quantum superposition | Similarity of consecutive vectors (cosine similarity of node sets). |
| **Entanglement Ratio** | Quantum entanglement | Cross-modal correlation (e.g., change in hue vs. change in motion). |
| **Persistence Index** | Structural stability | % of versions where vector topology (node count + ordering) remains unchanged. |
| **Decoherence Time** | Collapse under stress | Duration (in windows) before coherence < threshold. |

A vector is “stable” when `coherence ≥ 0.85`, `entanglement ≥ 0.6`, and `persistence ≥ 0.75`. These thresholds form the “Stability Metrics” deliverable.

### Stabilization insights
- Coherence close to 1.0 means the glimpse geometry barely changes between versions—great for repeatable control surfaces.
- Entanglement reveals whether senses agree. If hue never moves while motion swings wildly, the score stays low and the story is incomplete.
- Persistence being high tells us the topology (line vs. triangle) is reliable. It is a simple yes/no check before we hand vectors to planners.
- Decoherence time reminds us how long we can trust a pattern before re-measuring. Treat it like a warrant that eventually expires.

## Phase 4 – K1 Prerequisite (Application)
**Goal:** Map internal observer state → planetary management decisions.

### Hypothesis Operationalization
1. **Internal State Graph:** Aggregate stabilized vectors to build a self-knowledge lattice (habitual drifts, shocks, corrections).
2. **External Mapping:** Align lattice nodes with planetary levers (energy routing, transport flows, grid load balancing) via similarity metrics.
3. **Efficiency Score:** `Zero Friction Index = f(personal stability, planetary latency)`—high stability implies minimal control lag, echoing “knowing oneself → zero friction.”
4. **Manifesto Snippet:** “A civilization reaches K1 when every planetary control surface is a mirror of the observer’s mastered micro-movements; stability at the smallest scale guarantees stability across the grid.”

### Application notes
- The internal graph can be a simple adjacency list at first. What matters is linking each stabilized vector to the human correction that produced it.
- External mapping should start with one civic lever (e.g., traffic light timing) before jumping to full-grid claims.
- The manifesto statement above is the north star; every metric, log, and workflow should help prove or disprove it.

## Prototype Roadmap
1. **Implement `CognitiveUnit` + normalization utilities** (experiments module).
2. **Add `vectorize_behavior()` with Sidewalk Drift sample** including minimal triangle export (JSON + Markdown image hook).
3. **Compute stability metrics** for sample dataset; emit report to `docs/journal/idea_*.md` via workflow.
4. **Publish manifesto** section linking self-knowledge to planetary efficiency (appendix in this file or dedicated manifesto doc).

## Success Criteria Checklist
- [ ] Mathematical definition of the Cognitive Unit (above) codified in Python.
- [ ] Prototype algorithm for Sidewalk Drift producing a 3-node vector.
- [ ] Stability metrics emitted with coherent/entangled/persistent scores.
- [ ] Manifesto paragraph tying self-mastery to planetary control, ready for docs/manifesto export.

## Glimpse Practice Dictionary
This section keeps language plain so anyone can rehearse the ideas quickly.

| Term | Simple meaning | How to practice |
| --- | --- | --- |
| **Glimpse** | A short burst of attention (≈1–2 s) used to predict the very next move. | Pick a moving subject, watch for two seconds, and name what will happen next. Record whether you were right. |
| **Version** | A longer slice (≈5–10 s) that explains context and surroundings. | After three glimpses, zoom out: What story ties them together? Capture that as a paragraph. |
| **Drift Apex** | The furthest point from an expected path. | On a sidewalk or code trace, mark the moment something strayed. Note the cue that warned you. |
| **Stability Check** | Quick test of coherence, entanglement, and persistence. | After vectorizing, run the stability script and journal the scores plus what they imply. |
| **Zero Friction Index** | Shortcut score linking inner control to outer control. | Compare your stability scores with any external metric (traffic smoothness, battery drain). Adjust routines until the coupling improves. |

Practice loop: capture two glimpses, summarize one version, vectorize, run stability, then log what you learned. Repeat daily so the “glimpse muscle” stays fresh.

## Mental Model for Search – Locomotion ≈ Zoology
Use this checklist whenever you search for patterns in locomotion data. Treat each subject the way a field biologist treats an animal in motion.

1. **Name the species analog.** Decide whether the subject moves like a lone animal, a herd, or a flock. This gives you an instant baseline for cadence and spacing.
2. **Capture the gait signature.** Note stride length, tempo, and variability—just like recording gait cycles in zoology labs. These are your primary keywords for search.
3. **Log the habitat cues.** Temperature, obstacles, crowd density, and light conditions mirror the environmental notes a zoologist writes down. They narrow the search space.
4. **Map intent to animal behaviors.** Is the subject foraging, migrating, scouting, or escaping? Reframe the search question in those simple verbs so the engine knows what to highlight.
5. **Generate pattern hypotheses.** Expect certain cognition patterns based on the analog (e.g., flocking → `FLOW_MOTION + SPATIAL_RELATIONSHIPS`). List them before you run any queries.
6. **Run layered searches.** Start broad (all locomotion traces), then filter by gait signature, then by habitat cues. This mimics zooming from species to subspecies to individual.
7. **Evaluate stability like fitness.** Use coherence/entanglement/persistence to judge whether the motion is “fit” for its environment. If scores drop, assume the behavior is stressed.
8. **Journal the observation.** Close the loop with a short natural-language note (“Drift apex matched migrating geese pattern”). These notes replace the field notebook.

Following this loop keeps search grounded in familiar zoology logic while still producing machine-friendly vectors.

### Sticky Note – Online Search Prompts
Keep these quick notes visible when you open a browser:

1. "Locomotion zoology analogies" – collect diagrams comparing animal gaits with human navigation.
2. "Field biology data sheets" – borrow structure for logging habitat cues and drift events.
3. "Migration pattern visualization" – look for simple triangles or arcs that validate the Sidewalk Drift triangle.
4. "Flocking vs. solo movement metrics" – gather threshold ideas for entanglement/persistence scores.
5. "Biomechanics stride variability" – cross-check gait signatures with scientific baselines.
6. Jot any useful phrasing immediately into the research doc; don’t trust memory.

## Next Questions
1. Which additional senses (pressure, thermal) are necessary before scaling beyond K1 prerequisites?
2. How to embed stability metrics inside existing relationship analyzer outputs (`src/relationship_analyzer/...`)?
3. What data governance is required to treat observer states as planetary controls?
