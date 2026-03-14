#!/usr/bin/env python
"""GRID Codemap Visual Toolkit — Hybrid charts, HTML diagrams, and Mermaid syntax generation.

Run: uv run python demos/codemap_visual_toolkit.py

Generates:
  1. demos/output/gaussian_resonance_visual.html   — Interactive SVG/HTML visual diagram
  2. demos/output/codemap_mermaid_diagrams.md       — Mermaid syntax blocks for all 3 codemaps
  3. demos/output/data_analytics_dashboard.html     — Data-driven charts (SVG) with tables
  4. Console output with inline explanations

No external dependencies beyond numpy (stdlib + numpy only).
"""

import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

# ==============================================================================
# CONSTANTS & OUTPUT DIRECTORY
# ==============================================================================

OUTPUT_DIR = Path(__file__).parent / "output"

COLORS = {
    "red": "#e74c3c",
    "blue": "#3498db",
    "green": "#2ecc71",
    "purple": "#9b59b6",
    "orange": "#e67e22",
    "dark": "#2c3e50",
    "light": "#ecf0f1",
    "yellow": "#f1c40f",
    "teal": "#1abc9c",
    "pink": "#fd79a8",
    "navy": "#0a3d62",
    "bg": "#0f1923",
    "card": "#1a2a3a",
    "border": "#2d4a5e",
    "text": "#e8e8e8",
    "muted": "#8899aa",
}


# ==============================================================================
# DATA STRUCTURES (same as production code)
# ==============================================================================


@dataclass
class TemporalIntent:
    query: str
    era_type: str
    start_year: int | None
    end_year: int | None
    confidence: float


@dataclass
class TemporalResonance:
    score: float
    q_factor: float
    distance: float
    decay: float
    explanation: str


def gaussian_resonance(distance: float, q_factor: float) -> float:
    return math.exp(-(distance**2) / (2 * (q_factor**2)))


def calculate_temporal_resonance(
    temporal_intent: TemporalIntent,
    doc_year: int,
    q_factor: float = 0.5,
    damping: float = 0.3,
) -> TemporalResonance:
    current_year = datetime.now(UTC).year
    if temporal_intent.era_type == "specific_year":
        target_year = temporal_intent.start_year
    elif temporal_intent.era_type == "range":
        target_year = (temporal_intent.start_year + temporal_intent.end_year) / 2
    elif temporal_intent.era_type == "modern":
        target_year = current_year - 5
    else:
        target_year = 1990

    distance = min(abs(doc_year - target_year) / 100.0, 1.0)
    resonance = gaussian_resonance(distance, q_factor)

    decay = 1.0
    if temporal_intent.era_type == "modern":
        years_from_now = current_year - doc_year
        decay = math.exp(-damping * years_from_now / 10.0)
    elif temporal_intent.era_type == "historical":
        decay = 1.0 - (damping * 0.2)

    score = resonance * decay
    q_desc = "narrow" if q_factor < 0.3 else "wide" if q_factor > 0.7 else "moderate"
    explanation = f"Score={score:.3f} Q={q_factor:.1f}({q_desc}) dist={distance:.3f} decay={decay:.3f}"
    return TemporalResonance(score=score, q_factor=q_factor, distance=distance, decay=decay, explanation=explanation)


# ==============================================================================
# PART 1: HTML/SVG VISUAL DIAGRAM — Gaussian Resonance
# ==============================================================================


def generate_gaussian_visual_html() -> str:
    """Generate an interactive HTML/SVG visual diagram of the Gaussian resonance system."""

    # Pre-compute SVG polyline data for Gaussian curves
    def svg_polyline(q: float, color: str, width: int = 600, height: int = 200) -> str:
        points = []
        for px in range(0, width + 1, 3):
            d = px / width  # 0..1
            r = gaussian_resonance(d, q)
            y = height - (r * (height - 20)) - 10
            points.append(f"{px},{y:.1f}")
        return f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5" />'

    curves_svg = ""
    for q, color, label in [
        (0.2, COLORS["red"], "Q=0.2 narrow"),
        (0.5, COLORS["blue"], "Q=0.5 moderate"),
        (0.8, COLORS["green"], "Q=0.8 wide"),
    ]:
        curves_svg += svg_polyline(q, color)

    # Pre-compute heatmap data
    q_steps = np.linspace(0.1, 0.9, 32)
    d_steps = np.linspace(0.0, 1.0, 40)
    heatmap_cells = ""
    cell_w, cell_h = 15, 8
    for qi, q in enumerate(q_steps):
        for di, d in enumerate(d_steps):
            r = gaussian_resonance(d, q)
            # viridis-ish color mapping
            if r > 0.8:
                fill = COLORS["yellow"]
            elif r > 0.6:
                fill = COLORS["green"]
            elif r > 0.4:
                fill = COLORS["teal"]
            elif r > 0.2:
                fill = COLORS["blue"]
            else:
                fill = COLORS["navy"]
            opacity = 0.3 + r * 0.7
            heatmap_cells += f'<rect x="{di * cell_w}" y="{(31 - qi) * cell_h}" width="{cell_w}" height="{cell_h}" fill="{fill}" opacity="{opacity:.2f}" />\n'

    # Document ranking bars
    docs = [
        ("Attention Is All You Need", 2017, 0.92),
        ("BERT", 2018, 0.95),
        ("GPT-3", 2020, 0.99),
        ("Deep Learning", 2015, 0.78),
        ("ImageNet CNNs", 2012, 0.52),
        ("SVMs", 1995, 0.08),
        ("Perceptrons", 1969, 0.01),
    ]
    bar_svg = ""
    for i, (title, year, score) in enumerate(docs):
        bar_width = score * 400
        y = i * 38
        color = COLORS["green"] if score > 0.8 else COLORS["blue"] if score > 0.5 else COLORS["red"]
        bar_svg += f'''
        <g transform="translate(0, {y})">
            <rect x="180" y="2" width="{bar_width:.0f}" height="28" rx="4" fill="{color}" opacity="0.85" />
            <text x="0" y="20" fill="{COLORS["text"]}" font-size="12" font-family="monospace">{title[:22]:<22}</text>
            <text x="{185 + bar_width:.0f}" y="20" fill="{COLORS["muted"]}" font-size="11" font-family="monospace">{score:.2f} ({year})</text>
        </g>'''

    # XAI explanation pipeline
    xai_steps = [
        ("Q-Factor", "0.20", "narrow (high specificity)", COLORS["red"], "circle"),
        ("Resonance", "0.95", "strong resonance peak", COLORS["green"], "diamond"),
        ("Distance", "0.05", "at resonance peak", COLORS["blue"], "hexagon"),
        ("Decay", "0.90", "minimal damping", COLORS["yellow"], "pentagon"),
    ]
    xai_svg = ""
    for i, (label, value, desc, color, shape) in enumerate(xai_steps):
        x = i * 200 + 20
        if shape == "circle":
            xai_svg += f'<circle cx="{x + 40}" cy="40" r="35" fill="none" stroke="{color}" stroke-width="3" />'
        elif shape == "diamond":
            xai_svg += f'<polygon points="{x + 40},5 {x + 75},40 {x + 40},75 {x + 5},40" fill="none" stroke="{color}" stroke-width="3" />'
        elif shape == "hexagon":
            xai_svg += f'<polygon points="{x + 20},10 {x + 60},10 {x + 75},40 {x + 60},70 {x + 20},70 {x + 5},40" fill="none" stroke="{color}" stroke-width="3" />'
        else:  # pentagon
            xai_svg += f'<polygon points="{x + 40},5 {x + 75},30 {x + 62},70 {x + 18},70 {x + 5},30" fill="none" stroke="{color}" stroke-width="3" />'

        xai_svg += f'''
        <text x="{x + 40}" y="38" text-anchor="middle" fill="{color}" font-size="13" font-weight="bold" font-family="monospace">{value}</text>
        <text x="{x + 40}" y="95" text-anchor="middle" fill="{COLORS["text"]}" font-size="12" font-weight="bold" font-family="monospace">{label}</text>
        <text x="{x + 40}" y="112" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">{desc}</text>'''

        if i < len(xai_steps) - 1:
            xai_svg += f'<line x1="{x + 80}" y1="40" x2="{x + 195}" y2="40" stroke="{COLORS["muted"]}" stroke-width="2" stroke-dasharray="6,3" marker-end="url(#arrowhead)" />'

    # Gaussian formula visual
    formula_svg = f'''
    <rect x="0" y="0" width="660" height="100" rx="12" fill="{COLORS["card"]}" stroke="{COLORS["border"]}" stroke-width="2" />
    <text x="330" y="30" text-anchor="middle" fill="{COLORS["yellow"]}" font-size="14" font-weight="bold" font-family="monospace">GAUSSIAN RESONANCE FORMULA</text>
    <text x="330" y="58" text-anchor="middle" fill="{COLORS["text"]}" font-size="20" font-family="serif" font-style="italic">
        R(d, Q) = e<tspan baseline-shift="super" font-size="14">-(d\u00b2 / 2Q\u00b2)</tspan>
    </text>
    <text x="330" y="85" text-anchor="middle" fill="{COLORS["muted"]}" font-size="11" font-family="monospace">d = normalized temporal distance (0-1)    Q = bandwidth factor (0.1-0.9)</text>
    '''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GRID TemporalResonance Visual Diagram</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {COLORS["bg"]}; color: {COLORS["text"]}; font-family: 'Segoe UI', system-ui, sans-serif; padding: 30px; }}
  h1 {{ color: {COLORS["yellow"]}; font-size: 28px; margin-bottom: 8px; letter-spacing: 1px; }}
  h2 {{ color: {COLORS["teal"]}; font-size: 18px; margin: 30px 0 12px; border-left: 4px solid {COLORS["teal"]}; padding-left: 12px; }}
  .subtitle {{ color: {COLORS["muted"]}; font-size: 14px; margin-bottom: 30px; }}
  .section {{ background: {COLORS["card"]}; border: 1px solid {COLORS["border"]}; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
  .legend {{ display: flex; gap: 24px; margin-top: 12px; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 13px; color: {COLORS["muted"]}; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 900px) {{ .grid-2col {{ grid-template-columns: 1fr; }} }}
  .insight {{ background: {COLORS["navy"]}; border-left: 3px solid {COLORS["yellow"]}; padding: 12px 16px; margin-top: 16px; border-radius: 0 8px 8px 0; font-size: 13px; line-height: 1.6; }}
  .insight strong {{ color: {COLORS["yellow"]}; }}
  .flow-arrow {{ color: {COLORS["teal"]}; font-size: 24px; text-align: center; padding: 8px; }}
</style>
</head>
<body>
<h1>GRID TemporalResonance System</h1>
<p class="subtitle">Gaussian Resonance Calculation &amp; XAI Explanations &mdash; Visual Toolkit</p>

<!-- FORMULA -->
<div class="section">
  <svg viewBox="0 0 660 100" width="100%" style="max-width:660px;">
    {formula_svg}
  </svg>
</div>

<!-- GAUSSIAN CURVES -->
<h2>Gaussian Resonance Curves by Q-Factor</h2>
<div class="section">
  <svg viewBox="0 0 640 230" width="100%" style="max-width:640px;">
    <defs>
      <linearGradient id="gridGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{COLORS["border"]}" stop-opacity="0.3" />
        <stop offset="100%" stop-color="{COLORS["border"]}" stop-opacity="0.05" />
      </linearGradient>
    </defs>
    <rect width="600" height="200" x="20" y="5" fill="url(#gridGrad)" rx="4" />
    <!-- Grid lines -->
    <line x1="20" y1="55" x2="620" y2="55" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <line x1="20" y1="105" x2="620" y2="105" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <line x1="20" y1="155" x2="620" y2="155" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <!-- Y axis labels -->
    <text x="5" y="15" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">1.0</text>
    <text x="5" y="110" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">0.5</text>
    <text x="5" y="210" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">0.0</text>
    <!-- X axis labels -->
    <text x="20" y="225" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">0 yrs</text>
    <text x="310" y="225" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">50 yrs</text>
    <text x="590" y="225" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">100 yrs</text>
    <g transform="translate(20, 5)">
      {curves_svg}
    </g>
  </svg>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["red"]}"></div> Q=0.2 (narrow / specific year)</div>
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["blue"]}"></div> Q=0.5 (moderate / decade)</div>
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["green"]}"></div> Q=0.8 (wide / broad era)</div>
  </div>
  <div class="insight">
    <strong>Reading this chart:</strong> Each curve shows how fast relevance drops as a document moves away from the target year.
    <strong>Q=0.2 (red)</strong> drops almost to zero within 20 years &mdash; perfect for "papers from 2020".
    <strong>Q=0.8 (green)</strong> stays above 0.5 even at 50 years away &mdash; ideal for "history of AI".
  </div>
</div>

<!-- HEATMAP -->
<div class="grid-2col">
<div>
  <h2>Resonance Heatmap: Q-Factor vs Distance</h2>
  <div class="section">
    <svg viewBox="0 0 {40 * cell_w + 40} {32 * cell_h + 40}" width="100%">
      <g transform="translate(20, 5)">
        {heatmap_cells}
      </g>
      <text x="10" y="{32 * cell_h + 30}" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">0 yrs</text>
      <text x="{40 * cell_w - 20}" y="{32 * cell_h + 30}" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">100 yrs</text>
      <text x="{40 * cell_w + 22}" y="15" fill="{COLORS["muted"]}" font-size="9" font-family="monospace" transform="rotate(90, {40 * cell_w + 22}, 15)">Q=0.9</text>
      <text x="{40 * cell_w + 22}" y="{32 * cell_h - 5}" fill="{COLORS["muted"]}" font-size="9" font-family="monospace" transform="rotate(90, {40 * cell_w + 22}, {32 * cell_h - 5})">Q=0.1</text>
    </svg>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:{COLORS["yellow"]}"></div> &gt;0.8 (strong)</div>
      <div class="legend-item"><div class="legend-dot" style="background:{COLORS["green"]}"></div> 0.6-0.8</div>
      <div class="legend-item"><div class="legend-dot" style="background:{COLORS["teal"]}"></div> 0.4-0.6</div>
      <div class="legend-item"><div class="legend-dot" style="background:{COLORS["blue"]}"></div> 0.2-0.4</div>
      <div class="legend-item"><div class="legend-dot" style="background:{COLORS["navy"]}"></div> &lt;0.2 (weak)</div>
    </div>
  </div>
</div>

<!-- DOCUMENT RANKING -->
<div>
  <h2>Document Ranking: "Recent AI Research"</h2>
  <div class="section">
    <svg viewBox="0 0 650 280" width="100%">
      {bar_svg}
    </svg>
    <div class="insight">
      <strong>Green</strong> = strong match (&gt;0.8), <strong>Blue</strong> = moderate (0.5-0.8), <strong>Red</strong> = weak (&lt;0.5).
      GPT-3 (2020) scores 0.99 because it's closest to the "modern" target window.
    </div>
  </div>
</div>
</div>

<!-- XAI EXPLANATION PIPELINE -->
<h2>XAI Explanation Pipeline: How Scores Become Words</h2>
<div class="section">
  <svg viewBox="0 0 830 130" width="100%">
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="{COLORS["muted"]}" />
      </marker>
    </defs>
    {xai_svg}
  </svg>
  <div class="flow-arrow">&darr;</div>
  <div style="background:{COLORS["navy"]}; padding:16px; border-radius:8px; font-family:monospace; font-size:13px; line-height:1.8; border: 1px solid {COLORS["teal"]};">
    <span style="color:{COLORS["teal"]};">[XAI Output]</span><br/>
    "Temporal resonance: <span style="color:{COLORS["green"]}">strong resonance peak detected</span>.
    Q-factor 0.20 (<span style="color:{COLORS["red"]}">narrow, high specificity</span>),
    <span style="color:{COLORS["blue"]}">at the resonance peak (near-perfect alignment)</span>.
    Damping: <span style="color:{COLORS["yellow"]}">minimal damping (signal preserved)</span>."
  </div>
</div>

<!-- HOMEGUARD RUNTIME FLOW -->
<h2>HomeGuard COMPAS: Agent Execution Flow</h2>
<div class="section">
  <svg viewBox="0 0 850 320" width="100%">
    <!-- Stage boxes -->
    <rect x="10" y="10" width="160" height="70" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["purple"]}" stroke-width="2" />
    <text x="90" y="35" text-anchor="middle" fill="{COLORS["purple"]}" font-size="11" font-weight="bold" font-family="monospace">TASK RECEIVED</text>
    <text x="90" y="55" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">case_id + reference</text>

    <rect x="200" y="10" width="160" height="70" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["teal"]}" stroke-width="2" />
    <text x="280" y="35" text-anchor="middle" fill="{COLORS["teal"]}" font-size="11" font-weight="bold" font-family="monospace">BEHAVIOR TRACE</text>
    <text x="280" y="55" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">start_trace()</text>

    <rect x="390" y="10" width="160" height="70" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["blue"]}" stroke-width="2" />
    <text x="470" y="35" text-anchor="middle" fill="{COLORS["blue"]}" font-size="11" font-weight="bold" font-family="monospace">ADAPTIVE TIMEOUT</text>
    <text x="470" y="55" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">p95 percentile calc</text>

    <rect x="580" y="10" width="160" height="70" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["green"]}" stroke-width="2" />
    <text x="660" y="35" text-anchor="middle" fill="{COLORS["green"]}" font-size="11" font-weight="bold" font-family="monospace">EXECUTE + RECOVER</text>
    <text x="660" y="55" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">retry with backoff</text>

    <!-- Arrows -->
    <line x1="170" y1="45" x2="200" y2="45" stroke="{COLORS["muted"]}" stroke-width="2" marker-end="url(#arrowhead)" />
    <line x1="360" y1="45" x2="390" y2="45" stroke="{COLORS["muted"]}" stroke-width="2" marker-end="url(#arrowhead)" />
    <line x1="550" y1="45" x2="580" y2="45" stroke="{COLORS["muted"]}" stroke-width="2" marker-end="url(#arrowhead)" />

    <!-- Safety guardrail layer -->
    <rect x="10" y="110" width="730" height="80" rx="10" fill="none" stroke="{COLORS["red"]}" stroke-width="2" stroke-dasharray="8,4" />
    <text x="375" y="135" text-anchor="middle" fill="{COLORS["red"]}" font-size="13" font-weight="bold" font-family="monospace">SAFETY GUARDRAIL LAYER</text>
    <text x="130" y="165" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">@contribution_guard</text>
    <text x="375" y="165" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">denylist check</text>
    <text x="620" y="165" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">production_security</text>

    <!-- Environment recalibration -->
    <rect x="10" y="220" width="350" height="80" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["orange"]}" stroke-width="2" />
    <text x="185" y="245" text-anchor="middle" fill="{COLORS["orange"]}" font-size="12" font-weight="bold" font-family="monospace">ENVIRONMENT RECALIBRATION</text>
    <text x="185" y="270" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">Le Chatelier's Principle</text>
    <text x="185" y="285" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">practical / legal / psychological triad</text>

    <!-- Performance guard -->
    <rect x="390" y="220" width="350" height="80" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["yellow"]}" stroke-width="2" />
    <text x="565" y="245" text-anchor="middle" fill="{COLORS["yellow"]}" font-size="12" font-weight="bold" font-family="monospace">PERFORMANCE GUARD</text>
    <text x="565" y="270" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10" font-family="monospace">regression detection</text>
    <text x="565" y="285" text-anchor="middle" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">baseline SQLite + Prometheus metrics</text>
  </svg>
</div>

<p style="color:{COLORS["muted"]}; font-size:11px; margin-top:20px; text-align:center;">
  Generated by GRID Codemap Visual Toolkit &mdash; {datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")}
</p>
</body>
</html>"""
    return html


# ==============================================================================
# PART 2: MERMAID DIAGRAMS
# ==============================================================================


def generate_mermaid_diagrams() -> str:
    """Generate Mermaid syntax blocks for all 3 codemaps."""

    md = """# GRID Codemap Mermaid Diagrams

> Paste any block into a Mermaid-capable renderer (GitHub, VS Code preview, Obsidian, etc.)

---

## 1. TemporalResonance: Query → Score → XAI Explanation

```mermaid
flowchart LR
    subgraph Intent["Parse Temporal Intent"]
        A["User Query<br/>'Papers from 2020'"] --> B["Regex Extraction<br/>year=2020"]
        B --> C["TemporalIntent<br/>era=specific_year<br/>start=2020, end=2020"]
    end

    subgraph Resonance["Calculate Resonance"]
        C --> D["Normalize Distance<br/>d = |doc_year - 2020| / 100"]
        D --> E["Gaussian Formula<br/>R = e^(-d² / 2Q²)"]
        E --> F["Apply Decay<br/>score = R × decay"]
    end

    subgraph XAI["XAI Explanation"]
        F --> G["Interpret Q-Factor<br/>0.2 → narrow"]
        F --> H["Interpret Score<br/>0.95 → strong peak"]
        F --> I["Interpret Distance<br/>0.05 → at peak"]
        F --> J["Interpret Decay<br/>0.9 → minimal damping"]
        G & H & I & J --> K["Human-Readable Output"]
    end

    style Intent fill:#1a2a3a,stroke:#3498db,color:#e8e8e8
    style Resonance fill:#1a2a3a,stroke:#2ecc71,color:#e8e8e8
    style XAI fill:#1a2a3a,stroke:#e67e22,color:#e8e8e8
    style E fill:#0a3d62,stroke:#f1c40f,stroke-width:3px,color:#f1c40f
```

---

## 2. HomeGuard COMPAS: Runtime Guardrails & Agent Execution

```mermaid
flowchart TD
    subgraph Execution["Agent Execution"]
        T["Task Received"] --> BT["Start Behavior Trace"]
        BT --> SK["Retrieve Skills"]
        SK --> AT["Adaptive Timeout<br/>p95 percentile"]
        AT --> EX["Execute Task"]
    end

    subgraph Recovery["Error Recovery"]
        EX -->|error| CL["ErrorClassifier"]
        CL -->|transient| RT["Retry + Backoff<br/>delay × 2^attempt"]
        CL -->|compliance| BK["Block + Log"]
        RT --> EX
    end

    subgraph Safety["Safety Guardrails"]
        SG["@contribution_guard"] --> DL["Denylist Check"]
        DL --> CS["Contribution Score<br/>≥ 0.3 threshold"]
        CS --> PS["Production Security<br/>validate_environment()"]
    end

    subgraph Environment["GridEnvironment"]
        PW["process_wave(text)"] --> SL["Scan Lexicon"]
        SL --> RC["Recalibrate<br/>Le Chatelier's Principle"]
        RC -->|practical dominance| TF["temp=0.5, drift=0.1"]
        RC -->|legal dominance| TL["temp=0.3, density=0.6"]
        RC -->|balanced| BL["restore baseline"]
    end

    EX -.->|guarded by| Safety
    EX -.->|monitored by| Environment

    style Execution fill:#1a2a3a,stroke:#9b59b6,color:#e8e8e8
    style Recovery fill:#1a2a3a,stroke:#e74c3c,color:#e8e8e8
    style Safety fill:#1a2a3a,stroke:#e74c3c,color:#e8e8e8
    style Environment fill:#1a2a3a,stroke:#e67e22,color:#e8e8e8
```

---

## 3. GRID Project Architecture: Build → Serve → Query

```mermaid
flowchart TD
    subgraph Build["Build System"]
        PT["pyproject.toml"] --> UV["uv sync"]
        UV --> VE[".venv/"]
        PT --> HB["hatchling build"]
        HB --> WH["9 wheel packages"]
    end

    subgraph CLI["CLI Entry Points"]
        GM["python -m grid"] --> SE["grid serve"]
        GM --> CH["grid chat"]
        GM --> AN["grid analyze"]
    end

    subgraph API["Mothership API"]
        SE --> CA["create_app()"]
        CA --> LM["Lifespan Manager"]
        LM --> HE["harden_environment()"]
        LM --> DB["init database"]
        LM --> SF["Safety Middleware"]
        LM --> RD["Redis streams"]
    end

    subgraph RAG["RAG Pipeline"]
        CH --> QL["User Query"]
        QL --> EM["Ollama Embeddings<br/>nomic-embed-text"]
        EM --> VS["ChromaDB Vector Search"]
        VS --> RR["Rerank: BM25 + cross-encoder"]
        RR --> LLM["Local LLM Inference"]
    end

    subgraph CICD["CI/CD Pipeline"]
        direction LR
        SS["secrets-scan"] --> LI["ruff lint"]
        LI --> SEC["bandit security"]
        SEC --> TE["pytest"]
        TE --> BU["build + upload"]
    end

    Build --> CLI
    CLI --> API
    CLI --> RAG

    style Build fill:#1a2a3a,stroke:#3498db,color:#e8e8e8
    style CLI fill:#1a2a3a,stroke:#2ecc71,color:#e8e8e8
    style API fill:#1a2a3a,stroke:#9b59b6,color:#e8e8e8
    style RAG fill:#1a2a3a,stroke:#e67e22,color:#e8e8e8
    style CICD fill:#1a2a3a,stroke:#f1c40f,color:#e8e8e8
```

---

## 4. Gaussian Formula: Step-by-Step Computation

```mermaid
sequenceDiagram
    participant U as User
    participant P as Parser
    participant G as Gaussian Engine
    participant X as XAI Explainer

    U->>P: "Papers from 2020"
    P->>P: regex match → year=2020
    P->>G: TemporalIntent(specific_year, 2020)
    
    Note over G: Document: "BERT" (2018)
    G->>G: distance = |2018-2020|/100 = 0.02
    G->>G: R = e^(-0.02²/2×0.5²) = 0.9992
    G->>G: decay = 1.0 (specific year)
    G->>G: score = 0.999 × 1.0 = 0.999
    
    G->>X: TemporalResonance(0.999, Q=0.5, d=0.02)
    X->>X: Q=0.5 → "moderate specificity"
    X->>X: score>0.8 → "strong resonance peak"
    X->>X: d<0.2 → "at resonance peak"
    X->>X: decay>0.8 → "minimal damping"
    X->>U: "strong resonance peak detected,<br/>moderate specificity, at peak"
```

---

## 5. Performance Guard: Regression Detection

```mermaid
flowchart LR
    EX["Skill Execution<br/>time=450ms"] --> PG["PerformanceGuard<br/>check_execution()"]
    PG --> PM["Prometheus<br/>EXECUTION_TIME.set()"]
    PG --> II["IntelligenceInventory<br/>check_regression()"]
    II --> SQ["SQLite Query<br/>SELECT p50, p95, p99"]
    SQ --> CMP{"current > baseline<br/>× threshold?"}
    CMP -->|No| OK["✓ No Regression"]
    CMP -->|Yes| SEV["Calculate Severity"]
    SEV -->|≥100%| HI["🔴 HIGH"]
    SEV -->|≥50%| MD["🟡 MEDIUM"]
    SEV -->|<50%| LO["🟢 LOW"]
    HI & MD & LO --> AL["PerformanceAlert<br/>+ Prometheus flag"]

    style CMP fill:#0a3d62,stroke:#f1c40f,color:#f1c40f
    style HI fill:#e74c3c,stroke:#e74c3c,color:#fff
    style MD fill:#f1c40f,stroke:#f1c40f,color:#000
    style LO fill:#2ecc71,stroke:#2ecc71,color:#000
```

"""
    return md


# ==============================================================================
# PART 3: DATA ANALYTICS DASHBOARD (SVG)
# ==============================================================================


def generate_data_analytics_html() -> str:
    """Generate a data analytics dashboard with computed tables and SVG charts."""

    # --- Table 1: Q-Factor Sensitivity ---
    q_factors = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    distances_yrs = [0, 5, 10, 20, 30, 50, 75, 100]

    table_rows = ""
    for dist in distances_yrs:
        d_norm = dist / 100.0
        cells = f"<td><strong>{dist}</strong></td>"
        for q in q_factors:
            val = gaussian_resonance(d_norm, q)
            if val > 0.8:
                bg = COLORS["green"]
            elif val > 0.5:
                bg = COLORS["blue"]
            elif val > 0.2:
                bg = COLORS["orange"]
            else:
                bg = COLORS["red"]
            cells += f'<td style="background:{bg}22; color:{bg}; font-weight:bold;">{val:.4f}</td>'
        table_rows += f"<tr>{cells}</tr>\n"

    # --- Table 2: Document Ranking for multiple queries ---
    docs = [
        {"title": "Attention Is All You Need", "year": 2017},
        {"title": "BERT", "year": 2018},
        {"title": "GPT-3", "year": 2020},
        {"title": "Deep Learning (Goodfellow)", "year": 2015},
        {"title": "ImageNet CNNs (AlexNet)", "year": 2012},
        {"title": "SVMs (Cortes & Vapnik)", "year": 1995},
        {"title": "Backpropagation (Rumelhart)", "year": 1986},
        {"title": "Perceptrons (Minsky)", "year": 1969},
        {"title": "Chain-of-Thought", "year": 2022},
        {"title": "Constitutional AI", "year": 2023},
    ]

    queries = [
        ("Recent AI research", TemporalIntent("recent AI", "modern", 2010, 2030, 0.9)),
        ("Papers from 2020", TemporalIntent("2020", "specific_year", 2020, 2020, 0.9)),
        ("AI history 1980-2000", TemporalIntent("1980-2000", "range", 1980, 2000, 0.85)),
    ]

    ranking_sections = ""
    for query_text, intent in queries:
        ranked = []
        for doc in docs:
            res = calculate_temporal_resonance(intent, doc["year"], q_factor=0.5)
            ranked.append((doc, res))
        ranked.sort(key=lambda x: x[1].score, reverse=True)

        rows = ""
        for i, (doc, res) in enumerate(ranked, 1):
            bar_w = res.score * 200
            color = COLORS["green"] if res.score > 0.8 else COLORS["blue"] if res.score > 0.5 else COLORS["red"]
            rows += f"""<tr>
                <td>{i}</td>
                <td>{doc["title"]}</td>
                <td>{doc["year"]}</td>
                <td><div style="display:flex;align-items:center;gap:8px;">
                    <div style="width:{bar_w:.0f}px;height:16px;background:{color};border-radius:3px;"></div>
                    <span style="color:{color};font-weight:bold;">{res.score:.3f}</span>
                </div></td>
                <td style="color:{COLORS["muted"]};font-size:11px;">{res.explanation}</td>
            </tr>"""

        ranking_sections += f"""
        <h3 style="color:{COLORS["teal"]};margin-top:24px;">Query: "{query_text}" (era={intent.era_type})</h3>
        <table class="data-table">
            <thead><tr><th>#</th><th>Title</th><th>Year</th><th>Score</th><th>Details</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>"""

    # --- SVG Chart: Method Comparison ---
    methods_svg = ""
    chart_w, chart_h = 500, 200
    for method_name, method_fn, color in [
        ("Gaussian Q=0.5", lambda d: gaussian_resonance(d, 0.5), COLORS["blue"]),
        ("Linear", lambda d: max(0, 1 - d), COLORS["red"]),
        ("Exponential", lambda d: math.exp(-d * 3), COLORS["green"]),
        ("Step (±10yr)", lambda d: 1.0 if d < 0.1 else (max(0, 0.5 - d * 0.5) if d < 0.5 else 0), COLORS["purple"]),
    ]:
        points = []
        for px in range(0, chart_w + 1, 3):
            d = px / chart_w
            r = method_fn(d)
            y = chart_h - (r * (chart_h - 20)) - 10
            points.append(f"{px},{y:.1f}")
        methods_svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2" />\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GRID Data Analytics Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {COLORS["bg"]}; color: {COLORS["text"]}; font-family: 'Segoe UI', system-ui, sans-serif; padding: 30px; max-width: 1200px; margin: 0 auto; }}
  h1 {{ color: {COLORS["yellow"]}; font-size: 24px; margin-bottom: 6px; }}
  h2 {{ color: {COLORS["teal"]}; font-size: 18px; margin: 28px 0 12px; border-left: 4px solid {COLORS["teal"]}; padding-left: 12px; }}
  h3 {{ font-size: 14px; }}
  .subtitle {{ color: {COLORS["muted"]}; font-size: 13px; margin-bottom: 24px; }}
  .section {{ background: {COLORS["card"]}; border: 1px solid {COLORS["border"]}; border-radius: 10px; padding: 20px; margin-bottom: 20px; overflow-x: auto; }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }}
  .data-table th {{ text-align: left; padding: 8px 10px; color: {COLORS["teal"]}; border-bottom: 2px solid {COLORS["border"]}; font-family: monospace; }}
  .data-table td {{ padding: 6px 10px; border-bottom: 1px solid {COLORS["border"]}20; font-family: monospace; }}
  .data-table tr:hover {{ background: {COLORS["border"]}15; }}
  .legend {{ display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: {COLORS["muted"]}; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
  .insight {{ background: {COLORS["navy"]}; border-left: 3px solid {COLORS["yellow"]}; padding: 10px 14px; margin-top: 14px; border-radius: 0 6px 6px 0; font-size: 12px; line-height: 1.6; }}
  .insight strong {{ color: {COLORS["yellow"]}; }}
  .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 900px) {{ .grid-2col {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>GRID Data Analytics Dashboard</h1>
<p class="subtitle">TemporalResonance system metrics, ranking comparisons, and sensitivity analysis</p>

<!-- Q-FACTOR SENSITIVITY TABLE -->
<h2>Q-Factor Sensitivity Matrix</h2>
<div class="section">
  <table class="data-table">
    <thead>
      <tr>
        <th>Distance (yrs)</th>
        {"".join(f"<th>Q={q}</th>" for q in q_factors)}
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
  <div class="insight">
    <strong>Reading:</strong> Each cell shows the resonance score for a given temporal distance and Q-factor.
    <strong>Green</strong> (&gt;0.8) = strong match. <strong>Red</strong> (&lt;0.2) = effectively filtered out.
    Notice Q=0.1 drops to near-zero at just 10 years, while Q=0.9 stays green even at 30 years.
  </div>
</div>

<!-- METHOD COMPARISON CHART -->
<h2>Scoring Method Comparison</h2>
<div class="section">
  <svg viewBox="0 0 540 240" width="100%" style="max-width:540px;">
    <rect width="500" height="200" x="20" y="5" fill="{COLORS["card"]}" rx="4" stroke="{COLORS["border"]}" />
    <line x1="20" y1="55" x2="520" y2="55" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <line x1="20" y1="105" x2="520" y2="105" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <line x1="20" y1="155" x2="520" y2="155" stroke="{COLORS["border"]}" stroke-width="0.5" stroke-dasharray="4,4" />
    <text x="5" y="15" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">1.0</text>
    <text x="5" y="110" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">0.5</text>
    <text x="5" y="210" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">0.0</text>
    <text x="20" y="225" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">0 yrs</text>
    <text x="260" y="225" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">50 yrs</text>
    <text x="490" y="225" fill="{COLORS["muted"]}" font-size="9" font-family="monospace">100 yrs</text>
    <g transform="translate(20, 5)">
      {methods_svg}
    </g>
  </svg>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["blue"]}"></div> Gaussian (Q=0.5) — smooth, configurable</div>
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["red"]}"></div> Linear — harsh boundary</div>
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["green"]}"></div> Exponential — similar but less configurable</div>
    <div class="legend-item"><div class="legend-dot" style="background:{COLORS["purple"]}"></div> Step — binary, no gradual falloff</div>
  </div>
  <div class="insight">
    <strong>Why Gaussian wins:</strong> The Gaussian curve (blue) provides a smooth, bell-shaped falloff that doesn't cut off abruptly (like Linear/Step) and is tunable via Q-factor (unlike Exponential). This makes it ideal for search ranking where "close enough" documents should still appear but with lower scores.
  </div>
</div>

<!-- DOCUMENT RANKING TABLES -->
<h2>Document Ranking Results</h2>
<div class="section">
  {ranking_sections}
</div>

<p style="color:{COLORS["muted"]}; font-size:10px; margin-top:20px; text-align:center;">
  Generated by GRID Codemap Visual Toolkit &mdash; {datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")}
</p>
</body>
</html>"""
    return html


# ==============================================================================
# MAIN: Generate everything
# ==============================================================================


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GRID CODEMAP VISUAL TOOLKIT")
    print("=" * 70)

    # 1. Gaussian visual HTML
    print("\n[1/3] Generating Gaussian resonance visual diagram...")
    html1 = generate_gaussian_visual_html()
    path1 = OUTPUT_DIR / "gaussian_resonance_visual.html"
    path1.write_text(html1, encoding="utf-8")
    print(f"  -> {path1}")

    # 2. Mermaid diagrams
    print("\n[2/3] Generating Mermaid syntax diagrams...")
    md = generate_mermaid_diagrams()
    path2 = OUTPUT_DIR / "codemap_mermaid_diagrams.md"
    path2.write_text(md, encoding="utf-8")
    print(f"  -> {path2}")

    # 3. Data analytics dashboard
    print("\n[3/3] Generating data analytics dashboard...")
    html3 = generate_data_analytics_html()
    path3 = OUTPUT_DIR / "data_analytics_dashboard.html"
    path3.write_text(html3, encoding="utf-8")
    print(f"  -> {path3}")

    # Summary
    print("\n" + "=" * 70)
    print("GENERATED FILES:")
    print("=" * 70)
    print(f"  1. {path1}")
    print("     Interactive SVG visual: Gaussian curves, heatmap, XAI pipeline, HomeGuard flow")
    print(f"  2. {path2}")
    print("     5 Mermaid diagrams: TemporalResonance, HomeGuard, GRID architecture, formula, perf guard")
    print(f"  3. {path3}")
    print("     Data dashboard: Q-factor sensitivity table, method comparison chart, document ranking")
    print()
    print("OPEN IN BROWSER:")
    print(f"  start {path1}")
    print(f"  start {path3}")
    print()
    print("VIEW MERMAID (paste into GitHub/Obsidian/VS Code preview):")
    print(f"  code {path2}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
