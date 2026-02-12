/**
 * Shared API response types for the GRID backend.
 *
 * These were previously duplicated across individual page components.
 * Centralizing them here ensures a single source of truth and enables
 * the custom TanStack Query hooks in `src/hooks/` to be strongly typed.
 */

// ── Health / Observability ──────────────────────────────────────────

/** Unified health response — used by Dashboard and Observability. */
export interface HealthData {
  status?: string;
  version?: string;
  uptime?: number;
  cockpit?: Record<string, unknown>;
  components?: HealthComponent[];
  alerts?: HealthAlert[];
  [key: string]: unknown;
}

export interface HealthComponent {
  name: string;
  status: string;
  [key: string]: unknown;
}

export interface HealthAlert {
  level: string;
  message: string;
  [key: string]: unknown;
}

export interface MetricsResponse {
  uptime?: number;
  sessions?: number;
  operations?: number;
  components?: number;
  alerts?: number;
  [key: string]: unknown;
}

export interface ReadinessResponse {
  ready?: boolean;
  checks?: Record<string, boolean>;
  [key: string]: unknown;
}

export interface VersionResponse {
  name?: string;
  version?: string;
  environment?: string;
  debug?: boolean;
  python_version?: string;
  [key: string]: unknown;
}

export interface ChaosResilience {
  resilience_score?: number;
  components?: Record<string, unknown>;
  recommendations?: string[];
  [key: string]: unknown;
}

// ── Cognitive ───────────────────────────────────────────────────────

export interface CockpitState {
  status?: string;
  mode?: string;
  version?: string;
  uptime?: number;
  summary?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface NavigationPlan {
  goal?: string;
  primary_path?: Record<string, unknown>;
  alternatives?: Record<string, unknown>[];
  context?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ResonanceContext {
  active_activities?: number;
  context_state?: Record<string, unknown>;
  [key: string]: unknown;
}

// ── Security ────────────────────────────────────────────────────────

export interface SecurityStatus {
  authentication_level?: string;
  cors_policy?: string;
  rate_limiting?: string | boolean;
  security_headers?: boolean;
  [key: string]: unknown;
}

export interface SecurityHealthCheck {
  name: string;
  status: string;
  details?: string;
}

export interface SecurityHealth {
  overall_status?: string;
  checks?: SecurityHealthCheck[];
  compliance_score?: number;
  [key: string]: unknown;
}

export interface CorruptionStats {
  monitored_endpoints?: number;
  total_penalties?: number;
  system_status?: string;
  [key: string]: unknown;
}

export interface DrtOverview {
  status?: Record<string, unknown>;
  top_endpoints?: Record<string, unknown>[];
  [key: string]: unknown;
}

// ── Knowledge ───────────────────────────────────────────────────────

export interface RagStats {
  conversation_stats?: {
    active_sessions?: number;
    total_conversations?: number;
    [key: string]: unknown;
  };
  engine_info?: {
    model?: string;
    embedding_model?: string;
    vector_store?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface RagSession {
  session_id: string;
  turn_count?: number;
  metadata?: Record<string, unknown>;
}

// ── Intelligence ────────────────────────────────────────────────────

export interface IntelligenceResult {
  results?: Record<string, unknown>;
  timings?: Record<string, number>;
  interaction_count?: number;
  session_id?: string;
  [key: string]: unknown;
}
