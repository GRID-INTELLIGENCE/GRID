import { Knowledge } from "@/pages/Knowledge";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./test-utils";

const MOCK_KNOWLEDGE_STATS = {
  total_entities: 2,
  total_relationships: 1,
  entity_counts: { Document: 1, Concept: 1 },
  relationship_counts: { EXPLAINS: 1 },
  storage_path: "dev/knowledge_graph.json",
};

const MOCK_KNOWLEDGE_GRAPH = {
  nodes: [
    {
      id: "d1",
      label: "Doc A",
      entity_type: "Document",
      subtitle: "",
    },
    {
      id: "n1",
      label: "Concept One",
      entity_type: "Concept",
      subtitle: "First",
    },
  ],
  edges: [
    {
      id: "r1",
      source: "d1",
      target: "n1",
      type: "EXPLAINS",
      label: "EXPLAINS",
    },
  ],
  total_entities: 2,
  truncated: false,
};

describe("Knowledge", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/api/v1/rag/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              conversation_stats: {
                active_sessions: 3,
                total_conversations: 42,
              },
              engine_info: {
                model: "ministral",
                embedding_model: "nomic-embed-text-v2-moe",
                vector_store: "ChromaDB",
              },
            },
          });
        }
        if (endpoint === "/api/v1/skills/signal-quality") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { noise_to_signal_ratio: 0.12, quality: "high" },
          });
        }
        if (endpoint === "/api/v1/knowledge/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_STATS },
          });
        }
        if (endpoint.startsWith("/api/v1/knowledge/graph")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_GRAPH },
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });
  });

  it("renders title and description", () => {
    renderWithProviders(<Knowledge />);
    expect(screen.getByText("Knowledge Base")).toBeInTheDocument();
    expect(
      screen.getByText(/RAG metrics, persisted knowledge graph layout/)
    ).toBeInTheDocument();
  });

  it("renders RAG Engine and Conversations cards", () => {
    renderWithProviders(<Knowledge />);
    expect(screen.getByText("RAG Engine")).toBeInTheDocument();
    expect(screen.getByText("Conversations")).toBeInTheDocument();
  });

  it("renders knowledge graph section with stats from API", async () => {
    renderWithProviders(<Knowledge />);
    expect(screen.getByText("Knowledge graph")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("2 entities")).toBeInTheDocument();
      expect(screen.getByText("1 relationships")).toBeInTheDocument();
    });
  });

  it("shows engine info from API", async () => {
    renderWithProviders(<Knowledge />);
    await waitFor(() => {
      expect(screen.getByText("ministral")).toBeInTheDocument();
      expect(screen.getByText("ChromaDB")).toBeInTheDocument();
    });
  });

  it("shows conversation stats from API", async () => {
    renderWithProviders(<Knowledge />);
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument(); // active sessions
      expect(screen.getByText("42")).toBeInTheDocument(); // total conversations
    });
  });

  it("renders signal quality section when data is available", async () => {
    renderWithProviders(<Knowledge />);
    await waitFor(() => {
      expect(screen.getByText(/Knowledge Signal Quality/)).toBeInTheDocument();
    });
  });

  it("renders session lookup section", () => {
    renderWithProviders(<Knowledge />);
    expect(screen.getByText("Session Lookup")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Enter session ID…")
    ).toBeInTheDocument();
  });

  it("lookup button is disabled when input is empty", () => {
    renderWithProviders(<Knowledge />);
    const lookupBtn = screen.getByRole("button", { name: /Lookup/ });
    expect(lookupBtn).toBeDisabled();
  });

  it("lookup button is enabled when session id is entered", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Knowledge />);

    const input = screen.getByPlaceholderText("Enter session ID…");
    await user.type(input, "session-123");

    const lookupBtn = screen.getByRole("button", { name: /Lookup/ });
    expect(lookupBtn).toBeEnabled();
  });

  it("calls session lookup API on button click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Knowledge />);

    const input = screen.getByPlaceholderText("Enter session ID…");
    await user.type(input, "session-abc");

    const lookupBtn = screen.getByRole("button", { name: /Lookup/ });
    await user.click(lookupBtn);

    await waitFor(() => {
      expect(window.grid.api).toHaveBeenCalledWith(
        "GET",
        "/api/v1/rag/sessions/session-abc",
        undefined,
        expect.any(Object)
      );
    });
  });

  it("shows session details after lookup", async () => {
    const user = userEvent.setup();
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/api/v1/knowledge/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_STATS },
          });
        }
        if (endpoint.startsWith("/api/v1/knowledge/graph")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_GRAPH },
          });
        }
        if (endpoint === "/api/v1/rag/sessions/session-abc") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { session_id: "session-abc", turn_count: 5 },
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });

    renderWithProviders(<Knowledge />);
    const input = screen.getByPlaceholderText("Enter session ID…");
    await user.type(input, "session-abc");

    const lookupBtn = screen.getByRole("button", { name: /Lookup/ });
    await user.click(lookupBtn);

    await waitFor(() => {
      expect(screen.getByText("Session: session-abc")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });
  });

  it("shows error when session not found", async () => {
    const user = userEvent.setup();
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/api/v1/knowledge/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_STATS },
          });
        }
        if (endpoint.startsWith("/api/v1/knowledge/graph")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_GRAPH },
          });
        }
        if (endpoint.startsWith("/api/v1/rag/sessions/")) {
          return Promise.resolve({
            ok: false,
            status: 404,
            data: null,
            error: "Session not found",
          });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });

    renderWithProviders(<Knowledge />);
    const input = screen.getByPlaceholderText("Enter session ID…");
    await user.type(input, "nonexistent");

    const lookupBtn = screen.getByRole("button", { name: /Lookup/ });
    await user.click(lookupBtn);

    await waitFor(() => {
      expect(screen.getByText("Session not found")).toBeInTheDocument();
    });
  });

  it("has a refresh button", () => {
    renderWithProviders(<Knowledge />);
    const refreshBtn = screen.getByRole("button", { name: /Refresh/ });
    expect(refreshBtn).toBeInTheDocument();
  });

  it("shows an error when the graph payload omits nodes or edges", async () => {
    window.grid.api = vi
      .fn()
      .mockImplementation((_method: string, endpoint: string) => {
        if (endpoint === "/api/v1/knowledge/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: { ...MOCK_KNOWLEDGE_STATS },
          });
        }
        if (endpoint.startsWith("/api/v1/knowledge/graph")) {
          return Promise.resolve({ ok: true, status: 200, data: {} });
        }
        if (endpoint === "/api/v1/rag/stats") {
          return Promise.resolve({
            ok: true,
            status: 200,
            data: {
              conversation_stats: {
                active_sessions: 0,
                total_conversations: 0,
              },
              engine_info: {
                model: "x",
                embedding_model: "y",
                vector_store: "z",
              },
            },
          });
        }
        if (endpoint === "/api/v1/skills/signal-quality") {
          return Promise.resolve({ ok: true, status: 200, data: {} });
        }
        return Promise.resolve({ ok: true, status: 200, data: {} });
      });

    renderWithProviders(<Knowledge />);
    await waitFor(() => {
      expect(
        screen.getByText(
          /Knowledge graph response must include nodes and edges arrays/
        )
      ).toBeInTheDocument();
    });
  });
});
