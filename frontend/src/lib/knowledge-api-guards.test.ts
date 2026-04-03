import {
  parseKnowledgeGraphPayload,
  parseKnowledgeGraphStats,
} from "@/lib/knowledge-api-guards";
import { describe, expect, it } from "vitest";

describe("knowledge-api-guards", () => {
  it("parseKnowledgeGraphPayload accepts valid payload", () => {
    const p = parseKnowledgeGraphPayload({
      nodes: [{ id: "a" }],
      edges: [{ id: "e", source: "a", target: "a", type: "X", label: "x" }],
    });
    expect(p.nodes).toHaveLength(1);
    expect(p.edges).toHaveLength(1);
  });

  it("parseKnowledgeGraphPayload rejects missing arrays", () => {
    expect(() => parseKnowledgeGraphPayload({})).toThrow(/nodes and edges/);
  });

  it("parseKnowledgeGraphStats requires totals", () => {
    expect(() => parseKnowledgeGraphStats({})).toThrow(/total_entities/);
  });
});
