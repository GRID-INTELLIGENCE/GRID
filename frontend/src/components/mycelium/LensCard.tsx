import { cn } from "@/lib/utils";
import type { NavigationResult } from "@/types/mycelium";
import { Lightbulb, RefreshCw } from "lucide-react";

interface LensCardProps {
  result: NavigationResult;
  onTryDifferent: () => void;
  onClose: () => void;
}

export function LensCard({ result, onTryDifferent, onClose }: LensCardProps) {
  return (
    <div
      className="rounded-xl border border-[var(--primary)]/20 bg-[var(--card)] p-5 space-y-4 animate-fade-in"
      role="region"
      aria-label={`Exploring: ${result.concept}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Lightbulb
            className="h-4 w-4 text-[var(--primary)]"
            aria-hidden="true"
          />
          <h3 className="text-sm font-semibold text-[var(--foreground)]">
            {result.concept}
            <span className="ml-2 text-xs font-normal text-[var(--muted-foreground)]">
              {result.lens.pattern} lens
            </span>
          </h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close concept explorer"
          className={cn(
            "rounded-md p-1 text-[var(--muted-foreground)]",
            "hover:text-[var(--foreground)] hover:bg-[var(--accent)] transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
            "cursor-pointer"
          )}
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      {/* ELI5 — the simple explanation */}
      <p className="text-sm leading-relaxed text-[var(--foreground)]">
        {result.lens.eli5}
      </p>

      {/* Analogy */}
      {result.lens.analogy && (
        <p className="text-sm italic text-[var(--muted-foreground)] leading-relaxed">
          {result.lens.analogy}
        </p>
      )}

      {/* Visual hint */}
      {result.lens.visual_hint && (
        <p className="text-xs text-[var(--muted-foreground)]">
          {result.lens.visual_hint}
        </p>
      )}

      {/* Actions */}
      {result.alternatives_available > 0 && (
        <button
          type="button"
          onClick={onTryDifferent}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5",
            "text-xs font-medium text-[var(--muted-foreground)] transition-all",
            "hover:border-[var(--primary)]/40 hover:text-[var(--foreground)]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
            "cursor-pointer"
          )}
          aria-label={`Try a different lens for ${result.concept}. ${result.alternatives_available} alternatives available.`}
        >
          <RefreshCw className="h-3 w-3" aria-hidden="true" />
          Try different lens
          <span className="text-[var(--muted-foreground)]/60">
            ({result.alternatives_available} more)
          </span>
        </button>
      )}
    </div>
  );
}
