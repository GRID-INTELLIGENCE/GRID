import { Dashboard } from "@/pages/Dashboard";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders title and description", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText("GRID Intelligence Platform Overview")
    ).toBeInTheDocument();
  });

  it("shows Connecting badge when health is loading", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("Connecting…")).toBeInTheDocument();
  });

  it("shows System Online when health reports ok", async () => {
    window.grid.api = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      data: { status: "ok", version: "0.1.0", uptime: 1234 },
    });

    renderWithProviders(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("System Online")).toBeInTheDocument();
    });
  });

  it("shows Connecting when health fails", async () => {
    window.grid.api = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      data: null,
    });

    renderWithProviders(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("Connecting…")).toBeInTheDocument();
    });
  });

  it("renders all stat cards from config", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Cognitive")).toBeInTheDocument();
    expect(screen.getByText("Knowledge Base")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
  });

  it("shows static stat values from config", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Indexed")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("shows Operational for status stat when health is ok", async () => {
    window.grid.api = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      data: { status: "ok" },
    });

    renderWithProviders(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("Operational")).toBeInTheDocument();
    });
  });

  it("shows Offline for status stat when health fails", async () => {
    window.grid.api = vi.fn().mockResolvedValue({
      ok: false,
      status: 0,
      data: null,
    });

    renderWithProviders(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText("Offline")).toBeInTheDocument();
    });
  });

  it("renders quick action cards from config", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("AI Chat")).toBeInTheDocument();
    expect(screen.getByText("Quick RAG Query")).toBeInTheDocument();
    expect(screen.getByText("Intelligence Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Cognitive Patterns")).toBeInTheDocument();
    expect(screen.getByText("Security Overview")).toBeInTheDocument();
  });

  it("renders quick action descriptions", () => {
    renderWithProviders(<Dashboard />);
    expect(
      screen.getByText(/Start a conversation with your local LLM/)
    ).toBeInTheDocument();
  });
});
