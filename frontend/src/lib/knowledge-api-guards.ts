/**
 * Runtime validation for knowledge graph API payloads.
 * Ensures TanStack Query can surface errors instead of silently showing an empty graph.
 */

import type { KnowledgeGraphPayload, KnowledgeGraphStats } from "@/types/api";

export function parseKnowledgeGraphPayload(
  data: unknown
): KnowledgeGraphPayload {
  if (data === null || typeof data !== "object") {
    throw new Error("Knowledge graph response is not a JSON object");
  }
  const o = data as Record<string, unknown>;
  if (!Array.isArray(o.nodes) || !Array.isArray(o.edges)) {
    throw new Error(
      "Knowledge graph response must include nodes and edges arrays"
    );
  }
  if (o.total_entities !== undefined && typeof o.total_entities !== "number") {
    throw new Error(
      "Knowledge graph total_entities must be a number when present"
    );
  }
  if (o.truncated !== undefined && typeof o.truncated !== "boolean") {
    throw new Error("Knowledge graph truncated must be a boolean when present");
  }
  return data as KnowledgeGraphPayload;
}

export function parseKnowledgeGraphStats(data: unknown): KnowledgeGraphStats {
  if (data === null || typeof data !== "object") {
    throw new Error("Knowledge stats response is not a JSON object");
  }
  const o = data as Record<string, unknown>;
  if (
    typeof o.total_entities !== "number" ||
    typeof o.total_relationships !== "number"
  ) {
    throw new Error(
      "Knowledge stats response must include numeric total_entities and total_relationships"
    );
  }
  return data as KnowledgeGraphStats;
}
