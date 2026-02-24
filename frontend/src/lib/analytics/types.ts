export type EventCategory =
  | "session"
  | "synthesis"
  | "concept"
  | "feedback"
  | "depth"
  | "sensory"
  | "error";

export interface AnalyticsEvent {
  id: string;
  timestamp: number;
  sessionId: string;
  category: EventCategory;
  action: string;
  label?: string;
  value?: number;
  metadata?: Record<string, unknown>;
}

export interface SessionSummary {
  sessionId: string;
  startTime: number;
  endTime: number;
  eventCount: number;
  synthesisCount: number;
  conceptsExplored: number;
  feedbackCount: number;
  mostUsedDepth: string | null;
}
