# GRID: Architectural Reasoning
**The Philosophy of Geometric Resonance**

This document explains the technical "Why" behind the core architectural choices in GRID.

---

## 1. Why B-splines for Motion?
**Challenge**: Robotic movement data is often noisy, high-frequency, and difficult to generalize.
**Solution**: GRID uses **B-splines** (via `BSplineEncoder`) to project discrete movement patterns into a continuous, differentiable space.
- **Benefit**: Smooths jerky movements automatically.
- **Benefit**: Reduces 1,000+ data points into 16 control points, drastically lowering the dimensionality of the diffusion task.

---

## 2. Why Diffusion Models over GANs?
**Challenge**: GANs (Generative Adversarial Networks) are prone to mode collapse and struggle with the multimodality of complex trajectories.
**Solution**: **Motion Planning Diffusion (MPD)** learns a score-based prior over the entire trajectory space.
- **Benefit**: Can sample thousands of valid trajectories for the same start/goal pair.
- **Benefit**: Allows "Cost-Guided Sampling" where the AI can "steer" the trajectory during the denoising process without retraining.

---

## 3. Why Hybrid RAG (Vector + BM25)?
**Challenge**: Pure vector search (semantic) often misses specific technical identifiers (e.g., `GGML_ASSERT`), while Keyword search misses the "concept" of the error.
**Solution**: A **Hybrid Retrieval** architecture.
- **Benefit**: Vector search handles "How do I setup GRID?".
- **Benefit**: BM25 handles "Where is the `BSplineTrajectory` class located?".
- **Sync**: Result ranking is merged via Reciprocal Rank Fusion (RRF).

---

## 4. Why Navy Amber (Aesthetics)?
**Challenge**: Engineering burnout and "interface fatigue" in high-complexity environments.
**Solution**: A high-tension, high-contrast palette.
- **Navy**: Reduces eye strain during 12+ hour sprint cycles.
- **Amber**: Provides focused "signal" (600nm wavelength) for critical variables and errors.

---

**Philosophy**: *Precision through Resonance.*
**Last Revised**: 2026-01-06
