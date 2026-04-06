/**
 * Force-directed layout helpers for knowledge graphs.
 *
 * `computeForceLayout` preserves the original full-pair simulation.
 * `computeSampledForceLayout` uses sampled repulsion for larger graphs.
 */

export interface LayoutNode {
  id: string;
}

export interface LayoutEdge {
  source: string;
  target: string;
}

export interface PositionedNode {
  id: string;
  x: number;
  y: number;
}

interface SimPoint {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface LayoutOptions {
  iterations?: number;
  margin?: number;
}

interface SimConfig {
  iterations: number;
  margin: number;
  repulsion: number;
  attraction: number;
  damping: number;
  repulsionSamples?: number;
}

function initPositions(
  nodes: LayoutNode[],
  width: number,
  height: number
): { positions: Map<string, SimPoint>; ids: string[] } {
  const cx = width / 2;
  const cy = height / 2;
  const n = nodes.length;
  const r0 = Math.min(width, height) * 0.32;

  const positions = new Map<string, SimPoint>();
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(n, 1);
    positions.set(node.id, {
      x: cx + r0 * Math.cos(angle),
      y: cy + r0 * Math.sin(angle),
      vx: 0,
      vy: 0,
    });
  });

  return { positions, ids: nodes.map((x) => x.id) };
}

function simulate(
  positions: Map<string, SimPoint>,
  ids: string[],
  edges: LayoutEdge[],
  width: number,
  height: number,
  config: SimConfig
): Map<string, PositionedNode> {
  const {
    iterations,
    margin,
    repulsion,
    attraction,
    damping,
    repulsionSamples,
  } = config;
  const n = ids.length;

  for (let iter = 0; iter < iterations; iter++) {
    if (typeof repulsionSamples === "number") {
      const sampleCount = Math.max(
        2,
        Math.min(repulsionSamples, Math.max(2, n - 1))
      );
      const stride = Math.max(1, Math.floor((n - 1) / sampleCount));
      for (let i = 0; i < n; i++) {
        const a = positions.get(ids[i]);
        if (!a) continue;
        for (let s = 1; s <= sampleCount; s++) {
          const j = (i + s * stride + iter) % n;
          if (j === i) continue;
          const b = positions.get(ids[j]);
          if (!b) continue;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
          const f = repulsion / (dist * dist);
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }
    } else {
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const a = positions.get(ids[i]);
          const b = positions.get(ids[j]);
          if (!a || !b) continue;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
          const f = repulsion / (dist * dist);
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }
    }

    for (const edge of edges) {
      const a = positions.get(edge.source);
      const b = positions.get(edge.target);
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const f = attraction * dist;
      const fx = (dx / dist) * f;
      const fy = (dy / dist) * f;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    for (const id of ids) {
      const p = positions.get(id);
      if (!p) continue;
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= damping;
      p.vy *= damping;
      p.x = Math.max(margin, Math.min(width - margin, p.x));
      p.y = Math.max(margin, Math.min(height - margin, p.y));
    }
  }

  const out = new Map<string, PositionedNode>();
  for (const id of ids) {
    const p = positions.get(id);
    if (p) out.set(id, { id, x: p.x, y: p.y });
  }
  return out;
}

/**
 * Original full-pair simulation: O(n²) repulsion.
 */
export function computeForceLayout(
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  width: number,
  height: number,
  options?: LayoutOptions
): Map<string, PositionedNode> {
  const { positions, ids } = initPositions(nodes, width, height);
  return simulate(positions, ids, edges, width, height, {
    iterations: options?.iterations ?? 220,
    margin: options?.margin ?? 44,
    repulsion: 2800,
    attraction: 0.028,
    damping: 0.88,
  });
}

/**
 * Sampled repulsion simulation: near O(n * k) for k sampled neighbors.
 */
export function computeSampledForceLayout(
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  width: number,
  height: number,
  options?: LayoutOptions & { repulsionSamples?: number }
): Map<string, PositionedNode> {
  const { positions, ids } = initPositions(nodes, width, height);
  return simulate(positions, ids, edges, width, height, {
    iterations: options?.iterations ?? 120,
    margin: options?.margin ?? 40,
    repulsion: 2300,
    attraction: 0.022,
    damping: 0.9,
    repulsionSamples: options?.repulsionSamples ?? 24,
  });
}

export function serializeLayout(
  layout: Map<string, PositionedNode>
): PositionedNode[] {
  return [...layout.values()];
}

export function toPositionMap(
  positions: PositionedNode[]
): Map<string, PositionedNode> {
  const map = new Map<string, PositionedNode>();
  for (const p of positions) {
    map.set(p.id, p);
  }
  return map;
}
