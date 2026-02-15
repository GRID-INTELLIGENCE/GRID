import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { gridClient } from "@/lib/grid-client";
import { cn } from "@/lib/utils";
import { appConfig, getEndpoint } from "@/schema";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Clock,
  Database,
  FileText,
  Loader2,
  MessageSquare,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import { useCallback, useRef, useState } from "react";

interface RagSource {
  text: string;
  source: string;
  score: number;
  metadata?: Record<string, unknown>;
}

type StreamStage =
  | "idle"
  | "analysis_started"
  | "retrieval"
  | "documents_retrieved"
  | "answering"
  | "complete"
  | "error";

const stageLabels: Record<StreamStage, string> = {
  idle: "Ready",
  analysis_started: "Analyzing query…",
  retrieval: "Searching knowledge base…",
  documents_retrieved: "Documents found",
  answering: "Generating answer…",
  complete: "Complete",
  error: "Error",
};

const stageIcons: Record<
  StreamStage,
  React.ComponentType<{ className?: string }>
> = {
  idle: Search,
  analysis_started: Sparkles,
  retrieval: Database,
  documents_retrieved: BookOpen,
  answering: MessageSquare,
  complete: Zap,
  error: Zap,
};

export function RagQuery() {
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState<StreamStage>("idle");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<RagSource[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timings, setTimings] = useState<Record<string, number>>({});
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [showSources, setShowSources] = useState(true);
  const [conversationMode, setConversationMode] = useState(true);
  const [history, setHistory] = useState<
    { query: string; answer: string; sources: RagSource[]; timestamp: number }[]
  >([]);
  const answerRef = useRef<HTMLDivElement>(null);

  const handleStream = useCallback(async () => {
    const q = query.trim();
    if (!q || isStreaming) return;

    setIsStreaming(true);
    setAnswer("");
    setSources([]);
    setError(null);
    setTimings({});
    setStage("analysis_started");

    let fullAnswer = "";
    let collectedSources: RagSource[] = [];

    try {
      const handle = await gridClient.stream(
        "POST",
        getEndpoint(appConfig.rag.streamEndpointId),
        {
          query: q,
          session_id: conversationMode ? sessionId : undefined,
          top_k: 5,
          temperature: 0.7,
          enable_conversation: conversationMode,
          enable_multi_hop: true,
        }
      );

      handle.onChunk((chunk) => {
        if (chunk.type === "done") {
          setStage("complete");
          setIsStreaming(false);
          if (fullAnswer) {
            setHistory((prev) => [
              {
                query: q,
                answer: fullAnswer,
                sources: collectedSources,
                timestamp: Date.now(),
              },
              ...prev,
            ]);
          }
          return;
        }

        if (chunk.type === "error") {
          setError(chunk.error ?? "Stream error");
          setStage("error");
          setIsStreaming(false);
          return;
        }

        if (chunk.type === "chunk" && chunk.data) {
          const data = chunk.data as Record<string, unknown>;
          const eventType = data.type as string | undefined;

          switch (eventType) {
            case "analysis_started":
              setStage("analysis_started");
              break;
            case "retrieval":
              setStage("retrieval");
              break;
            case "documents_retrieved":
              setStage("documents_retrieved");
              if (Array.isArray(data.documents)) {
                collectedSources = (data.documents as RagSource[]).map((d) => ({
                  text: d.text ?? "",
                  source: d.source ?? "unknown",
                  score: d.score ?? 0,
                  metadata: d.metadata,
                }));
                setSources(collectedSources);
              }
              break;
            case "answer_chunk":
              setStage("answering");
              if (typeof data.content === "string") {
                fullAnswer += data.content;
                setAnswer(fullAnswer);
                answerRef.current?.scrollIntoView({
                  behavior: "smooth",
                  block: "end",
                });
              }
              break;
            case "complete":
              setStage("complete");
              if (data.timings && typeof data.timings === "object") {
                setTimings(data.timings as Record<string, number>);
              }
              break;
            default:
              // Handle text chunks (fallback)
              if (typeof data.content === "string") {
                fullAnswer += data.content;
                setAnswer(fullAnswer);
              }
          }
        }

        if (chunk.type === "text" && chunk.data) {
          fullAnswer += String(chunk.data);
          setAnswer(fullAnswer);
          setStage("answering");
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stream connection failed");
      setStage("error");
      setIsStreaming(false);
    }
  }, [query, isStreaming, sessionId, conversationMode]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleStream();
  };

  const StageIcon = stageIcons[stage];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {appConfig.rag.title}
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {appConfig.rag.description}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-[var(--muted-foreground)]">
            <input
              type="checkbox"
              checked={conversationMode}
              onChange={(e) => setConversationMode(e.target.checked)}
              className="rounded border-[var(--border)]"
            />
            Conversational
          </label>
          {stage !== "idle" && (
            <Badge
              variant={
                stage === "complete"
                  ? "success"
                  : stage === "error"
                    ? "destructive"
                    : "secondary"
              }
              className="gap-1.5"
            >
              <StageIcon className="h-3 w-3" />
              {stageLabels[stage]}
            </Badge>
          )}
        </div>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={appConfig.rag.placeholder}
            className="pl-10"
          />
        </div>
        <Button type="submit" disabled={isStreaming || !query.trim()}>
          {isStreaming ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            appConfig.rag.submitLabel
          )}
        </Button>
      </form>

      {/* Streaming progress indicators */}
      {isStreaming && (
        <div className="flex items-center gap-3">
          {(
            [
              "analysis_started",
              "retrieval",
              "documents_retrieved",
              "answering",
            ] as StreamStage[]
          ).map((s, i) => {
            const active = stage === s;
            const done =
              [
                "analysis_started",
                "retrieval",
                "documents_retrieved",
                "answering",
              ].indexOf(stage) > i;
            return (
              <div key={s} className="flex items-center gap-1.5">
                <div
                  className={cn(
                    "h-2 w-2 rounded-full transition-colors",
                    active
                      ? "bg-[var(--primary)] animate-pulse"
                      : done
                        ? "bg-[var(--primary)]"
                        : "bg-[var(--muted)]"
                  )}
                />
                <span
                  className={cn(
                    "text-[10px]",
                    active
                      ? "text-[var(--foreground)] font-medium"
                      : "text-[var(--muted-foreground)]"
                  )}
                >
                  {stageLabels[s].replace("…", "")}
                </span>
                {i < 3 && <div className="h-px w-4 bg-[var(--border)]" />}
              </div>
            );
          })}
        </div>
      )}

      {/* Streaming answer */}
      {(answer || isStreaming) && (
        <Card className="border-[var(--primary)]/20 glow-primary">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-[var(--primary)]" />
              Answer
              {isStreaming && stage === "answering" && (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--muted-foreground)]" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              ref={answerRef}
              className="text-sm leading-relaxed whitespace-pre-wrap"
            >
              {answer}
              {isStreaming && !answer && (
                <span className="text-[var(--muted-foreground)] animate-pulse">
                  Waiting for response…
                </span>
              )}
            </div>
            {/* Timing badges */}
            {Object.keys(timings).length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5 border-t border-[var(--border)] pt-3">
                <Clock className="h-3.5 w-3.5 text-[var(--muted-foreground)]" />
                {Object.entries(timings).map(([key, val]) => (
                  <Badge
                    key={key}
                    variant="outline"
                    className="text-[10px] font-mono"
                  >
                    {key}:{" "}
                    {typeof val === "number"
                      ? `${val.toFixed(0)}ms`
                      : String(val)}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-2 text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            {showSources ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
            Sources ({sources.length})
          </button>
          {showSources &&
            sources.map((src, i) => (
              <Card key={i} className="glass">
                <CardContent className="flex items-start gap-3 p-4">
                  <FileText className="mt-0.5 h-4 w-4 shrink-0 text-[var(--primary)]" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium truncate">
                        {src.source}
                      </span>
                      <Badge variant="outline" className="shrink-0">
                        {(src.score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)] line-clamp-3">
                      {src.text}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <Card className="border-[var(--destructive)]/30">
          <CardContent className="p-4">
            <p className="text-sm text-[var(--destructive)]">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Conversation history */}
      {history.length > 0 && (
        <div className="space-y-3 border-t border-[var(--border)] pt-4">
          <h3 className="text-sm font-medium text-[var(--muted-foreground)]">
            Previous queries ({history.length})
          </h3>
          {history.map((entry) => (
            <Card key={entry.timestamp} className="glass">
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-[var(--primary)]">
                    Q:{" "}
                    {entry.query.length > 100
                      ? `${entry.query.slice(0, 100)}…`
                      : entry.query}
                  </p>
                  <span className="text-[10px] text-[var(--muted-foreground)]">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-[var(--muted-foreground)] line-clamp-4 whitespace-pre-wrap">
                  {entry.answer}
                </p>
                {entry.sources.length > 0 && (
                  <p className="text-[10px] text-[var(--muted-foreground)]">
                    {entry.sources.length} source
                    {entry.sources.length > 1 ? "s" : ""} referenced
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
