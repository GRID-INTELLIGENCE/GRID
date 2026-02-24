import { memo } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface FeedbackBarProps {
  onSimpler: () => void;
  onDeeper: () => void;
  disabled?: boolean;
}

export const FeedbackBar = memo(function FeedbackBar({
  onSimpler,
  onDeeper,
  disabled,
}: FeedbackBarProps) {
  return (
    <div
      className="flex items-center gap-2"
      role="group"
      aria-label="Content feedback"
    >
      <FeedbackButton
        onClick={onSimpler}
        disabled={disabled}
        icon={<ChevronDown className="h-3.5 w-3.5" />}
        label="Simpler"
        description="Make this easier to understand"
      />
      <FeedbackButton
        onClick={onDeeper}
        disabled={disabled}
        icon={<ChevronUp className="h-3.5 w-3.5" />}
        label="Deeper"
        description="Show me more detail"
      />
    </div>
  );
});

function FeedbackButton({
  onClick,
  disabled,
  icon,
  label,
  description,
}: {
  onClick: () => void;
  disabled?: boolean;
  icon: React.ReactNode;
  label: string;
  description: string;
}) {
  const [adjusting, setAdjusting] = useState(false);

  const handleClick = () => {
    setAdjusting(true);
    onClick();
    setTimeout(() => setAdjusting(false), 800);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      aria-label={description}
      className={cn(
        "group inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5",
        "text-xs font-medium text-[var(--muted-foreground)] transition-all",
        "hover:border-[var(--primary)]/40 hover:text-[var(--foreground)] hover:bg-[var(--accent)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
        "disabled:opacity-50 disabled:pointer-events-none cursor-pointer",
        adjusting &&
          "animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-[var(--card)] via-[var(--accent)] to-[var(--card)]"
      )}
    >
      <span className="transition-transform group-hover:scale-110">{icon}</span>
      {adjusting ? "Adjusting..." : label}
    </button>
  );
}
