import { app, BrowserWindow, ipcMain, session } from "electron";
import path from "path";
import {
  gridApiSchema,
  gridStreamSchema,
  ollamaApiSchema,
  ollamaStreamSchema,
  executeToolSchema,
  planPreviewSchema,
  validateIpc,
} from "./ipc-schemas";

let mainWindow: BrowserWindow | null = null;

const isDev = !app.isPackaged;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    frame: false,
    titleBarStyle: "hidden",
    backgroundColor: "#09090b",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── Content Security Policy ──────────────────────────────────────

function installCSP(): void {
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const cspDirectives = [
      "default-src 'self'",
      // Allow Vite HMR websocket in dev mode
      isDev ? "script-src 'self' 'unsafe-inline'" : "script-src 'self'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      isDev
        ? "connect-src 'self' ws://localhost:* http://localhost:* http://127.0.0.1:*"
        : "connect-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; ");

    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [cspDirectives],
      },
    });
  });
}

// ── Window control IPC handlers ──────────────────────────────────

ipcMain.handle("window:minimize", () => mainWindow?.minimize());
ipcMain.handle("window:maximize", () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});
ipcMain.handle("window:close", () => mainWindow?.close());
ipcMain.handle("window:isMaximized", () => mainWindow?.isMaximized() ?? false);

// ── GRID API proxy — validated IPC ───────────────────────────────

ipcMain.handle(
  "grid:api",
  async (
    _event,
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => {
    const validation = validateIpc(gridApiSchema, {
      method,
      endpoint,
      body,
    });
    if (!validation.success) {
      return { ok: false, status: 0, data: null, error: validation.error };
    }

    const baseUrl = process.env.GRID_API_URL ?? "http://127.0.0.1:8000";
    const url = `${baseUrl}${validation.data.endpoint}`;
    try {
      const res = await fetch(url, {
        method: validation.data.method,
        headers: {
          "Content-Type": "application/json",
          ...headers, // Include authorization headers
        },
        body: validation.data.body
          ? JSON.stringify(validation.data.body)
          : undefined,
      });
      return {
        ok: res.ok,
        status: res.status,
        data: await res.json(),
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, status: 0, data: null, error: message };
    }
  }
);

// ── Streaming API proxy — NDJSON/SSE ─────────────────────────────

ipcMain.handle(
  "grid:stream",
  async (
    event,
    method: string,
    endpoint: string,
    body?: unknown,
    headers?: Record<string, string>
  ) => {
    const validation = validateIpc(gridStreamSchema, {
      method,
      endpoint,
      body,
    });
    const streamId = `stream-${Date.now()}`;

    if (!validation.success) {
      return { ok: false, streamId, error: validation.error };
    }

    const baseUrl = process.env.GRID_API_URL ?? "http://127.0.0.1:8000";
    const url = `${baseUrl}${validation.data.endpoint}`;
    try {
      const res = await fetch(url, {
        method: validation.data.method,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/x-ndjson",
          ...headers, // Include authorization headers
        },
        body: validation.data.body
          ? JSON.stringify(validation.data.body)
          : undefined,
      });
      if (!res.ok || !res.body) {
        return { ok: false, streamId, error: `HTTP ${res.status}` };
      }
      // Read NDJSON stream and forward chunks to renderer
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      (async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed) continue;
              try {
                const chunk = JSON.parse(trimmed);
                event.sender.send(`grid:stream:${streamId}`, {
                  type: "chunk",
                  data: chunk,
                });
              } catch {
                event.sender.send(`grid:stream:${streamId}`, {
                  type: "text",
                  data: trimmed,
                });
              }
            }
          }
          event.sender.send(`grid:stream:${streamId}`, {
            type: "done",
          });
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : String(err);
          event.sender.send(`grid:stream:${streamId}`, {
            type: "error",
            error: msg,
          });
        }
      })();
      return { ok: true, streamId };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, streamId, error: message };
    }
  }
);

// ── Ollama direct proxy — validated IPC ──────────────────────────

ipcMain.handle(
  "ollama:api",
  async (_event, method: string, endpoint: string, body?: unknown) => {
    const validation = validateIpc(ollamaApiSchema, {
      method,
      endpoint,
      body,
    });
    if (!validation.success) {
      return { ok: false, status: 0, data: null, error: validation.error };
    }

    const ollamaUrl = process.env.OLLAMA_URL ?? "http://127.0.0.1:11434";
    const url = `${ollamaUrl}${validation.data.endpoint}`;
    try {
      const res = await fetch(url, {
        method: validation.data.method,
        headers: { "Content-Type": "application/json" },
        body: validation.data.body
          ? JSON.stringify(validation.data.body)
          : undefined,
      });
      return {
        ok: res.ok,
        status: res.status,
        data: await res.json(),
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, status: 0, data: null, error: message };
    }
  }
);

// ── Ollama streaming chat — validated IPC ────────────────────────

ipcMain.handle(
  "ollama:stream",
  async (
    event,
    model: string,
    messages: { role: string; content: string }[],
    temperature?: number
  ) => {
    const validation = validateIpc(ollamaStreamSchema, {
      model,
      messages,
      temperature,
    });
    const streamId = `ollama-${Date.now()}`;

    if (!validation.success) {
      return { ok: false, streamId, error: validation.error };
    }

    const ollamaUrl = process.env.OLLAMA_URL ?? "http://127.0.0.1:11434";
    try {
      const res = await fetch(`${ollamaUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: validation.data.model,
          messages: validation.data.messages,
          stream: true,
          options: {
            temperature: validation.data.temperature ?? 0.7,
          },
        }),
      });
      if (!res.ok || !res.body) {
        return {
          ok: false,
          streamId,
          error: `Ollama HTTP ${res.status}`,
        };
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      (async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed) continue;
              try {
                const chunk = JSON.parse(trimmed);
                if (chunk.message?.content) {
                  event.sender.send(`ollama:stream:${streamId}`, {
                    type: "token",
                    content: chunk.message.content,
                    done: chunk.done ?? false,
                  });
                }
                if (chunk.done) {
                  event.sender.send(`ollama:stream:${streamId}`, {
                    type: "done",
                    model: chunk.model,
                    total_duration: chunk.total_duration,
                    eval_count: chunk.eval_count,
                  });
                }
              } catch {
                /* skip malformed */
              }
            }
          }
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : String(err);
          event.sender.send(`ollama:stream:${streamId}`, {
            type: "error",
            error: msg,
          });
        }
      })();
      return { ok: true, streamId };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, streamId, error: message };
    }
  }
);

// ── Tool System IPC handlers ─────────────────────────────────────

ipcMain.handle(
  "tools:execute",
  async (
    _event,
    toolId: string,
    args: Record<string, unknown>,
    dryRun: boolean
  ) => {
    const validation = validateIpc(executeToolSchema, {
      toolId,
      arguments: args,
      dryRun,
    });
    if (!validation.success) {
      return { ok: false, error: validation.error };
    }

    const baseUrl = process.env.GRID_API_URL ?? "http://127.0.0.1:8000";
    const url = `${baseUrl}/api/v1/tools/execute`;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_id: validation.data.toolId,
          arguments: validation.data.arguments,
          dry_run: validation.data.dryRun,
        }),
      });
      if (!res.ok) {
        return { ok: false, error: `HTTP ${res.status}` };
      }
      const data = await res.json();
      return { ok: true, data };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, error: message };
    }
  }
);

ipcMain.handle(
  "tools:plan",
  async (_event, goal: string, context?: string, model?: string) => {
    const validation = validateIpc(planPreviewSchema, { goal, context, model });
    if (!validation.success) {
      return { ok: false, error: validation.error };
    }

    const baseUrl = process.env.GRID_API_URL ?? "http://127.0.0.1:8000";
    const url = `${baseUrl}/api/v1/tools/plan`;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: validation.data.goal,
          context: validation.data.context,
          model: validation.data.model,
        }),
      });
      if (!res.ok) {
        return { ok: false, error: `HTTP ${res.status}` };
      }
      const data = await res.json();
      return { ok: true, data };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false, error: message };
    }
  }
);

ipcMain.handle("tools:list", async () => {
  const baseUrl = process.env.GRID_API_URL ?? "http://127.0.0.1:8000";
  const url = `${baseUrl}/api/v1/tools`;
  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}` };
    }
    const data = await res.json();
    return { ok: true, data };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: message };
  }
});

// ── App lifecycle ────────────────────────────────────────────────

app.whenReady().then(() => {
  installCSP();
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
