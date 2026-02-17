/**
 * Custom TanStack Query mutation hooks for GRID backend API.
 */

import { gridClient } from "@/lib/grid-client";
import type { IntelligenceResult, NavigationPlan } from "@/types/api";
import type { ApiResponse } from "@/lib/grid-client";
import { useMutation } from "@tanstack/react-query";

// ── Intelligence ────────────────────────────────────────────────────

interface IntelligenceProcessInput {
  data: string;
  capabilities: string[];
  includeEvidence: boolean;
}

export function useIntelligenceProcess() {
  return useMutation({
    mutationFn: async (input: IntelligenceProcessInput) => {
      const res = await gridClient.post<IntelligenceResult>(
        "/api/v1/intelligence/process",
        {
          data: {
            input: input.data,
            capabilities: input.capabilities,
          },
          context: { source: "grid-frontend", timestamp: Date.now() },
          include_evidence: input.includeEvidence,
          reset_session: false,
        }
      );
      return res;
    },
  });
}

// ── Cognitive: Navigation Plan ──────────────────────────────────────

interface NavigationPlanInput {
  goal: string;
  maxAlternatives?: number;
  enableLearning?: boolean;
}

export function useNavigationPlan() {
  return useMutation({
    mutationFn: async (input: NavigationPlanInput) => {
      const res = await gridClient.post<NavigationPlan>(
        "/api/v1/navigation/plan",
        {
          goal: input.goal,
          max_alternatives: input.maxAlternatives ?? 3,
          enable_learning: input.enableLearning ?? true,
        }
      );
      return res;
    },
  });
}

// ── Knowledge: Session operations ───────────────────────────────────

export function useSessionLookup() {
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return gridClient.get<{
        session_id: string;
        turn_count?: number;
        metadata?: Record<string, unknown>;
      }>(`/api/v1/rag/sessions/${sessionId}`);
    },
  });
}

export function useSessionDelete() {
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return gridClient.delete(`/api/v1/rag/sessions/${sessionId}`);
    },
  });
}

export type { ApiResponse, IntelligenceProcessInput, NavigationPlanInput };
