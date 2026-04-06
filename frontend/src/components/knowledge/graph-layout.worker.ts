import {
  computeSampledForceLayout,
  serializeLayout,
  type LayoutEdge,
  type LayoutNode,
} from "@/components/knowledge/graph-layout";

interface LayoutRequest {
  requestId: string;
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  width: number;
  height: number;
  iterations: number;
  repulsionSamples: number;
}

type LayoutResponse =
  | {
      type: "layout";
      requestId: string;
      positions: ReturnType<typeof serializeLayout>;
      durationMs: number;
    }
  | {
      type: "error";
      requestId: string;
      message: string;
    };

self.onmessage = (event: MessageEvent<LayoutRequest>) => {
  const {
    requestId,
    nodes,
    edges,
    width,
    height,
    iterations,
    repulsionSamples,
  } = event.data;
  const start = performance.now();

  try {
    const layout = computeSampledForceLayout(nodes, edges, width, height, {
      iterations,
      repulsionSamples,
    });
    const durationMs = Math.round(performance.now() - start);
    const payload: LayoutResponse = {
      type: "layout",
      requestId,
      positions: serializeLayout(layout),
      durationMs,
    };
    self.postMessage(payload);
  } catch (error) {
    const payload: LayoutResponse = {
      type: "error",
      requestId,
      message:
        error instanceof Error ? error.message : "Unknown graph layout error",
    };
    self.postMessage(payload);
  }
};
