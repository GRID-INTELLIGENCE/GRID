/**
 * PlanPreview — displays an LLM-generated execution plan with
 * step-by-step status, dry-run toggle, and execute/cancel actions.
 */

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Plan, PlanExecutionResult, StepResult } from "@/schema/tools";
import type { ExecutionProgress } from "@/lib/tool-executor";
import {
  CheckCircle2,
  Circle,
  CircleDot,
  Loader2,
  Play,
  Shield,
  SkipForward,
  X,
  XCircle,
} from "lucide-react";

// ── Step status icon ──────────────────────────────────────────────────

function StepIcon({ result }: { result?: StepResult }) {
  if (!result) {
    return <Circle className="h-4 w-4 text-[var(--muted-foreground)]" />;
  }
  switch (result.status) {
    case "success":
      return <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />;
    case "skipped":
      return <SkipForward className="h-4 w-4 text-[var(--muted-foreground)]" />;
    case "error":
      return <XCircle className="h-4 w-4 text-[var(--destructive)]" />;
  }
}

// ── Category badge variant ────────────────────────────────────────────

const categoryVariants: Record<
  string,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  recon: "default",
  network: "secondary",
  security: "warning",
  info: "success",
};

// ── Props ─────────────────────────────────────────────────────────────

interface PlanPreviewProps {
  plan: Plan;
  /** Execution result (if the plan has been run). */
  executionResult?: PlanExecutionResult;
  /** Live progress during execution. */
  progress?: ExecutionProgress;
  /** Whether execution is in progress. */
  isExecuting?: boolean;
  /** Dry-run mode toggle state. */
  dryRun?: boolean;
  /** Called when the user toggles dry-run mode. */
  onDryRunChange?: (dryRun: boolean) => void;
  /** Called when the user clicks "Execute". */
  onExecute?: () => void;
  /** Called when the user clicks "Cancel". */
  onCancel?: () => void;
  className?: string;
}

export function PlanPreview({
  plan,
  executionResult,
  progress,
  isExecuting = false,
  dryRun = false,
  onDryRunChange,
  onExecute,
  onCancel,
  className,
}: PlanPreviewProps) {
  const sorted = [...plan.steps].sort((a, b) => a.order - b.order);
  const resultMap = new Map(
    executionResult?.results.map((r) => [r.stepOrder, r])
  );

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{plan.goal}</CardTitle>
            <CardDescription>
              {sorted.length} step{sorted.length !== 1 ? "s" : ""}
              {plan.estimatedDurationMs
                ? ` \u00B7 ~${Math.ceil(plan.estimatedDurationMs / 1000)}s estimated`
                : ""}
            </CardDescription>
          </div>
          {isExecuting && (
            <Loader2 className="h-5 w-5 animate-spin text-[var(--primary)]" />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Step list */}
        <ol className="space-y-3">
          {sorted.map((step, idx) => {
            const result = resultMap.get(step.order);
            const isActive =
              isExecuting && progress?.currentStep === idx && !result;

            return (
              <li
                key={step.order}
                className={cn(
                  "flex items-start gap-3 rounded-lg border p-3 text-sm",
                  "border-[var(--border)] bg-[var(--card)]",
                  isActive &&
                    "border-[var(--primary)]/50 bg-[var(--primary)]/5",
                  result?.status === "error" &&
                    "border-[var(--destructive)]/30 bg-[var(--destructive)]/5"
                )}
              >
                <div className="mt-0.5 shrink-0">
                  {isActive ? (
                    <Loader2 className="h-4 w-4 animate-spin text-[var(--primary)]" />
                  ) : (
                    <StepIcon result={result} />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{step.call.toolId}</span>
                    <Badge
                      variant={
                        categoryVariants[step.call.toolId] ?? "secondary"
                      }
                      className="text-[10px]"
                    >
                      {step.call.description}
                    </Badge>
                  </div>

                  <pre className="mt-1 overflow-x-auto text-xs text-[var(--muted-foreground)]">
                    {JSON.stringify(step.call.arguments, null, 2)}
                  </pre>

                  {result?.status === "error" && (
                    <p className="mt-1 text-xs text-[var(--destructive)]">
                      {result.error}
                    </p>
                  )}
                  {result?.status === "skipped" && (
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                      {result.reason}
                    </p>
                  )}
                  {result?.status === "success" && (
                    <details className="mt-1">
                      <summary className="cursor-pointer text-xs text-[var(--muted-foreground)]">
                        Result ({result.durationMs}ms)
                      </summary>
                      <pre className="mt-1 max-h-40 overflow-auto text-xs text-[var(--muted-foreground)]">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </li>
            );
          })}
        </ol>

        {/* Execution summary */}
        {executionResult && (
          <div className="flex items-center gap-2 rounded-lg bg-[var(--muted)]/50 px-3 py-2 text-xs text-[var(--muted-foreground)]">
            <CircleDot className="h-3.5 w-3.5" />
            Completed in {executionResult.totalDurationMs}ms
            {" \u2014 "}
            {
              executionResult.results.filter((r) => r.status === "success")
                .length
            }{" "}
            succeeded,{" "}
            {executionResult.results.filter((r) => r.status === "error").length}{" "}
            failed,{" "}
            {
              executionResult.results.filter((r) => r.status === "skipped")
                .length
            }{" "}
            skipped
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between border-t border-[var(--border)] pt-3">
          <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => onDryRunChange?.(e.target.checked)}
              disabled={isExecuting}
              className="accent-[var(--primary)]"
            />
            <Shield className="h-3.5 w-3.5" />
            Dry run
          </label>

          <div className="flex gap-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                disabled={isExecuting}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm",
                  "border border-[var(--border)] text-[var(--muted-foreground)]",
                  "hover:bg-[var(--muted)] disabled:opacity-50",
                  "transition-colors"
                )}
              >
                <X className="h-3.5 w-3.5" />
                Cancel
              </button>
            )}
            {onExecute && (
              <button
                type="button"
                onClick={onExecute}
                disabled={isExecuting || !!executionResult}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium",
                  "bg-[var(--primary)] text-[var(--primary-foreground)]",
                  "hover:bg-[var(--primary)]/90 disabled:opacity-50",
                  "transition-colors"
                )}
              >
                {isExecuting ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5" />
                )}
                {dryRun ? "Preview" : "Execute"}
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
