import { cn } from "@/lib/utils";
import { Copy, Minus, Square, X } from "lucide-react";
import { useEffect, useState } from "react";

const isElectron = typeof window !== "undefined" && !!window.windowControls;

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
        <div className="h-4 w-4 rounded-sm bg-[var(--primary)] glow-primary" />
        <span className="text-xs font-bold tracking-widest uppercase text-[var(--muted-foreground)]">
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
