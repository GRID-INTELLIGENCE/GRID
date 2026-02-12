import { OfflineBanner } from "@/components/ui/OfflineBanner";
import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderWithProviders } from "./test-utils";

/**
 * Helper to simulate online/offline status changes.
 *
 * jsdom doesn't implement `navigator.onLine` as writable by default,
 * so we use Object.defineProperty + manual event dispatch.
 */
function setOnlineStatus(online: boolean) {
  Object.defineProperty(navigator, "onLine", {
    value: online,
    writable: true,
    configurable: true,
  });
  window.dispatchEvent(new Event(online ? "online" : "offline"));
}

describe("OfflineBanner", () => {
  beforeEach(() => {
    // Default: browser is online
    Object.defineProperty(navigator, "onLine", {
      value: true,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    // Restore online
    Object.defineProperty(navigator, "onLine", {
      value: true,
      writable: true,
      configurable: true,
    });
  });

  it("does not render when online", () => {
    renderWithProviders(<OfflineBanner />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders when offline", () => {
    Object.defineProperty(navigator, "onLine", {
      value: false,
      writable: true,
      configurable: true,
    });
    renderWithProviders(<OfflineBanner />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/You are offline/)).toBeInTheDocument();
  });

  it("shows banner when going offline", () => {
    renderWithProviders(<OfflineBanner />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    act(() => {
      setOnlineStatus(false);
    });

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("hides banner when going back online", () => {
    Object.defineProperty(navigator, "onLine", {
      value: false,
      writable: true,
      configurable: true,
    });
    renderWithProviders(<OfflineBanner />);
    expect(screen.getByRole("alert")).toBeInTheDocument();

    act(() => {
      setOnlineStatus(true);
    });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("can be dismissed with the close button", async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, "onLine", {
      value: false,
      writable: true,
      configurable: true,
    });
    renderWithProviders(<OfflineBanner />);
    expect(screen.getByRole("alert")).toBeInTheDocument();

    const dismissBtn = screen.getByRole("button", {
      name: /dismiss offline banner/i,
    });
    await user.click(dismissBtn);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("re-appears after dismiss when status changes again", async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, "onLine", {
      value: false,
      writable: true,
      configurable: true,
    });
    renderWithProviders(<OfflineBanner />);

    // Dismiss it
    const dismissBtn = screen.getByRole("button", {
      name: /dismiss offline banner/i,
    });
    await user.click(dismissBtn);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    // Go online then offline again
    act(() => {
      setOnlineStatus(true);
    });
    act(() => {
      setOnlineStatus(false);
    });

    // Banner should re-appear
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("accepts custom className", () => {
    Object.defineProperty(navigator, "onLine", {
      value: false,
      writable: true,
      configurable: true,
    });
    renderWithProviders(<OfflineBanner className="my-custom-class" />);
    const banner = screen.getByRole("alert");
    expect(banner.className).toContain("my-custom-class");
  });
});
