/**
 * Browser-mode shim for Electron IPC bridges.
 *
 * When running in a browser (npm run dev:renderer), `window.grid`,
 * `window.ollama`, and `window.windowControls` are not available because
 * they are injected by Electron's preload script.
 *
 * This shim provides realistic demo data so that all pages render
 * meaningfully during development and presentations.
 *
 * Only installed when `window.grid` is NOT already defined (browser mode).
 */
import { extractKeywords } from "@/lib/text-utils";

const IS_ELECTRON =
  typeof window !== "undefined" && typeof window.grid !== "undefined";

// ── Demo data for each endpoint ──────────────────────────────────────

const DEMO_RESPONSES: Record<string, unknown> = {
  // ── Health / Observability ──
  "/health": {
    status: "healthy",
    version: "0.4.0-dev",
    uptime: 86412,
    components: [
      { name: "FastAPI", status: "healthy" },
      { name: "Ollama", status: "healthy" },
      { name: "RAG Engine", status: "ready" },
      { name: "Safety Layer", status: "active" },
      { name: "Pattern Engine", status: "active" },
    ],
    alerts: [],
  },
  "/metrics": {
    uptime: 86412,
    sessions: 24,
    operations: 1847,
    components: 5,
    alerts: 0,
    resilience_score: 0.92,
  },
  "/health/ready": {
    ready: true,
    checks: {
      database: true,
      ollama: true,
      rag_engine: true,
      safety_layer: true,
    },
  },
  "/version": {
    name: "GRID",
    version: "0.4.0-dev",
    environment: "development",
    debug: true,
    python_version: "3.13.2",
  },
  "/health/chaos-resilience": {
    resilience_score: 0.92,
    components: {
      api: { score: 0.95, status: "resilient" },
      database: { score: 0.88, status: "resilient" },
      ollama: { score: 0.91, status: "resilient" },
    },
    recommendations: [
      "Consider adding circuit breaker to database connections",
    ],
  },

  // ── Security ──
  "/security/status": {
    authentication_level: "session",
    cors_policy: "strict",
    rate_limiting: "enabled",
    security_headers: true,
    encryption: "enabled",
    pii_protection: true,
    audit_logging: "enabled",
    input_sanitization: true,
  },
  "/health/security": {
    overall_status: "healthy",
    compliance_score: 94,
    checks: [
      {
        name: "Authentication",
        status: "pass",
        details: "Session-based auth active",
      },
      { name: "Rate Limiting", status: "pass", details: "100 req/min per IP" },
      {
        name: "Input Sanitization",
        status: "pass",
        details: "XSS & SQL injection protection",
      },
      {
        name: "PII Detection",
        status: "pass",
        details: "Non-punitive, local only",
      },
      { name: "CORS Policy", status: "pass", details: "Strict origin checks" },
      {
        name: "Security Headers",
        status: "pass",
        details: "CSP, HSTS, X-Frame-Options",
      },
      { name: "Encryption", status: "pass", details: "TLS 1.3 enforced" },
      { name: "Audit Trail", status: "pass", details: "All actions logged" },
      {
        name: "Password Policy",
        status: "warn",
        details: "Consider enforcing complexity requirements",
      },
    ],
  },
  "/corruption/stats": {
    monitored_endpoints: 14,
    total_penalties: 0,
    system_status: "clean",
    last_scan: "2026-02-24T07:30:00Z",
    scan_interval_seconds: 300,
  },
  "/drt/system-overview": {
    status: {
      active: true,
      mode: "balanced",
      trust_level: 0.87,
    },
    dimensions: {
      practical: { score: 0.72, trend: "stable" },
      legal: { score: 0.65, trend: "improving" },
      psychological: { score: 0.81, trend: "stable" },
    },
    recent_sessions: 12,
    balance_coefficient: 0.67,
  },

  // ── Cognitive ──
  "/api/v1/cockpit/state": {
    status: "active",
    mode: "adaptive",
    version: "0.4.0",
    uptime: 86400,
    summary: {
      active_threads: 3,
      processed_queries: 142,
      cognitive_load: "moderate",
    },
  },
  "/api/v1/resonance/context": {
    active_activities: 2,
    context_state: {
      current_focus: "exploration",
      resonance_level: "hum",
      depth: "americano",
    },
  },
  "/api/v1/skills/health": {
    status: "healthy",
    registered_skills: 8,
    active_skills: 6,
    skills: [
      { name: "Pattern Recognition", status: "active" },
      { name: "Text Synthesis", status: "active" },
      { name: "Concept Explorer", status: "active" },
      { name: "Safety Guard", status: "active" },
      { name: "Adaptive Scaffold", status: "active" },
      { name: "Sensory Mode", status: "active" },
    ],
  },

  // ── Knowledge ──
  "/api/v1/rag/stats": {
    conversation_stats: {
      active_sessions: 3,
      total_conversations: 47,
      avg_turns_per_session: 6.2,
    },
    engine_info: {
      model: "ministral",
      embedding_model: "sentence-transformers",
      vector_store: "ChromaDB",
      documents_indexed: 156,
    },
  },
  "/api/v1/skills/signal-quality": {
    overall_quality: 0.89,
    dimensions: {
      relevance: 0.91,
      coherence: 0.87,
      confidence: 0.88,
    },
    sample_size: 1200,
  },
};

// ── Streaming demo data ──────────────────────────────────────────────

let streamCounter = 0;

// ── Install shim ─────────────────────────────────────────────────────

export function installBrowserShim(): void {
  if (IS_ELECTRON) return; // Already in Electron — do nothing

  console.log(
    "%c[GRID] Browser mode — demo data active",
    "color: #f59e0b; font-weight: bold"
  );

  // Shim window.grid
  if (!window.grid) {
    (window as unknown as Record<string, unknown>).grid = {
      api: async (
        _method: string,
        endpoint: string,
        _body?: unknown,
        _headers?: Record<string, string>
      ) => {
        // Small delay to simulate network
        await new Promise((r) => setTimeout(r, 150 + Math.random() * 200));

        const data = DEMO_RESPONSES[endpoint];
        if (data) {
          return { ok: true, status: 200, data };
        }
        // For unknown endpoints, return empty success
        return { ok: true, status: 200, data: {} };
      },

      stream: async (
        _method: string,
        _endpoint: string,
        _body?: unknown,
        _headers?: Record<string, string>
      ) => {
        const id = `demo-stream-${++streamCounter}`;
        return { ok: true, streamId: id };
      },

      onStreamChunk: (
        _streamId: string,
        callback: (chunk: unknown) => void
      ) => {
        // Simulate a few chunks then done
        const chunks = [
          { type: "text", data: "This is a demo response. " },
          {
            type: "text",
            data: "The backend is not connected, but the UI is fully functional. ",
          },
          { type: "text", data: "Start the API server to see live data." },
          { type: "done", data: null },
        ];
        let i = 0;
        const timer = setInterval(() => {
          if (i < chunks.length) {
            callback(chunks[i]);
            i++;
          } else {
            clearInterval(timer);
          }
        }, 200);
        return () => clearInterval(timer);
      },
    };
  }

  // Shim window.ollama
  if (!window.ollama) {
    (window as unknown as Record<string, unknown>).ollama = {
      api: async (_method: string, endpoint: string, _body?: unknown) => {
        await new Promise((r) => setTimeout(r, 100));
        if (endpoint === "/api/tags") {
          return {
            ok: true,
            status: 200,
            data: {
              models: [
                {
                  name: "ministral",
                  model: "ministral:latest",
                  size: 4_700_000_000,
                  digest: "demo123",
                  modified_at: "2026-02-24T00:00:00Z",
                },
              ],
            },
          };
        }
        return { ok: true, status: 200, data: {} };
      },

      chat: async () => {
        const id = `demo-chat-${++streamCounter}`;
        return { ok: true, streamId: id };
      },

      onChatToken: (_streamId: string, callback: (token: unknown) => void) => {
        const tokens = [
          "Hello! ",
          "I'm running in ",
          "demo mode. ",
          "The Ollama backend ",
          "is not connected, ",
          "but I can show you ",
          "how the chat interface works.",
        ];
        let i = 0;
        const timer = setInterval(() => {
          if (i < tokens.length) {
            callback({ type: "token", content: tokens[i], done: false });
            i++;
          } else {
            callback({
              type: "done",
              content: "",
              done: true,
              model: "ministral",
              total_duration: 2500000000,
              eval_count: tokens.length,
            });
            clearInterval(timer);
          }
        }, 100);
        return () => clearInterval(timer);
      },
    };
  }

  // Shim window.mycelium
  if (!(window as unknown as Record<string, unknown>).mycelium) {
    const extractGist = (text: string): string => {
      const sentences = text
        .split(/[.!?]+/)
        .filter((s) => s.trim().length > 10);
      return sentences[0]?.trim() + "." || text.slice(0, 120);
    };

    const extractHighlightsShim = (text: string) => {
      return extractKeywords(text, 8).map((word: string, i: number) => ({
        text: word,
        priority: i < 2 ? "critical" : i < 5 ? "high" : "medium",
        context: "",
        category: "concept",
      }));
    };

    const shimDelay = (ms: number) => new Promise((r) => setTimeout(r, ms));

    (window as unknown as Record<string, unknown>).mycelium = {
      async synthesize(text: string, depth: string) {
        await shimDelay(300);
        const gist = extractGist(text);
        const highlights = extractHighlightsShim(text);
        const sentences = text
          .split(/[.!?]+/)
          .filter((s: string) => s.trim().length > 10);
        const n = depth === "espresso" ? 2 : depth === "americano" ? 4 : 7;
        const summary =
          sentences.slice(0, Math.min(n, sentences.length)).join(". ").trim() +
          ".";
        return {
          gist,
          highlights,
          summary,
          explanation: summary,
          analogy: "",
          compression_ratio: gist.length / Math.max(text.length, 1),
          depth,
          patterns: [],
          scaffolding_applied: [],
        };
      },
      async summarize(text: string, sentences: number) {
        await shimDelay(200);
        const s = text
          .split(/[.!?]+/)
          .filter((s: string) => s.trim().length > 10);
        return s.slice(0, sentences).join(". ").trim() + ".";
      },
      async simplify(text: string) {
        await shimDelay(200);
        return extractGist(text);
      },
      async keywords(text: string, topN: number) {
        await shimDelay(100);
        return extractHighlightsShim(text).slice(0, topN);
      },
      async explore(concept: string) {
        await shimDelay(150);
        return {
          concept,
          lens: {
            pattern: "flow",
            analogy: `Think of ${concept} as a river — data flows through it.`,
            eli5: `${concept} is like a helper that remembers things for you.`,
            visual_hint: "Picture a flowing stream.",
            when_useful: "When you need to understand how data moves.",
          },
          alternatives_available: 2,
        };
      },
      async tryDifferent(concept: string) {
        await shimDelay(150);
        return {
          concept,
          lens: {
            pattern: "spatial",
            analogy: `Picture ${concept} as a shelf — things are stored in specific spots.`,
            eli5: `${concept} is like a shelf next to you with things you use a lot.`,
            visual_hint: "Imagine a bookshelf with labeled sections.",
            when_useful: "When you need to understand structure.",
          },
          alternatives_available: 1,
        };
      },
      async eli5(concept: string) {
        await shimDelay(100);
        return `${concept} is like a magic box that helps you do things faster.`;
      },
      async feedback() {
        await shimDelay(50);
      },
      async setUser() {
        await shimDelay(50);
      },
      async setSensory() {
        await shimDelay(50);
        return "Profile updated.";
      },
      async concepts() {
        await shimDelay(50);
        return [
          "cache",
          "recursion",
          "database",
          "api",
          "encryption",
          "load_balancer",
          "queue",
          "pub_sub",
          "rate_limit",
          "leaderboard",
          "search_index",
          "hash_map",
          "tree",
          "graph",
          "middleware",
          "websocket",
        ];
      },
    };
  }

  // Shim window.tools
  if (!window.tools) {
    (window as unknown as Record<string, unknown>).tools = {
      executeTool: async () => ({
        ok: true,
        data: { result: "Demo tool execution complete" },
      }),
      planPreview: async () => ({
        ok: true,
        data: { steps: ["Step 1: Analyze", "Step 2: Plan", "Step 3: Execute"] },
      }),
      listTools: async () => ({
        ok: true,
        data: [
          { id: "mycelium", name: "Mycelium", status: "active" },
          { id: "rag", name: "RAG Query", status: "active" },
          { id: "pattern", name: "Pattern Engine", status: "active" },
        ],
      }),
    };
  }
}
