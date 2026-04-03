/**
 * Simple force-directed layout for small knowledge graphs (no d3 dependency).
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

/**
 * Run a short force simulation: repulsion between all pairs, attraction along edges.
 */
export function computeForceLayout(
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  width: number,
  height: number,
  options?: { iterations?: number; margin?: number }
): Map<string, PositionedNode> {
  const iterations = options?.iterations ?? 220;
  const margin = options?.margin ?? 44;
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

  const repulsion = 2800;
  const attraction = 0.028;
  const damping = 0.88;
  const ids = nodes.map((x) => x.id);

  for (let iter = 0; iter < iterations; iter++) {
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

    for (const e of edges) {
      const a = positions.get(e.source);
      const b = positions.get(e.target);
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
