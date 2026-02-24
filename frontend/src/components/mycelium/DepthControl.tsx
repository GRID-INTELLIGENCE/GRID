import { cn } from "@/lib/utils";
import type { Depth } from "@/types/mycelium";

const depths: { value: Depth; label: string; description: string }[] = [
  { value: "espresso", label: "Espresso", description: "Quick gist" },
  { value: "americano", label: "Americano", description: "Balanced" },
  { value: "cold_brew", label: "Cold Brew", description: "Full depth" },
];

interface DepthControlProps {
  value: Depth;
  onChange: (depth: Depth) => void;
  disabled?: boolean;
}

export function DepthControl({ value, onChange, disabled }: DepthControlProps) {
  return (
    <fieldset
      className="flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--card)] p-1"
      disabled={disabled}
    >
      <legend className="sr-only">Synthesis depth</legend>
      {depths.map((d) => (
        <button
          key={d.value}
          type="button"
          role="radio"
          aria-checked={value === d.value}
          aria-label={`${d.label}: ${d.description}`}
          onClick={() => onChange(d.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-medium transition-all",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
            "cursor-pointer",
            value === d.value
              ? "bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm"
              : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--accent)]"
          )}
        >
          {d.label}
        </button>
      ))}
    </fieldset>
  );
}
