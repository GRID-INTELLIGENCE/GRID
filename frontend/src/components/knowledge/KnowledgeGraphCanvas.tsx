import { computeForceLayout } from "@/components/knowledge/graph-layout";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "@/types/api";
import { useId, useMemo, useState } from "react";

const W = 720;
const H = 400;

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return `${s.slice(0, max - 1)}…`;
}

interface KnowledgeGraphCanvasProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export function KnowledgeGraphCanvas({
  nodes,
  edges,
}: KnowledgeGraphCanvasProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const reactId = useId();
  const markerId = `kg-arrow-${reactId.replace(/\W/g, "")}`;

  const positions = useMemo(() => {
    if (nodes.length === 0) {
      return new Map<string, { id: string; x: number; y: number }>();
    }
    return computeForceLayout(
      nodes.map((n) => ({ id: n.id })),
      edges.map((e) => ({ source: e.source, target: e.target })),
      W,
      H
    );
  }, [nodes, edges]);

  if (nodes.length === 0) {
    return (
      <p className="text-xs text-[var(--muted-foreground)] py-8 text-center">
        No graph nodes yet. Ingest documents via the API or{" "}
        <code className="rounded bg-[var(--muted)] px-1">
          grid knowledge ingest
        </code>
        .
      </p>
    );
  }

  const docColor = "var(--primary)";
  const conceptFill = "var(--muted)";
  const conceptStroke = "var(--primary)";

  return (
    <div className="space-y-2">
      <svg
        role="img"
        aria-label="Knowledge graph visualization"
        viewBox={`0 0 ${W} ${H}`}
        className="w-full max-h-[min(420px,55vh)] rounded-md border border-[var(--border)] bg-[var(--muted)]/30"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <marker
            id={markerId}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--muted-foreground)" />
          </marker>
        </defs>

        {edges.map((e) => {
          const a = positions.get(e.source);
          const b = positions.get(e.target);
          if (!a || !b) return null;
          const isExplains = e.type === "EXPLAINS";
          return (
            <line
              key={e.id}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke="var(--muted-foreground)"
              strokeOpacity={0.55}
              strokeWidth={isExplains ? 1 : 1.35}
              strokeDasharray={isExplains ? "5 4" : undefined}
              markerEnd={`url(#${markerId})`}
            />
          );
        })}

        {nodes.map((n) => {
          const p = positions.get(n.id);
          if (!p) return null;
          const isDoc = n.entity_type === "Document";
          const r = isDoc ? 11 : 8;
          const label = truncate(n.label, 22);
          return (
            <g
              key={n.id}
              onMouseEnter={() => setHoverId(n.id)}
              onMouseLeave={() => setHoverId(null)}
              className="cursor-default"
            >
              <circle
                cx={p.x}
                cy={p.y}
                r={r}
                fill={isDoc ? docColor : conceptFill}
                stroke={isDoc ? docColor : conceptStroke}
                strokeWidth={isDoc ? 0 : 1.5}
                opacity={hoverId && hoverId !== n.id ? 0.45 : 1}
              />
              <text
                x={p.x}
                y={p.y + r + 14}
                textAnchor="middle"
                className="fill-[var(--foreground)] text-[9px] font-medium"
                style={{ pointerEvents: "none" }}
              >
                {label}
              </text>
            </g>
          );
        })}
      </svg>

      {hoverId ? (
        <p className="text-[10px] text-[var(--muted-foreground)] min-h-[2.5rem]">
          {nodes.find((x) => x.id === hoverId)?.subtitle ||
            nodes.find((x) => x.id === hoverId)?.label}
        </p>
      ) : (
        <p className="text-[10px] text-[var(--muted-foreground)]">
          <span className="inline-flex items-center gap-1 mr-3">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: "var(--primary)" }}
            />{" "}
            Document
          </span>
          <span className="inline-flex items-center gap-1 mr-3">
            <span className="inline-block h-2 w-2 rounded-full border border-[var(--primary)] bg-[var(--muted)]" />{" "}
            Concept
          </span>
          <span className="mr-2">—</span>
          dashed: EXPLAINS · solid: CONNECTS_TO / other
        </p>
      )}
    </div>
  );
}
