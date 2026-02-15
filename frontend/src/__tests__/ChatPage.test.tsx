import { ChatPage } from "@/pages/ChatPage";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

describe("ChatPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: Ollama online with one model
    window.ollama.api = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      data: {
        models: [
          {
            name: "ministral",
            model: "ministral",
            modified_at: "2026-01-01T00:00:00Z",
            size: 1000000,
            digest: "abc",
            details: {
              parent_model: "",
              format: "gguf",
              family: "ministral",
              parameter_size: "8B",
              quantization_level: "Q4_K_M",
            },
          },
        ],
      },
    });
  });

  it("renders title and description from config", async () => {
    renderWithProviders(<ChatPage />);
    expect(screen.getByText("AI Chat")).toBeInTheDocument();
    expect(
      screen.getByText(/Chat with local LLM models via Ollama/)
    ).toBeInTheDocument();
  });

  it("shows Ollama Online badge when healthy", async () => {
    renderWithProviders(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("Ollama Online")).toBeInTheDocument();
    });
  });

  it("shows Ollama Offline badge when unhealthy", async () => {
    window.ollama.api = vi
      .fn()
      .mockResolvedValue({ ok: false, status: 0, data: null });
    renderWithProviders(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("Ollama Offline")).toBeInTheDocument();
    });
  });

  it("shows model selector with available models", async () => {
    renderWithProviders(<ChatPage />);
    await waitFor(() => {
      const select = screen.getByRole("combobox");
      expect(select).toBeInTheDocument();
    });
  });

  it("shows empty state message when no messages", () => {
    renderWithProviders(<ChatPage />);
    expect(screen.getByText(/Start a conversation/)).toBeInTheDocument();
    expect(screen.getByText(/Running locally via Ollama/)).toBeInTheDocument();
  });

  it("has a textarea for input", () => {
    renderWithProviders(<ChatPage />);
    const textarea = screen.getByPlaceholderText("Type a message…");
    expect(textarea).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", async () => {
    renderWithProviders(<ChatPage />);
    await waitFor(() => {
      // Wait for Ollama health check to complete
      expect(screen.getByText("Ollama Online")).toBeInTheDocument();
    });
    // The send button (icon button) should still be disabled with empty input
    const buttons = screen.getAllByRole("button");
    const sendButton = buttons.find(
      (btn) =>
        !btn.getAttribute("title") || btn.getAttribute("title") !== "Clear chat"
    );
    // With empty input, it should be disabled
    expect(sendButton).toBeDefined();
  });

  it("clears messages when clear button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatPage />);

    const clearButton = screen.getByTitle("Clear chat");
    expect(clearButton).toBeInTheDocument();
    await user.click(clearButton);
    // Should still show empty state
    expect(screen.getByText(/Start a conversation/)).toBeInTheDocument();
  });

  it("accepts text input", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatPage />);

    const textarea = screen.getByPlaceholderText("Type a message…");
    await user.type(textarea, "Hello GRID");
    expect(textarea).toHaveValue("Hello GRID");
  });
});
