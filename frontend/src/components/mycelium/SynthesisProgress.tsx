import { useEffect, useState } from "react";

const phases = [
  { label: "Reading", duration: 1200 },
  { label: "Analyzing", duration: 1800 },
  { label: "Synthesizing", duration: 2400 },
] as const;

interface SynthesisProgressProps {
  active: boolean;
}

export function SynthesisProgress({ active }: SynthesisProgressProps) {
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      // Reset on next tick to avoid synchronous setState in effect
      const reset = setTimeout(() => setPhaseIndex(0), 0);
      return () => clearTimeout(reset);
    }

    let idx = 0;
    const advance = () => {
      idx = Math.min(idx + 1, phases.length - 1);
      setPhaseIndex(idx);
    };

    const timers = phases.slice(0, -1).map((_phase, i) =>
      setTimeout(
        advance,
        phases.slice(0, i + 1).reduce((s, p) => s + p.duration, 0)
      )
    );

    return () => timers.forEach(clearTimeout);
  }, [active]);

  if (!active) return null;

  const phase = phases[phaseIndex];

  return (
    <div
      className="flex items-center gap-3"
      role="status"
      aria-live="polite"
      aria-label={`${phase.label} your text`}
    >
      {/* Tendril growth SVG */}
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        className="shrink-0"
        aria-hidden="true"
      >
        {phases.map((_, i) => {
          const reached = i <= phaseIndex;
          const cx = 4 + i * 8;
          return (
            <g key={i}>
              {i > 0 && (
                <line
                  x1={cx - 8}
                  y1="12"
                  x2={cx}
                  y2="12"
                  stroke={reached ? "var(--primary)" : "var(--muted)"}
                  strokeWidth="2"
                  strokeLinecap="round"
                  style={
                    reached
                      ? {
                          animation:
                            "connect-nodes 0.4s var(--motion-easing-decelerate) forwards",
                          animationDelay: `${i * 200}ms`,
                        }
                      : undefined
                  }
                />
              )}
              <circle
                cx={cx}
                cy="12"
                r={reached ? 3 : 2}
                fill={reached ? "var(--primary)" : "var(--muted)"}
                style={
                  reached
                    ? {
                        animation:
                          "scale-in 0.3s var(--motion-easing-organic) forwards",
                        animationDelay: `${i * 200}ms`,
                      }
                    : undefined
                }
              />
            </g>
          );
        })}
      </svg>

      <span className="text-sm font-medium text-[var(--muted-foreground)]">
        {phase.label}...
      </span>
    </div>
  );
}
