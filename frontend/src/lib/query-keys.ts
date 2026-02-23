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
} as const;
