import { cn } from "@/lib/utils";
import type { SensoryProfile } from "@/types/mycelium";
import {
  Accessibility,
  Eye,
  Focus,
  Leaf,
  Monitor,
  ScanEye,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const profiles: {
  value: SensoryProfile;
  label: string;
  icon: LucideIcon;
}[] = [
  { value: "default", label: "Default", icon: Monitor },
  { value: "low_vision", label: "Low Vision", icon: Eye },
  { value: "screen_reader", label: "Screen Reader", icon: ScanEye },
  { value: "cognitive", label: "Cognitive", icon: Accessibility },
  { value: "focus", label: "Focus", icon: Focus },
  { value: "calm", label: "Calm", icon: Leaf },
];

interface SensoryPickerProps {
  value: SensoryProfile;
  onChange: (profile: SensoryProfile) => void;
}

export function SensoryPicker({ value, onChange }: SensoryPickerProps) {
  return (
    <fieldset className="flex flex-wrap gap-1.5">
      <legend className="sr-only">Sensory profile</legend>
      {profiles.map((p) => {
        const Icon = p.icon;
        const active = value === p.value;
        return (
          <button
            key={p.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={`${p.label} sensory profile`}
            onClick={() => onChange(p.value)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
              "cursor-pointer",
              active
                ? "border-[var(--primary)]/40 bg-[var(--primary)]/10 text-[var(--primary)]"
                : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--primary)]/20 hover:text-[var(--foreground)]"
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {p.label}
          </button>
        );
      })}
    </fieldset>
  );
}
