import { cn } from "@/lib/utils";
import { Copy, Minus, Square, X } from "lucide-react";
import { useEffect, useState } from "react";

const isElectron = typeof window !== "undefined" && !!window.windowControls;

/** SVG logo mark: 4 interconnected nodes — mycelium network motif */
function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {/* Edges */}
      <line
        x1="6"
        y1="6"
        x2="18"
        y2="6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      <line
        x1="6"
        y1="6"
        x2="6"
        y2="18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      <line
        x1="18"
        y1="6"
        x2="18"
        y2="18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      <line
        x1="6"
        y1="18"
        x2="18"
        y2="18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      <line
        x1="6"
        y1="6"
        x2="18"
        y2="18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.3"
      />
      {/* Nodes */}
      <circle cx="6" cy="6" r="2.5" fill="var(--primary)" />
      <circle cx="18" cy="6" r="2.5" fill="var(--primary)" />
      <circle cx="6" cy="18" r="2.5" fill="var(--primary)" />
      <circle cx="18" cy="18" r="2.5" fill="var(--primary)" />
    </svg>
  );
}

export function TitleBar() {
  const [maximized, setMaximized] = useState(false);

  useEffect(() => {
    if (!isElectron) return;
    const cleanup = window.windowControls.onMaximizeChange(setMaximized);
    window.windowControls.isMaximized().then(setMaximized);
    return cleanup;
  }, []);

  return (
    <header
      className="flex h-10 shrink-0 items-center justify-between border-b border-[var(--border)] bg-[var(--sidebar)]"
      style={
        isElectron
          ? ({ WebkitAppRegion: "drag" } as React.CSSProperties)
          : undefined
      }
    >
      {/* App identity */}
      <div className="flex items-center gap-2 pl-4">
        <LogoMark className="h-5 w-5 text-[var(--primary)] animate-pulse-organic" />
        <span
          className="text-xs font-bold uppercase text-[var(--muted-foreground)]"
          style={{
            letterSpacing: "0.15em",
            fontFamily: "var(--typography-font-family)",
          }}
        >
          GRID
        </span>
      </div>

      {/* Window controls — only in Electron */}
      {isElectron && (
        <div
          className="flex h-full"
          style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}
        >
          {[
            {
              icon: Minus,
              action: () => window.windowControls.minimize(),
              label: "Minimize",
            },
            {
              icon: maximized ? Copy : Square,
              action: () => window.windowControls.maximize(),
              label: maximized ? "Restore" : "Maximize",
            },
            {
              icon: X,
              action: () => window.windowControls.close(),
              label: "Close",
              danger: true,
            },
          ].map(({ icon: Icon, action, label, danger }) => (
            <button
              key={label}
              onClick={action}
              aria-label={label}
              className={cn(
                "flex h-full w-12 items-center justify-center transition-colors",
                danger
                  ? "hover:bg-[var(--destructive)] hover:text-white"
                  : "hover:bg-[var(--accent)]"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
            </button>
          ))}
        </div>
      )}
    </header>
  );
}
