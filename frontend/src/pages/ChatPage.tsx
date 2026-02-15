import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { OllamaModel, OllamaToken } from "@/lib/grid-client";
import { ollamaClient } from "@/lib/grid-client";
import { cn } from "@/lib/utils";
import { appConfig } from "@/schema";
import { Bot, Circle, Loader2, RefreshCw, Send, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  model?: string;
  duration?: number;
  tokenCount?: number;
}

export function ChatPage() {
  const cfg = appConfig.chat;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedModel, setSelectedModel] = useState(cfg.defaultModel);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load available models on mount
  useEffect(() => {
    (async () => {
      const healthy = await ollamaClient.isHealthy();
      setOllamaOnline(healthy);
      if (healthy) {
        const list = await ollamaClient.listModels();
        setModels(list);
        // Auto-select first preferred model that exists
        const available = new Set(list.map((m) => m.name));
        const preferred = cfg.preferredModels.find((m) => available.has(m));
        if (preferred) setSelectedModel(preferred);
      }
    })();
  }, [cfg.preferredModels]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      model: selectedModel,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setIsStreaming(true);

    try {
      // Build messages array for Ollama
      const history = [
        { role: "system" as const, content: cfg.systemPrompt },
        ...messages.map((m) => ({ role: m.role, content: m.content })),
        { role: "user" as const, content: text },
      ];

      const handle = await ollamaClient.chat(selectedModel, history);
      const cleanup = handle.onToken((token: OllamaToken) => {
        if (token.type === "token" && token.content) {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              last.content += token.content;
            }
            return updated;
          });
        }
        if (token.type === "done") {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              last.model = token.model;
              last.duration = token.total_duration
                ? Math.round(token.total_duration / 1_000_000)
                : undefined;
              last.tokenCount = token.eval_count;
            }
            return updated;
          });
          setIsStreaming(false);
          cleanup();
        }
        if (token.type === "error") {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              last.content = `Error: ${token.error}`;
            }
            return updated;
          });
          setIsStreaming(false);
          cleanup();
        }
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === "assistant") {
          last.content = `Connection error: ${err instanceof Error ? err.message : String(err)}`;
        }
        return updated;
      });
      setIsStreaming(false);
    }
  }, [input, isStreaming, messages, selectedModel, cfg.systemPrompt]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-full flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{cfg.title}</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {cfg.description}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Model selector */}
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          >
            {models.length > 0 ? (
              models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))
            ) : (
              <option value={selectedModel}>{selectedModel}</option>
            )}
          </select>

          {/* Ollama status */}
          <Badge
            variant={ollamaOnline ? "success" : "warning"}
            className="gap-1.5"
          >
            <Circle
              className={cn(
                "h-2 w-2 fill-current",
                ollamaOnline ? "text-[var(--success)]" : "text-[var(--warning)]"
              )}
            />
            {ollamaOnline ? "Ollama Online" : "Ollama Offline"}
          </Badge>

          <Button
            variant="ghost"
            size="icon"
            onClick={clearChat}
            title="Clear chat"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1 pb-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-3">
              <Bot className="mx-auto h-12 w-12 text-[var(--muted-foreground)] opacity-40" />
              <p className="text-sm text-[var(--muted-foreground)]">
                Start a conversation with <strong>{selectedModel}</strong>
              </p>
              <p className="text-xs text-[var(--muted-foreground)] opacity-60">
                Running locally via Ollama — your data stays private
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3 px-2 py-3 rounded-lg",
              msg.role === "user" ? "bg-transparent" : "bg-[var(--card)]/50"
            )}
          >
            <div
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
                msg.role === "user"
                  ? "bg-[var(--primary)]"
                  : "bg-[var(--accent)]"
              )}
            >
              {msg.role === "user" ? (
                <User className="h-3.5 w-3.5 text-[var(--primary-foreground)]" />
              ) : (
                <Bot className="h-3.5 w-3.5 text-[var(--primary)]" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium">
                  {msg.role === "user" ? "You" : "GRID"}
                </span>
                {msg.model && (
                  <Badge variant="outline" className="text-[10px] py-0 px-1.5">
                    {msg.model}
                  </Badge>
                )}
                {msg.duration !== undefined && (
                  <span className="text-[10px] text-[var(--muted-foreground)]">
                    {msg.duration}ms
                  </span>
                )}
                {msg.tokenCount !== undefined && (
                  <span className="text-[10px] text-[var(--muted-foreground)]">
                    {msg.tokenCount} tokens
                  </span>
                )}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {msg.content}
                {msg.role === "assistant" && !msg.content && isStreaming && (
                  <span className="inline-flex items-center gap-1 text-[var(--muted-foreground)]">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Thinking…
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Input area */}
      <Card className="mt-auto shrink-0">
        <CardContent className="flex items-end gap-3 p-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={cfg.placeholder}
            rows={1}
            className="flex-1 resize-none rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm placeholder:text-[var(--muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] max-h-32"
            style={{ minHeight: "2.5rem" }}
          />
          <Button
            size="icon"
            onClick={sendMessage}
            disabled={!input.trim() || isStreaming || !ollamaOnline}
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
