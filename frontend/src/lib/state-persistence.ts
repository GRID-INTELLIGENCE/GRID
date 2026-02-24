/**
 * State persistence layer — saves/restores QueryClient cache to localStorage.
 */

import { QueryClient } from "@tanstack/react-query";

const STORAGE_KEY = "grid-query-cache";

export function initializeStatePersistence(): void {
  // No-op on startup — cache is loaded when QueryClient is created
}

export function createPersistedQueryClient(): QueryClient {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes (Electron, no tab switching)
        gcTime: 30 * 60 * 1000, // 30 minutes
        refetchOnWindowFocus: false, // Electron — no tab switching
        retry: 1,
      },
    },
  });

  // Restore cache from localStorage on creation
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const entries = JSON.parse(raw) as {
        queryKey: readonly unknown[];
        data: unknown;
      }[];
      for (const entry of entries) {
        client.setQueryData(entry.queryKey, entry.data);
      }
    }
  } catch {
    // Corrupt cache — ignore
  }

  // Persist cache on window unload
  if (typeof window !== "undefined") {
    window.addEventListener("beforeunload", () => {
      try {
        const cache = client.getQueryCache().getAll();
        const entries = cache
          .filter((q) => q.state.data !== undefined)
          .slice(0, 50)
          .map((q) => ({
            queryKey: q.queryKey,
            data: q.state.data,
          }));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
      } catch {
        // Storage full or unavailable — ignore
      }
    });
  }

  return client;
}
