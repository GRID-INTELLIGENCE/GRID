import { IntelligencePage } from "@/pages/IntelligencePage";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("IntelligencePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders title and description from config", () => {
    renderWithProviders(<IntelligencePage />);
    expect(screen.getByText("Intelligence Pipeline")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Process inputs through the full GRID intelligence stack/
      )
    ).toBeInTheDocument();
  });

  it("renders all three capability toggles", () => {
    renderWithProviders(<IntelligencePage />);
    expect(screen.getByText("Pattern Recognition")).toBeInTheDocument();
    expect(screen.getByText("Reasoning")).toBeInTheDocument();
    expect(screen.getByText("Security Analysis")).toBeInTheDocument();
  });

  it("shows active capability count badge", () => {
    renderWithProviders(<IntelligencePage />);
    expect(screen.getByText("3 / 3 active")).toBeInTheDocument();
  });

  it("toggles capabilities on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    // Click Pattern Recognition to deactivate it
    const patternButton = screen
      .getByText("Pattern Recognition")
      .closest("button")!;
    await user.click(patternButton);

    // Should now show 2 / 3 active
    expect(screen.getByText("2 / 3 active")).toBeInTheDocument();

    // Click again to reactivate
    await user.click(patternButton);
    expect(screen.getByText("3 / 3 active")).toBeInTheDocument();
  });

  it("has include evidence checkbox checked by default", () => {
    renderWithProviders(<IntelligencePage />);
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("can uncheck include evidence", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  it("has a textarea for input", () => {
    renderWithProviders(<IntelligencePage />);
    const textarea = screen.getByPlaceholderText(
      "Enter data to process through the intelligence pipeline…"
    );
    expect(textarea).toBeInTheDocument();
  });

  it("process button is disabled when input is empty", () => {
    renderWithProviders(<IntelligencePage />);
    const processBtn = screen.getByRole("button", { name: /Process/ });
    expect(processBtn).toBeDisabled();
  });

  it("process button is enabled when input has text", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    const textarea = screen.getByPlaceholderText(
      "Enter data to process through the intelligence pipeline…"
    );
    await user.type(textarea, "Analyze this text");

    const processBtn = screen.getByRole("button", { name: /Process/ });
    expect(processBtn).toBeEnabled();
  });

  it("process button is disabled when all capabilities are deselected", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    // Type some input first
    const textarea = screen.getByPlaceholderText(
      "Enter data to process through the intelligence pipeline…"
    );
    await user.type(textarea, "test");

    // Deselect all capabilities
    const buttons = ["Pattern Recognition", "Reasoning", "Security Analysis"];
    for (const name of buttons) {
      const btn = screen.getByText(name).closest("button")!;
      await user.click(btn);
    }

    expect(screen.getByText("0 / 3 active")).toBeInTheDocument();
    const processBtn = screen.getByRole("button", { name: /Process/ });
    expect(processBtn).toBeDisabled();
  });

  it("calls grid API when form is submitted", async () => {
    const user = userEvent.setup();
    window.grid.api = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      data: {
        results: { analysis: "test complete" },
        timings: { processing: 150 },
        interaction_count: 1,
      },
    });

    renderWithProviders(<IntelligencePage />);

    const textarea = screen.getByPlaceholderText(
      "Enter data to process through the intelligence pipeline…"
    );
    await user.type(textarea, "Analyze network traffic");

    const processBtn = screen.getByRole("button", { name: /Process/ });
    await user.click(processBtn);

    await waitFor(() => {
      expect(window.grid.api).toHaveBeenCalledWith(
        "POST",
        "/api/v1/intelligence/process",
        expect.objectContaining({
          data: expect.objectContaining({
            input: "Analyze network traffic",
          }),
          include_evidence: true,
          reset_session: false,
        }),
        expect.any(Object)
      );
    });
  });

  it("shows Ctrl+Enter helper text", () => {
    renderWithProviders(<IntelligencePage />);
    expect(screen.getByText("Ctrl+Enter to submit")).toBeInTheDocument();
  });

  it("does not show clear history button when history is empty", () => {
    renderWithProviders(<IntelligencePage />);
    expect(screen.queryByText("Clear history")).not.toBeInTheDocument();
  });
});
