import { Sidebar } from "@/components/layout/Sidebar";
import { TitleBar } from "@/components/layout/TitleBar";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("TitleBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the GRID app identity", () => {
    renderWithProviders(<TitleBar />);
    expect(screen.getByText("GRID")).toBeInTheDocument();
  });

  it("renders window control buttons", () => {
    renderWithProviders(<TitleBar />);
    expect(
      screen.getByRole("button", { name: "Minimize" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Maximize" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("calls minimize when minimize button clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TitleBar />);

    await user.click(screen.getByRole("button", { name: "Minimize" }));
    expect(window.windowControls.minimize).toHaveBeenCalled();
  });

  it("calls maximize when maximize button clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TitleBar />);

    await user.click(screen.getByRole("button", { name: "Maximize" }));
    expect(window.windowControls.maximize).toHaveBeenCalled();
  });

  it("calls close when close button clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TitleBar />);

    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(window.windowControls.close).toHaveBeenCalled();
  });

  it("shows Restore label when maximized", async () => {
    window.windowControls.isMaximized = vi.fn().mockResolvedValue(true);
    // Simulate the onMaximizeChange callback firing with true
    window.windowControls.onMaximizeChange = vi
      .fn()
      .mockImplementation((cb: (maximized: boolean) => void) => {
        cb(true);
        return () => undefined;
      });

    renderWithProviders(<TitleBar />);
    expect(
      await screen.findByRole("button", { name: "Restore" })
    ).toBeInTheDocument();
  });

  it("subscribes to maximize changes and cleans up", () => {
    const cleanup = vi.fn();
    window.windowControls.onMaximizeChange = vi.fn().mockReturnValue(cleanup);

    const { unmount } = renderWithProviders(<TitleBar />);
    expect(window.windowControls.onMaximizeChange).toHaveBeenCalled();

    unmount();
    expect(cleanup).toHaveBeenCalled();
  });
});

describe("Sidebar", () => {
  it("renders primary navigation items", () => {
    renderWithProviders(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("AI Chat")).toBeInTheDocument();
    expect(screen.getByText("RAG Query")).toBeInTheDocument();
    expect(screen.getByText("Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Cognitive")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Observability")).toBeInTheDocument();
    expect(screen.getByText("Knowledge")).toBeInTheDocument();
    expect(screen.getByText("Terminal")).toBeInTheDocument();
  });

  it("renders secondary navigation items", () => {
    renderWithProviders(<Sidebar />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders navigation links with correct paths", () => {
    renderWithProviders(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveAttribute("href", "/");

    const chatLink = screen.getByText("AI Chat").closest("a");
    expect(chatLink).toHaveAttribute("href", "/chat");

    const settingsLink = screen.getByText("Settings").closest("a");
    expect(settingsLink).toHaveAttribute("href", "/settings");
  });
});
