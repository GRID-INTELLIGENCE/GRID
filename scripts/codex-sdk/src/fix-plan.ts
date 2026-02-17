/**
 * Fix-plan generator: maps CI failure indicators to structured
 * remediation steps with concrete repo commands.
 *
 * This module is pure logic â€” no Codex SDK dependency â€” so it can
 * run independently of the thread-based diagnostics flow.
 */

import type { CiParseResult } from "./types.js";

// ---------------------------------------------------------------------------
// Remediation catalogue
// ---------------------------------------------------------------------------

export type RemediationStep = {
  /** Short human label */
  title: string;
  /** Shell command to run from repo root */
  command: string;
  /** Why this step helps */
  rationale: string;
  /** CI indicator names that trigger this step */
  triggers: string[];
  /** Execution order weight (lower = earlier) */
  priority: number;
};

export type FixPlan = {
  correlationId: string;
  timestamp: string;
  ciSummary: string;
  steps: RemediationStep[];
  unmappedIndicators: string[];
};

/**
 * Master catalogue of remediation steps keyed by CI indicator name.
 * Each indicator can map to multiple steps. Steps are deduplicated
 * when the plan is assembled.
 */
const CATALOGUE: Record<string, Omit<RemediationStep, "triggers">[]> = {
  pytest_failures: [
    {
      title: "Re-run failing pytest suite",
      command: "cd E:\\grid && uv run pytest tests/ -v --tb=short",
      rationale: "Reproduce the failure locally to confirm the issue.",
      priority: 10,
    },
    {
      title: "Run pytest on last-changed files",
      command: "cd E:\\grid && uv run pytest tests/ -v --last-failed",
      rationale: "Narrow down to only the tests that previously failed.",
      priority: 15,
    },
  ],
  traceback: [
    {
      title: "Re-run pytest with full tracebacks",
      command: "cd E:\\grid && uv run pytest tests/ -v --tb=long",
      rationale: "Full traceback output aids root-cause analysis.",
      priority: 12,
    },
  ],
  exception: [
    {
      title: "Type-check codebase",
      command: "cd E:\\grid && uv run mypy src/",
      rationale:
        "Static analysis catches type errors that cause runtime exceptions.",
      priority: 20,
    },
  ],
  gha_error: [
    {
      title: "Lint codebase",
      command: "cd E:\\grid && uv run ruff check .",
      rationale:
        "GitHub Actions error annotations often originate from lint violations.",
      priority: 5,
    },
    {
      title: "Auto-fix lint issues",
      command:
        "cd E:\\grid && uv run ruff format . && uv run ruff check . --fix",
      rationale:
        "Auto-fixable lint and formatting issues are the cheapest to resolve.",
      priority: 6,
    },
  ],
  npm_error: [
    {
      title: "Reinstall Node dependencies",
      command: "cd E:\\grid\\frontend && npm ci",
      rationale: "npm ERR usually indicates dependency resolution issues.",
      priority: 8,
    },
    {
      title: "Build frontend",
      command: "cd E:\\grid\\frontend && npm run build",
      rationale: "Confirm the frontend compiles after dependency fix.",
      priority: 9,
    },
  ],
  test_failure: [
    {
      title: "Run full test suite",
      command: "cd E:\\grid && uv run pytest tests/ -v",
      rationale:
        "Generic test failure â€” re-run everything to locate the break.",
      priority: 10,
    },
  ],
  exit_code: [
    {
      title: "Check process exit codes",
      command: "cd E:\\grid && uv run pytest tests/ -v --tb=short",
      rationale: "Non-zero exit codes often come from test or build failures.",
      priority: 11,
    },
  ],
};

// Fallback if no indicators match anything in the catalogue
const FALLBACK_STEPS: Omit<RemediationStep, "triggers">[] = [
  {
    title: "Run lint + format checks",
    command:
      "cd E:\\grid && uv run ruff format --check . && uv run ruff check .",
    rationale: "Baseline code-quality gate.",
    priority: 1,
  },
  {
    title: "Run full test suite",
    command: "cd E:\\grid && uv run pytest tests/ -v",
    rationale: "Baseline test execution.",
    priority: 2,
  },
  {
    title: "Type-check codebase",
    command: "cd E:\\grid && uv run mypy src/",
    rationale: "Baseline static analysis.",
    priority: 3,
  },
];

// ---------------------------------------------------------------------------
// Plan assembly
// ---------------------------------------------------------------------------

/**
 * Build a fix plan from parsed CI results.
 * Steps are deduplicated by command and sorted by priority.
 */
export const buildFixPlan = (
  ci: CiParseResult,
  correlationId: string,
): FixPlan => {
  const seen = new Set<string>();
  const steps: RemediationStep[] = [];
  const unmapped: string[] = [];

  for (const [indicator] of Object.entries(ci.indicators)) {
    const entries = CATALOGUE[indicator];
    if (!entries) {
      unmapped.push(indicator);
      continue;
    }

    for (const entry of entries) {
      if (seen.has(entry.command)) {
        continue;
      }
      seen.add(entry.command);
      steps.push({ ...entry, triggers: [indicator] });
    }
  }

  // Merge triggers for duplicate commands that were already added by
  // a different indicator path (belt-and-suspenders dedup).
  const merged = new Map<string, RemediationStep>();
  for (const step of steps) {
    const existing = merged.get(step.command);
    if (existing) {
      existing.triggers = [
        ...new Set([...existing.triggers, ...step.triggers]),
      ];
    } else {
      merged.set(step.command, step);
    }
  }

  let plan = [...merged.values()];

  // If nothing matched, use fallback steps
  if (plan.length === 0) {
    plan = FALLBACK_STEPS.map((s) => ({ ...s, triggers: ["fallback"] }));
  }

  plan.sort((a, b) => a.priority - b.priority);

  return {
    correlationId,
    timestamp: new Date().toISOString(),
    ciSummary: ci.summary,
    steps: plan,
    unmappedIndicators: unmapped,
  };
};

// ---------------------------------------------------------------------------
// Human-readable formatter
// ---------------------------------------------------------------------------

export const formatFixPlan = (plan: FixPlan): string => {
  const lines: string[] = [
    "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•",
    "  AUTO-FIX PLAN",
    `  Correlation: ${plan.correlationId}`,
    `  Generated:   ${plan.timestamp}`,
    "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•",
    "",
    `CI Summary: ${plan.ciSummary}`,
    "",
  ];

  plan.steps.forEach((step, i) => {
    lines.push(`Step ${i + 1}: ${step.title}`);
    lines.push(`  Triggers:  ${step.triggers.join(", ")}`);
    lines.push(`  Rationale: ${step.rationale}`);
    lines.push(`  Command:   ${step.command}`);
    lines.push("");
  });

  if (plan.unmappedIndicators.length > 0) {
    lines.push(`Unmapped indicators: ${plan.unmappedIndicators.join(", ")}`);
    lines.push(
      "  â†’ These require manual investigation or Codex thread analysis.",
    );
    lines.push("");
  }

  return lines.join("\n");
};

/**
 * Build the Codex prompt that asks for a structured fix plan
 * based on CI failure data. Used when --mode fix-plan is set.
 */
export const buildFixPlanPrompt = (
  ci: CiParseResult,
  plan: FixPlan,
): string => {
  const parts = [
    "You are a CI/CD diagnostics expert for a Python/FastAPI monorepo.",
    "Below is the parsed CI failure summary and a preliminary auto-generated fix plan.",
    "Review the plan, refine ordering, add any missing steps, and produce a final",
    "structured remediation plan in JSON format with fields: steps[]{title, command, rationale, priority}.",
    "",
    "CI Failure Summary:",
    plan.ciSummary,
    "",
    "Detected signals:",
    ...ci.signals.slice(0, 15).map((s) => `- ${s}`),
    "",
    "Preliminary fix plan:",
    ...plan.steps.map(
      (s, i) => `${i + 1}. [${s.triggers.join(",")}] ${s.title}: ${s.command}`,
    ),
    "",
    plan.unmappedIndicators.length > 0
      ? `Unmapped indicators needing investigation: ${plan.unmappedIndicators.join(", ")}`
      : "",
    "",
    "Produce the final remediation plan.",
  ];

  return parts.filter(Boolean).join("\n");
};
