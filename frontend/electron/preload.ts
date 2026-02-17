import { contextBridge, ipcRenderer } from "electron";

export interface GridAPI {
  api: (
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => Promise<{ ok: boolean; status: number; data: unknown; error?: string }>;
  stream: (
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => Promise<{ ok: boolean; streamId: string; error?: string }>;
  onStreamChunk: (
    streamId: string,
    callback: (chunk: StreamChunk) => void
  ) => () => void;
}

export interface OllamaAPI {
  api: (
    method: string,
    endpoint: string,
    body?: unknown
  ) => Promise<{ ok: boolean; status: number; data: unknown; error?: string }>;
  chat: (
    model: string,
    messages: { role: string; content: string }[],
    temperature?: number
  ) => Promise<{ ok: boolean; streamId: string; error?: string }>;
  onChatToken: (
    streamId: string,
    callback: (token: OllamaToken) => void
  ) => () => void;
}

export interface StreamChunk {
  type: "chunk" | "text" | "done" | "error";
  data?: unknown;
  error?: string;
}

export interface OllamaToken {
  type: "token" | "done" | "error";
  content?: string;
  done?: boolean;
  model?: string;
  total_duration?: number;
  eval_count?: number;
  error?: string;
}

export interface WindowAPI {
  minimize: () => Promise<void>;
  maximize: () => Promise<void>;
  close: () => Promise<void>;
  isMaximized: () => Promise<boolean>;
  onMaximizeChange: (callback: (maximized: boolean) => void) => () => void;
}

export interface ToolsAPI {
  executeTool: (
    toolId: string,
    args: Record<string, unknown>,
    dryRun?: boolean
  ) => Promise<{
    ok: boolean;
    data?: unknown;
    error?: string;
  }>;
  planPreview: (
    goal: string,
    context?: string,
    model?: string
  ) => Promise<{
    ok: boolean;
    data?: unknown;
    error?: string;
  }>;
  listTools: () => Promise<{
    ok: boolean;
    data?: unknown;
    error?: string;
  }>;
}

contextBridge.exposeInMainWorld("grid", {
  api: (
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => ipcRenderer.invoke("grid:api", method, endpoint, body, headers),
  stream: (
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => ipcRenderer.invoke("grid:stream", method, endpoint, body, headers),
  onStreamChunk: (streamId: string, callback: (chunk: StreamChunk) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, chunk: StreamChunk) =>
      callback(chunk);
    ipcRenderer.on(`grid:stream:${streamId}`, handler);
    return () => ipcRenderer.removeListener(`grid:stream:${streamId}`, handler);
  },
} satisfies GridAPI);

contextBridge.exposeInMainWorld("ollama", {
  api: (method: string, endpoint: string, body?: unknown) =>
    ipcRenderer.invoke("ollama:api", method, endpoint, body),
  chat: (
    model: string,
    messages: { role: string; content: string }[],
    temperature?: number
  ) => ipcRenderer.invoke("ollama:stream", model, messages, temperature),
  onChatToken: (streamId: string, callback: (token: OllamaToken) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, token: OllamaToken) =>
      callback(token);
    ipcRenderer.on(`ollama:stream:${streamId}`, handler);
    return () =>
      ipcRenderer.removeListener(`ollama:stream:${streamId}`, handler);
  },
} satisfies OllamaAPI);

contextBridge.exposeInMainWorld("windowControls", {
  minimize: () => ipcRenderer.invoke("window:minimize"),
  maximize: () => ipcRenderer.invoke("window:maximize"),
  close: () => ipcRenderer.invoke("window:close"),
  isMaximized: () => ipcRenderer.invoke("window:isMaximized"),
  onMaximizeChange: (callback: (maximized: boolean) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, maximized: boolean) =>
      callback(maximized);
    ipcRenderer.on("window:maximized-changed", handler);
    return () =>
      ipcRenderer.removeListener("window:maximized-changed", handler);
  },
} satisfies WindowAPI);

contextBridge.exposeInMainWorld("tools", {
  executeTool: (
    toolId: string,
    args: Record<string, unknown>,
    dryRun?: boolean
  ) => ipcRenderer.invoke("tools:execute", toolId, args, dryRun ?? false),
  planPreview: (goal: string, context?: string, model?: string) =>
    ipcRenderer.invoke("tools:plan", goal, context, model),
  listTools: () => ipcRenderer.invoke("tools:list"),
} satisfies ToolsAPI);
