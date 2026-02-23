/**
 * Typed wrappers around the Electron preload bridge (window.grid / window.ollama).
 *
 * Re-exports convenience singletons `gridClient` and `ollamaClient`
 * plus the types that pages and hooks import.
 */

import type { StreamChunk, OllamaToken } from "../../electron/preload";

// ── Public types ──────────────────────────────────────────────────────

export type { StreamChunk, OllamaToken };

export interface ApiResponse<T = unknown> {
  ok: boolean;
  status: number;
  data: T;
  error?: string;
}

export interface OllamaModel {
  name: string;
  model: string;
  size: number;
  digest?: string;
  modified_at?: string;
}

export interface StreamHandle {
  streamId: string;
  onChunk: (cb: (chunk: StreamChunk) => void) => () => void;
}

export interface ChatHandle {
  streamId: string;
  onToken: (cb: (token: OllamaToken) => void) => () => void;
}

// ── Default headers ───────────────────────────────────────────────────

function defaultHeaders(): Record<string, string> {
  return { "X-Client": "grid-frontend" };
}

// ── GridClient ────────────────────────────────────────────────────────

class GridClient {
  async get<T = unknown>(endpoint: string): Promise<ApiResponse<T>> {
    const res = await window.grid.api(
      "GET",
      endpoint,
      undefined,
      defaultHeaders()
    );
    return res as ApiResponse<T>;
  }

  async post<T = unknown>(
    endpoint: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const res = await window.grid.api("POST", endpoint, body, defaultHeaders());
    return res as ApiResponse<T>;
  }

  async put<T = unknown>(
    endpoint: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const res = await window.grid.api("PUT", endpoint, body, defaultHeaders());
    return res as ApiResponse<T>;
  }

  async delete<T = unknown>(endpoint: string): Promise<ApiResponse<T>> {
    const res = await window.grid.api(
      "DELETE",
      endpoint,
      undefined,
      defaultHeaders()
    );
    return res as ApiResponse<T>;
  }

  async stream(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<StreamHandle> {
    const res = await window.grid.stream(
      method,
      endpoint,
      body,
      defaultHeaders()
    );
    if (!res.ok) {
      throw new Error(res.error ?? "Stream failed");
    }
    return {
      streamId: res.streamId,
      onChunk: (cb) => window.grid.onStreamChunk(res.streamId, cb),
    };
  }
}

// ── OllamaClient ─────────────────────────────────────────────────────

class OllamaClient {
  async listModels(): Promise<OllamaModel[]> {
    try {
      const res = await window.ollama.api("GET", "/api/tags");
      if (!res.ok) return [];
      const data = res.data as { models?: OllamaModel[] } | null;
      return data?.models ?? [];
    } catch {
      return [];
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      const res = await window.ollama.api("GET", "/api/tags");
      return res.ok;
    } catch {
      return false;
    }
  }

  async chat(
    model: string,
    messages: { role: string; content: string }[],
    temperature?: number
  ): Promise<ChatHandle> {
    const res = await window.ollama.chat(model, messages, temperature);
    if (!res.ok) {
      throw new Error(res.error ?? "Chat failed");
    }
    return {
      streamId: res.streamId,
      onToken: (cb) => window.ollama.onChatToken(res.streamId, cb),
    };
  }

  async generate(
    model: string,
    prompt: string,
    system?: string
  ): Promise<string> {
    const res = await window.ollama.api("POST", "/api/generate", {
      model,
      prompt,
      system,
      stream: false,
    });
    if (!res.ok) {
      throw new Error("Ollama generate failed");
    }
    const data = res.data as { response?: string } | null;
    return data?.response ?? "";
  }
}

// ── Singleton exports ─────────────────────────────────────────────────

export const gridClient = new GridClient();
export const ollamaClient = new OllamaClient();
