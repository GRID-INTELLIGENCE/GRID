import type { AnalyticsEvent, SessionSummary } from "./types";

const DB_NAME = "grid-analytics";
const DB_VERSION = 1;
const EVENTS_STORE = "events";
const BATCH_INTERVAL = 500;
const PURGE_DAYS = 30;

let db: IDBDatabase | null = null;
let eventQueue: AnalyticsEvent[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function openDB(): Promise<IDBDatabase> {
  if (db) return Promise.resolve(db);

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(EVENTS_STORE)) {
        const store = database.createObjectStore(EVENTS_STORE, {
          keyPath: "id",
        });
        store.createIndex("sessionId", "sessionId", { unique: false });
        store.createIndex("timestamp", "timestamp", { unique: false });
        store.createIndex("category", "category", { unique: false });
      }
    };

    request.onsuccess = () => {
      db = request.result;
      resolve(db);
    };

    request.onerror = () => reject(request.error);
  });
}

function flushQueue(): void {
  if (eventQueue.length === 0) return;

  const batch = [...eventQueue];
  eventQueue = [];

  openDB()
    .then((database) => {
      const tx = database.transaction(EVENTS_STORE, "readwrite");
      const store = tx.objectStore(EVENTS_STORE);
      for (const event of batch) {
        store.put(event);
      }
    })
    .catch(() => {
      // Fire-and-forget: silently drop events if DB fails
    });
}

function scheduleFlush(): void {
  if (flushTimer) return;
  flushTimer = setTimeout(() => {
    flushTimer = null;
    flushQueue();
  }, BATCH_INTERVAL);
}

export function storeEvent(event: AnalyticsEvent): void {
  eventQueue.push(event);
  scheduleFlush();
}

export async function getEventsBySession(
  sessionId: string
): Promise<AnalyticsEvent[]> {
  const database = await openDB();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(EVENTS_STORE, "readonly");
    const store = tx.objectStore(EVENTS_STORE);
    const index = store.index("sessionId");
    const request = index.getAll(sessionId);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function getSessionSummaries(): Promise<SessionSummary[]> {
  const database = await openDB();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(EVENTS_STORE, "readonly");
    const store = tx.objectStore(EVENTS_STORE);
    const request = store.getAll();

    request.onsuccess = () => {
      const events: AnalyticsEvent[] = request.result;
      const sessions = new Map<string, AnalyticsEvent[]>();

      for (const event of events) {
        const list = sessions.get(event.sessionId) ?? [];
        list.push(event);
        sessions.set(event.sessionId, list);
      }

      const summaries: SessionSummary[] = [];
      for (const [sessionId, sessionEvents] of sessions) {
        const timestamps = sessionEvents.map((e) => e.timestamp);
        const depthCounts = new Map<string, number>();

        let synthesisCount = 0;
        let conceptsExplored = 0;
        let feedbackCount = 0;

        for (const e of sessionEvents) {
          if (e.category === "synthesis" && e.action === "complete")
            synthesisCount++;
          if (e.category === "concept") conceptsExplored++;
          if (e.category === "feedback") feedbackCount++;
          if (e.category === "depth") {
            const d = e.label ?? "unknown";
            depthCounts.set(d, (depthCounts.get(d) ?? 0) + 1);
          }
        }

        let mostUsedDepth: string | null = null;
        let maxCount = 0;
        for (const [depth, count] of depthCounts) {
          if (count > maxCount) {
            maxCount = count;
            mostUsedDepth = depth;
          }
        }

        summaries.push({
          sessionId,
          startTime: Math.min(...timestamps),
          endTime: Math.max(...timestamps),
          eventCount: sessionEvents.length,
          synthesisCount,
          conceptsExplored,
          feedbackCount,
          mostUsedDepth,
        });
      }

      summaries.sort((a, b) => b.startTime - a.startTime);
      resolve(summaries);
    };

    request.onerror = () => reject(request.error);
  });
}

export async function exportAllData(): Promise<string> {
  const database = await openDB();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(EVENTS_STORE, "readonly");
    const store = tx.objectStore(EVENTS_STORE);
    const request = store.getAll();
    request.onsuccess = () => resolve(JSON.stringify(request.result, null, 2));
    request.onerror = () => reject(request.error);
  });
}

export async function clearAllData(): Promise<void> {
  const database = await openDB();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(EVENTS_STORE, "readwrite");
    const store = tx.objectStore(EVENTS_STORE);
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function purgeOldEvents(): Promise<void> {
  const cutoff = Date.now() - PURGE_DAYS * 24 * 60 * 60 * 1000;
  const database = await openDB();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(EVENTS_STORE, "readwrite");
    const store = tx.objectStore(EVENTS_STORE);
    const index = store.index("timestamp");
    const range = IDBKeyRange.upperBound(cutoff);
    const request = index.openCursor(range);

    request.onsuccess = () => {
      const cursor = request.result;
      if (cursor) {
        cursor.delete();
        cursor.continue();
      } else {
        resolve();
      }
    };

    request.onerror = () => reject(request.error);
  });
}
