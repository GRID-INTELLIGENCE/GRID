import { cn } from "@/lib/utils";
import type { Highlight } from "@/types/mycelium";

const priorityStyles: Record<Highlight["priority"], string> = {
  critical:
    "bg-[var(--primary)]/15 text-[var(--primary)] border-[var(--primary)]/30",
  high: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  medium:
    "bg-[var(--muted)]/50 text-[var(--muted-foreground)] border-[var(--border)]",
  low: "bg-transparent text-[var(--muted-foreground)] border-[var(--border)]",
};

interface HighlightPillProps {
  highlight: Highlight;
  onClick?: () => void;
}

export function HighlightPill({ highlight, onClick }: HighlightPillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all",
        "hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
        "cursor-pointer select-none",
        priorityStyles[highlight.priority]
      )}
      aria-label={`${highlight.priority} keyword: ${highlight.text}`}
    >
      {highlight.priority === "critical" && (
        <span
          className="h-1.5 w-1.5 rounded-full bg-current"
          aria-hidden="true"
        />
      )}
      {highlight.text}
    </button>
  );
}
