import { memo } from "react";
import { cn } from "@/lib/utils";
import type { Depth } from "@/types/mycelium";
import { Coffee, Droplets, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const depths: {
  value: Depth;
  label: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    value: "espresso",
    label: "Espresso",
    description: "Quick gist",
    icon: Zap,
  },
  {
    value: "americano",
    label: "Americano",
    description: "Balanced",
    icon: Coffee,
  },
  {
    value: "cold_brew",
    label: "Cold Brew",
    description: "Full depth",
    icon: Droplets,
  },
];

interface DepthControlProps {
  value: Depth;
  onChange: (depth: Depth) => void;
  disabled?: boolean;
}

export const DepthControl = memo(function DepthControl({
  value,
  onChange,
  disabled,
}: DepthControlProps) {
  return (
    <fieldset
      className="relative flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--card)] p-1"
      disabled={disabled}
    >
      <legend className="sr-only">Synthesis depth</legend>
      {depths.map((d) => {
        const Icon = d.icon;
        const active = value === d.value;
        return (
          <button
            key={d.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={`${d.label}: ${d.description}`}
            onClick={() => onChange(d.value)}
            className={cn(
              "relative inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
              "cursor-pointer",
              active
                ? "bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm"
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--accent)]"
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {d.label}
          </button>
        );
      })}
    </fieldset>
  );
});
