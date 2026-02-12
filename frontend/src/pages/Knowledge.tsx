import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useRagStats,
  useSessionDelete,
  useSessionLookup,
  useSignalQuality,
} from "@/hooks";
import { cn } from "@/lib/utils";
import type { RagSession } from "@/types/api";
import {
  Database,
  Folder,
  Loader2,
  MessageSquare,
  RefreshCw,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";

export function Knowledge() {
  const [sessionIdInput, setSessionIdInput] = useState("");
  const [sessionDetail, setSessionDetail] = useState<RagSession | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);

  const stats = useRagStats();
  const signalQuality = useSignalQuality();
  const sessionLookup = useSessionLookup();
  const sessionDelete = useSessionDelete();

  const statsData = stats.data;
  const signalData = signalQuality.data;

  const lookupSession = () => {
    if (!sessionIdInput.trim()) return;
    setSessionError(null);
    setSessionDetail(null);
    sessionLookup.mutate(sessionIdInput.trim(), {
      onSuccess(res) {
        if (res.ok && res.data) {
          setSessionDetail(res.data);
        } else {
          setSessionError(res.error ?? "Session not found");
        }
      },
      onError(err) {
        setSessionError(err instanceof Error ? err.message : "Lookup failed");
      },
    });
  };

  const deleteSession = (id: string) => {
    sessionDelete.mutate(id, {
      onSuccess() {
        setSessionDetail(null);
        setSessionIdInput("");
        stats.refetch();
      },
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            RAG system statistics, conversation sessions, and knowledge quality
            metrics
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            stats.refetch();
            signalQuality.refetch();
          }}
        >
          <RefreshCw
            className={cn(
              "mr-1.5 h-3.5 w-3.5",
              stats.isFetching && "animate-spin"
            )}
          />
          Refresh
        </Button>
      </div>

      {/* RAG engine info + conversation stats row */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Engine info */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Database className="h-4 w-4 text-[var(--primary)]" />
              RAG Engine
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {statsData?.engine_info ? (
              <>
                {statsData.engine_info.model && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      LLM Model
                    </span>
                    <Badge variant="outline">
                      {String(statsData.engine_info.model)}
                    </Badge>
                  </div>
                )}
                {statsData.engine_info.embedding_model && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      Embedding
                    </span>
                    <span className="text-[10px] font-mono">
                      {String(statsData.engine_info.embedding_model)}
                    </span>
                  </div>
                )}
                {statsData.engine_info.vector_store && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      Vector Store
                    </span>
                    <Badge variant="secondary">
                      {String(statsData.engine_info.vector_store)}
                    </Badge>
                  </div>
                )}
                {/* Render any extra engine info */}
                {Object.entries(statsData.engine_info)
                  .filter(
                    ([k]) =>
                      !["model", "embedding_model", "vector_store"].includes(k)
                  )
                  .map(([key, val]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-[var(--muted-foreground)] capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="font-mono text-[10px]">
                        {String(val)}
                      </span>
                    </div>
                  ))}
              </>
            ) : stats.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                RAG engine offline
              </p>
            )}
          </CardContent>
        </Card>

        {/* Conversation stats */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <MessageSquare className="h-4 w-4 text-[var(--primary)]" />
              Conversations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {statsData?.conversation_stats ? (
              <>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--muted-foreground)]">
                    Active sessions
                  </span>
                  <span className="font-bold">
                    {String(statsData.conversation_stats.active_sessions ?? 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--muted-foreground)]">
                    Total conversations
                  </span>
                  <span className="font-bold">
                    {String(
                      statsData.conversation_stats.total_conversations ?? 0
                    )}
                  </span>
                </div>
                {Object.entries(statsData.conversation_stats)
                  .filter(
                    ([k]) =>
                      !["active_sessions", "total_conversations"].includes(k)
                  )
                  .map(([key, val]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-[var(--muted-foreground)] capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="font-mono text-[10px]">
                        {String(val)}
                      </span>
                    </div>
                  ))}
              </>
            ) : stats.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                No conversation data
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Signal quality */}
      {signalData && (
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="h-4 w-4 text-[var(--primary)]" />
              Knowledge Signal Quality (NSR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded bg-[var(--muted)] p-3 text-[10px] overflow-auto max-h-40">
              {JSON.stringify(signalData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Session lookup */}
      <Card className="glass">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Folder className="h-4 w-4 text-[var(--primary)]" />
            Session Lookup
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <input
              value={sessionIdInput}
              onChange={(e) => setSessionIdInput(e.target.value)}
              placeholder="Enter session ID…"
              className="flex-1 rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm placeholder:text-[var(--muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
              onKeyDown={(e) => e.key === "Enter" && lookupSession()}
            />
            <Button
              onClick={lookupSession}
              disabled={sessionLookup.isPending || !sessionIdInput.trim()}
            >
              {sessionLookup.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Lookup"
              )}
            </Button>
          </div>

          {sessionError && (
            <p className="text-xs text-[var(--destructive)]">{sessionError}</p>
          )}

          {sessionDetail && (
            <div className="rounded-md bg-[var(--muted)] p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium">
                  Session: {sessionDetail.session_id}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-[var(--destructive)]"
                  onClick={() => deleteSession(sessionDetail.session_id)}
                  title="Delete session"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
              {sessionDetail.turn_count !== undefined && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--muted-foreground)]">Turns</span>
                  <span className="font-mono">{sessionDetail.turn_count}</span>
                </div>
              )}
              {sessionDetail.metadata &&
                Object.keys(sessionDetail.metadata).length > 0 && (
                  <pre className="text-[10px] overflow-auto">
                    {JSON.stringify(sessionDetail.metadata, null, 2)}
                  </pre>
                )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
