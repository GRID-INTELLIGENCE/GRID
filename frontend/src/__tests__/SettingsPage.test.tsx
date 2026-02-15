import { SettingsPage } from "@/pages/SettingsPage";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("SettingsPage", () => {
  it("renders title and description", () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(
      screen.getByText("Configure GRID frontend and backend connection")
    ).toBeInTheDocument();
  });

  it("renders API Connection section", () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByText("API Connection")).toBeInTheDocument();
    expect(
      screen.getByText("Core backend endpoints used by the UI")
    ).toBeInTheDocument();
  });

  it("renders Backend URL setting with resolved value", () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByText("Backend URL")).toBeInTheDocument();
    expect(screen.getByText("http://127.0.0.1:8000")).toBeInTheDocument();
  });

  it("renders Ollama URL setting with resolved value", () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByText("Ollama URL")).toBeInTheDocument();
    expect(screen.getByText("http://127.0.0.1:11434")).toBeInTheDocument();
  });
});
