/**
 * Hooks for detecting browser online/offline status.
 *
 * Uses `navigator.onLine` + `"online"` / `"offline"` events.
 *
 * - `useOnlineStatus()` — returns a boolean that is reactive.
 * - `useConnectivityEpoch()` — returns a monotonically increasing
 *   counter that increments on every connectivity change. Useful for
 *   invalidating UI state (e.g. dismissed banners) across transitions.
 */

import { useEffect, useSyncExternalStore } from "react";
import { onlineManager } from "@tanstack/react-query";

/* ------------------------------------------------------------------ */
/*  Online / Offline boolean store                                     */
/* ------------------------------------------------------------------ */

function subscribe(callback: () => void) {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getSnapshot() {
  return navigator.onLine;
}

function getServerSnapshot() {
  return true; // SSR always assumes online
}

/**
 * Returns `true` when the browser reports as online.
 *
 * Also syncs TanStack Query's `onlineManager` so that queries
 * automatically pause when the browser goes offline and resume
 * when it comes back online.
 */
export function useOnlineStatus(): boolean {
  const isOnline = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );

  // Keep TanStack Query's online manager in sync
  useEffect(() => {
    onlineManager.setOnline(isOnline);
  }, [isOnline]);

  return isOnline;
}

/* ------------------------------------------------------------------ */
/*  Connectivity epoch store                                           */
/* ------------------------------------------------------------------ */

let _epoch = 0;

function epochSubscribe(callback: () => void) {
  const handler = () => {
    _epoch++;
    callback();
  };
  window.addEventListener("online", handler);
  window.addEventListener("offline", handler);
  return () => {
    window.removeEventListener("online", handler);
    window.removeEventListener("offline", handler);
  };
}

function getEpochSnapshot() {
  return _epoch;
}

function getEpochServerSnapshot() {
  return 0;
}

/**
 * Returns a monotonically increasing number that increments on every
 * connectivity change (online ↔ offline). Two renders with the same
 * epoch value are guaranteed to be in the same connectivity "session".
 *
 * This is useful for invalidating dismiss-state in UI components
 * without resorting to `useEffect` + `setState` or ref access during
 * render.
 */
export function useConnectivityEpoch(): number {
  return useSyncExternalStore(
    epochSubscribe,
    getEpochSnapshot,
    getEpochServerSnapshot
  );
}
