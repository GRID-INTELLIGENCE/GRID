import { useCallback, useMemo } from "react";

interface ConceptNode {
  id: string;
  label: string;
}

interface ConceptEdge {
  from: string;
  to: string;
}

interface NetworkVizProps {
  concepts: string[];
  onConceptClick?: (concept: string) => void;
}

/** Simple force-free layout: arrange nodes in a circle */
function layoutNodes(nodes: ConceptNode[], width: number, height: number) {
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(cx, cy) - 30;

  return nodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
    return {
      ...node,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });
}

/** Connect every node to its neighbors (circular adjacency) */
function generateEdges(nodes: ConceptNode[]): ConceptEdge[] {
  if (nodes.length < 2) return [];
  const edges: ConceptEdge[] = [];
  for (let i = 0; i < nodes.length; i++) {
    const next = (i + 1) % nodes.length;
    edges.push({ from: nodes[i].id, to: nodes[next].id });
    // Add cross-links for density (every 3rd node)
    if (nodes.length > 4 && i % 3 === 0) {
      const cross = (i + Math.floor(nodes.length / 3)) % nodes.length;
      edges.push({ from: nodes[i].id, to: nodes[cross].id });
    }
  }
  return edges;
}

const WIDTH = 320;
const HEIGHT = 240;

export function NetworkViz({ concepts, onConceptClick }: NetworkVizProps) {
  const nodes: ConceptNode[] = useMemo(
    () =>
      concepts
        .slice(0, 12)
        .map((c) => ({ id: c, label: c.replace(/_/g, " ") })),
    [concepts]
  );

  const positioned = useMemo(() => layoutNodes(nodes, WIDTH, HEIGHT), [nodes]);
  const edges = useMemo(() => generateEdges(nodes), [nodes]);

  const posMap = useMemo(() => {
    const m = new Map<string, { x: number; y: number }>();
    for (const p of positioned) m.set(p.id, p);
    return m;
  }, [positioned]);

  const handleClick = useCallback(
    (concept: string) => onConceptClick?.(concept),
    [onConceptClick]
  );

  if (concepts.length === 0) return null;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="w-full max-w-sm"
      role="img"
      aria-label="Concept network visualization"
    >
      {/* Edges */}
      {edges.map((edge, i) => {
        const from = posMap.get(edge.from);
        const to = posMap.get(edge.to);
        if (!from || !to) return null;
        return (
          <line
            key={`e-${i}`}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            stroke="var(--border)"
            strokeWidth="1"
            opacity="0.5"
            style={{
              animation:
                "connect-nodes var(--motion-duration-organic) var(--motion-easing-decelerate) backwards",
              animationDelay: `${i * 80}ms`,
            }}
          />
        );
      })}

      {/* Nodes */}
      {positioned.map((node, i) => (
        <g
          key={node.id}
          style={{
            cursor: "pointer",
            animation:
              "scale-in var(--motion-duration-normal) var(--motion-easing-organic) backwards",
            animationDelay: `${i * 60}ms`,
            transformOrigin: `${node.x}px ${node.y}px`,
          }}
          onClick={() => handleClick(node.id)}
          role="button"
          tabIndex={0}
          aria-label={`Explore concept: ${node.label}`}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleClick(node.id);
          }}
        >
          <circle
            cx={node.x}
            cy={node.y}
            r="6"
            fill="var(--primary)"
            opacity="0.9"
          />
          <text
            x={node.x}
            y={node.y + 16}
            textAnchor="middle"
            fill="var(--muted-foreground)"
            fontSize="8"
            fontFamily="var(--typography-font-family)"
          >
            {node.label.length > 12
              ? node.label.slice(0, 11) + "..."
              : node.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
