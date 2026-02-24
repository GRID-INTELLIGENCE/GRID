import { cn } from "@/lib/utils";
import type { SynthesisResult } from "@/types/mycelium";
import { Check, ChevronRight, Copy } from "lucide-react";
import { useCallback, useId, useState } from "react";
import { HighlightPill } from "./HighlightPill";

interface OutputDisplayProps {
  result: SynthesisResult;
  onKeywordClick?: (keyword: string) => void;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border border-[var(--border)] px-2 py-1",
        "text-[10px] font-medium text-[var(--muted-foreground)] transition-all",
        "hover:border-[var(--primary)]/40 hover:text-[var(--foreground)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
        "cursor-pointer",
        copied && "border-green-500/40 text-green-500"
      )}
    >
      {copied ? (
        <Check className="h-3 w-3" aria-hidden="true" />
      ) : (
        <Copy className="h-3 w-3" aria-hidden="true" />
      )}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

/** Animated SVG arc gauge for compression ratio */
function CompressionGauge({ ratio }: { ratio: number }) {
  const pct = Math.round(ratio * 100);
  const radius = 14;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - ratio);

  return (
    <svg
      width="36"
      height="36"
      viewBox="0 0 36 36"
      aria-hidden="true"
      className="shrink-0"
    >
      <circle
        cx="18"
        cy="18"
        r={radius}
        fill="none"
        stroke="var(--muted)"
        strokeWidth="3"
      />
      <circle
        cx="18"
        cy="18"
        r={radius}
        fill="none"
        stroke="var(--primary)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 18 18)"
        style={{
          transition:
            "stroke-dashoffset 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)",
        }}
      />
      <text
        x="18"
        y="18"
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--muted-foreground)"
        fontSize="8"
        fontWeight="600"
      >
        {pct}%
      </text>
    </svg>
  );
}

export function OutputDisplay({ result, onKeywordClick }: OutputDisplayProps) {
  const [expanded, setExpanded] = useState(false);
  const explanationId = useId();

  return (
    <div className="space-y-4" role="region" aria-label="Synthesis result">
      {/* Gist — staggered fade-in, the most important thing */}
      <div className="animate-fade-in" aria-live="polite" aria-atomic="true">
        <div className="flex items-start justify-between gap-3">
          <p className="text-lg font-medium leading-relaxed text-[var(--foreground)]">
            {result.gist}
          </p>
          <CopyButton text={result.gist} />
        </div>
      </div>

      {/* Compression badge with animated arc gauge */}
      <div
        className="flex items-center gap-3 text-xs text-[var(--muted-foreground)] animate-fade-in"
        style={{ animationDelay: "100ms", animationFillMode: "backwards" }}
      >
        <CompressionGauge ratio={result.compression_ratio} />
        <div className="flex flex-col gap-0.5">
          <span>
            Compressed to {Math.round(result.compression_ratio * 100)}% of
            original
          </span>
          {result.patterns.length > 0 && (
            <span className="text-[var(--muted-foreground)]/70">
              {result.patterns.join(", ")} detected
            </span>
          )}
        </div>
      </div>

      {/* Highlights — staggered entrance */}
      {result.highlights.length > 0 && (
        <div
          className="space-y-2 animate-fade-in"
          style={{ animationDelay: "200ms", animationFillMode: "backwards" }}
        >
          <h3 className="text-xs font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
            Key Points
          </h3>
          <div
            className="flex flex-wrap gap-1.5"
            role="list"
            aria-label="Keywords"
          >
            {result.highlights.map((h, i) => (
              <div key={`${h.text}-${i}`} role="listitem">
                <HighlightPill
                  highlight={h}
                  onClick={() => onKeywordClick?.(h.text)}
                  index={i}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary — staggered after highlights */}
      {result.summary && (
        <div
          className="space-y-1.5 animate-fade-in"
          style={{ animationDelay: "300ms", animationFillMode: "backwards" }}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
              Summary
            </h3>
            <CopyButton text={result.summary} />
          </div>
          <p className="text-sm leading-relaxed text-[var(--foreground)]/80">
            {result.summary}
          </p>
        </div>
      )}

      {/* Expandable explanation — progressive disclosure */}
      {result.explanation && result.explanation !== result.summary && (
        <div>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            aria-expanded={expanded}
            aria-controls={explanationId}
            className={cn(
              "flex items-center gap-1.5 text-xs font-medium text-[var(--muted-foreground)]",
              "hover:text-[var(--foreground)] transition-colors cursor-pointer",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] rounded"
            )}
          >
            <ChevronRight
              className={cn(
                "h-3.5 w-3.5 transition-transform",
                expanded && "rotate-90"
              )}
              aria-hidden="true"
            />
            {expanded ? "Hide" : "Show"} full explanation
          </button>

          {expanded && (
            <div
              id={explanationId}
              className="mt-3 rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 text-sm leading-relaxed animate-fade-in"
            >
              {result.explanation}

              {result.analogy && (
                <div className="mt-3 border-t border-[var(--border)] pt-3 text-[var(--muted-foreground)] italic">
                  {result.analogy}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
