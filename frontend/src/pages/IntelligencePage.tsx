import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useIntelligenceProcess } from "@/hooks";
import { cn } from "@/lib/utils";
import { appConfig, iconRegistry } from "@/schema";
import type { IconKey } from "@/schema/app-schema";
import type { IntelligenceResult } from "@/types/api";
import { ChevronRight, Loader2, Play, RotateCcw, Sparkles } from "lucide-react";
import { useCallback, useState } from "react";

type CapabilityId = string;

export function IntelligencePage() {
  const cfg = appConfig.intelligence;
  const [input, setInput] = useState("");
  const [selectedCapabilities, setSelectedCapabilities] = useState<
    Set<CapabilityId>
  >(new Set(cfg.capabilities.map((c) => c.id)));
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [history, setHistory] = useState<
    { input: string; result: IntelligenceResult; timestamp: number }[]
  >([]);

  const process = useIntelligenceProcess();

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim()) return;
      const trimmed = input.trim();
      process.mutate(
        {
          data: trimmed,
          capabilities: Array.from(selectedCapabilities),
          includeEvidence,
        },
        {
          onSuccess(res) {
            if (res.ok && res.data) {
              setHistory((prev) => [
                { input: trimmed, result: res.data, timestamp: Date.now() },
                ...prev,
              ]);
            }
          },
        }
      );
    },
    [input, process, selectedCapabilities, includeEvidence]
  );

  const toggleCapability = (id: string) => {
    setSelectedCapabilities((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{cfg.title}</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {cfg.description}
          </p>
        </div>
        <Badge variant="outline" className="gap-1.5">
          <Sparkles className="h-3 w-3" />
          {selectedCapabilities.size} / {cfg.capabilities.length} active
        </Badge>
      </div>

      {/* Capability toggles */}
      <div className="grid gap-3 sm:grid-cols-3">
        {cfg.capabilities.map((cap) => {
          const Icon = iconRegistry[cap.icon as IconKey];
          const active = selectedCapabilities.has(cap.id);
          return (
            <button
              key={cap.id}
              onClick={() => toggleCapability(cap.id)}
              className={cn(
                "group flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition-all",
                active
                  ? "border-[var(--primary)] bg-[var(--primary)]/5 shadow-sm"
                  : "border-[var(--border)] bg-[var(--card)] opacity-60 hover:opacity-80"
              )}
            >
              <div className="flex w-full items-center justify-between">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-md",
                    active ? "bg-[var(--primary)]/10" : "bg-[var(--muted)]"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4",
                      active
                        ? "text-[var(--primary)]"
                        : "text-[var(--muted-foreground)]"
                    )}
                  />
                </div>
                <div
                  className={cn(
                    "h-2.5 w-2.5 rounded-full transition-colors",
                    active ? "bg-[var(--primary)]" : "bg-[var(--muted)]"
                  )}
                />
              </div>
              <div>
                <p className="text-sm font-medium">{cap.label}</p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {cap.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
            <input
              type="checkbox"
              checked={includeEvidence}
              onChange={(e) => setIncludeEvidence(e.target.checked)}
              className="rounded border-[var(--border)]"
            />
            Include evidence
          </label>
        </div>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter data to process through the intelligence pipeline…"
          rows={4}
          className="w-full resize-none rounded-lg border border-[var(--input)] bg-transparent px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-[var(--muted-foreground)]">
            Ctrl+Enter to submit
          </p>
          <div className="flex gap-2">
            {history.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setHistory([])}
              >
                <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                Clear history
              </Button>
            )}
            <Button
              type="submit"
              disabled={
                process.isPending ||
                !input.trim() ||
                selectedCapabilities.size === 0
              }
            >
              {process.isPending ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-1.5 h-4 w-4" />
              )}
              Process
            </Button>
          </div>
        </div>
      </form>

      {/* Error */}
      {process.data && !process.data.ok && (
        <Card className="border-[var(--destructive)]/30">
          <CardContent className="p-4">
            <p className="text-sm text-[var(--destructive)]">
              {process.data.error ??
                "Failed to reach intelligence pipeline. Is the API server running?"}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Results history */}
      {history.map((entry, idx) => (
        <Card
          key={entry.timestamp}
          className={cn(
            "glass",
            idx === 0 && "border-[var(--primary)]/20 glow-primary"
          )}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-sm">
                <ChevronRight className="h-3.5 w-3.5 text-[var(--primary)]" />
                {entry.input.length > 80
                  ? `${entry.input.slice(0, 80)}…`
                  : entry.input}
              </CardTitle>
              <div className="flex items-center gap-2">
                {entry.result.interaction_count !== undefined && (
                  <Badge variant="outline" className="text-[10px]">
                    interaction #{entry.result.interaction_count}
                  </Badge>
                )}
                {entry.result.timings && (
                  <Badge variant="secondary" className="text-[10px]">
                    {Object.values(entry.result.timings)
                      .reduce((a, b) => a + b, 0)
                      .toFixed(0)}
                    ms total
                  </Badge>
                )}
                <span className="text-[10px] text-[var(--muted-foreground)]">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Timings breakdown */}
            {entry.result.timings &&
              Object.keys(entry.result.timings).length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Object.entries(entry.result.timings).map(([key, val]) => (
                    <Badge
                      key={key}
                      variant="outline"
                      className="text-[10px] font-mono"
                    >
                      {key}: {val.toFixed(1)}ms
                    </Badge>
                  ))}
                </div>
              )}
            {/* Results data */}
            {entry.result.results && (
              <pre className="overflow-x-auto rounded-md bg-[var(--muted)] p-3 text-xs leading-relaxed">
                {JSON.stringify(entry.result.results, null, 2)}
              </pre>
            )}
            {/* Fallback for unexpected shapes */}
            {!entry.result.results && (
              <pre className="overflow-x-auto rounded-md bg-[var(--muted)] p-3 text-xs leading-relaxed">
                {JSON.stringify(entry.result, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
