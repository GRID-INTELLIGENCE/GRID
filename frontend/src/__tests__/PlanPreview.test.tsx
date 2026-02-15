import { PlanPreview } from "@/components/ui/PlanPreview";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";
import type { Plan, PlanExecutionResult } from "@/schema/tools";

// ── Fixtures ──────────────────────────────────────────────────────────

function makePlan(overrides: Partial<Plan> = {}): Plan {
  return {
    id: "plan-1",
    goal: "Investigate example.com",
    steps: [
      {
        order: 0,
        call: {
          toolId: "dns-lookup",
          arguments: { host: "example.com", recordType: "A" },
          description: "DNS lookup",
        },
        dryRun: false,
      },
      {
        order: 1,
        call: {
          toolId: "whois",
          arguments: { host: "example.com" },
          description: "WHOIS lookup",
        },
        dryRun: false,
      },
    ],
    createdAt: Date.now(),
    ...overrides,
  };
}

const completedResult: PlanExecutionResult = {
  planId: "plan-1",
  results: [
    {
      status: "success",
      stepOrder: 0,
      data: { ip: "93.184.216.34" },
      durationMs: 120,
    },
    {
      status: "error",
      stepOrder: 1,
      error: "Connection timed out",
      durationMs: 3000,
    },
  ],
  totalDurationMs: 3120,
  completedAt: Date.now(),
};

const allSuccessResult: PlanExecutionResult = {
  planId: "plan-1",
  results: [
    {
      status: "success",
      stepOrder: 0,
      data: { ip: "93.184.216.34" },
      durationMs: 120,
    },
    {
      status: "skipped",
      stepOrder: 1,
      reason: "Dry run",
    },
  ],
  totalDurationMs: 120,
  completedAt: Date.now(),
};

// ── Tests ─────────────────────────────────────────────────────────────

describe("PlanPreview", () => {
  it("renders the plan goal", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(screen.getByText("Investigate example.com")).toBeInTheDocument();
  });

  it("renders all steps with tool IDs", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(screen.getByText("dns-lookup")).toBeInTheDocument();
    expect(screen.getByText("whois")).toBeInTheDocument();
  });

  it("shows step count", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(screen.getByText(/2 steps/)).toBeInTheDocument();
  });

  it("shows singular step count for single step", () => {
    const plan = makePlan({
      steps: [
        {
          order: 0,
          call: {
            toolId: "ping",
            arguments: { host: "8.8.8.8" },
            description: "Ping",
          },
          dryRun: false,
        },
      ],
    });
    renderWithProviders(<PlanPreview plan={plan} />);
    expect(screen.getByText(/1 step(?!s)/)).toBeInTheDocument();
  });

  it("shows estimated duration when provided", () => {
    const plan = makePlan({ estimatedDurationMs: 5000 });
    renderWithProviders(<PlanPreview plan={plan} />);
    expect(screen.getByText(/~5s estimated/)).toBeInTheDocument();
  });

  it("does not show estimated duration when absent", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(screen.queryByText(/estimated/)).not.toBeInTheDocument();
  });

  it("renders step descriptions as badges", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(screen.getByText("DNS lookup")).toBeInTheDocument();
    expect(screen.getByText("WHOIS lookup")).toBeInTheDocument();
  });

  it("renders step arguments as JSON", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    // Both steps contain "host": "example.com", so use getAllByText
    const matches = screen.getAllByText(/"host": "example.com"/);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  // ── Actions ───────────────────────────────────────────────────────

  it("renders execute button when onExecute is provided", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} onExecute={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /execute/i })
    ).toBeInTheDocument();
  });

  it("renders cancel button when onCancel is provided", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} onCancel={vi.fn()} />);
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("does not render execute button when onExecute is absent", () => {
    renderWithProviders(<PlanPreview plan={makePlan()} />);
    expect(
      screen.queryByRole("button", { name: /execute/i })
    ).not.toBeInTheDocument();
  });

  it("calls onExecute when execute button is clicked", async () => {
    const user = userEvent.setup();
    const onExecute = vi.fn();
    renderWithProviders(
      <PlanPreview plan={makePlan()} onExecute={onExecute} />
    );
    await user.click(screen.getByRole("button", { name: /execute/i }));
    expect(onExecute).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    renderWithProviders(<PlanPreview plan={makePlan()} onCancel={onCancel} />);
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  // ── Dry-run toggle ────────────────────────────────────────────────

  it("shows dry-run checkbox", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} onDryRunChange={vi.fn()} />
    );
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
    expect(screen.getByText("Dry run")).toBeInTheDocument();
  });

  it("dry-run checkbox reflects dryRun prop", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} dryRun={true} onDryRunChange={vi.fn()} />
    );
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it("calls onDryRunChange when checkbox is toggled", async () => {
    const user = userEvent.setup();
    const onDryRunChange = vi.fn();
    renderWithProviders(
      <PlanPreview
        plan={makePlan()}
        dryRun={false}
        onDryRunChange={onDryRunChange}
      />
    );
    await user.click(screen.getByRole("checkbox"));
    expect(onDryRunChange).toHaveBeenCalledWith(true);
  });

  it('shows "Preview" label when dryRun is true', () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} dryRun={true} onExecute={vi.fn()} />
    );
    expect(
      screen.getByRole("button", { name: /preview/i })
    ).toBeInTheDocument();
  });

  it('shows "Execute" label when dryRun is false', () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} dryRun={false} onExecute={vi.fn()} />
    );
    expect(
      screen.getByRole("button", { name: /execute/i })
    ).toBeInTheDocument();
  });

  // ── Executing state ───────────────────────────────────────────────

  it("disables execute button while executing", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} isExecuting={true} onExecute={vi.fn()} />
    );
    // When isExecuting, the button text changes to include the spinner
    // but it should still be findable and disabled
    const buttons = screen.getAllByRole("button");
    const executeBtn = buttons.find(
      (b) =>
        b.textContent?.includes("Execute") || b.textContent?.includes("Preview")
    );
    expect(executeBtn).toBeDisabled();
  });

  it("disables cancel button while executing", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} isExecuting={true} onCancel={vi.fn()} />
    );
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
  });

  it("disables dry-run checkbox while executing", () => {
    renderWithProviders(
      <PlanPreview
        plan={makePlan()}
        isExecuting={true}
        onDryRunChange={vi.fn()}
      />
    );
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });

  // ── Execution results ─────────────────────────────────────────────

  it("disables execute button after execution completes", () => {
    renderWithProviders(
      <PlanPreview
        plan={makePlan()}
        executionResult={completedResult}
        onExecute={vi.fn()}
      />
    );
    const buttons = screen.getAllByRole("button");
    const executeBtn = buttons.find(
      (b) =>
        b.textContent?.includes("Execute") || b.textContent?.includes("Preview")
    );
    expect(executeBtn).toBeDisabled();
  });

  it("shows completion summary with timing", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={completedResult} />
    );
    expect(screen.getByText(/3120ms/)).toBeInTheDocument();
  });

  it("shows succeeded count in summary", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={completedResult} />
    );
    expect(screen.getByText(/1 succeeded/)).toBeInTheDocument();
  });

  it("shows failed count in summary", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={completedResult} />
    );
    expect(screen.getByText(/1 failed/)).toBeInTheDocument();
  });

  it("shows skipped count in summary", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={allSuccessResult} />
    );
    expect(screen.getByText(/1 skipped/)).toBeInTheDocument();
  });

  it("displays error message for failed steps", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={completedResult} />
    );
    expect(screen.getByText("Connection timed out")).toBeInTheDocument();
  });

  it("displays skipped reason for skipped steps", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={allSuccessResult} />
    );
    // "Dry run" appears both as the skip reason and the checkbox label
    const matches = screen.getAllByText("Dry run");
    expect(matches.length).toBe(2);
    // The skip reason is rendered inside a <p> tag
    const skipReason = matches.find((el) => el.tagName === "P");
    expect(skipReason).toBeInTheDocument();
  });

  it("displays success result duration", () => {
    renderWithProviders(
      <PlanPreview plan={makePlan()} executionResult={completedResult} />
    );
    expect(screen.getByText(/Result \(120ms\)/)).toBeInTheDocument();
  });

  // ── className ─────────────────────────────────────────────────────

  it("accepts custom className", () => {
    const { container } = renderWithProviders(
      <PlanPreview plan={makePlan()} className="my-custom-class" />
    );
    // The Card is the outermost element
    const card = container.firstElementChild;
    expect(card?.className).toContain("my-custom-class");
  });
});
