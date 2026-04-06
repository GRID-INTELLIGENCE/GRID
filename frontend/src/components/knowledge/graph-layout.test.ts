import { describe, expect, it } from "vitest";
import { computeForceLayout, computeSampledForceLayout } from "./graph-layout";

describe("computeForceLayout", () => {
  it("returns bounded positions for a triangle", () => {
    const nodes = [{ id: "a" }, { id: "b" }, { id: "c" }];
    const edges = [
      { source: "a", target: "b" },
      { source: "b", target: "c" },
    ];
    const pos = computeForceLayout(nodes, edges, 400, 300, {
      iterations: 80,
      margin: 20,
    });
    expect(pos.size).toBe(3);
    for (const p of pos.values()) {
      expect(p.x).toBeGreaterThanOrEqual(20);
      expect(p.x).toBeLessThanOrEqual(380);
      expect(p.y).toBeGreaterThanOrEqual(20);
      expect(p.y).toBeLessThanOrEqual(280);
    }
  });

  it("handles single node", () => {
    const pos = computeForceLayout([{ id: "only" }], [], 200, 200, {
      iterations: 10,
    });
    expect(pos.size).toBe(1);
  });

  it("computes sampled layout for larger node sets", () => {
    const nodes = Array.from({ length: 200 }, (_, i) => ({ id: `n${i}` }));
    const edges = Array.from({ length: 199 }, (_, i) => ({
      source: `n${i}`,
      target: `n${i + 1}`,
    }));
    const pos = computeSampledForceLayout(nodes, edges, 900, 600, {
      iterations: 25,
      repulsionSamples: 16,
    });
    expect(pos.size).toBe(200);
  });
});
