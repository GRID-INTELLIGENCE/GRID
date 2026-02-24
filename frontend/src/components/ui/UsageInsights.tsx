import { useAnalyticsContext } from "@/context/AnalyticsContext";
import { cn } from "@/lib/utils";
import type { SessionSummary } from "@/lib/analytics/types";
import { Download, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

export function UsageInsights(): React.JSX.Element {
  const { getInsights, exportData, clearData } = useAnalyticsContext();
  const [summaries, setSummaries] = useState<SessionSummary[]>([]);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    getInsights()
      .then(setSummaries)
      .catch(() => undefined);
  }, [getInsights]);

  const totalSyntheses = summaries.reduce((s, r) => s + r.synthesisCount, 0);
  const totalSessions = summaries.length;

  // Most used depth across all sessions
  const depthCounts = new Map<string, number>();
  for (const s of summaries) {
    if (s.mostUsedDepth) {
      depthCounts.set(
        s.mostUsedDepth,
        (depthCounts.get(s.mostUsedDepth) ?? 0) + 1
      );
    }
  }
  const depthEntries = [...depthCounts.entries()].sort((a, b) => b[1] - a[1]);
  const maxDepthCount = depthEntries[0]?.[1] ?? 0;

  const handleExport = useCallback(async () => {
    const json = await exportData();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `grid-analytics-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [exportData]);

  const handleClear = useCallback(async () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    await clearData();
    setSummaries([]);
    setConfirming(false);
  }, [confirming, clearData]);

  return (
    <div className="space-y-4">
      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Total syntheses" value={totalSyntheses} />
        <StatCard label="Sessions" value={totalSessions} />
        <StatCard
          label="Concepts explored"
          value={summaries.reduce((s, r) => s + r.conceptsExplored, 0)}
        />
      </div>

      {/* Depth usage bar chart */}
      {depthEntries.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
            Depth Preference
          </h4>
          <div className="space-y-1.5">
            {depthEntries.map(([depth, count]) => (
              <div key={depth} className="flex items-center gap-2">
                <span className="w-20 text-xs text-[var(--muted-foreground)] capitalize">
                  {depth}
                </span>
                <div className="flex-1 h-2 rounded-full bg-[var(--muted)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--primary)] transition-all"
                    style={{ width: `${(count / maxDepthCount) * 100}%` }}
                  />
                </div>
                <span className="w-6 text-right text-xs text-[var(--muted-foreground)]">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleExport}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5",
            "text-xs font-medium text-[var(--muted-foreground)] transition-all cursor-pointer",
            "hover:border-[var(--primary)]/40 hover:text-[var(--foreground)]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
          )}
        >
          <Download className="h-3 w-3" aria-hidden="true" />
          Export JSON
        </button>
        <button
          type="button"
          onClick={handleClear}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5",
            "text-xs font-medium transition-all cursor-pointer",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
            confirming
              ? "border-[var(--destructive)]/40 text-[var(--destructive)] hover:bg-[var(--destructive)]/10"
              : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--destructive)]/40 hover:text-[var(--destructive)]"
          )}
        >
          <Trash2 className="h-3 w-3" aria-hidden="true" />
          {confirming ? "Confirm clear" : "Clear data"}
        </button>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-3">
      <p className="text-2xl font-semibold text-[var(--foreground)]">{value}</p>
      <p className="text-xs text-[var(--muted-foreground)]">{label}</p>
    </div>
  );
}
