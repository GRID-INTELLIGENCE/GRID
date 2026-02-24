import "@testing-library/jest-dom/vitest";
import "fake-indexeddb/auto";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Automatic cleanup after each test
afterEach(() => {
  cleanup();
});

// ── Mock window.grid (Electron IPC bridge) ──────────────────────
const mockGridApi = vi
  .fn()
  .mockResolvedValue({ ok: true, status: 200, data: {} });
const mockGridStream = vi
  .fn()
  .mockResolvedValue({ ok: true, streamId: "test-stream-1" });
const mockGridOnStreamChunk = vi.fn().mockReturnValue(() => undefined);

Object.defineProperty(window, "grid", {
  value: {
    api: mockGridApi,
    stream: mockGridStream,
    onStreamChunk: mockGridOnStreamChunk,
  },
  writable: true,
});

// ── Mock window.ollama (Ollama IPC bridge) ──────────────────────
const mockOllamaApi = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  data: {
    models: [
      {
        name: "ministral",
        model: "ministral",
        modified_at: "2026-01-01T00:00:00Z",
        size: 1000000,
        digest: "abc123",
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
const mockOllamaChat = vi
  .fn()
  .mockResolvedValue({ ok: true, streamId: "ollama-test-1" });
const mockOllamaOnChatToken = vi.fn().mockReturnValue(() => undefined);

Object.defineProperty(window, "ollama", {
  value: {
    api: mockOllamaApi,
    chat: mockOllamaChat,
    onChatToken: mockOllamaOnChatToken,
  },
  writable: true,
});

// ── Mock window.windowControls ──────────────────────────────────
Object.defineProperty(window, "windowControls", {
  value: {
    minimize: vi.fn(),
    maximize: vi.fn(),
    close: vi.fn(),
    isMaximized: vi.fn().mockResolvedValue(false),
    onMaximizeChange: vi.fn().mockReturnValue(() => undefined),
  },
  writable: true,
});

// ── Mock window.mycelium (Mycelium IPC bridge) ─────────────────
const mockMyceliumSynthesize = vi.fn().mockResolvedValue({
  gist: "Light is electromagnetic radiation.",
  highlights: [
    {
      text: "electromagnetic",
      priority: "critical",
      context: "",
      category: "concept",
    },
    { text: "radiation", priority: "high", context: "", category: "concept" },
  ],
  summary: "Light is electromagnetic radiation. It travels at 299,792,458 m/s.",
  explanation: "Electromagnetic radiation spans the full spectrum.",
  analogy: "Think of light like ripples on a pond.",
  compression_ratio: 0.12,
  depth: "americano",
  patterns: ["repetition"],
  scaffolding_applied: [],
});
const mockMyceliumExplore = vi.fn().mockResolvedValue({
  concept: "cache",
  lens: {
    pattern: "flow",
    analogy: "A cache is like a shelf next to you.",
    eli5: "A shelf with stuff you use a lot.",
    visual_hint: "Picture a bookshelf.",
    when_useful: "When things need to be fast.",
  },
  alternatives_available: 2,
});
const mockMyceliumFeedback = vi.fn().mockResolvedValue(undefined);
const mockMyceliumConcepts = vi
  .fn()
  .mockResolvedValue(["cache", "recursion", "database", "api", "encryption"]);

Object.defineProperty(window, "mycelium", {
  value: {
    synthesize: mockMyceliumSynthesize,
    summarize: vi.fn().mockResolvedValue("Summary text."),
    simplify: vi.fn().mockResolvedValue("Simple text."),
    keywords: vi.fn().mockResolvedValue([]),
    explore: mockMyceliumExplore,
    tryDifferent: mockMyceliumExplore,
    eli5: vi.fn().mockResolvedValue("A simple explanation."),
    feedback: mockMyceliumFeedback,
    setUser: vi.fn().mockResolvedValue(undefined),
    setSensory: vi.fn().mockResolvedValue("Profile updated."),
    concepts: mockMyceliumConcepts,
  },
  writable: true,
});

// ── Mock scrollTo (jsdom doesn't implement) ─────────────────────
Element.prototype.scrollTo = vi.fn();
Element.prototype.scrollIntoView = vi.fn();

// ── Mock navigator.clipboard (jsdom doesn't implement) ──────────
// Use configurable: true so userEvent.setup() can also stub clipboard
Object.defineProperty(navigator, "clipboard", {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
    readText: vi.fn().mockResolvedValue(""),
    read: vi.fn().mockResolvedValue([]),
  },
  writable: true,
  configurable: true,
});

// ── Export mocks for test access ────────────────────────────────
export {
  mockGridApi,
  mockGridOnStreamChunk,
  mockGridStream,
  mockMyceliumConcepts,
  mockMyceliumExplore,
  mockMyceliumFeedback,
  mockMyceliumSynthesize,
  mockOllamaApi,
  mockOllamaChat,
  mockOllamaOnChatToken,
};
