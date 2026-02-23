/**
 * Plan executor — runs a Plan's steps sequentially through the ToolRegistry.
 */

import type { Plan, PlanExecutionResult, StepResult } from "@/schema/tools";
import { toolRegistry } from "./tool-registry";

export interface ExecutionProgress {
  currentStep: number;
  totalSteps: number;
  planId: string;
}

export interface ExecutePlanOptions {
  dryRun?: boolean;
  stopOnError?: boolean;
  onProgress?: (progress: ExecutionProgress) => void;
}

export async function executePlan(
  plan: Plan,
  options: ExecutePlanOptions = {}
): Promise<PlanExecutionResult> {
  const { dryRun = false, stopOnError = true, onProgress } = options;
  const sorted = [...plan.steps].sort((a, b) => a.order - b.order);
  const results: StepResult[] = [];
  const start = performance.now();
  let failed = false;

  for (let i = 0; i < sorted.length; i++) {
    const step = sorted[i];

    onProgress?.({
      currentStep: i,
      totalSteps: sorted.length,
      planId: plan.id,
    });

    // Global or per-step dry run
    if (dryRun || step.dryRun) {
      results.push({
        status: "skipped",
        stepOrder: step.order,
        reason: "dry run",
      });
      continue;
    }

    // Skip remaining steps after a failure
    if (failed && stopOnError) {
      results.push({
        status: "skipped",
        stepOrder: step.order,
        reason: "Skipped due to earlier failure",
      });
      continue;
    }

    const tool = toolRegistry.get(step.call.toolId);
    if (!tool) {
      results.push({
        status: "error",
        stepOrder: step.order,
        error: `Unknown tool: "${step.call.toolId}"`,
      });
      failed = true;
      continue;
    }

    // Validate input
    const parsed = tool.inputSchema.safeParse(step.call.arguments);
    if (!parsed.success) {
      results.push({
        status: "error",
        stepOrder: step.order,
        error: `Input validation failed: ${parsed.error.message}`,
      });
      failed = true;
      continue;
    }

    // Execute
    const stepStart = performance.now();
    try {
      const data = await tool.execute(parsed.data);
      results.push({
        status: "success",
        stepOrder: step.order,
        data: data as Record<string, unknown>,
        durationMs: Math.round(performance.now() - stepStart),
      });
    } catch (err) {
      results.push({
        status: "error",
        stepOrder: step.order,
        error: err instanceof Error ? err.message : String(err),
        durationMs: Math.round(performance.now() - stepStart),
      });
      failed = true;
    }
  }

  return {
    planId: plan.id,
    results,
    totalDurationMs: Math.round(performance.now() - start),
    completedAt: Date.now(),
  };
}
