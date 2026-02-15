/**
 * Custom TanStack Query hooks for GRID backend API queries.
 *
 * Each hook wraps `useQuery` with the correct query key, endpoint,
 * and type, and auto-extracts the response data from the `ApiResponse`
 * envelope so consumers get `T | null` instead of `ApiResponse<T>`.
 */

import { gridClient } from "@/lib/grid-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  ChaosResilience,
  CockpitState,
  CorruptionStats,
  DrtOverview,
  HealthData,
  MetricsResponse,
  RagStats,
  ReadinessResponse,
  ResonanceContext,
  SecurityHealth,
  SecurityStatus,
  VersionResponse,
} from "@/types/api";
import { useQuery } from "@tanstack/react-query";

// ── Internal helper ─────────────────────────────────────────────────

interface GridQueryOptions {
  queryKey: readonly unknown[];
  endpoint: string;
  staleTime?: number;
  refetchInterval?: number;
  enabled?: boolean;
}

/**
 * Base helper that wraps `useQuery` with the GRID API pattern:
 * - Calls `gridClient.get<T>(endpoint)`
 * - Unwraps `ApiResponse<T>` → returns `T | null`
 * - Forwards staleTime / refetchInterval / enabled
 */
function useGridQuery<T>(options: GridQueryOptions) {
  return useQuery({
    queryKey: options.queryKey,
    queryFn: async () => {
      const response = await gridClient.get<T>(options.endpoint);
      if (!response.ok) return null;
      return response.data;
    },
    staleTime: options.staleTime,
    refetchInterval: options.refetchInterval,
    enabled: options.enabled,
  });
}

// ── Health / Observability hooks ────────────────────────────────────

export function useHealth(opts?: { refetchInterval?: number }) {
  const query = useGridQuery<HealthData>({
    queryKey: queryKeys.health.all,
    endpoint: "/health",
    staleTime: 10_000,
    refetchInterval: opts?.refetchInterval ?? 15_000,
  });

  return {
    ...query,
    /** Convenience: backend responded ok AND status is "ok" or "healthy" */
    isOnline:
      !!query.data &&
      (query.data.status === "ok" || query.data.status === "healthy"),
  };
}

export function useMetrics() {
  return useGridQuery<MetricsResponse>({
    queryKey: queryKeys.metrics.all,
    endpoint: "/metrics",
    staleTime: 10_000,
    refetchInterval: 15_000,
  });
}

export function useReadiness() {
  return useGridQuery<ReadinessResponse>({
    queryKey: queryKeys.readiness.all,
    endpoint: "/health/ready",
    staleTime: 10_000,
    refetchInterval: 20_000,
  });
}

export function useVersion() {
  return useGridQuery<VersionResponse>({
    queryKey: queryKeys.version.all,
    endpoint: "/version",
    staleTime: 120_000,
  });
}

export function useChaosResilience() {
  return useGridQuery<ChaosResilience>({
    queryKey: queryKeys.chaos.all,
    endpoint: "/health/chaos-resilience",
    staleTime: 30_000,
  });
}

// ── Cognitive hooks ─────────────────────────────────────────────────

export function useCockpitState() {
  return useGridQuery<CockpitState>({
    queryKey: queryKeys.cockpit.state(),
    endpoint: "/api/v1/cockpit/state",
    staleTime: 10_000,
    refetchInterval: 15_000,
  });
}

export function useResonanceContext() {
  return useGridQuery<ResonanceContext>({
    queryKey: queryKeys.resonance.context(),
    endpoint: "/api/v1/resonance/context",
    staleTime: 10_000,
    refetchInterval: 20_000,
  });
}

export function useSkillsHealth() {
  return useGridQuery<Record<string, unknown>>({
    queryKey: queryKeys.skills.health(),
    endpoint: "/api/v1/skills/health",
    staleTime: 30_000,
  });
}

// ── Security hooks ──────────────────────────────────────────────────

export function useSecurityStatus() {
  return useGridQuery<SecurityStatus>({
    queryKey: queryKeys.security.status(),
    endpoint: "/security/status",
    staleTime: 30_000,
  });
}

export function useSecurityHealth() {
  return useGridQuery<SecurityHealth>({
    queryKey: queryKeys.security.health(),
    endpoint: "/health/security",
    staleTime: 30_000,
  });
}

export function useCorruptionStats() {
  return useGridQuery<CorruptionStats>({
    queryKey: queryKeys.corruption.stats(),
    endpoint: "/corruption/stats",
    staleTime: 30_000,
  });
}

export function useDrtOverview() {
  return useGridQuery<DrtOverview>({
    queryKey: queryKeys.drt.overview(),
    endpoint: "/drt/system-overview",
    staleTime: 30_000,
  });
}

// ── Knowledge hooks ─────────────────────────────────────────────────

export function useRagStats() {
  return useGridQuery<RagStats>({
    queryKey: queryKeys.rag.stats(),
    endpoint: "/api/v1/rag/stats",
    staleTime: 30_000,
  });
}

export function useSignalQuality() {
  return useGridQuery<Record<string, unknown>>({
    queryKey: queryKeys.skills.signalQuality(),
    endpoint: "/api/v1/skills/signal-quality",
    staleTime: 60_000,
  });
}
