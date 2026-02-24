import { useCallback, useEffect, useRef, useState } from "react";
import { Compass, Loader2, Play, Sparkles, Users } from "lucide-react";

/* ──────────────────────────────────────────────────────────────────
 * Types
 * ────────────────────────────────────────────────────────────────── */

type Status = "idle" | "running" | "done" | "error";

interface Party {
  name: string;
  kind: string;
  title: string;
  primary_goal: string;
}

interface DiscussionEntry {
  speaker: string;
  text: string;
}

interface MagnitudinalCompass {
  direction: string;
  reasoning: string;
  confidence: number;
  key_factors: string[];
}

/* ──────────────────────────────────────────────────────────────────
 * Mock LLM simulation (runs locally — no API calls)
 * Replace with real ApiClient calls when backend endpoint is ready.
 * ────────────────────────────────────────────────────────────────── */

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function fetchParties(topic: string): Promise<Party[]> {
  await delay(1200);
  return [
    {
      name: "Dr. Lena Vasquez",
      kind: "person",
      title: "Chief Systems Architect",
      primary_goal: "Ensure scalable directional alignment for " + topic,
    },
    {
      name: "Audit Trail Subsystem",
      kind: "system",
      title: "Data Provenance Engine",
      primary_goal: "Uphold data integrity across every boundary",
    },
    {
      name: "Developer Experience",
      kind: "concept",
      title: "Usability Advocate",
      primary_goal: "Protect accessibility as complexity grows",
    },
    {
      name: "Raj Patel",
      kind: "person",
      title: "Security & Compliance Officer",
      primary_goal: "Maintain safety boundaries and regulatory compliance",
    },
  ];
}

async function fetchAmbiance(topic: string): Promise<string> {
  await delay(900);
  return `A circular holographic chamber materialises — four translucent seats arranged in perfect symmetry around a slowly rotating 3D projection of "${topic}". Ambient indigo light pulses along the edges. No seat is elevated; every position holds equal weight. The mood is deliberate, focused, and soulful — a space built for transparent reasoning, not performance.`;
}

async function fetchStatement(
  party: Party,
  _topic: string,
  _ambiance: string
): Promise<string> {
  await delay(800 + Math.random() * 600);

  const statements: Record<string, string> = {
    "Dr. Lena Vasquez":
      "The directive compass must encode scalability constraints directly into our architecture. Every new magnitude — whether external providers, federation layers, or distribution channels — needs a compatibility gate. I propose a Magnitudinal Compatibility Index: if an integration can't prove it preserves local-first guarantees, it doesn't ship. Growth without principle is just entropy.",
    "Audit Trail Subsystem":
      "As a data provenance engine, my concern is traceable causality. Every decision that passes through GRID's compass must carry a cryptographic audit signature — who requested it, what data informed it, and what confidence level the system assigned. Without signed provenance chains at every boundary crossing, the compass heading becomes unverifiable.",
    "Developer Experience":
      "Magnitude is meaningless if developers can't navigate the system. Every expansion adds cognitive load. I advocate for progressive disclosure: new magnitudes are opt-in, surfaced only when context demands them. The default experience must remain simple, fast, and transparent. Complexity is earned, never imposed. The compass must point toward usability as much as capability.",
    "Raj Patel":
      "Every compass heading creates a new attack surface. The safety boundaries we've built — security contracts, validation layers, audit trails — are non-negotiable. No direction is approved without a corresponding threat model and boundary test suite. If we can't test it, we can't ship it. Security is the compass's true north.",
  };
  return (
    statements[party.name] ??
    `As ${party.title}, I believe the directive compass must account for ${party.primary_goal.toLowerCase()}.`
  );
}

async function fetchCompass(
  _topic: string,
  _history: DiscussionEntry[]
): Promise<MagnitudinalCompass> {
  await delay(1400);
  return {
    direction:
      "Adopt a phased magnitudinal expansion with mandatory compatibility gates at every boundary — growth is gated by safety, provenance, usability, and architectural integrity.",
    reasoning:
      "All four parties converge on gated expansion: the architect demands compatibility indices, the provenance engine requires signed audit chains, the usability advocate insists on progressive disclosure, and security mandates threat models. The common thread is that no direction ships ungated.",
    confidence: 0.94,
    key_factors: [
      "Magnitudinal Compatibility Index",
      "Signed provenance chains",
      "Progressive disclosure model",
      "Security-gated compass headings",
    ],
  };
}

/* ──────────────────────────────────────────────────────────────────
 * Sub-components
 * ────────────────────────────────────────────────────────────────── */

/* ── Party node in the visual view ──────────────────────────────── */
function PartyNode({
  party,
  index,
  total,
  isActive,
}: {
  party: Party;
  index: number;
  total: number;
  isActive: boolean;
}) {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
  const radius = 38; // % from center
  const x = 50 + radius * Math.cos(angle);
  const y = 50 + radius * Math.sin(angle);

  const kindColors: Record<string, string> = {
    person: "border-indigo-400/60 bg-indigo-950/40",
    system: "border-cyan-400/60 bg-cyan-950/40",
    concept: "border-violet-400/60 bg-violet-950/40",
    object: "border-amber-400/60 bg-amber-950/40",
    organisation: "border-emerald-400/60 bg-emerald-950/40",
    data_entity: "border-rose-400/60 bg-rose-950/40",
  };

  const kindDotColors: Record<string, string> = {
    person: "bg-indigo-400",
    system: "bg-cyan-400",
    concept: "bg-violet-400",
    object: "bg-amber-400",
    organisation: "bg-emerald-400",
    data_entity: "bg-rose-400",
  };

  return (
    <div
      className={`absolute flex flex-col items-center transition-all duration-700 ease-out ${
        isActive ? "animate-pulse-slow" : ""
      }`}
      style={{
        left: `${x}%`,
        top: `${y}%`,
        transform: "translate(-50%, -50%)",
        opacity: 1,
        animation: `fade-scale-in 0.6s ease-out ${index * 0.15}s both`,
      }}
    >
      <div
        className={`flex h-16 w-16 items-center justify-center rounded-full border-2 backdrop-blur-sm ${
          kindColors[party.kind] ?? "border-slate-400/60 bg-slate-950/40"
        } ${isActive ? "shadow-lg shadow-indigo-500/20" : ""}`}
      >
        <span className="text-lg font-bold text-slate-100">
          {party.name.charAt(0)}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-1.5">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            kindDotColors[party.kind] ?? "bg-slate-400"
          }`}
        />
        <span className="text-xs font-medium text-slate-300 max-w-[7rem] truncate">
          {party.name}
        </span>
      </div>
      <span className="text-[0.65rem] text-slate-500 max-w-[8rem] truncate text-center">
        {party.title}
      </span>
    </div>
  );
}

/* ── Discussion entry in the feed ───────────────────────────────── */
function DiscussionBlock({ entry }: { entry: DiscussionEntry }) {
  return (
    <div
      className="rounded-lg border border-slate-700/50 bg-slate-900/60 p-4 backdrop-blur-sm"
      style={{ animation: "fade-slide-up 0.4s ease-out both" }}
    >
      <div className="mb-2 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-900/50 text-xs font-bold text-indigo-300">
          {entry.speaker.charAt(0)}
        </div>
        <span className="text-sm font-semibold text-slate-200">
          {entry.speaker}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-slate-400">{entry.text}</p>
    </div>
  );
}

/* ── Compass result block ───────────────────────────────────────── */
function CompassBlock({ compass }: { compass: MagnitudinalCompass }) {
  return (
    <div
      className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/60 to-slate-950/80 p-5 backdrop-blur-sm"
      style={{ animation: "fade-scale-in 0.6s ease-out both" }}
    >
      <div className="mb-3 flex items-center gap-2">
        <Compass className="h-5 w-5 text-indigo-400" />
        <span className="text-sm font-bold uppercase tracking-wider text-indigo-300">
          Magnitudinal Compass
        </span>
        <span className="ml-auto rounded-full bg-indigo-900/50 px-2.5 py-0.5 text-xs font-semibold text-indigo-300">
          {(compass.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
      <p className="mb-3 text-sm font-medium leading-relaxed text-slate-200">
        {compass.direction}
      </p>
      <p className="mb-3 text-xs leading-relaxed text-slate-400">
        {compass.reasoning}
      </p>
      {compass.key_factors.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {compass.key_factors.map((f, i) => (
            <span
              key={i}
              className="rounded-md bg-slate-800/60 px-2 py-0.5 text-xs text-slate-400"
            >
              {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
 * Main Page Component
 * ────────────────────────────────────────────────────────────────── */

export function RoundTablePage() {
  /* state */
  const [topic, setTopic] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [stepMsg, setStepMsg] = useState("");
  const [parties, setParties] = useState<Party[]>([]);
  const [ambiance, setAmbiance] = useState("");
  const [history, setHistory] = useState<DiscussionEntry[]>([]);
  const [compass, setCompass] = useState<MagnitudinalCompass | null>(null);
  const [activeParty, setActiveParty] = useState<string | null>(null);

  const feedRef = useRef<HTMLDivElement>(null);

  /* auto-scroll feed */
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [history, compass]);

  /* execution loop */
  const runSimulation = useCallback(async () => {
    if (!topic.trim()) return;

    // Reset
    setStatus("running");
    setHistory([]);
    setAmbiance("");
    setCompass(null);
    setParties([]);
    setActiveParty(null);

    try {
      // Phase 1 — Parties
      setStepMsg("Inferring parties…");
      const inferredParties = await fetchParties(topic);
      setParties(inferredParties);

      // Phase 2 — Ambiance
      setStepMsg("Constructing environment…");
      const setting = await fetchAmbiance(topic);
      setAmbiance(setting);

      // Phase 3 — Discussion (sequential, one at a time)
      for (const party of inferredParties) {
        setStepMsg(`${party.name} is speaking…`);
        setActiveParty(party.name);
        const statement = await fetchStatement(party, topic, setting);
        setHistory((prev) => [
          ...prev,
          { speaker: party.name, text: statement },
        ]);
      }
      setActiveParty(null);

      // Phase 4 — Compass
      setStepMsg("Calculating magnitudinal compass…");
      const compassResult = await fetchCompass(topic, history);
      setCompass(compassResult);

      setStepMsg("");
      setStatus("done");
    } catch {
      setStatus("error");
      setStepMsg("An error occurred during the session.");
    }
  }, [topic, history]);

  const isLocked = status === "running";

  return (
    <div className="flex h-[calc(100vh-3.5rem)] gap-0 overflow-hidden animate-fade-in">
      {/* ── LEFT: Visual Observation View ──────────────────────── */}
      <div className="relative flex w-1/2 flex-col items-center justify-center border-r border-slate-800/50 bg-gradient-to-b from-slate-950 to-slate-900">
        {/* Center ambiance node */}
        <div className="relative h-[70vh] w-full max-w-[500px]">
          {/* Center circle */}
          <div
            className={`absolute left-1/2 top-1/2 flex h-36 w-36 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-indigo-500/20 bg-indigo-950/20 backdrop-blur-sm transition-all duration-500 ${
              isLocked ? "shadow-lg shadow-indigo-500/10" : ""
            }`}
          >
            {status === "idle" && (
              <Sparkles className="h-8 w-8 text-indigo-500/40" />
            )}
            {isLocked && (
              <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
            )}
            {status === "done" && (
              <Compass className="h-8 w-8 text-indigo-400" />
            )}
          </div>

          {/* Connection lines */}
          {parties.length > 0 && (
            <svg
              className="pointer-events-none absolute inset-0 h-full w-full"
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
            >
              {parties.map((_, i) => {
                const angle = (i / parties.length) * 2 * Math.PI - Math.PI / 2;
                const r = 38;
                const x = 50 + r * Math.cos(angle);
                const y = 50 + r * Math.sin(angle);
                return (
                  <line
                    key={i}
                    x1="50"
                    y1="50"
                    x2={x}
                    y2={y}
                    stroke="oklch(0.65 0.19 252 / 0.15)"
                    strokeWidth="0.3"
                    strokeDasharray="1 1"
                  />
                );
              })}
            </svg>
          )}

          {/* Party nodes */}
          {parties.map((party, i) => (
            <PartyNode
              key={party.name}
              party={party}
              index={i}
              total={parties.length}
              isActive={activeParty === party.name}
            />
          ))}
        </div>

        {/* Ambiance text */}
        {ambiance && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950 to-transparent px-6 pb-5 pt-10">
            <p className="text-center text-xs leading-relaxed text-slate-500 italic">
              {ambiance}
            </p>
          </div>
        )}

        {/* Step indicator */}
        {stepMsg && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 rounded-full bg-indigo-950/60 px-4 py-1.5 backdrop-blur-sm">
            <span className="flex items-center gap-2 text-xs font-medium text-indigo-300">
              <Loader2 className="h-3 w-3 animate-spin" />
              {stepMsg}
            </span>
          </div>
        )}
      </div>

      {/* ── RIGHT: Interaction Feed ────────────────────────────── */}
      <div className="flex w-1/2 flex-col bg-slate-950">
        {/* Header / Input bar */}
        <div className="flex shrink-0 items-center gap-3 border-b border-slate-800/50 px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-900/30">
            <Users className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mr-auto">
            <h1 className="text-sm font-bold text-slate-200">
              Digital Round Table
            </h1>
            <p className="text-xs text-slate-500">
              DRTP — Governed by GRID Autonomy
            </p>
          </div>
          {status === "done" && (
            <span className="rounded-full bg-emerald-900/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
              Complete
            </span>
          )}
        </div>

        {/* Topic input */}
        <div className="flex shrink-0 items-center gap-2 border-b border-slate-800/30 px-5 py-3">
          <input
            type="text"
            placeholder="Enter the topic for discussion…"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={isLocked}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isLocked) runSimulation();
            }}
            className="h-9 flex-1 rounded-lg border border-slate-700/50 bg-slate-900/50 px-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-500/50 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={runSimulation}
            disabled={isLocked || !topic.trim()}
            className="flex h-9 items-center gap-1.5 rounded-lg bg-indigo-600 px-4 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLocked ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            {isLocked ? "Running" : "Start"}
          </button>
        </div>

        {/* Discussion feed */}
        <div
          ref={feedRef}
          className="flex-1 space-y-3 overflow-y-auto px-5 py-4"
        >
          {/* Idle state */}
          {status === "idle" && history.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <Sparkles className="mx-auto mb-3 h-10 w-10 text-slate-700" />
                <p className="text-sm text-slate-600">
                  Enter a topic to convene the round table
                </p>
                <p className="mt-1 text-xs text-slate-700">
                  All parties hold equal standing — transparent reasoning only
                </p>
              </div>
            </div>
          )}

          {/* Statement entries */}
          {history.map((entry, i) => (
            <DiscussionBlock key={`${entry.speaker}-${i}`} entry={entry} />
          ))}

          {/* Compass output */}
          {compass && <CompassBlock compass={compass} />}
        </div>
      </div>

      {/* ── Animations ────────────────────────────────────────── */}
      <style>{`
        @keyframes fade-scale-in {
          from {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.7);
          }
          to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
          }
        }
        @keyframes fade-slide-up {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-pulse-slow {
          animation: pulse-slow 2s ease-in-out infinite;
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </div>
  );
}
