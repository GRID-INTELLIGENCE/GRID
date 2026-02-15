import {
  ExecuteToolPayloadSchema,
  PlanPreviewPayloadSchema,
  PlanSchema,
  PlanStepSchema,
  StepResultSchema,
  ToolCallSchema,
  ToolCategorySchema,
  ToolMetadataSchema,
} from "@/schema/tools";
import { describe, expect, it } from "vitest";

// ── ToolCategorySchema ────────────────────────────────────────────────

describe("ToolCategorySchema", () => {
  it.each(["recon", "network", "security", "info"])('accepts "%s"', (cat) => {
    expect(ToolCategorySchema.parse(cat)).toBe(cat);
  });

  it("rejects invalid categories", () => {
    expect(() => ToolCategorySchema.parse("hacking")).toThrow();
  });
});

// ── ToolMetadataSchema ────────────────────────────────────────────────

describe("ToolMetadataSchema", () => {
  it("parses valid metadata", () => {
    const meta = {
      id: "ping",
      name: "Ping",
      description: "Send ICMP echo requests",
      category: "network",
    };
    expect(ToolMetadataSchema.parse(meta)).toEqual(meta);
  });

  it("rejects missing fields", () => {
    expect(() => ToolMetadataSchema.parse({ id: "ping" })).toThrow();
  });
});

// ── ToolCallSchema ────────────────────────────────────────────────────

describe("ToolCallSchema", () => {
  it("parses a valid tool call", () => {
    const call = {
      toolId: "dns-lookup",
      arguments: { host: "example.com", recordType: "A" },
      description: "Look up A records for example.com",
    };
    expect(ToolCallSchema.parse(call)).toEqual(call);
  });

  it("rejects missing description", () => {
    expect(() =>
      ToolCallSchema.parse({
        toolId: "ping",
        arguments: {},
      })
    ).toThrow();
  });
});

// ── PlanStepSchema ────────────────────────────────────────────────────

describe("PlanStepSchema", () => {
  it("parses a valid step with dryRun default", () => {
    const step = {
      order: 0,
      call: {
        toolId: "ping",
        arguments: { host: "8.8.8.8" },
        description: "Ping Google DNS",
      },
    };
    const parsed = PlanStepSchema.parse(step);
    expect(parsed.dryRun).toBe(false);
    expect(parsed.order).toBe(0);
  });

  it("accepts explicit dryRun=true", () => {
    const step = {
      order: 1,
      call: {
        toolId: "whois",
        arguments: { host: "example.com" },
        description: "WHOIS lookup",
      },
      dryRun: true,
    };
    expect(PlanStepSchema.parse(step).dryRun).toBe(true);
  });

  it("rejects negative order", () => {
    expect(() =>
      PlanStepSchema.parse({
        order: -1,
        call: {
          toolId: "ping",
          arguments: {},
          description: "test",
        },
      })
    ).toThrow();
  });
});

// ── PlanSchema ────────────────────────────────────────────────────────

describe("PlanSchema", () => {
  const validPlan = {
    id: "plan-1",
    goal: "Investigate example.com",
    steps: [
      {
        order: 0,
        call: {
          toolId: "dns-lookup",
          arguments: { host: "example.com" },
          description: "DNS lookup",
        },
      },
      {
        order: 1,
        call: {
          toolId: "whois",
          arguments: { host: "example.com" },
          description: "WHOIS lookup",
        },
      },
    ],
    createdAt: Date.now(),
  };

  it("parses a valid plan", () => {
    const parsed = PlanSchema.parse(validPlan);
    expect(parsed.steps).toHaveLength(2);
    expect(parsed.goal).toBe("Investigate example.com");
  });

  it("accepts optional estimatedDurationMs", () => {
    const parsed = PlanSchema.parse({
      ...validPlan,
      estimatedDurationMs: 5000,
    });
    expect(parsed.estimatedDurationMs).toBe(5000);
  });

  it("rejects missing goal", () => {
    const { goal: _, ...noGoal } = validPlan;
    expect(() => PlanSchema.parse(noGoal)).toThrow();
  });

  it("allows empty steps array", () => {
    const parsed = PlanSchema.parse({ ...validPlan, steps: [] });
    expect(parsed.steps).toHaveLength(0);
  });
});

// ── StepResultSchema ──────────────────────────────────────────────────

describe("StepResultSchema", () => {
  it("parses a success result", () => {
    const result = {
      status: "success" as const,
      stepOrder: 0,
      data: { latency: 12 },
      durationMs: 150,
    };
    expect(StepResultSchema.parse(result)).toEqual(result);
  });

  it("parses a skipped result", () => {
    const result = {
      status: "skipped" as const,
      stepOrder: 1,
      reason: "Dry run",
    };
    expect(StepResultSchema.parse(result)).toEqual(result);
  });

  it("parses an error result", () => {
    const result = {
      status: "error" as const,
      stepOrder: 2,
      error: "Connection refused",
      durationMs: 3000,
    };
    expect(StepResultSchema.parse(result)).toEqual(result);
  });

  it("rejects unknown status", () => {
    expect(() =>
      StepResultSchema.parse({ status: "unknown", stepOrder: 0 })
    ).toThrow();
  });
});

// ── IPC Payload Schemas ───────────────────────────────────────────────

describe("ExecuteToolPayloadSchema", () => {
  it("parses valid payload with dryRun default", () => {
    const payload = { toolId: "ping", arguments: { host: "1.1.1.1" } };
    const parsed = ExecuteToolPayloadSchema.parse(payload);
    expect(parsed.dryRun).toBe(false);
  });

  it("accepts explicit dryRun", () => {
    const payload = {
      toolId: "ping",
      arguments: { host: "1.1.1.1" },
      dryRun: true,
    };
    expect(ExecuteToolPayloadSchema.parse(payload).dryRun).toBe(true);
  });
});

describe("PlanPreviewPayloadSchema", () => {
  it("parses valid payload", () => {
    const payload = { goal: "Scan example.com" };
    expect(PlanPreviewPayloadSchema.parse(payload)).toEqual(payload);
  });

  it("accepts optional context", () => {
    const payload = {
      goal: "Scan example.com",
      context: "Production server",
    };
    expect(PlanPreviewPayloadSchema.parse(payload)).toEqual(payload);
  });
});
