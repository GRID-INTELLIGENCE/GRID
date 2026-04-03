import { describe, expect, it } from "vitest";
import { computeForceLayout } from "./graph-layout";

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
});
