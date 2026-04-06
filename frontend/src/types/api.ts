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

/** Persisted JSON knowledge graph — counts from GET /api/v1/knowledge/stats */
export interface KnowledgeGraphStats {
  total_entities?: number;
  total_relationships?: number;
  entity_counts?: Record<string, number>;
  relationship_counts?: Record<string, number>;
  storage_path?: string;
  [key: string]: unknown;
}

export type GraphDecisionCode =
  | "SCHEMA_INVALID"
  | "GRAPH_TOO_LARGE"
  | "LAYOUT_TIMEOUT"
  | "INCONSISTENT_GRAPH"
  | "UNSUPPORTED_REQUEST";

export interface GraphDecisionErrorPayload {
  code: GraphDecisionCode;
  message: string;
  status: number;
  suggested_actions?: string[];
  details?: Record<string, unknown>;
}

export interface KnowledgeGraphLimits {
  requested_max_nodes?: number | null;
  applied_max_nodes: number;
  max_edges: number;
  timeout_ms: number;
  export_ms?: number;
}

/** Payload from GET /api/v1/knowledge/graph */
export interface KnowledgeGraphNode {
  id: string;
  label: string;
  entity_type: string;
  subtitle?: string;
}

export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
}

export interface KnowledgeGraphPayload {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  storage_path?: string;
  /** Full entity count in store (may exceed nodes.length when truncated). */
  total_entities?: number;
  /** True when max_nodes capped the node set. */
  truncated?: boolean;
  /** Stable hash for the node/edge payload, suitable as a layout cache key. */
  graph_hash?: string;
  limits?: KnowledgeGraphLimits;
}

// ── Admission Gate ──────────────────────────────────────────────────

export interface AdmissionPolicyBillboard {
  billboard_version: string;
  principles: Record<string, boolean>;
  ethical_dos: string[];
  ethical_donts: string[];
  penalty_tiers: Record<string, string>;
  caution: string;
  evolution_notice: string;
  timestamp: string;
}

export interface AdmissionGateStats {
  total_admitted: number;
  total_rejected: number;
  rejection_reasons: Record<string, number>;
  tracked_entities: number;
  bannered_entities: number;
  timestamp: string;
}

export interface AdmissionViolation {
  type: string;
  penalty_points: number;
  metadata: Record<string, unknown>;
}

export interface AdmissionEntityReport {
  entity_id: string;
  found: boolean;
  violation_count: number;
  total_penalty_points: number;
  bannered: boolean;
  banner_reason: string;
  profit_mask_violations: number;
  penalty_tier: string;
  tier_description: string;
  violations: AdmissionViolation[];
  timestamp: string;
}

export interface AdmissionBanneredEntities {
  count: number;
  entities: AdmissionEntityReport[];
  timestamp: string;
}

export interface ComplianceCheckRequest {
  payload: Record<string, unknown>;
  headers?: Record<string, string>;
  entity_id?: string;
  target_path?: string;
}

export interface PenaltyApplyRequest {
  entity_id: string;
  violation_type: string;
  profit_masked?: boolean;
  metadata?: Record<string, unknown>;
  reason?: string;
}

export interface PenaltyRevokeRequest {
  entity_id: string;
  action: "revoke_banner" | "reduce_penalty" | "full_reset";
  reduction_points?: number;
  reason?: string;
}

// ── Intelligence ────────────────────────────────────────────────────

export interface IntelligenceResult {
  results?: Record<string, unknown>;
  timings?: Record<string, number>;
  interaction_count?: number;
  session_id?: string;
  [key: string]: unknown;
}
