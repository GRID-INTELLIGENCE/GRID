# Vision Layer: Visualizing Information as Force

**Role:** The visualization engine for the Grid/Circuits platform.
**Goal:** Render information propagation, influence trajectories, and assumption structures into human-perceptible flow graphs.

---

## Core Concept

If the **Sound Layer** is about *ambient monitoring* and *anomaly detection* (hearing the state), the **Vision Layer** is about *structural understanding* and *pathway tracing* (seeing the flow).

It translates the abstract physics of information (nodes, vectors, resonance) into concrete visual topology.

## First Principles

### 1. Structural Fidelity
The visual graph must reflect the underlying information model:
- **Entities** are nodes (points of accumulation).
- **Relationships** are edges (vectors of influence).
- **Flows** are paths (trajectories of propagation).

### 2. Assumption Tracking
Visualizations are interpretations. The system must explicitly render *why* a connection exists.
- "Inferred from name similarity"
- "Explicitly linked in source text"
- "Derived from pattern resonance"

### 3. Flow-First Topology
Unlike static knowledge graphs, the Vision Layer emphasizes **directionality** and **sequence**. Information moves; the visualization should imply motion or at least vector potential.

---

## Architecture (The Visualizer Engine)

The Visualizer operates as a transformation pipeline:

### 1. Inputs (Structured Data)
- **Concept Maps**: `concept_mappings.json`
- **Dialogue Flows**: `dialogue_flows.json`
- **Link Definitions**: `*_links.json` (Quantum, Hardware, AI)
- **Workflow Definitions**: Markdown tables defining directional derivatives.
- **Example Runs**: Trace logs of specific execution paths.

### 2. Process (The Engine)
1.  **Parse & Normalize**: Ingest heterogeneous inputs into a common graph model.
2.  **Build Graph**: Instantiate nodes (concepts, steps) and edges (sequences, links).
3.  **Pattern Application**: Apply flow rules (e.g., "Table rows imply sequence", "Dialogue implies teach->verify").
4.  **Assumption Logging**: Record every heuristic inference made during graph construction.

### 3. Outputs (The Renderable)
- **Graph JSON**: Standard node/edge format for renderers (D3, Cytoscape, Manim).
- **Named Flows**: Specific paths highlighted as distinct logical units (e.g., "Circle of Fifths Progression").
- **Assumptions List**: A sidecar dataset explaining the interpretive leaps.

---

## Visual Ontology

### Nodes (Information Nodes)
- **Concepts**: Static ideas or definitions.
- **Steps**: Actionable points in a workflow.
- **States**: Conditions of the system at a point in time.
- **Entities**: Agents or objects accumulating information.

### Edges (Influence Vectors)
- **Sequence**: A -> B (Temporal or logical progression).
- **Cross-link**: Lateral connections between domains (e.g., Music theory linking to Quantum mechanics).
- **Instance Path**: A specific trace of an executed run.
- **Influence**: A directional force vector (Polarity/Magnitude).

### Flows (Resonance Signatures)
- **Backbone**: The primary structural path (e.g., the main derivative table).
- **Dialogue**: Interactive loops (Anchor -> Teach -> Verify).
- **Example Run**: A concrete instantiation of a path.

---

## Integration with Sensory Goldilocks Zone

The Vision Layer contributes to **sensory coherence** by:
- Providing spatial structure to abstract data.
- Reducing cognitive load by making implicit connections explicit.
- working in unison with the Sound Layer (e.g., clicking a node triggers its sonic signature).

When vision (structure) and sound (state) align, the user perceives the "physics" of the information environment intuitively.
