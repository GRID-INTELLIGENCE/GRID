import { cn } from "@/lib/utils";
import { useOnlineStatus } from "@/hooks/use-online-status";
import { useConnectivityEpoch } from "@/hooks/use-online-status";
import { WifiOff, X } from "lucide-react";
import { useState } from "react";

/**
 * A persistent banner that appears when the browser goes offline.
 *
 * - Uses `useOnlineStatus()` to react to connectivity changes.
 * - Dismissible via an X button; re-appears if offline status
 *   changes (goes online then offline again).
 *
 * Dismissed state is keyed to a monotonic **connectivity epoch**
 * (incremented on every online/offline transition). When the user
 * dismisses the banner we store the current epoch. The dismissal
 * is only valid while the stored epoch matches the live one — any
 * subsequent connectivity change bumps the epoch, invalidating the
 * old dismissal. No effects or refs needed.
 */
export function OfflineBanner({ className }: { className?: string }) {
  const isOnline = useOnlineStatus();
  const epoch = useConnectivityEpoch();

  // `dismissedEpoch` stores the epoch at the time the user clicked
  // dismiss. Dismissal is valid only while the epoch hasn't changed.
  const [dismissedEpoch, setDismissedEpoch] = useState<number | null>(null);

  const dismissed = dismissedEpoch === epoch;

  if (isOnline || dismissed) return null;

  return (
    <div
      role="alert"
      className={cn(
        "flex items-center justify-between gap-3 border-b px-4 py-2",
        "border-[var(--warning)]/30 bg-[var(--warning)]/10 text-[var(--warning)]",
        "text-sm font-medium",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <WifiOff className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span>
          You are offline. Some features may be unavailable until connectivity
          is restored.
        </span>
      </div>
      <button
        type="button"
        aria-label="Dismiss offline banner"
        onClick={() => setDismissedEpoch(epoch)}
        className={cn(
          "shrink-0 rounded-md p-1",
          "hover:bg-[var(--warning)]/20",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
          "transition-colors"
        )}
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
