export type Depth = "espresso" | "americano" | "cold_brew";

export type SensoryProfile =
  | "default"
  | "low_vision"
  | "screen_reader"
  | "cognitive"
  | "focus"
  | "calm";

export type ResonanceLevel = "silent" | "hum" | "ring";

export type ExpertiseLevel =
  | "child"
  | "beginner"
  | "familiar"
  | "proficient"
  | "expert";

export type CognitiveStyle =
  | "visual"
  | "narrative"
  | "analytical"
  | "kinesthetic";

export type EngagementTone = "playful" | "warm" | "direct" | "academic";

export interface Highlight {
  text: string;
  priority: "low" | "medium" | "high" | "critical";
  context: string;
  category: string;
}

export interface SynthesisResult {
  gist: string;
  highlights: Highlight[];
  summary: string;
  explanation: string;
  analogy: string;
  compression_ratio: number;
  depth: Depth;
  patterns: string[];
  scaffolding_applied: string[];
}

export interface PatternLens {
  pattern: string;
  analogy: string;
  eli5: string;
  visual_hint: string;
  when_useful: string;
}

export interface NavigationResult {
  concept: string;
  lens: PatternLens;
  alternatives_available: number;
}

export interface UserTraits {
  expertise?: ExpertiseLevel;
  cognitive_style?: CognitiveStyle;
  tone?: EngagementTone;
  depth?: Depth;
  challenges?: string[];
}

export interface MyceliumState {
  input: string;
  result: SynthesisResult | null;
  depth: Depth;
  sensoryProfile: SensoryProfile;
  isProcessing: boolean;
  exploredConcept: NavigationResult | null;
  concepts: string[];
  error: string | null;
}
