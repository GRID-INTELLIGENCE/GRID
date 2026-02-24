import { memo } from "react";
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
import { useState } from "react";

const profiles: {
  value: SensoryProfile;
  label: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    value: "default",
    label: "Default",
    description: "Standard display settings",
    icon: Monitor,
  },
  {
    value: "low_vision",
    label: "Low Vision",
    description: "Larger text, higher contrast",
    icon: Eye,
  },
  {
    value: "screen_reader",
    label: "Screen Reader",
    description: "Optimized for screen reader output",
    icon: ScanEye,
  },
  {
    value: "cognitive",
    label: "Cognitive",
    description: "Simplified layout, reduced complexity",
    icon: Accessibility,
  },
  {
    value: "focus",
    label: "Focus",
    description: "Minimal distractions, key content only",
    icon: Focus,
  },
  {
    value: "calm",
    label: "Calm",
    description: "Reduced motion, softer colors",
    icon: Leaf,
  },
];

interface SensoryPickerProps {
  value: SensoryProfile;
  onChange: (profile: SensoryProfile) => void;
}

export const SensoryPicker = memo(function SensoryPicker({
  value,
  onChange,
}: SensoryPickerProps) {
  const [hoveredProfile, setHoveredProfile] = useState<SensoryProfile | null>(
    null
  );
  const activeDescription = profiles.find(
    (p) => p.value === (hoveredProfile ?? value)
  )?.description;

  return (
    <fieldset className="space-y-2">
      <legend className="sr-only">Sensory profile</legend>
      <div className="flex flex-wrap gap-1.5">
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
              aria-describedby="sensory-description"
              onClick={() => onChange(p.value)}
              onMouseEnter={() => setHoveredProfile(p.value)}
              onMouseLeave={() => setHoveredProfile(null)}
              onFocus={() => setHoveredProfile(p.value)}
              onBlur={() => setHoveredProfile(null)}
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
      </div>
      <p
        id="sensory-description"
        className="text-xs text-[var(--muted-foreground)] transition-opacity min-h-[1.25rem]"
        aria-live="polite"
      >
        {activeDescription}
      </p>
    </fieldset>
  );
});
