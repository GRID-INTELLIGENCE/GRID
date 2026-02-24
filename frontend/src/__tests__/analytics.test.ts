import { describe, expect, it, beforeEach } from "vitest";
import {
  storeEvent,
  getEventsBySession,
  getSessionSummaries,
  exportAllData,
  clearAllData,
} from "@/lib/analytics/storage";
import type { AnalyticsEvent } from "@/lib/analytics/types";

function createEvent(overrides: Partial<AnalyticsEvent> = {}): AnalyticsEvent {
  return {
    id: `e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    timestamp: Date.now(),
    sessionId: "test-session-1",
    category: "synthesis",
    action: "complete",
    ...overrides,
  };
}

describe("Analytics storage", () => {
  beforeEach(async () => {
    await clearAllData();
  });

  it("stores and retrieves events by session", async () => {
    const event = createEvent({ sessionId: "s1" });
    storeEvent(event);

    // Wait for batched flush
    await new Promise((r) => setTimeout(r, 600));

    const events = await getEventsBySession("s1");
    expect(events).toHaveLength(1);
    expect(events[0].id).toBe(event.id);
  });

  it("returns empty array for unknown session", async () => {
    const events = await getEventsBySession("nonexistent");
    expect(events).toHaveLength(0);
  });

  it("generates session summaries", async () => {
    const events = [
      createEvent({
        sessionId: "s1",
        category: "session",
        action: "start",
        timestamp: 1000,
      }),
      createEvent({
        sessionId: "s1",
        category: "synthesis",
        action: "complete",
        timestamp: 2000,
      }),
      createEvent({
        sessionId: "s1",
        category: "synthesis",
        action: "complete",
        timestamp: 3000,
      }),
      createEvent({
        sessionId: "s1",
        category: "concept",
        action: "explore",
        timestamp: 4000,
      }),
      createEvent({
        sessionId: "s1",
        category: "depth",
        action: "change",
        label: "espresso",
        timestamp: 5000,
      }),
      createEvent({
        sessionId: "s1",
        category: "session",
        action: "end",
        timestamp: 6000,
      }),
    ];

    for (const e of events) storeEvent(e);
    await new Promise((r) => setTimeout(r, 600));

    const summaries = await getSessionSummaries();
    expect(summaries).toHaveLength(1);
    expect(summaries[0].synthesisCount).toBe(2);
    expect(summaries[0].conceptsExplored).toBe(1);
    expect(summaries[0].mostUsedDepth).toBe("espresso");
  });

  it("exports all data as JSON string", async () => {
    storeEvent(createEvent({ sessionId: "s1" }));
    storeEvent(createEvent({ sessionId: "s2" }));
    await new Promise((r) => setTimeout(r, 600));

    const json = await exportAllData();
    const parsed = JSON.parse(json);
    expect(parsed).toHaveLength(2);
  });

  it("clears all data", async () => {
    storeEvent(createEvent());
    await new Promise((r) => setTimeout(r, 600));

    await clearAllData();

    const summaries = await getSessionSummaries();
    expect(summaries).toHaveLength(0);
  });

  it("handles multiple sessions independently", async () => {
    storeEvent(
      createEvent({
        sessionId: "s1",
        category: "synthesis",
        action: "complete",
      })
    );
    storeEvent(
      createEvent({
        sessionId: "s2",
        category: "synthesis",
        action: "complete",
      })
    );
    storeEvent(
      createEvent({
        sessionId: "s2",
        category: "synthesis",
        action: "complete",
      })
    );
    await new Promise((r) => setTimeout(r, 600));

    const summaries = await getSessionSummaries();
    expect(summaries).toHaveLength(2);

    const s1 = summaries.find((s) => s.sessionId === "s1");
    const s2 = summaries.find((s) => s.sessionId === "s2");
    expect(s1?.synthesisCount).toBe(1);
    expect(s2?.synthesisCount).toBe(2);
  });
});
