import { DepthControl } from "@/components/mycelium/DepthControl";
import { FeedbackBar } from "@/components/mycelium/FeedbackBar";
import { LensCard } from "@/components/mycelium/LensCard";
import { OutputDisplay } from "@/components/mycelium/OutputDisplay";
import { SensoryPicker } from "@/components/mycelium/SensoryPicker";
import { Button } from "@/components/ui/button";
import { useMycelium } from "@/hooks/use-mycelium";
import { cn } from "@/lib/utils";
import {
  ChevronRight,
  Loader2,
  Search,
  Settings2,
  Sparkles,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export function MyceliumPage() {
  const {
    input,
    result,
    depth,
    sensoryProfile,
    isProcessing,
    exploredConcept,
    concepts,
    error,
    setInput,
    setDepth,
    setSensory,
    synthesize,
    feedback,
    explore,
    tryDifferent,
    clearExplored,
    loadConcepts,
    clear,
  } = useMycelium();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [conceptSearch, setConceptSearch] = useState("");
  const [showConceptPanel, setShowConceptPanel] = useState(false);

  // Load available concepts on mount
  useEffect(() => {
    loadConcepts();
  }, [loadConcepts]);

  // Auto-resize textarea
  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      const el = e.target;
      requestAnimationFrame(() => {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 320) + "px";
      });
    },
    [setInput]
  );

  // Keyboard shortcut: Ctrl+Enter to synthesize
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        synthesize();
      }
    },
    [synthesize]
  );

  // Click a keyword → explore it as a concept
  const handleKeywordClick = useCallback(
    (keyword: string) => {
      explore(keyword);
    },
    [explore]
  );

  // P1.3: Memoize filtered concepts
  const filteredConcepts = useMemo(
    () =>
      concepts.filter((c) =>
        c.toLowerCase().includes(conceptSearch.toLowerCase())
      ),
    [concepts, conceptSearch]
  );

  // P4.4: Word count + reading time
  const inputStats = useMemo(() => {
    if (!input.length) return null;
    const words = input.trim().split(/\s+/).filter(Boolean).length;
    const readingMinutes = Math.max(1, Math.ceil(words / 238));
    return { chars: input.length, words, readingMinutes };
  }, [input]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Page header — minimal */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">
            Mycelium
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Paste text. Get the essence.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DepthControl
            value={depth}
            onChange={setDepth}
            disabled={isProcessing}
          />
          <button
            type="button"
            onClick={() => setShowSettings((s) => !s)}
            aria-label="Accessibility settings"
            aria-expanded={showSettings}
            className={cn(
              "rounded-lg border border-[var(--border)] p-2 transition-colors",
              "hover:bg-[var(--accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
              "cursor-pointer",
              showSettings && "bg-[var(--accent)] text-[var(--foreground)]"
            )}
          >
            <Settings2 className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Settings panel — progressive disclosure */}
      {showSettings && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
              Sensory Profile
            </h2>
            <button
              type="button"
              onClick={() => setShowSettings(false)}
              aria-label="Close settings"
              className="rounded p-0.5 text-[var(--muted-foreground)] hover:text-[var(--foreground)] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <SensoryPicker value={sensoryProfile} onChange={setSensory} />
        </div>
      )}

      {/* Input area */}
      <div className="space-y-3">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Paste or type any text here..."
            aria-label="Text to synthesize"
            rows={4}
            className={cn(
              "w-full resize-none rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3",
              "text-sm leading-relaxed text-[var(--foreground)] placeholder:text-[var(--muted-foreground)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
              "transition-colors"
            )}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              onClick={synthesize}
              disabled={!input.trim() || isProcessing}
              size="default"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Sparkles className="h-4 w-4" aria-hidden="true" />
              )}
              {isProcessing ? "Synthesizing..." : "Synthesize"}
            </Button>

            {input.trim() && (
              <button
                type="button"
                onClick={clear}
                aria-label="Clear input and results"
                className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] rounded px-2 py-1"
              >
                Clear
              </button>
            )}
          </div>

          <span className="text-xs text-[var(--muted-foreground)]">
            {inputStats
              ? `${inputStats.chars.toLocaleString()} chars · ${inputStats.words.toLocaleString()} words · ${inputStats.readingMinutes} min read`
              : "Ctrl+Enter to synthesize"}
          </span>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--destructive)]/30 bg-[var(--destructive)]/10 px-4 py-3 text-sm text-[var(--destructive)]"
        >
          {error}
        </div>
      )}

      {/* Output — appears after synthesis */}
      {result && (
        <div className="space-y-4">
          <OutputDisplay result={result} onKeywordClick={handleKeywordClick} />

          {/* Feedback bar */}
          <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
            <FeedbackBar
              onSimpler={() => feedback(true, false)}
              onDeeper={() => feedback(false, true)}
              disabled={isProcessing}
            />
            <button
              type="button"
              onClick={() => setShowConceptPanel((s) => !s)}
              aria-label="Explore concepts"
              aria-expanded={showConceptPanel}
              className={cn(
                "inline-flex items-center gap-1 text-xs text-[var(--muted-foreground)]",
                "hover:text-[var(--foreground)] transition-colors cursor-pointer",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] rounded px-2 py-1"
              )}
            >
              <Search className="h-3 w-3" aria-hidden="true" />
              Explore concepts
              <ChevronRight
                className={cn(
                  "h-3 w-3 transition-transform",
                  showConceptPanel && "rotate-90"
                )}
                aria-hidden="true"
              />
            </button>
          </div>
        </div>
      )}

      {/* Concept explorer — opened by keyword click or explicit toggle */}
      {exploredConcept && (
        <LensCard
          result={exploredConcept}
          onTryDifferent={() => tryDifferent(exploredConcept.concept)}
          onClose={clearExplored}
        />
      )}

      {/* Concept browser panel */}
      {showConceptPanel && !exploredConcept && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
              Concept Library
            </h2>
            <button
              type="button"
              onClick={() => setShowConceptPanel(false)}
              aria-label="Close concept library"
              className="rounded p-0.5 text-[var(--muted-foreground)] hover:text-[var(--foreground)] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <input
            type="search"
            value={conceptSearch}
            onChange={(e) => setConceptSearch(e.target.value)}
            placeholder="Search concepts..."
            aria-label="Search concepts"
            className={cn(
              "w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-1.5",
              "text-sm placeholder:text-[var(--muted-foreground)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            )}
          />

          <div
            className="flex flex-wrap gap-1.5"
            role="list"
            aria-label="Available concepts"
          >
            {filteredConcepts.map((concept) => (
              <button
                key={concept}
                type="button"
                role="listitem"
                onClick={() => {
                  explore(concept);
                  setShowConceptPanel(false);
                }}
                className={cn(
                  "rounded-full border border-[var(--border)] px-3 py-1 text-xs font-medium",
                  "text-[var(--muted-foreground)] transition-all cursor-pointer",
                  "hover:border-[var(--primary)]/30 hover:text-[var(--foreground)] hover:bg-[var(--accent)]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
                )}
              >
                {concept.replace(/_/g, " ")}
              </button>
            ))}
            {filteredConcepts.length === 0 && (
              <p className="text-xs text-[var(--muted-foreground)] py-2">
                No concepts match &ldquo;{conceptSearch}&rdquo;
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
