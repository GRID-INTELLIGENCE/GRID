/**
 * Runtime validation for knowledge graph API payloads.
 * Ensures TanStack Query can surface errors instead of silently showing an empty graph.
 */

import type {
  GraphDecisionCode,
  GraphDecisionErrorPayload,
  KnowledgeGraphPayload,
  KnowledgeGraphStats,
} from "@/types/api";

const GRAPH_DECISION_CODES: ReadonlySet<GraphDecisionCode> = new Set([
  "SCHEMA_INVALID",
  "GRAPH_TOO_LARGE",
  "LAYOUT_TIMEOUT",
  "INCONSISTENT_GRAPH",
  "UNSUPPORTED_REQUEST",
]);

function asObject(data: unknown): Record<string, unknown> | null {
  if (data === null || typeof data !== "object") {
    return null;
  }
  return data as Record<string, unknown>;
}

function isGraphDecisionCode(value: unknown): value is GraphDecisionCode {
  return (
    typeof value === "string" &&
    GRAPH_DECISION_CODES.has(value as GraphDecisionCode)
  );
}

function tryParseGraphDecisionPayload(
  data: unknown,
  status?: number
): GraphDecisionErrorPayload | null {
  const top = asObject(data);
  if (!top) return null;

  const maybeDetail = asObject(top.detail);
  const source = maybeDetail ?? top;
  if (!isGraphDecisionCode(source.code) || typeof source.message !== "string") {
    return null;
  }

  const payloadStatus =
    typeof source.status === "number"
      ? source.status
      : typeof status === "number"
        ? status
        : 0;
  const suggestedActions = Array.isArray(source.suggested_actions)
    ? source.suggested_actions.filter(
        (item): item is string => typeof item === "string"
      )
    : [];
  const details = asObject(source.details) ?? {};

  return {
    code: source.code,
    message: source.message,
    status: payloadStatus,
    suggested_actions: suggestedActions,
    details,
  };
}

function parseGraphNode(
  raw: unknown,
  index: number
): KnowledgeGraphPayload["nodes"][number] {
  const o = asObject(raw);
  if (!o) {
    throw new Error(`Knowledge graph node[${index}] is not an object`);
  }
  if (typeof o.id !== "string")
    throw new Error(`Knowledge graph node[${index}].id must be a string`);
  if (typeof o.label !== "string")
    throw new Error(`Knowledge graph node[${index}].label must be a string`);
  if (typeof o.entity_type !== "string") {
    throw new Error(
      `Knowledge graph node[${index}].entity_type must be a string`
    );
  }
  const subtitle = typeof o.subtitle === "string" ? o.subtitle : "";
  return {
    id: o.id,
    label: o.label,
    entity_type: o.entity_type,
    subtitle,
  };
}

function parseGraphEdge(
  raw: unknown,
  index: number
): KnowledgeGraphPayload["edges"][number] {
  const o = asObject(raw);
  if (!o) {
    throw new Error(`Knowledge graph edge[${index}] is not an object`);
  }
  if (typeof o.id !== "string")
    throw new Error(`Knowledge graph edge[${index}].id must be a string`);
  if (typeof o.source !== "string")
    throw new Error(`Knowledge graph edge[${index}].source must be a string`);
  if (typeof o.target !== "string")
    throw new Error(`Knowledge graph edge[${index}].target must be a string`);
  if (typeof o.type !== "string")
    throw new Error(`Knowledge graph edge[${index}].type must be a string`);
  if (typeof o.label !== "string")
    throw new Error(`Knowledge graph edge[${index}].label must be a string`);
  return {
    id: o.id,
    source: o.source,
    target: o.target,
    type: o.type,
    label: o.label,
  };
}

export class GraphDecisionError extends Error {
  readonly code: GraphDecisionCode;
  readonly status: number;
  readonly suggestedActions: string[];
  readonly details: Record<string, unknown>;

  constructor(payload: GraphDecisionErrorPayload) {
    super(`${payload.code}: ${payload.message}`);
    this.name = "GraphDecisionError";
    this.code = payload.code;
    this.status = payload.status;
    this.suggestedActions = payload.suggested_actions ?? [];
    this.details = payload.details ?? {};
  }
}

export function parseGraphDecisionError(
  data: unknown,
  status?: number
): GraphDecisionError | null {
  const payload = tryParseGraphDecisionPayload(data, status);
  return payload ? new GraphDecisionError(payload) : null;
}

export function parseKnowledgeGraphPayload(
  data: unknown
): KnowledgeGraphPayload {
  const decisionError = parseGraphDecisionError(data);
  if (decisionError) {
    throw decisionError;
  }

  const o = asObject(data);
  if (!o) {
    throw new Error("Knowledge graph response is not a JSON object");
  }

  if (!Array.isArray(o.nodes) || !Array.isArray(o.edges)) {
    throw new Error(
      "Knowledge graph response must include nodes and edges arrays"
    );
  }

  const nodes = o.nodes.map((node, idx) => parseGraphNode(node, idx));
  const edges = o.edges.map((edge, idx) => parseGraphEdge(edge, idx));

  if (o.total_entities !== undefined && !Number.isInteger(o.total_entities)) {
    throw new Error(
      "Knowledge graph total_entities must be a number when present"
    );
  }

  if (o.truncated !== undefined && typeof o.truncated !== "boolean") {
    throw new Error("Knowledge graph truncated must be a boolean when present");
  }

  if (o.storage_path !== undefined && typeof o.storage_path !== "string") {
    throw new Error(
      "Knowledge graph storage_path must be a string when present"
    );
  }

  if (o.graph_hash !== undefined && typeof o.graph_hash !== "string") {
    throw new Error("Knowledge graph graph_hash must be a string when present");
  }

  let limits: KnowledgeGraphPayload["limits"];
  if (o.limits !== undefined) {
    const l = asObject(o.limits);
    if (!l) {
      throw new Error("Knowledge graph limits must be an object when present");
    }
    if (!Number.isInteger(l.applied_max_nodes)) {
      throw new Error(
        "Knowledge graph limits.applied_max_nodes must be an integer"
      );
    }
    if (!Number.isInteger(l.max_edges)) {
      throw new Error("Knowledge graph limits.max_edges must be an integer");
    }
    if (!Number.isInteger(l.timeout_ms)) {
      throw new Error("Knowledge graph limits.timeout_ms must be an integer");
    }
    if (
      l.requested_max_nodes !== undefined &&
      l.requested_max_nodes !== null &&
      !Number.isInteger(l.requested_max_nodes)
    ) {
      throw new Error(
        "Knowledge graph limits.requested_max_nodes must be an integer or null when present"
      );
    }
    if (l.export_ms !== undefined && !Number.isInteger(l.export_ms)) {
      throw new Error(
        "Knowledge graph limits.export_ms must be an integer when present"
      );
    }
    limits = {
      requested_max_nodes:
        typeof l.requested_max_nodes === "number"
          ? l.requested_max_nodes
          : null,
      applied_max_nodes: Number(l.applied_max_nodes),
      max_edges: Number(l.max_edges),
      timeout_ms: Number(l.timeout_ms),
      export_ms: typeof l.export_ms === "number" ? l.export_ms : undefined,
    };
  }

  return {
    nodes,
    edges,
    storage_path:
      typeof o.storage_path === "string" ? o.storage_path : undefined,
    total_entities:
      typeof o.total_entities === "number" ? o.total_entities : undefined,
    truncated: typeof o.truncated === "boolean" ? o.truncated : undefined,
    graph_hash: typeof o.graph_hash === "string" ? o.graph_hash : undefined,
    limits,
  };
}

export function parseKnowledgeGraphStats(data: unknown): KnowledgeGraphStats {
  const o = asObject(data);
  if (!o) {
    throw new Error("Knowledge stats response is not a JSON object");
  }
  if (
    typeof o.total_entities !== "number" ||
    typeof o.total_relationships !== "number"
  ) {
    throw new Error(
      "Knowledge stats response must include numeric total_entities and total_relationships"
    );
  }
  return {
    ...o,
    total_entities: o.total_entities,
    total_relationships: o.total_relationships,
    entity_counts: asObject(o.entity_counts) as
      | Record<string, number>
      | undefined,
    relationship_counts: asObject(o.relationship_counts) as
      | Record<string, number>
      | undefined,
    storage_path:
      typeof o.storage_path === "string" ? o.storage_path : undefined,
  };
}
