/**
 * Shared types for the Codex SDK diagnostics toolchain.
 */

export type RunRecord = {
  basePrompt?: string;
  prompt: string;
  result: unknown;
  timestamp: string;
};

export type CiFailureBlock = {
  indicator: string;
  line: number;
  group?: string;
  context: string[];
};

export type CiParseResult = {
  sourcePath: string;
  summary: string;
  indicators: Record<string, number>;
  signals: string[];
  blocks: CiFailureBlock[];
  blocksTruncated: boolean;
};

export type RunOutput = {
  threadId: string | null;
  ci?: CiParseResult;
  fixPlan?: import("./fix-plan.js").FixPlan;
  runs: RunRecord[];
};

export type DiagnosticsMode = "diagnose" | "fix-plan";

export type Options = {
  mode: DiagnosticsMode;
  prompt: string;
  followup?: string;
  threadId?: string;
  outPath?: string;
  ciLogPath?: string;
  ciContextLines: number;
  ciMaxBlocks: number;
};

export type LogLevel = "INFO" | "WARN" | "ERROR";
