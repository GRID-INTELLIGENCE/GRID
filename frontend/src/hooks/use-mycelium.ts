import { useCallback, useMemo, useReducer } from "react";
import { extractKeywords } from "@/lib/text-utils";
import type {
  Depth,
  MyceliumState,
  NavigationResult,
  SensoryProfile,
  SynthesisResult,
  UserTraits,
} from "@/types/mycelium";

// ── Actions ──────────────────────────────────────────────────────
type Action =
  | { type: "SET_INPUT"; payload: string }
  | { type: "SET_DEPTH"; payload: Depth }
  | { type: "SET_SENSORY"; payload: SensoryProfile }
  | { type: "START_PROCESSING" }
  | { type: "SET_RESULT"; payload: SynthesisResult }
  | { type: "SET_ERROR"; payload: string }
  | { type: "SET_EXPLORED"; payload: NavigationResult | null }
  | { type: "SET_CONCEPTS"; payload: string[] }
  | { type: "CLEAR" };

const initialState: MyceliumState = {
  input: "",
  result: null,
  depth: "americano",
  sensoryProfile: "default",
  isProcessing: false,
  exploredConcept: null,
  concepts: [],
  error: null,
};

function reducer(state: MyceliumState, action: Action): MyceliumState {
  switch (action.type) {
    case "SET_INPUT":
      return { ...state, input: action.payload, error: null };
    case "SET_DEPTH":
      return { ...state, depth: action.payload };
    case "SET_SENSORY":
      return { ...state, sensoryProfile: action.payload };
    case "START_PROCESSING":
      return { ...state, isProcessing: true, error: null };
    case "SET_RESULT":
      return { ...state, result: action.payload, isProcessing: false };
    case "SET_ERROR":
      return { ...state, error: action.payload, isProcessing: false };
    case "SET_EXPLORED":
      return { ...state, exploredConcept: action.payload };
    case "SET_CONCEPTS":
      return { ...state, concepts: action.payload };
    case "CLEAR":
      return { ...initialState };
    default:
      return state;
  }
}

// ── IPC bridge types ─────────────────────────────────────────────
interface MyceliumBridge {
  synthesize: (
    text: string,
    depth: Depth,
    sensory: SensoryProfile
  ) => Promise<SynthesisResult>;
  summarize: (text: string, sentences: number) => Promise<string>;
  simplify: (text: string) => Promise<string>;
  keywords: (
    text: string,
    topN: number
  ) => Promise<SynthesisResult["highlights"]>;
  explore: (
    concept: string,
    pattern?: string
  ) => Promise<NavigationResult | null>;
  tryDifferent: (concept: string) => Promise<NavigationResult | null>;
  eli5: (concept: string) => Promise<string>;
  feedback: (tooComplex?: boolean, tooSimple?: boolean) => Promise<void>;
  setUser: (traits: UserTraits) => Promise<void>;
  setSensory: (profile: SensoryProfile) => Promise<string>;
  concepts: () => Promise<string[]>;
}

function getBridge(): MyceliumBridge {
  const w = window as unknown as Record<string, unknown>;
  if (w.mycelium) return w.mycelium as MyceliumBridge;

  // Fallback: local synthesis using a mock that mirrors the Python backend
  return createLocalBridge();
}

function createLocalBridge(): MyceliumBridge {
  // Lightweight in-browser fallback — enables the UI to work
  // without the Python backend running. Uses simple heuristics.
  function extractGist(text: string): string {
    const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 10);
    return sentences[0]?.trim() + "." || text.slice(0, 120);
  }

  function extractHighlights(text: string): SynthesisResult["highlights"] {
    return extractKeywords(text, 8).map((word, i) => ({
      text: word,
      priority:
        i < 2
          ? ("critical" as const)
          : i < 5
            ? ("high" as const)
            : ("medium" as const),
      context: "",
      category: "concept",
    }));
  }

  return {
    async synthesize(text, depth) {
      await delay(300);
      const gist = extractGist(text);
      const highlights = extractHighlights(text);
      const sentences = text
        .split(/[.!?]+/)
        .filter((s) => s.trim().length > 10);
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
    async summarize(text, sentences) {
      await delay(200);
      const s = text.split(/[.!?]+/).filter((s) => s.trim().length > 10);
      return s.slice(0, sentences).join(". ").trim() + ".";
    },
    async simplify(text) {
      await delay(200);
      return extractGist(text);
    },
    async keywords(text, topN) {
      await delay(100);
      return extractHighlights(text).slice(0, topN);
    },
    async explore(concept) {
      await delay(150);
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
    async tryDifferent(concept) {
      await delay(150);
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
    async eli5(concept) {
      await delay(100);
      return `${concept} is like a magic box that helps you do things faster.`;
    },
    async feedback() {
      await delay(50);
    },
    async setUser() {
      await delay(50);
    },
    async setSensory() {
      await delay(50);
      return "Profile updated.";
    },
    async concepts() {
      await delay(50);
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

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

// ── Hook ─────────────────────────────────────────────────────────
export function useMycelium() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const bridge = useMemo(() => getBridge(), []);

  const setInput = useCallback((text: string) => {
    dispatch({ type: "SET_INPUT", payload: text });
  }, []);

  const setDepth = useCallback((depth: Depth) => {
    dispatch({ type: "SET_DEPTH", payload: depth });
  }, []);

  const setSensory = useCallback(
    async (profile: SensoryProfile) => {
      dispatch({ type: "SET_SENSORY", payload: profile });
      await bridge.setSensory(profile);
    },
    [bridge]
  );

  const synthesize = useCallback(async () => {
    if (!state.input.trim()) return;
    dispatch({ type: "START_PROCESSING" });
    try {
      const result = await bridge.synthesize(
        state.input,
        state.depth,
        state.sensoryProfile
      );
      dispatch({ type: "SET_RESULT", payload: result });
    } catch (err) {
      dispatch({
        type: "SET_ERROR",
        payload: err instanceof Error ? err.message : "Synthesis failed",
      });
    }
  }, [state.input, state.depth, state.sensoryProfile, bridge]);

  const feedback = useCallback(
    async (tooComplex?: boolean, tooSimple?: boolean) => {
      await bridge.feedback(tooComplex, tooSimple);
      // Re-synthesize with adjusted depth
      if (state.input.trim()) {
        dispatch({ type: "START_PROCESSING" });
        try {
          const newDepth: Depth = tooComplex
            ? state.depth === "cold_brew"
              ? "americano"
              : "espresso"
            : state.depth === "espresso"
              ? "americano"
              : "cold_brew";
          dispatch({ type: "SET_DEPTH", payload: newDepth });
          const result = await bridge.synthesize(
            state.input,
            newDepth,
            state.sensoryProfile
          );
          dispatch({ type: "SET_RESULT", payload: result });
        } catch {
          // Feedback failed silently — not critical
        }
      }
    },
    [bridge, state.input, state.depth, state.sensoryProfile]
  );

  const explore = useCallback(
    async (concept: string) => {
      try {
        const result = await bridge.explore(concept);
        dispatch({ type: "SET_EXPLORED", payload: result });
      } catch {
        dispatch({ type: "SET_EXPLORED", payload: null });
      }
    },
    [bridge]
  );

  const tryDifferent = useCallback(
    async (concept: string) => {
      try {
        const result = await bridge.tryDifferent(concept);
        dispatch({ type: "SET_EXPLORED", payload: result });
      } catch {
        dispatch({ type: "SET_EXPLORED", payload: null });
      }
    },
    [bridge]
  );

  const loadConcepts = useCallback(async () => {
    const list = await bridge.concepts();
    dispatch({ type: "SET_CONCEPTS", payload: list });
  }, [bridge]);

  const clearExplored = useCallback(() => {
    dispatch({ type: "SET_EXPLORED", payload: null });
  }, []);

  const clear = useCallback(() => {
    dispatch({ type: "CLEAR" });
  }, []);

  return {
    ...state,
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
  };
}
