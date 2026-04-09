/**
 * Centralized TanStack Query key factory.
 *
 * Using a factory ensures keys stay consistent across hooks and
 * makes cache invalidation straightforward.
 */

export const queryKeys = {
  health: {
    all: ["health"] as const,
  },
  metrics: {
    all: ["metrics"] as const,
  },
  readiness: {
    all: ["readiness"] as const,
  },
  version: {
    all: ["version"] as const,
  },
  chaos: {
    all: ["chaos"] as const,
  },
  cockpit: {
    state: () => ["cockpit", "state"] as const,
  },
  resonance: {
    context: () => ["resonance", "context"] as const,
  },
  skills: {
    health: () => ["skills", "health"] as const,
    signalQuality: () => ["skills", "signalQuality"] as const,
  },
  security: {
    status: () => ["security", "status"] as const,
    health: () => ["security", "health"] as const,
  },
  corruption: {
    stats: () => ["corruption", "stats"] as const,
  },
  drt: {
    overview: () => ["drt", "overview"] as const,
  },
  rag: {
    stats: () => ["rag", "stats"] as const,
  },
  knowledge: {
    stats: () => ["knowledge", "stats"] as const,
    graph: (opts?: { maxNodes?: number; maxEdges?: number }) =>
      [
        "knowledge",
        "graph",
        opts?.maxNodes ?? "default",
        opts?.maxEdges ?? "default",
      ] as const,
  },
  admission: {
    policy: () => ["admission", "policy"] as const,
    stats: () => ["admission", "stats"] as const,
    bannered: () => ["admission", "bannered"] as const,
  },
  mcq: {
    banks: {
      all: ["mcq", "banks"] as const,
      list: (params?: {
        owner_id?: string;
        is_public?: boolean;
        tags?: string[];
      }) => ["mcq", "banks", "list", params ?? {}] as const,
      detail: (id: string) => ["mcq", "banks", id] as const,
    },
    questions: {
      all: ["mcq", "questions"] as const,
      list: (params?: {
        bank_id?: string;
        difficulty?: string;
        tags?: string[];
      }) => ["mcq", "questions", "list", params ?? {}] as const,
      detail: (id: string) => ["mcq", "questions", id] as const,
    },
  },
} as const;
