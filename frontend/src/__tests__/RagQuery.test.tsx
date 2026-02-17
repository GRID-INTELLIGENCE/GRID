import { RagQuery } from "@/pages/RagQuery";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("RagQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders title and description from config", () => {
    renderWithProviders(<RagQuery />);
    expect(screen.getByText("RAG Query")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Search indexed knowledge with retrieval-augmented generation/
      )
    ).toBeInTheDocument();
  });

  it("has a search input with placeholder", () => {
    renderWithProviders(<RagQuery />);
    const input = screen.getByPlaceholderText(
      "Ask a question about your knowledge base…"
    );
    expect(input).toBeInTheDocument();
  });

  it("has a search submit button", () => {
    renderWithProviders(<RagQuery />);
    const button = screen.getByRole("button", { name: /Search/ });
    expect(button).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    renderWithProviders(<RagQuery />);
    const button = screen.getByRole("button", { name: /Search/ });
    expect(button).toBeDisabled();
  });

  it("submit button is enabled when input has text", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RagQuery />);

    const input = screen.getByPlaceholderText(
      "Ask a question about your knowledge base…"
    );
    await user.type(input, "How does the RAG system work?");

    const button = screen.getByRole("button", { name: /Search/ });
    expect(button).toBeEnabled();
  });

  it("has a conversational mode checkbox", () => {
    renderWithProviders(<RagQuery />);
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toBeChecked(); // default on
    expect(screen.getByText("Conversational")).toBeInTheDocument();
  });

  it("can toggle conversational mode", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RagQuery />);

    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  it("calls grid stream when form is submitted", async () => {
    const user = userEvent.setup();
    const mockCleanup = vi.fn();
    window.grid.stream = vi
      .fn()
      .mockResolvedValue({ ok: true, streamId: "rag-stream-1" });
    window.grid.onStreamChunk = vi.fn().mockReturnValue(mockCleanup);

    renderWithProviders(<RagQuery />);

    const input = screen.getByPlaceholderText(
      "Ask a question about your knowledge base…"
    );
    await user.type(input, "What is GRID?");

    const button = screen.getByRole("button", { name: /Search/ });
    await user.click(button);

    expect(window.grid.stream).toHaveBeenCalledWith(
      "POST",
      "/rag/query/stream",
      expect.objectContaining({ query: "What is GRID?" }),
      expect.any(Object)
    );
  });

  it("does not show conversation history initially", () => {
    renderWithProviders(<RagQuery />);
    expect(screen.queryByText("Previous queries")).not.toBeInTheDocument();
  });
});
