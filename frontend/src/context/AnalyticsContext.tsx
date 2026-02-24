import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useAnalytics } from "@/hooks/use-analytics";
import { purgeOldEvents } from "@/lib/analytics/storage";
import type { EventCategory, SessionSummary } from "@/lib/analytics/types";

const STORAGE_KEY = "grid-analytics-enabled";

interface AnalyticsContextValue {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
  track: (
    category: EventCategory,
    action: string,
    label?: string,
    value?: number,
    metadata?: Record<string, unknown>
  ) => void;
  getInsights: () => Promise<SessionSummary[]>;
  exportData: () => Promise<string>;
  clearData: () => Promise<void>;
}

const AnalyticsContext = createContext<AnalyticsContextValue | null>(null);

function getStoredEnabled(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== "false";
  } catch {
    return true;
  }
}

export function AnalyticsProvider({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const [enabled, setEnabledState] = useState(getStoredEnabled);
  const analytics = useAnalytics();

  const setEnabled = useCallback((next: boolean) => {
    setEnabledState(next);
    try {
      localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      // localStorage unavailable
    }
  }, []);

  // Auto-purge old events on startup
  useEffect(() => {
    if (enabled) {
      purgeOldEvents().catch(() => undefined);
    }
  }, [enabled]);

  // Track session start
  useEffect(() => {
    if (enabled) {
      analytics.track("session", "start");
    }

    const handleUnload = () => {
      if (enabled) {
        analytics.track("session", "end");
      }
    };

    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, [enabled, analytics]);

  const track: AnalyticsContextValue["track"] = useCallback(
    (...args) => {
      if (enabled) analytics.track(...args);
    },
    [enabled, analytics]
  );

  return (
    <AnalyticsContext.Provider
      value={{
        enabled,
        setEnabled,
        track,
        getInsights: analytics.getInsights,
        exportData: analytics.exportData,
        clearData: analytics.clearData,
      }}
    >
      {children}
    </AnalyticsContext.Provider>
  );
}

export function useAnalyticsContext(): AnalyticsContextValue {
  const ctx = useContext(AnalyticsContext);
  if (!ctx) {
    throw new Error(
      "useAnalyticsContext must be used within an AnalyticsProvider"
    );
  }
  return ctx;
}
