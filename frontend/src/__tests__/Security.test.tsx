import { Security } from "@/pages/Security";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("Security", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/security/status") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              authentication_level: "strict",
              cors_policy: "restrictive",
              rate_limiting: "enabled",
              security_headers: true,
            },
          });
        }
        if (endpoint === "/health/security") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              overall_status: "compliant",
              compliance_score: 87,
              checks: [
                { name: "Authentication", status: "pass" },
                { name: "Rate Limiting", status: "pass" },
                { name: "TLS", status: "warn", details: "Self-signed cert" },
              ],
            },
          });
        }
        if (endpoint === "/corruption/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              monitored_endpoints: 15,
              total_penalties: 0,
              system_status: "clean",
            },
          });
        }
        if (endpoint === "/drt/system-overview") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { status: { active: true }, top_endpoints: [] },
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });
  });

  it("renders title and description", () => {
    renderWithProviders(<Security />);
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(
      screen.getByText(/Security posture, compliance checks/)
    ).toBeInTheDocument();
  });

  it("shows security posture data from API", async () => {
    renderWithProviders(<Security />);
    await waitFor(() => {
      expect(screen.getByText("strict")).toBeInTheDocument();
      expect(screen.getByText("restrictive")).toBeInTheDocument();
      expect(screen.getByText("enabled")).toBeInTheDocument();
    });
  });

  it("shows compliance score badge", async () => {
    renderWithProviders(<Security />);
    await waitFor(() => {
      expect(screen.getByText("87%")).toBeInTheDocument();
    });
  });

  it("renders compliance check items", async () => {
    renderWithProviders(<Security />);
    await waitFor(() => {
      expect(screen.getByText("Authentication")).toBeInTheDocument();
      expect(screen.getByText("Rate Limiting")).toBeInTheDocument();
      expect(screen.getByText("TLS")).toBeInTheDocument();
    });
  });

  it("shows corruption monitor section", async () => {
    renderWithProviders(<Security />);
    expect(screen.getByText("Corruption Monitor")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("clean")).toBeInTheDocument();
    });
  });

  it("shows DRT analysis section", () => {
    renderWithProviders(<Security />);
    expect(screen.getByText("DRT Analysis")).toBeInTheDocument();
  });

  it("has a refresh button", () => {
    renderWithProviders(<Security />);
    const refreshBtn = screen.getByRole("button", { name: /Refresh/ });
    expect(refreshBtn).toBeInTheDocument();
  });

  it("shows offline message when all endpoints fail", async () => {
    window.grid.api = vi
      .fn()
      .mockResolvedValue({ ok: false, status: 0, data: null });

    renderWithProviders(<Security />);
    await waitFor(() => {
      expect(
        screen.getByText(/Unable to reach GRID backend security endpoints/)
      ).toBeInTheDocument();
    });
  });
});
