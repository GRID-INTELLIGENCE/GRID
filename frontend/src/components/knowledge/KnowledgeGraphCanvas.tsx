import {
  computeSampledForceLayout,
  type PositionedNode,
  toPositionMap,
} from "@/components/knowledge/graph-layout";
import { GraphDecisionError } from "@/lib/knowledge-api-guards";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "@/types/api";
import { useDeferredValue, useEffect, useId, useReducer } from "react";

const W = 720;
const H = 400;
const LAYOUT_TIMEOUT_MS = 1_500;
const LAYOUT_ITERATIONS = 120;
const LAYOUT_REPULSION_SAMPLES = 24;
const LAYOUT_CACHE_MAX = 12;

const layoutCache = new Map<string, PositionedNode[]>();

function cacheLayout(key: string, positions: PositionedNode[]): void {
  if (layoutCache.size >= LAYOUT_CACHE_MAX) {
    const oldest = layoutCache.keys().next().value;
    if (typeof oldest === "string") layoutCache.delete(oldest);
  }
  layoutCache.set(key, positions);
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return `${s.slice(0, max - 1)}…`;
}

interface KnowledgeGraphCanvasProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  graphHash?: string;
}

interface LayoutState {
  positions: Map<string, PositionedNode>;
  pending: boolean;
  error: GraphDecisionError | null;
  durationMs: number | null;
  hoverId: string | null;
}

type LayoutAction =
  | { type: "reset" }
  | { type: "start" }
  | { type: "done"; positions: Map<string, PositionedNode>; durationMs: number }
  | { type: "fail"; error: GraphDecisionError }
  | { type: "cache_hit"; positions: Map<string, PositionedNode> }
  | { type: "hover"; id: string | null };

const initialLayoutState: LayoutState = {
  positions: new Map(),
  pending: false,
  error: null,
  durationMs: null,
  hoverId: null,
};

function layoutReducer(state: LayoutState, action: LayoutAction): LayoutState {
  switch (action.type) {
    case "reset":
      return { ...initialLayoutState, hoverId: state.hoverId };
    case "start":
      return { ...state, pending: true, error: null };
    case "done":
      return {
        ...state,
        pending: false,
        error: null,
        positions: action.positions,
        durationMs: action.durationMs,
      };
    case "fail":
      return { ...state, pending: false, error: action.error };
    case "cache_hit":
      return {
        ...state,
        pending: false,
        error: null,
        positions: action.positions,
      };
    case "hover":
      return { ...state, hoverId: action.id };
  }
}

export function KnowledgeGraphCanvas({
  nodes,
  edges,
  graphHash,
}: KnowledgeGraphCanvasProps) {
  const [layout, dispatch] = useReducer(layoutReducer, initialLayoutState);
  const {
    positions,
    pending: layoutPending,
    error: layoutError,
    durationMs: layoutDurationMs,
    hoverId,
  } = layout;
  const reactId = useId();
  const markerId = `kg-arrow-${reactId.replace(/\W/g, "")}`;
  const deferredNodes = useDeferredValue(nodes);
  const deferredEdges = useDeferredValue(edges);

  useEffect(() => {
    if (deferredNodes.length === 0) {
      dispatch({ type: "reset" });
      return;
    }

    const cacheKey = `${graphHash ?? "nohash"}:${deferredNodes.length}:${
      deferredEdges.length
    }:${W}x${H}`;
    const cached = layoutCache.get(cacheKey);
    if (cached) {
      dispatch({ type: "cache_hit", positions: toPositionMap(cached) });
      return;
    }

    let canceled = false;
    let worker: Worker | null = null;
    const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    const failWith = (
      code: "LAYOUT_TIMEOUT" | "SCHEMA_INVALID",
      message: string
    ) => {
      if (canceled) return;
      dispatch({
        type: "fail",
        error: new GraphDecisionError({
          code,
          message,
          status: code === "LAYOUT_TIMEOUT" ? 503 : 422,
          suggested_actions: [
            "Reduce max_nodes on the graph query",
            "Retry the graph render",
          ],
          details: {
            node_count: deferredNodes.length,
            edge_count: deferredEdges.length,
          },
        }),
      });
    };

    const applyLayout = (next: PositionedNode[], durationMs: number): void => {
      if (canceled) return;
      cacheLayout(cacheKey, next);
      dispatch({ type: "done", positions: toPositionMap(next), durationMs });
    };

    dispatch({ type: "start" });

    const timeoutId = window.setTimeout(() => {
      if (worker) {
        worker.terminate();
      }
      failWith("LAYOUT_TIMEOUT", "Graph layout exceeded client render budget");
    }, LAYOUT_TIMEOUT_MS);

    if (typeof Worker !== "undefined") {
      worker = new Worker(
        new URL("./graph-layout.worker.ts", import.meta.url),
        {
          type: "module",
        }
      );
      worker.onmessage = (
        event: MessageEvent<
          | {
              type: "layout";
              requestId: string;
              positions: PositionedNode[];
              durationMs: number;
            }
          | { type: "error"; requestId: string; message: string }
        >
      ) => {
        const payload = event.data;
        if (payload.requestId !== requestId) return;
        window.clearTimeout(timeoutId);
        worker?.terminate();
        if (payload.type === "error") {
          failWith("SCHEMA_INVALID", payload.message);
          return;
        }
        applyLayout(payload.positions, payload.durationMs);
      };
      worker.onerror = () => {
        window.clearTimeout(timeoutId);
        worker?.terminate();
        failWith("SCHEMA_INVALID", "Knowledge graph worker failed");
      };
      worker.postMessage({
        requestId,
        nodes: deferredNodes.map((n) => ({ id: n.id })),
        edges: deferredEdges.map((e) => ({
          source: e.source,
          target: e.target,
        })),
        width: W,
        height: H,
        iterations: LAYOUT_ITERATIONS,
        repulsionSamples: LAYOUT_REPULSION_SAMPLES,
      });
    } else {
      try {
        const started = performance.now();
        const fallbackLayout = computeSampledForceLayout(
          deferredNodes.map((n) => ({ id: n.id })),
          deferredEdges.map((e) => ({ source: e.source, target: e.target })),
          W,
          H,
          {
            iterations: LAYOUT_ITERATIONS,
            repulsionSamples: LAYOUT_REPULSION_SAMPLES,
          }
        );
        const durationMs = Math.round(performance.now() - started);
        window.clearTimeout(timeoutId);
        if (durationMs > LAYOUT_TIMEOUT_MS) {
          failWith(
            "LAYOUT_TIMEOUT",
            "Knowledge graph layout exceeded client render budget"
          );
        } else {
          applyLayout([...fallbackLayout.values()], durationMs);
        }
      } catch (error) {
        window.clearTimeout(timeoutId);
        failWith(
          "SCHEMA_INVALID",
          error instanceof Error
            ? error.message
            : "Failed to compute graph layout"
        );
      }
    }

    return () => {
      canceled = true;
      window.clearTimeout(timeoutId);
      if (worker) {
        worker.terminate();
      }
    };
  }, [deferredEdges, deferredNodes, graphHash]);

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

        {deferredEdges.map((e) => {
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

        {deferredNodes.map((n) => {
          const p = positions.get(n.id);
          if (!p) return null;
          const isDoc = n.entity_type === "Document";
          const r = isDoc ? 11 : 8;
          const label = truncate(n.label, 22);
          return (
            <g
              key={n.id}
              onMouseEnter={() => dispatch({ type: "hover", id: n.id })}
              onMouseLeave={() => dispatch({ type: "hover", id: null })}
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

      {layoutPending ? (
        <p className="text-[10px] text-[var(--muted-foreground)]">
          Computing graph layout…
        </p>
      ) : null}

      {layoutError ? (
        <p className="text-[10px] text-[var(--destructive)]" role="alert">
          {layoutError.code}: {layoutError.message}
          {layoutError.suggestedActions.length > 0
            ? ` — ${layoutError.suggestedActions.join(" · ")}`
            : ""}
        </p>
      ) : null}

      {layoutDurationMs != null ? (
        <p className="text-[10px] text-[var(--muted-foreground)]">
          Layout duration: {layoutDurationMs}ms
        </p>
      ) : null}

      {hoverId ? (
        <p className="text-[10px] text-[var(--muted-foreground)] min-h-[2.5rem]">
          {deferredNodes.find((x) => x.id === hoverId)?.subtitle ||
            deferredNodes.find((x) => x.id === hoverId)?.label}
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
