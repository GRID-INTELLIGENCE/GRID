/**
 * Mycelium Demo — Interactive Presentation Page
 *
 * Showcases Mycelium's core value proposition:
 * Same source text → different readers → each gets what they need.
 */

import { cn } from "@/lib/utils";
import { extractKeywords } from "@/lib/text-utils";
import { useState, useCallback, useMemo } from "react";
import {
  BookOpen,
  Brain,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Eye,
  Lightbulb,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";

/* ── Types ─────────────────────────────────────────────────────────── */

interface Persona {
  id: string;
  label: string;
  icon: string;
  description: string;
}

interface ConceptLens {
  name: string;
  pattern: string;
  eli5: string;
  analogy: string;
  visual: string;
  altEli5?: string;
  altAnalogy?: string;
}

interface DemoSection {
  id: string;
  title: string;
  text: string;
  context: string;
}

/* ── Data ──────────────────────────────────────────────────────────── */

const PERSONAS: Persona[] = [
  {
    id: "expert",
    label: "Expert Analyst",
    icon: "🔬",
    description: "Deep knowledge — wants precision, nuance, full depth",
  },
  {
    id: "stakeholder",
    label: "Business Stakeholder",
    icon: "💼",
    description: "Knows basics — wants actionable takeaways",
  },
  {
    id: "newcomer",
    label: "New Team Member",
    icon: "🌱",
    description: "First week — needs gentle onboarding",
  },
];

const DEMO_SECTIONS: DemoSection[] = [
  {
    id: "grid",
    title: "GRID Platform Analysis",
    context: "Environmental Intelligence report",
    text: "The Environmental Intelligence middleware detected dimensional imbalance in the DRTP framework during the latest Roundtable session. The Practical dimension scored 0.82 while Legal scored 0.31 and Psychological scored 0.45. This indicates the conversation was heavily skewed toward actionable items without sufficient consideration of regulatory constraints or emotional impact on stakeholders. The system applied a temperature adjustment of +0.15 to bias LLM responses toward legal and psychological grounding. Three nudge injections were triggered at turns 4, 7, and 11 to restore equilibrium. The overall balance coefficient improved from 0.39 to 0.67 over the session, representing a 72% improvement in dimensional balance.",
  },
  {
    id: "ml",
    title: "Machine Learning",
    context: "Neural network training passage",
    text: "Neural networks learn through backpropagation, an algorithm that computes the gradient of the loss function with respect to each weight by the chain rule, composing gradients from the output layer backward through the network. During training, the network feeds input data forward through layers of artificial neurons, each applying a nonlinear activation function such as ReLU or sigmoid. The predicted output is compared against the true label using a loss function like cross-entropy or mean squared error.",
  },
  {
    id: "legal",
    title: "Data Privacy",
    context: "Compliance briefing",
    text: "Under the framework's data governance requirements, all personally identifiable information must be processed exclusively on local infrastructure without transmission to external services. This includes biometric identifiers, geolocation data, device fingerprints, behavioral analytics, and session-correlated metadata. The retention period for interaction logs is capped at 90 days, after which automated purging must occur without manual intervention. Users retain the right to request immediate deletion of their profile data.",
  },
];

const CONCEPT_LENSES: ConceptLens[] = [
  {
    name: "cache",
    pattern: "flow",
    eli5: "A shelf next to you with stuff you use a lot. Saves walking to the warehouse.",
    analogy:
      "A river with pools — fast water flows past, pools hold what you need nearby.",
    visual:
      "Picture a river. The pools are your cache. Water is data flowing through.",
    altEli5:
      "Like checking your fridge. Milk expires, so you check before using it.",
    altAnalogy: "A heartbeat — regular pulses of checking and refreshing.",
  },
  {
    name: "recursion",
    pattern: "repetition",
    eli5: "A box inside a box inside a box. Open one, find another. Same shape, smaller.",
    analogy:
      "Mirrors facing each other — the same image repeating smaller and smaller.",
    visual:
      "Picture Russian nesting dolls. Each one contains a smaller version of itself.",
  },
  {
    name: "encryption",
    pattern: "combination",
    eli5: "Writing a secret message in code. Only your friend knows the code.",
    analogy: "A lockbox with two keys — one to lock, one to unlock.",
    visual:
      "Picture a treasure chest. The lock scrambles what's inside. The key unscrambles it.",
  },
  {
    name: "API",
    pattern: "cause",
    eli5: "You ask for pizza. The waiter goes to the kitchen and brings it. The waiter is the API.",
    analogy:
      "A waiter in a restaurant — you tell them what you want, they bring it from the kitchen.",
    visual:
      "Picture a counter with a window. You speak into the window, food comes out.",
    altEli5:
      "A tube. You put a question in one end, an answer comes out the other.",
    altAnalogy:
      "A pipeline with valves — requests flow in, responses flow out.",
  },
  {
    name: "database",
    pattern: "spatial",
    eli5: "A big notebook where you write things down so you don't forget.",
    analogy: "A library with organized shelves — every book has an address.",
    visual: "Picture a giant filing cabinet. Each drawer has a label.",
    altEli5: "Like filling out the same form for every student in a school.",
    altAnalogy: "A filing system — same structure repeated for every record.",
  },
];

/* ── Simulated synthesis per persona ───────────────────────────────── */

function getPersonaResult(section: DemoSection, persona: Persona) {
  const sentences = section.text.split(/\.\s+/).filter(Boolean);
  switch (persona.id) {
    case "expert":
      return {
        gist: sentences.slice(0, 2).join(". ") + ".",
        keywords: extractKeywords(section.text, 8),
        summary: section.text,
        depth: "Cold Brew ☕",
        compression: Math.round(
          (sentences[0].length / section.text.length) * 100
        ),
      };
    case "stakeholder":
      return {
        gist: sentences[0] + ".",
        keywords: extractKeywords(section.text, 5),
        summary:
          sentences.slice(0, Math.ceil(sentences.length * 0.6)).join(". ") +
          ".",
        depth: "Americano ☕",
        compression: Math.round(
          (sentences[0].length / section.text.length) * 100
        ),
      };
    default: {
      const kw = extractKeywords(section.text, 3);
      return {
        gist: sentences[0] + ".",
        keywords: kw,
        summary: sentences[0] + ". (Key ideas: " + kw.join(", ") + ")",
        depth: "Espresso ☕",
        compression: Math.round(
          (sentences[0].length / section.text.length) * 100
        ),
      };
    }
  }
}

/* ── Sub-components ────────────────────────────────────────────────── */

function SectionHead({
  title,
  sub,
  icon,
}: {
  title: string;
  sub: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--primary)]/10 text-[var(--primary)]">
        {icon}
      </div>
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-xs text-[var(--muted-foreground)]">{sub}</p>
      </div>
    </div>
  );
}

function PersonaTab({
  p,
  active,
  onClick,
}: {
  p: Persona;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 border cursor-pointer",
        active
          ? "border-[var(--primary)]/40 bg-[var(--primary)]/10 text-[var(--foreground)] shadow-[0_0_20px_rgba(59,130,246,0.1)]"
          : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--primary)]/20 hover:bg-[var(--accent)]"
      )}
    >
      <span className="text-xl">{p.icon}</span>
      <div className="text-left">
        <div className="font-semibold text-xs">{p.label}</div>
        <div className="text-[10px] opacity-70 hidden sm:block">
          {p.description}
        </div>
      </div>
    </button>
  );
}

function Pill({ word, rank }: { word: string; rank: number }) {
  const pri = rank < 3 ? "critical" : rank < 5 ? "high" : "medium";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border",
        "transition-transform hover:scale-105",
        pri === "critical" &&
          "bg-[var(--primary)]/15 text-[var(--primary)] border-[var(--primary)]/30",
        pri === "high" && "bg-amber-500/15 text-amber-400 border-amber-500/30",
        pri === "medium" &&
          "bg-[var(--muted)]/50 text-[var(--muted-foreground)] border-[var(--border)]"
      )}
    >
      {pri === "critical" && (
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
      )}
      {word}
    </span>
  );
}

function ConceptCard({
  c,
  open,
  onToggle,
}: {
  c: ConceptLens;
  open: boolean;
  onToggle: () => void;
}) {
  const [alt, setAlt] = useState(false);

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-300 overflow-hidden",
        open
          ? "border-[var(--primary)]/30 bg-[var(--primary)]/5 shadow-[0_0_30px_rgba(59,130,246,0.08)]"
          : "border-[var(--border)] hover:border-[var(--primary)]/20"
      )}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <Lightbulb
            className={cn(
              "h-4 w-4",
              open ? "text-[var(--primary)]" : "text-[var(--muted-foreground)]"
            )}
          />
          <span className="font-semibold text-sm capitalize">{c.name}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--muted)] text-[var(--muted-foreground)]">
            {c.pattern} lens
          </span>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-[var(--muted-foreground)]" />
        ) : (
          <ChevronDown className="h-4 w-4 text-[var(--muted-foreground)]" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 animate-fade-in">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
                ELI5
              </span>
              <p className="text-sm font-medium">
                {alt && c.altEli5 ? c.altEli5 : c.eli5}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
                Analogy
              </span>
              <p className="text-sm italic text-[var(--muted-foreground)]">
                {alt && c.altAnalogy ? c.altAnalogy : c.analogy}
              </p>
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
              Visual Hint
            </span>
            <p className="text-sm text-[var(--muted-foreground)]">
              🎨 {c.visual}
            </p>
          </div>
          {c.altEli5 && (
            <button
              onClick={() => setAlt(!alt)}
              className="text-xs text-[var(--primary)] hover:underline cursor-pointer flex items-center gap-1"
            >
              <ChevronRight className="h-3 w-3" />
              {alt ? "Back to original lens" : "Try a different lens"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main ──────────────────────────────────────────────────────────── */

export function MyceliumDemo() {
  const [personaId, setPersonaId] = useState("stakeholder");
  const [sectionId, setSectionId] = useState("grid");
  const [openConcept, setOpenConcept] = useState<string | null>("cache");

  const persona = useMemo(
    () => PERSONAS.find((p) => p.id === personaId)!,
    [personaId]
  );
  const section = useMemo(
    () => DEMO_SECTIONS.find((s) => s.id === sectionId)!,
    [sectionId]
  );
  const result = useMemo(
    () => getPersonaResult(section, persona),
    [section, persona]
  );

  const toggle = useCallback(
    (n: string) => setOpenConcept((p) => (p === n ? null : n)),
    []
  );

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-12 animate-fade-in">
      {/* Hero */}
      <div className="text-center space-y-2 pt-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--primary)]/20 bg-[var(--primary)]/5 text-[var(--primary)] text-xs font-medium mb-2">
          <Sparkles className="h-3 w-3" />
          Interactive Demonstration
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          Mycelium — Universal Comprehension Layer
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] max-w-xl mx-auto">
          Same source text. Different readers. Each gets what they need.
          <br />
          <span className="text-[var(--primary)]">
            All processing is local. Zero external dependencies.
          </span>
        </p>
      </div>

      {/* ── 1. Adaptive Synthesis ──────────────────────────────────── */}
      <section className="space-y-4">
        <SectionHead
          title="Adaptive Synthesis"
          sub="Watch how the same text transforms for different audiences"
          icon={<Users className="h-5 w-5" />}
        />

        {/* Source tabs */}
        <div className="flex gap-2 flex-wrap">
          {DEMO_SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSectionId(s.id)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer",
                sectionId === s.id
                  ? "border-[var(--primary)]/40 bg-[var(--primary)]/10 text-[var(--primary)]"
                  : "border-[var(--border)] text-[var(--muted-foreground)] hover:bg-[var(--accent)]"
              )}
            >
              {s.title}
            </button>
          ))}
        </div>

        {/* Source */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-wider text-[var(--muted-foreground)]">
              Source — {section.context}
            </span>
            <span className="text-[10px] text-[var(--muted-foreground)] font-mono">
              {section.text.length} chars
            </span>
          </div>
          <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
            {section.text}
          </p>
        </div>

        {/* Personas */}
        <div className="grid gap-2 sm:grid-cols-3">
          {PERSONAS.map((p) => (
            <PersonaTab
              key={p.id}
              p={p}
              active={personaId === p.id}
              onClick={() => setPersonaId(p.id)}
            />
          ))}
        </div>

        {/* Result */}
        <div
          key={`${sectionId}-${personaId}`}
          className="rounded-xl border border-[var(--primary)]/20 bg-gradient-to-b from-[var(--primary)]/5 to-transparent p-5 space-y-4 animate-fade-in"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">{persona.icon}</span>
              <span className="text-sm font-semibold">{persona.label}</span>
              <span className="text-[10px] ml-1 px-2 py-0.5 rounded-full bg-[var(--muted)] text-[var(--muted-foreground)]">
                {result.depth}
              </span>
            </div>
            <span className="text-xs text-[var(--muted-foreground)]">
              ✂️ {result.compression}% of original
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
              Gist
            </span>
            <p className="text-base font-semibold mt-1 leading-relaxed">
              {result.gist}
            </p>
          </div>

          <div>
            <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
              Key Points
            </span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {result.keywords.map((kw, i) => (
                <Pill key={kw} word={kw} rank={i} />
              ))}
            </div>
          </div>

          <div>
            <span className="text-[10px] uppercase text-[var(--muted-foreground)] tracking-wider">
              Summary
            </span>
            <p className="text-sm text-[var(--muted-foreground)] mt-1 leading-relaxed">
              {result.summary}
            </p>
          </div>
        </div>
      </section>

      {/* ── 2. Concept Explorer ────────────────────────────────────── */}
      <section className="space-y-4">
        <SectionHead
          title="Concept Explorer"
          sub="Every concept through multiple cognitive lenses — if one doesn't click, try another"
          icon={<Brain className="h-5 w-5" />}
        />
        <div className="space-y-2">
          {CONCEPT_LENSES.map((c) => (
            <ConceptCard
              key={c.name}
              c={c}
              open={openConcept === c.name}
              onToggle={() => toggle(c.name)}
            />
          ))}
        </div>
      </section>

      {/* ── 3. Architecture ────────────────────────────────────────── */}
      <section className="space-y-4">
        <SectionHead
          title="How It Works"
          sub="Pure Python heuristics — no AI/LLM dependency, all local"
          icon={<Zap className="h-5 w-5" />}
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: <Eye className="h-4 w-4" />,
              t: "PersonaEngine",
              d: "Detects expertise from vocabulary, cognitive style from phrasing, attention span from query length",
            },
            {
              icon: <Sparkles className="h-4 w-4" />,
              t: "Synthesizer",
              d: "TF-based keyword extraction, 4-heuristic sentence scoring, 6 structural pattern detectors",
            },
            {
              icon: <Lightbulb className="h-4 w-4" />,
              t: "PatternNavigator",
              d: "15 concepts × multiple geometric lenses, resonance feedback adapts lens selection",
            },
            {
              icon: <BookOpen className="h-4 w-4" />,
              t: "AdaptiveScaffold",
              d: "5 depth levels, 8 strategies: chunking, simplification, step-by-step, analogy",
            },
            {
              icon: <Users className="h-4 w-4" />,
              t: "SensoryMode",
              d: "6 profiles: Default, Low Vision, Screen Reader, Cognitive, Focus, Calm",
            },
            {
              icon: <Brain className="h-4 w-4" />,
              t: "SafetyGuard",
              d: "Input validation, PII detection (non-punitive), bounds enforcement, memory caps",
            },
          ].map((c) => (
            <div
              key={c.t}
              className="rounded-xl border border-[var(--border)] p-4 hover:border-[var(--primary)]/20 transition-all space-y-2"
            >
              <div className="flex items-center gap-2 text-[var(--primary)]">
                {c.icon}
                <span className="text-sm font-semibold">{c.t}</span>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
                {c.d}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <div className="text-center py-4 border-t border-[var(--border)] space-y-1">
        <p className="text-xs text-[var(--muted-foreground)]">
          174 tests · ~3,000 lines · 8 modules · Zero external dependencies
        </p>
        <p className="text-[10px] text-[var(--muted-foreground)]/60">
          🔒 All processing local · Privacy absolute · No data transmitted
        </p>
      </div>
    </div>
  );
}
