import { Observability } from "@/pages/Observability";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("Observability", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/health") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              status: "healthy",
              components: [
                { name: "database", status: "healthy" },
                { name: "cache", status: "healthy" },
              ],
              alerts: [],
            },
          });
        }
        if (endpoint === "/metrics") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              uptime: 7200,
              sessions: 5,
              operations: 142,
              components: 8,
              alerts: 0,
            },
          });
        }
        if (endpoint === "/health/ready") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              ready: true,
              checks: { cockpit: true, database: true, redis: false },
            },
          });
        }
        if (endpoint === "/version") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              name: "GRID Mothership",
              version: "0.1.0",
              environment: "development",
              python_version: "3.13.11",
            },
          });
        }
        if (endpoint === "/health/chaos-resilience") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              resilience_score: 85,
              recommendations: ["Enable circuit breakers"],
            },
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });
  });

  it("renders title and description", () => {
    renderWithProviders(<Observability />);
    expect(screen.getByText("Observability")).toBeInTheDocument();
    expect(
      screen.getByText(/System health, metrics, resilience scoring/)
    ).toBeInTheDocument();
  });

  it("shows status badge from health endpoint", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      const matches = screen.getAllByText("healthy");
      expect(matches.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows uptime from metrics", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      expect(screen.getByText("2h 0m")).toBeInTheDocument();
    });
  });

  it("shows operations count from metrics", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      expect(screen.getByText("142")).toBeInTheDocument();
    });
  });

  it("shows resilience score badge", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
  });

  it("renders readiness probes section", () => {
    renderWithProviders(<Observability />);
    expect(screen.getByText("Readiness Probes")).toBeInTheDocument();
  });

  it("renders system info section", () => {
    renderWithProviders(<Observability />);
    expect(screen.getByText("System Info")).toBeInTheDocument();
  });

  it("shows version info from API", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      expect(screen.getByText("GRID Mothership")).toBeInTheDocument();
      expect(screen.getByText("0.1.0")).toBeInTheDocument();
      expect(screen.getByText("development")).toBeInTheDocument();
      expect(screen.getByText("3.13.11")).toBeInTheDocument();
    });
  });

  it("shows component list from health data", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      const dbMatches = screen.getAllByText("database");
      expect(dbMatches.length).toBeGreaterThanOrEqual(1);
      const cacheMatches = screen.getAllByText("cache");
      expect(cacheMatches.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows resilience recommendations", async () => {
    renderWithProviders(<Observability />);
    await waitFor(() => {
      expect(screen.getByText("Enable circuit breakers")).toBeInTheDocument();
    });
  });

  it("has a refresh button", () => {
    renderWithProviders(<Observability />);
    const refreshBtn = screen.getByRole("button", { name: /Refresh/ });
    expect(refreshBtn).toBeInTheDocument();
  });
});
