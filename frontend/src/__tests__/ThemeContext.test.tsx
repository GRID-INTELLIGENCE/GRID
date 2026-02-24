import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { ThemeProvider, useTheme } from "@/context/ThemeContext";

function ThemeDisplay() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <button onClick={() => setTheme("light")}>Light</button>
      <button onClick={() => setTheme("dark")}>Dark</button>
      <button onClick={() => setTheme("mycelium")}>Mycelium</button>
    </div>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("defaults to dark theme", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
  });

  it("applies theme class to document element", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("switches to light theme on click", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );

    await user.click(screen.getByText("Light"));
    expect(screen.getByTestId("current-theme")).toHaveTextContent("light");
    expect(document.documentElement.classList.contains("light")).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("switches to mycelium theme on click", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );

    await user.click(screen.getByText("Mycelium"));
    expect(screen.getByTestId("current-theme")).toHaveTextContent("mycelium");
    expect(document.documentElement.classList.contains("mycelium")).toBe(true);
  });

  it("persists theme choice to localStorage", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );

    await user.click(screen.getByText("Mycelium"));
    expect(localStorage.getItem("grid-theme")).toBe("mycelium");
  });

  it("restores theme from localStorage on mount", () => {
    localStorage.setItem("grid-theme", "light");
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("light");
  });

  it("ignores invalid stored theme values", () => {
    localStorage.setItem("grid-theme", "invalid-theme");
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
  });

  it("throws when useTheme is used outside provider", () => {
    // Suppress console.error for expected error
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<ThemeDisplay />)).toThrow(
      "useTheme must be used within a ThemeProvider"
    );
    spy.mockRestore();
  });
});
