import { TerminalPage } from "@/pages/TerminalPage";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("TerminalPage", () => {
  it("renders title and description", () => {
    renderWithProviders(<TerminalPage />);
    expect(screen.getByText("Terminal")).toBeInTheDocument();
    expect(
      screen.getByText("Interactive terminal for GRID CLI commands")
    ).toBeInTheDocument();
  });

  it("renders GRID Shell card", () => {
    renderWithProviders(<TerminalPage />);
    expect(screen.getByText("GRID Shell")).toBeInTheDocument();
  });

  it("shows command prompt placeholder", () => {
    renderWithProviders(<TerminalPage />);
    expect(screen.getByText("grid>")).toBeInTheDocument();
    expect(screen.getByText("Type a command…")).toBeInTheDocument();
  });
});
