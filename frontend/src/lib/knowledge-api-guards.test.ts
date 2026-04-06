import {
  GraphDecisionError,
  parseGraphDecisionError,
  parseKnowledgeGraphPayload,
  parseKnowledgeGraphStats,
} from "@/lib/knowledge-api-guards";
import { describe, expect, it } from "vitest";

describe("knowledge-api-guards", () => {
  it("parseKnowledgeGraphPayload accepts valid payload", () => {
    const p = parseKnowledgeGraphPayload({
      nodes: [{ id: "a", label: "A", entity_type: "Concept", subtitle: "" }],
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

  it("parseGraphDecisionError extracts FastAPI detail payload", () => {
    const err = parseGraphDecisionError(
      {
        detail: {
          code: "GRAPH_TOO_LARGE",
          message: "too large",
          status: 409,
          suggested_actions: ["reduce max_nodes"],
        },
      },
      409
    );
    expect(err).toBeInstanceOf(GraphDecisionError);
    expect(err?.code).toBe("GRAPH_TOO_LARGE");
  });
});
