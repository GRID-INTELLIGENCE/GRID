/**
 * Tests for ToolRegistry and ToolExecutor.
 */
import { z } from "zod";
import { toolRegistry } from "@/lib/tool-registry";
import { executePlan } from "@/lib/tool-executor";
import type { Plan, Tool } from "@/schema/tools";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ── Helpers ───────────────────────────────────────────────────────────

const EchoInputSchema = z.object({ message: z.string() });
type EchoInput = z.infer<typeof EchoInputSchema>;

function makeTool(
  id: string,
  overrides: Partial<Tool<EchoInput, { echo: string }>> = {}
): Tool<EchoInput, { echo: string }> {
  return {
    id,
    name: overrides.name ?? `Tool ${id}`,
    description: overrides.description ?? `Description for ${id}`,
    category: overrides.category ?? "info",
    inputSchema: EchoInputSchema,
    execute: overrides.execute ?? (async (input) => ({ echo: input.message })),
  };
}

// ── ToolRegistry ──────────────────────────────────────────────────────

describe("ToolRegistry", () => {
  beforeEach(() => {
    toolRegistry.clear();
  });

  afterEach(() => {
    toolRegistry.clear();
  });

  it("starts empty", () => {
    expect(toolRegistry.size).toBe(0);
    expect(toolRegistry.getAll()).toEqual([]);
  });

  it("registers and retrieves a tool", () => {
    const tool = makeTool("echo");
    toolRegistry.register(tool);
    expect(toolRegistry.has("echo")).toBe(true);
    expect(toolRegistry.get("echo")).toBe(tool);
    expect(toolRegistry.size).toBe(1);
  });

  it("throws on duplicate registration", () => {
    toolRegistry.register(makeTool("echo"));
    expect(() => toolRegistry.register(makeTool("echo"))).toThrow(
      /already registered/
    );
  });

  it("unregisters a tool", () => {
    toolRegistry.register(makeTool("echo"));
    expect(toolRegistry.unregister("echo")).toBe(true);
    expect(toolRegistry.has("echo")).toBe(false);
    expect(toolRegistry.size).toBe(0);
  });

  it("unregister returns false for unknown tool", () => {
    expect(toolRegistry.unregister("nonexistent")).toBe(false);
  });

  it("filters by category", () => {
    toolRegistry.register(makeTool("a", { category: "recon" }));
    toolRegistry.register(makeTool("b", { category: "network" }));
    toolRegistry.register(makeTool("c", { category: "recon" }));

    const reconTools = toolRegistry.getByCategory("recon");
    expect(reconTools).toHaveLength(2);
    expect(reconTools.map((t) => t.id).sort()).toEqual(["a", "c"]);
  });

  it("returns serializable metadata", () => {
    toolRegistry.register(makeTool("echo"));
    const meta = toolRegistry.getMetadata();
    expect(meta).toEqual([
      {
        id: "echo",
        name: "Tool echo",
        description: "Description for echo",
        category: "info",
      },
    ]);
  });

  it("clear removes all tools", () => {
    toolRegistry.register(makeTool("a"));
    toolRegistry.register(makeTool("b"));
    toolRegistry.clear();
    expect(toolRegistry.size).toBe(0);
  });
});

// ── ToolExecutor ──────────────────────────────────────────────────────

describe("ToolExecutor", () => {
  beforeEach(() => {
    toolRegistry.clear();
  });

  afterEach(() => {
    toolRegistry.clear();
  });

  function makePlan(steps: Plan["steps"], overrides: Partial<Plan> = {}): Plan {
    return {
      id: "test-plan",
      goal: "Test goal",
      steps,
      createdAt: Date.now(),
      ...overrides,
    };
  }

  it("executes a single-step plan successfully", async () => {
    const executeFn = vi.fn(async (input: EchoInput) => ({
      echo: input.message,
    }));
    toolRegistry.register(makeTool("echo", { execute: executeFn }));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "hello" },
          description: "Echo hello",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.planId).toBe("test-plan");
    expect(result.results).toHaveLength(1);
    expect(result.results[0].status).toBe("success");
    if (result.results[0].status === "success") {
      expect(result.results[0].data).toEqual({ echo: "hello" });
    }
    expect(executeFn).toHaveBeenCalledWith({ message: "hello" });
  });

  it("executes steps in order", async () => {
    const callOrder: number[] = [];
    toolRegistry.register(
      makeTool("echo", {
        execute: async (input) => {
          callOrder.push(Number(input.message));
          return { echo: input.message };
        },
      })
    );

    const plan = makePlan([
      {
        order: 2,
        call: {
          toolId: "echo",
          arguments: { message: "2" },
          description: "Step 2",
        },
        dryRun: false,
      },
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "0" },
          description: "Step 0",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "echo",
          arguments: { message: "1" },
          description: "Step 1",
        },
        dryRun: false,
      },
    ]);

    await executePlan(plan);
    expect(callOrder).toEqual([0, 1, 2]);
  });

  it("dry-run mode skips all steps", async () => {
    const executeFn = vi.fn(async () => ({ echo: "should not run" }));
    toolRegistry.register(makeTool("echo", { execute: executeFn }));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "hello" },
          description: "Echo",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan, { dryRun: true });
    expect(result.results[0].status).toBe("skipped");
    expect(executeFn).not.toHaveBeenCalled();
  });

  it("per-step dryRun flag is respected", async () => {
    const executeFn = vi.fn(async (input: EchoInput) => ({
      echo: input.message,
    }));
    toolRegistry.register(makeTool("echo", { execute: executeFn }));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "live" },
          description: "Live step",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "echo",
          arguments: { message: "dry" },
          description: "Dry step",
        },
        dryRun: true,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.results[0].status).toBe("success");
    expect(result.results[1].status).toBe("skipped");
    expect(executeFn).toHaveBeenCalledTimes(1);
  });

  it("stops on error by default", async () => {
    const executeFn = vi.fn(async () => {
      throw new Error("boom");
    });
    toolRegistry.register(makeTool("fail", { execute: executeFn }));
    toolRegistry.register(makeTool("echo"));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "fail",
          arguments: { message: "x" },
          description: "Failing step",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "echo",
          arguments: { message: "y" },
          description: "Should be skipped",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.results[0].status).toBe("error");
    expect(result.results[1].status).toBe("skipped");
    if (result.results[1].status === "skipped") {
      expect(result.results[1].reason).toMatch(/earlier failure/);
    }
  });

  it("continues on error when stopOnError=false", async () => {
    const executeFn = vi.fn(async () => {
      throw new Error("boom");
    });
    toolRegistry.register(makeTool("fail", { execute: executeFn }));
    toolRegistry.register(makeTool("echo"));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "fail",
          arguments: { message: "x" },
          description: "Failing step",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "echo",
          arguments: { message: "y" },
          description: "Should still run",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan, { stopOnError: false });
    expect(result.results[0].status).toBe("error");
    expect(result.results[1].status).toBe("success");
  });

  it("returns error for unknown tool", async () => {
    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "nonexistent",
          arguments: { message: "x" },
          description: "Unknown tool",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.results[0].status).toBe("error");
    if (result.results[0].status === "error") {
      expect(result.results[0].error).toMatch(/Unknown tool/);
    }
  });

  it("returns error for invalid input", async () => {
    toolRegistry.register(makeTool("echo"));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { wrong_field: 123 },
          description: "Bad input",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.results[0].status).toBe("error");
    if (result.results[0].status === "error") {
      expect(result.results[0].error).toMatch(/validation failed/i);
    }
  });

  it("marks step as error on timeout", async () => {
    const executeFn = vi.fn(async () => {
      await new Promise((resolve) => {
        setTimeout(resolve, 100);
      });
      return { echo: "late" };
    });

    toolRegistry.register(makeTool("echo", { execute: executeFn }));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "slow" },
          description: "Slow step",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan, { stepTimeoutMs: 10 });
    expect(result.results[0].status).toBe("error");
    if (result.results[0].status === "error") {
      expect(result.results[0].error).toMatch(/timed out/i);
      expect(result.results[0].durationMs).toBeGreaterThanOrEqual(10);
    }
  });

  it("fires onProgress callback", async () => {
    toolRegistry.register(makeTool("echo"));
    const progress: number[] = [];

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "a" },
          description: "Step 0",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "echo",
          arguments: { message: "b" },
          description: "Step 1",
        },
        dryRun: false,
      },
    ]);

    await executePlan(plan, {
      onProgress: (p) => progress.push(p.currentStep),
    });

    expect(progress).toEqual([0, 1]);
  });

  it("includes totalDurationMs and completedAt", async () => {
    toolRegistry.register(makeTool("echo"));

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "echo",
          arguments: { message: "a" },
          description: "Step",
        },
        dryRun: false,
      },
    ]);

    const result = await executePlan(plan);
    expect(result.totalDurationMs).toBeGreaterThanOrEqual(0);
    expect(result.completedAt).toBeGreaterThan(0);
  });

  it("returns error step when stepTimeoutMs is exceeded", async () => {
    // Register a slow tool that takes 100ms
    toolRegistry.register({
      id: "slow-tool",
      name: "Slow Tool",
      description: "A slow tool",
      category: "info",
      inputSchema: z.object({ message: z.string() }),
      execute: async () => {
        await new Promise((r) => setTimeout(r, 100));
        return { result: "done" };
      },
    });

    const plan = makePlan([
      {
        order: 0,
        call: {
          toolId: "slow-tool",
          arguments: { message: "test" },
          description: "Slow step",
        },
        dryRun: false,
      },
    ]);

    // Set timeout to 10ms, which is less than the 100ms the tool needs
    const result = await executePlan(plan, { stepTimeoutMs: 10 });
    expect(result.results[0].status).toBe("error");
    if (result.results[0].status === "error") {
      expect(result.results[0].error).toMatch(/timed out/i);
    }
  });
});
