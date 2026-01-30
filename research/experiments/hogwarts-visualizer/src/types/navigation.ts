/**
 * Navigation API type definitions matching backend schemas.
 */

export interface NavigationStep {
  id: string;
  name: string;
  description: string;
  estimated_time_seconds: number;
  dependencies: string[];
  outputs: string[];
  confidence: number;
}

export interface NavigationPath {
  id: string;
  name: string;
  description: string;
  steps: NavigationStep[];
  complexity: string;
  estimated_total_time: number;
  confidence: number;
  recommendation_score: number;
  reasoning: string | null;
  metadata: Record<string, unknown>;
}

export interface NavigationPlan {
  request_id: string;
  reasoning: string;
  processing_time_ms: number;
  learning_applied: boolean;
  adaptation_triggered: boolean;
  recommended_path: NavigationPath | null;
  paths: NavigationPath[];
  confidence_scores: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface NavigationRequest {
  goal: string | Record<string, unknown>;
  context?: Record<string, unknown>;
  max_alternatives?: number;
  enable_learning?: boolean;
  learning_weight?: number;
  adaptation_threshold?: number;
  source?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: {
    request_id: string;
    timestamp?: string;
    version?: string;
  };
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface NavigationPlanResponse extends ApiResponse<NavigationPlan> {}
