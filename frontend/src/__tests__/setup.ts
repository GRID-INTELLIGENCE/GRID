import "@testing-library/jest-dom/vitest";
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

// ── Mock scrollTo (jsdom doesn't implement) ─────────────────────
Element.prototype.scrollTo = vi.fn();
Element.prototype.scrollIntoView = vi.fn();

// ── Export mocks for test access ────────────────────────────────
export {
  mockGridApi,
  mockGridOnStreamChunk,
  mockGridStream,
  mockOllamaApi,
  mockOllamaChat,
  mockOllamaOnChatToken,
};
