import { useCallback, useRef } from "react";
import type {
  AnalyticsEvent,
  EventCategory,
  SessionSummary,
} from "@/lib/analytics/types";
import {
  clearAllData,
  exportAllData,
  getSessionSummaries,
  storeEvent,
} from "@/lib/analytics/storage";

let sessionId: string | null = null;

function getSessionId(): string {
  if (!sessionId) {
    sessionId = `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }
  return sessionId;
}

function generateId(): string {
  return `e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function isEnabled(): boolean {
  try {
    return localStorage.getItem("grid-analytics-enabled") !== "false";
  } catch {
    return true;
  }
}

export function useAnalytics() {
  const enabledRef = useRef(isEnabled());

  const track = useCallback(
    (
      category: EventCategory,
      action: string,
      label?: string,
      value?: number,
      metadata?: Record<string, unknown>
    ): void => {
      if (!enabledRef.current) return;

      const event: AnalyticsEvent = {
        id: generateId(),
        timestamp: Date.now(),
        sessionId: getSessionId(),
        category,
        action,
        label,
        value,
        metadata,
      };

      storeEvent(event);
    },
    []
  );

  const getInsights = useCallback((): Promise<SessionSummary[]> => {
    return getSessionSummaries();
  }, []);

  const exportData = useCallback((): Promise<string> => {
    return exportAllData();
  }, []);

  const clearData = useCallback((): Promise<void> => {
    return clearAllData();
  }, []);

  return { track, getInsights, exportData, clearData };
}
