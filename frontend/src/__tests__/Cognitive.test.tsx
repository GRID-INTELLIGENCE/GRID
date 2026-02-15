import { Cognitive } from "@/pages/Cognitive";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("Cognitive", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: cockpit running, resonance has data, skills healthy
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/api/v1/cockpit/state") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { status: "running", mode: "normal", uptime: 3600 },
          });
        }
        if (endpoint === "/api/v1/resonance/context") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { active_activities: 3 },
          });
        }
        if (endpoint === "/api/v1/skills/health") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { total_skills: 40, healthy: 38 },
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });
  });

  it("renders title and description", () => {
    renderWithProviders(<Cognitive />);
    expect(screen.getByText("Cognitive Patterns")).toBeInTheDocument();
    expect(
      screen.getByText(/Monitor event-driven cognitive processing/)
    ).toBeInTheDocument();
  });

  it("renders cockpit, resonance, and skills cards", () => {
    renderWithProviders(<Cognitive />);
    expect(screen.getByText("Cockpit")).toBeInTheDocument();
    expect(screen.getByText("Resonance")).toBeInTheDocument();
    expect(screen.getByText("Skills")).toBeInTheDocument();
  });

  it("shows cockpit status from API", async () => {
    renderWithProviders(<Cognitive />);
    await waitFor(() => {
      expect(screen.getByText("running")).toBeInTheDocument();
    });
  });

  it("shows resonance active activities", async () => {
    renderWithProviders(<Cognitive />);
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
    });
  });

  it("renders navigation planner section", () => {
    renderWithProviders(<Cognitive />);
    expect(screen.getByText("Navigation Planner")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Describe your goal…")
    ).toBeInTheDocument();
  });

  it("plan button is disabled when goal is empty", () => {
    renderWithProviders(<Cognitive />);
    const planBtn = screen.getByRole("button", { name: /Plan/ });
    expect(planBtn).toBeDisabled();
  });

  it("plan button is enabled when goal has text", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Cognitive />);

    const input = screen.getByPlaceholderText("Describe your goal…");
    await user.type(input, "Optimize security pipeline");

    const planBtn = screen.getByRole("button", { name: /Plan/ });
    expect(planBtn).toBeEnabled();
  });

  it("calls navigation plan API when plan button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Cognitive />);

    const input = screen.getByPlaceholderText("Describe your goal…");
    await user.type(input, "Build a RAG pipeline");

    const planBtn = screen.getByRole("button", { name: /Plan/ });
    await user.click(planBtn);

    await waitFor(() => {
      expect(window.grid.api).toHaveBeenCalledWith(
        "POST",
        "/api/v1/navigation/plan",
        expect.objectContaining({
          goal: "Build a RAG pipeline",
          max_alternatives: 3,
          enable_learning: true,
        }),
        expect.any(Object)
      );
    });
  });

  it("has a refresh button", () => {
    renderWithProviders(<Cognitive />);
    const refreshBtn = screen.getByRole("button", { name: /Refresh/ });
    expect(refreshBtn).toBeInTheDocument();
  });

  it("shows fallback when cockpit is offline", async () => {
    window.grid.api = vi.fn().mockResolvedValue({
      ok: false,
      status: 0,
      data: null,
      error: "Connection refused",
    });

    renderWithProviders(<Cognitive />);
    await waitFor(() => {
      expect(screen.getByText("Unable to reach cockpit")).toBeInTheDocument();
    });
  });
});
