/**
 * Custom TanStack Query mutation hooks for GRID backend API.
 */

import { gridClient } from "@/lib/grid-client";
import type { IntelligenceResult, NavigationPlan } from "@/types/api";
import type { ApiResponse } from "@/lib/grid-client";
import type {
  MCQBankCreate,
  MCQBankResponse,
  MCQBankUpdate,
  MCQQuestionCreate,
  MCQQuestionResponse,
  MCQQuestionUpdate,
  MCQSubmissionCreate,
  MCQSubmissionResponse,
} from "@/types/mcq";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";

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

// ── MCQ: Bank mutations ──────────────────────────────────────────────

export function useCreateMCQBank() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: MCQBankCreate) => {
      const res = await gridClient.post<ApiResponse<MCQBankResponse>>(
        "/api/v1/mcq/banks",
        input
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to create bank");
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.banks.all });
    },
  });
}

export function useUpdateMCQBank() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      bankId,
      input,
    }: {
      bankId: string;
      input: MCQBankUpdate;
    }) => {
      const res = await gridClient.put<ApiResponse<MCQBankResponse>>(
        `/api/v1/mcq/banks/${bankId}`,
        input
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to update bank");
      return res.data;
    },
    onSuccess: (_, { bankId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.banks.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.mcq.banks.detail(bankId),
      });
    },
  });
}

export function useDeleteMCQBank() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (bankId: string) => {
      const res = await gridClient.delete(`/api/v1/mcq/banks/${bankId}`);
      if (!res.ok) throw new Error(res.error ?? "Failed to delete bank");
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.banks.all });
    },
  });
}

// ── MCQ: Question mutations ──────────────────────────────────────────

export function useCreateMCQQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: MCQQuestionCreate) => {
      const res = await gridClient.post<ApiResponse<MCQQuestionResponse>>(
        "/api/v1/mcq/questions",
        input
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to create question");
      return res.data;
    },
    onSuccess: (_, input) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.questions.all });
      if (input.bank_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.mcq.banks.detail(input.bank_id),
        });
      }
    },
  });
}

export function useUpdateMCQQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      questionId,
      input,
    }: {
      questionId: string;
      input: MCQQuestionUpdate;
    }) => {
      const res = await gridClient.put<ApiResponse<MCQQuestionResponse>>(
        `/api/v1/mcq/questions/${questionId}`,
        input
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to update question");
      return res.data;
    },
    onSuccess: (_, { questionId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.questions.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.mcq.questions.detail(questionId),
      });
    },
  });
}

export function useDeleteMCQQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (questionId: string) => {
      const res = await gridClient.delete(
        `/api/v1/mcq/questions/${questionId}`
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to delete question");
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.questions.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.mcq.banks.all });
    },
  });
}

// ── MCQ: Submission mutations ────────────────────────────────────────

export function useSubmitMCQAnswers() {
  return useMutation({
    mutationFn: async (input: MCQSubmissionCreate) => {
      const res = await gridClient.post<ApiResponse<MCQSubmissionResponse>>(
        "/api/v1/mcq/submit",
        input
      );
      if (!res.ok) throw new Error(res.error ?? "Failed to submit answers");
      return res.data;
    },
  });
}

export type {
  ApiResponse,
  IntelligenceProcessInput,
  NavigationPlanInput,
  MCQBankCreate,
  MCQBankUpdate,
  MCQQuestionCreate,
  MCQQuestionUpdate,
  MCQSubmissionCreate,
};
