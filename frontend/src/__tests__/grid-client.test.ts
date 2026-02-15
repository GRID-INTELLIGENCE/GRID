import { gridClient, ollamaClient } from "@/lib/grid-client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("GridClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("get", () => {
    it("calls grid.api with GET and endpoint", async () => {
      window.grid.api = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        data: { status: "healthy" },
      });

      const result = await gridClient.get("/health");
      expect(window.grid.api).toHaveBeenCalledWith(
        "GET",
        "/health",
        undefined,
        expect.any(Object)
      );
      expect(result.ok).toBe(true);
      expect(result.data).toEqual({ status: "healthy" });
    });
  });

  describe("post", () => {
    it("calls grid.api with POST, endpoint, and body", async () => {
      window.grid.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: { answer: "test" } });

      const body = { query: "hello" };
      const result = await gridClient.post("/rag/query", body);
      expect(window.grid.api).toHaveBeenCalledWith(
        "POST",
        "/rag/query",
        body,
        expect.any(Object)
      );
      expect(result.ok).toBe(true);
    });

    it("passes undefined body when not provided", async () => {
      window.grid.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: {} });

      await gridClient.post("/test");
      expect(window.grid.api).toHaveBeenCalledWith(
        "POST",
        "/test",
        undefined,
        expect.any(Object)
      );
    });
  });

  describe("put", () => {
    it("calls grid.api with PUT", async () => {
      window.grid.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: {} });

      await gridClient.put("/api/v1/cockpit/mode", { mode: "test" });
      expect(window.grid.api).toHaveBeenCalledWith(
        "PUT",
        "/api/v1/cockpit/mode",
        { mode: "test" },
        expect.any(Object)
      );
    });
  });

  describe("delete", () => {
    it("calls grid.api with DELETE", async () => {
      window.grid.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: {} });

      await gridClient.delete("/api/v1/rag/sessions/123");
      expect(window.grid.api).toHaveBeenCalledWith(
        "DELETE",
        "/api/v1/rag/sessions/123",
        undefined,
        expect.any(Object)
      );
    });
  });

  describe("stream", () => {
    it("returns stream handle on success", async () => {
      const mockCleanup = vi.fn();
      window.grid.stream = vi
        .fn()
        .mockResolvedValue({ ok: true, streamId: "stream-42" });
      window.grid.onStreamChunk = vi.fn().mockReturnValue(mockCleanup);

      const handle = await gridClient.stream("POST", "/rag/query/stream", {
        query: "test",
      });
      expect(window.grid.stream).toHaveBeenCalledWith(
        "POST",
        "/rag/query/stream",
        { query: "test" },
        expect.any(Object)
      );
      expect(handle.streamId).toBe("stream-42");

      // onChunk should wire up the listener
      const cb = vi.fn();
      const cleanup = handle.onChunk(cb);
      expect(window.grid.onStreamChunk).toHaveBeenCalledWith("stream-42", cb);
      expect(cleanup).toBe(mockCleanup);
    });

    it("throws when stream fails", async () => {
      window.grid.stream = vi
        .fn()
        .mockResolvedValue({ ok: false, streamId: "s-1", error: "HTTP 500" });

      await expect(gridClient.stream("POST", "/test")).rejects.toThrow(
        "HTTP 500"
      );
    });

    it("throws generic error when no error message", async () => {
      window.grid.stream = vi
        .fn()
        .mockResolvedValue({ ok: false, streamId: "s-1" });

      await expect(gridClient.stream("POST", "/test")).rejects.toThrow(
        "Stream failed"
      );
    });
  });
});

describe("OllamaClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("listModels", () => {
    it("returns models from Ollama API", async () => {
      window.ollama.api = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        data: {
          models: [
            { name: "ministral", model: "ministral", size: 1000 },
            {
              name: "mistral-nemo:latest",
              model: "mistral-nemo:latest",
              size: 2000,
            },
          ],
        },
      });

      const models = await ollamaClient.listModels();
      expect(window.ollama.api).toHaveBeenCalledWith("GET", "/api/tags");
      expect(models).toHaveLength(2);
      expect(models[0].name).toBe("ministral");
    });

    it("returns empty array when API fails", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: false, status: 500, data: null });

      const models = await ollamaClient.listModels();
      expect(models).toEqual([]);
    });

    it("returns empty array when no models field", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: {} });

      const models = await ollamaClient.listModels();
      expect(models).toEqual([]);
    });
  });

  describe("isHealthy", () => {
    it("returns true when Ollama is reachable", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: { models: [] } });

      const healthy = await ollamaClient.isHealthy();
      expect(healthy).toBe(true);
    });

    it("returns false when Ollama is down", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: false, status: 0, data: null });

      const healthy = await ollamaClient.isHealthy();
      expect(healthy).toBe(false);
    });

    it("returns false when api throws", async () => {
      window.ollama.api = vi.fn().mockRejectedValue(new Error("Network error"));

      const healthy = await ollamaClient.isHealthy();
      expect(healthy).toBe(false);
    });
  });

  describe("chat", () => {
    it("returns chat handle on success", async () => {
      const mockCleanup = vi.fn();
      window.ollama.chat = vi
        .fn()
        .mockResolvedValue({ ok: true, streamId: "ollama-99" });
      window.ollama.onChatToken = vi.fn().mockReturnValue(mockCleanup);

      const messages = [{ role: "user", content: "hello" }];
      const handle = await ollamaClient.chat("ministral", messages, 0.5);

      expect(window.ollama.chat).toHaveBeenCalledWith(
        "ministral",
        messages,
        0.5
      );
      expect(handle.streamId).toBe("ollama-99");

      const cb = vi.fn();
      const cleanup = handle.onToken(cb);
      expect(window.ollama.onChatToken).toHaveBeenCalledWith(
        "ollama-99",
        expect.any(Function)
      );
      expect(cleanup).toBe(mockCleanup);
    });

    it("throws when chat fails", async () => {
      window.ollama.chat = vi.fn().mockResolvedValue({
        ok: false,
        streamId: "o-1",
        error: "Model not found",
      });

      await expect(
        ollamaClient.chat("unknown", [{ role: "user", content: "hi" }])
      ).rejects.toThrow("Model not found");
    });
  });

  describe("generate", () => {
    it("returns generated text", async () => {
      window.ollama.api = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        data: { response: "Hello world" },
      });

      const result = await ollamaClient.generate(
        "ministral",
        "Say hello",
        "Be friendly"
      );
      expect(window.ollama.api).toHaveBeenCalledWith("POST", "/api/generate", {
        model: "ministral",
        prompt: "Say hello",
        system: "Be friendly",
        stream: false,
      });
      expect(result).toBe("Hello world");
    });

    it("returns empty string when no response field", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, data: {} });

      const result = await ollamaClient.generate("ministral", "test");
      expect(result).toBe("");
    });

    it("throws when generate fails", async () => {
      window.ollama.api = vi
        .fn()
        .mockResolvedValue({ ok: false, status: 500, data: null });

      await expect(ollamaClient.generate("ministral", "test")).rejects.toThrow(
        "Ollama generate failed"
      );
    });
  });
});
