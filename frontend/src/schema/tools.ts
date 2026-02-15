/**
 * Tool System — Zod schemas and TypeScript types.
 *
 * Defines the `Tool<TInput, TOutput>` interface that every built-in
 * or user-defined tool must implement, plus the plan/execution schemas
 * used by IPC channels.
 */
import { z } from "zod";

// ── Tool Category ─────────────────────────────────────────────────────

export const ToolCategorySchema = z.enum([
  "recon",
  "network",
  "security",
  "info",
]);
export type ToolCategory = z.infer<typeof ToolCategorySchema>;

// ── Tool Definition ───────────────────────────────────────────────────

/**
 * A tool is a self-describing, validated unit of execution.
 *
 * - `id` — unique machine-readable identifier (e.g. `"dns-lookup"`)
 * - `name` — human-readable display name
 * - `description` — one-line summary for the LLM planner / UI
 * - `category` — used for grouping in the UI
 * - `inputSchema` — Zod schema that validates + types the input
 * - `execute` — the actual implementation; receives validated input
 *
 * Generic params allow each tool to declare its own I/O shapes while
 * the registry can hold `Tool<unknown, unknown>` for dynamic dispatch.
 */
export interface Tool<
  TInput = Record<string, unknown>,
  TOutput = Record<string, unknown>,
> {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly category: ToolCategory;
  readonly inputSchema: z.ZodType<TInput>;
  execute(input: TInput): Promise<TOutput>;
}

// ── Tool Metadata (serializable subset for UI / LLM) ─────────────────

export const ToolMetadataSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  category: ToolCategorySchema,
});
export type ToolMetadata = z.infer<typeof ToolMetadataSchema>;

// ── Plan Schemas ──────────────────────────────────────────────────────

export const ToolCallSchema = z.object({
  toolId: z.string(),
  arguments: z.record(z.unknown()),
  description: z.string(),
});
export type ToolCall = z.infer<typeof ToolCallSchema>;

export const PlanStepSchema = z.object({
  order: z.number().int().nonnegative(),
  call: ToolCallSchema,
  /** When true the executor should show the user what *would* happen. */
  dryRun: z.boolean().default(false),
});
export type PlanStep = z.infer<typeof PlanStepSchema>;

export const PlanSchema = z.object({
  id: z.string(),
  goal: z.string(),
  steps: z.array(PlanStepSchema),
  estimatedDurationMs: z.number().nonnegative().optional(),
  createdAt: z.number(),
});
export type Plan = z.infer<typeof PlanSchema>;

// ── Step Execution Result ─────────────────────────────────────────────

export const StepResultSchema = z.discriminatedUnion("status", [
  z.object({
    status: z.literal("success"),
    stepOrder: z.number(),
    data: z.record(z.unknown()),
    durationMs: z.number(),
  }),
  z.object({
    status: z.literal("skipped"),
    stepOrder: z.number(),
    reason: z.string(),
  }),
  z.object({
    status: z.literal("error"),
    stepOrder: z.number(),
    error: z.string(),
    durationMs: z.number().optional(),
  }),
]);
export type StepResult = z.infer<typeof StepResultSchema>;

export const PlanExecutionResultSchema = z.object({
  planId: z.string(),
  results: z.array(StepResultSchema),
  totalDurationMs: z.number(),
  completedAt: z.number(),
});
export type PlanExecutionResult = z.infer<typeof PlanExecutionResultSchema>;

// ── IPC Payload Schemas ───────────────────────────────────────────────

export const ExecuteToolPayloadSchema = z.object({
  toolId: z.string(),
  arguments: z.record(z.unknown()),
  dryRun: z.boolean().default(false),
});
export type ExecuteToolPayload = z.infer<typeof ExecuteToolPayloadSchema>;

export const PlanPreviewPayloadSchema = z.object({
  goal: z.string(),
  context: z.string().optional(),
});
export type PlanPreviewPayload = z.infer<typeof PlanPreviewPayloadSchema>;
