import { Codex } from "@openai/codex-sdk";
import { config } from "dotenv";
import { randomUUID } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { buildFixPlan, buildFixPlanPrompt, formatFixPlan } from "./fix-plan.js";
import type {
  CiParseResult,
  DiagnosticsMode,
  LogLevel,
  Options,
  RunOutput,
  RunRecord,
} from "./types.js";

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------

const CURRENT_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(CURRENT_DIR, "..", "..", "..");

config({ path: resolve(REPO_ROOT, ".env") });

const REQUIRED_ENV = ["OPENAI_API_KEY"] as const;

const CORRELATION_ID = process.env.CODEX_CORRELATION_ID ?? randomUUID();

// ---------------------------------------------------------------------------
// Structured logging (JSON, correlation-id aware)
// ---------------------------------------------------------------------------

const logEvent = (level: LogLevel, message: string, fields?: Record<string, unknown>): void => {
  const payload = {
    timestamp: new Date().toISOString(),
    level,
    message,
    correlation_id: CORRELATION_ID,
    ...fields,
  };

  const line = JSON.stringify(payload);
  if (level === "ERROR") {
    console.error(line);
    return;
  }

  console.log(line);
};

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

const VALID_MODES: DiagnosticsMode[] = ["diagnose", "fix-plan"];

const normalizeOptional = (value?: string): string | undefined => {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
};

const parseArgs = (argv: string[]): Options => {
  const options: Partial<Options> = {
    mode: "diagnose",
    ciContextLines: 8,
    ciMaxBlocks: 6,
  };
  const args = [...argv];

  while (args.length > 0) {
    const key = args.shift();
    if (!key) {
      continue;
    }

    switch (key) {
      case "--mode":
        options.mode = args.shift() as DiagnosticsMode | undefined;
        break;
      case "--prompt":
        options.prompt = args.shift();
        break;
      case "--followup":
        options.followup = normalizeOptional(args.shift());
        break;
      case "--threadId":
        options.threadId = args.shift();
        break;
      case "--out":
        options.outPath = args.shift();
        break;
      case "--ci-log":
        options.ciLogPath = normalizeOptional(args.shift());
        break;
      case "--ci-context":
        options.ciContextLines = Number.parseInt(args.shift() ?? "", 10);
        break;
      case "--ci-max-blocks":
        options.ciMaxBlocks = Number.parseInt(args.shift() ?? "", 10);
        break;
      default:
        throw new Error(`Unknown argument: ${key}`);
    }
  }

  // Validate mode
  const mode = options.mode ?? "diagnose";
  if (!VALID_MODES.includes(mode)) {
    throw new Error(`--mode must be one of: ${VALID_MODES.join(", ")}`);
  }

  // In fix-plan mode, a CI log is required; prompt defaults to a plan request
  if (mode === "fix-plan") {
    if (!options.ciLogPath) {
      throw new Error("--ci-log is required in fix-plan mode.");
    }
    if (!options.prompt) {
      options.prompt = "Produce a structured remediation plan for these CI failures.";
    }
  }

  if (!options.prompt) {
    throw new Error("Missing required --prompt argument.");
  }

  const ciContextLines = options.ciContextLines ?? 8;
  const ciMaxBlocks = options.ciMaxBlocks ?? 6;

  if (!Number.isFinite(ciContextLines) || ciContextLines <= 0) {
    throw new Error("--ci-context must be a positive integer.");
  }

  if (!Number.isFinite(ciMaxBlocks) || ciMaxBlocks <= 0) {
    throw new Error("--ci-max-blocks must be a positive integer.");
  }

  return {
    ...options,
    mode,
    ciContextLines,
    ciMaxBlocks,
  } as Options;
};

// ---------------------------------------------------------------------------
// Env check
// ---------------------------------------------------------------------------

const ensureEnv = (): void => {
  const missing = REQUIRED_ENV.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    const message = `Missing required environment variables: ${missing.join(", ")}`;
    throw new Error(message);
  }
};

// ---------------------------------------------------------------------------
// Output path resolution
// ---------------------------------------------------------------------------

const resolveOutputPath = (outPath?: string): string => {
  if (outPath) {
    return resolve(process.cwd(), outPath);
  }
  return resolve(REPO_ROOT, "scripts", "codex-sdk", "output", "latest.json");
};

// ---------------------------------------------------------------------------
// CI log parsing
// ---------------------------------------------------------------------------

const CI_INDICATORS: Array<{ name: string; pattern: RegExp }> = [
  { name: "gha_error", pattern: /^##\[error\]/i },
  { name: "exit_code", pattern: /Process completed with exit code|exit code\s+\d+/i },
  { name: "pytest_failures", pattern: /=+ FAILURES =+|FAILED\b|AssertionError\b/i },
  { name: "traceback", pattern: /Traceback \(most recent call last\)/i },
  { name: "exception", pattern: /\b(Exception|Error):/ },
  { name: "npm_error", pattern: /npm ERR!/i },
  { name: "test_failure", pattern: /\btests? failed\b|\bfailures?\b/i },
];

const parseCiLog = (
  contents: string,
  sourcePath: string,
  contextLines: number,
  maxBlocks: number,
): CiParseResult => {
  const lines = contents.split(/\r?\n/);
  const indicators: Record<string, number> = {};
  const signals: string[] = [];
  const blocks: Array<{ indicator: string; line: number; group?: string; context: string[] }> = [];
  const signalSet = new Set<string>();
  let currentGroup: string | undefined;
  let blocksTruncated = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const groupMatch = line.match(/^##\[group\](.*)$/);
    if (groupMatch) {
      currentGroup = groupMatch[1]?.trim() || undefined;
      continue;
    }

    if (line.startsWith("##[endgroup]")) {
      currentGroup = undefined;
      continue;
    }

    const indicator = CI_INDICATORS.find((entry) => entry.pattern.test(line));
    if (!indicator) {
      continue;
    }

    indicators[indicator.name] = (indicators[indicator.name] ?? 0) + 1;
    const signal = line.trim();
    if (signal && !signalSet.has(signal)) {
      signalSet.add(signal);
      signals.push(signal);
    }

    if (blocks.length < maxBlocks) {
      const start = Math.max(0, index - contextLines);
      const end = Math.min(lines.length, index + contextLines + 1);
      blocks.push({
        indicator: indicator.name,
        line: index + 1,
        group: currentGroup,
        context: lines.slice(start, end),
      });
    } else {
      blocksTruncated = true;
    }
  }

  const indicatorSummary = Object.entries(indicators)
    .map(([name, count]: [string, number]) => `${name}: ${count}`)
    .join(", ");

  const summaryParts = [
    `Signals: ${signals.length}`,
    `Blocks captured: ${blocks.length}`,
    indicatorSummary ? `Indicators: ${indicatorSummary}` : "Indicators: none",
  ];

  return {
    sourcePath,
    summary: summaryParts.join(" | "),
    indicators,
    signals,
    blocks,
    blocksTruncated,
  };
};

const formatCiSummary = (ci: CiParseResult): string => {
  const lines: string[] = [];
  lines.push(`CI log: ${ci.sourcePath}`);
  lines.push(`Summary: ${ci.summary}`);

  if (ci.signals.length > 0) {
    lines.push("Signals:");
    lines.push(...ci.signals.slice(0, 10).map((s: string) => `- ${s}`));
  }

  if (ci.blocks.length > 0) {
    lines.push("Failure blocks:");
    ci.blocks.forEach((block, blockIndex) => {
      const header = `Block ${blockIndex + 1} (${block.indicator} @ line ${block.line}`;
      lines.push(block.group ? `${header}, group: ${block.group})` : `${header})`);
      lines.push(...block.context.map((contextLine: string) => `  ${contextLine}`));
    });
  }

  if (ci.blocksTruncated) {
    lines.push("Note: Additional failure blocks were truncated.");
  }

  return lines.join("\n");
};

const buildPrompt = (basePrompt: string, ci?: CiParseResult): string => {
  if (!ci) {
    return basePrompt;
  }
  return [basePrompt, "", "CI Failure Summary:", formatCiSummary(ci)].join("\n");
};

// ---------------------------------------------------------------------------
// CI log loading helper
// ---------------------------------------------------------------------------

const loadCiLog = async (options: Options): Promise<CiParseResult | undefined> => {
  if (!options.ciLogPath) {
    return undefined;
  }

  const resolvedLogPath = resolve(process.cwd(), options.ciLogPath);
  logEvent("INFO", "ci_log_parse_start", { path: resolvedLogPath });
  const logContents = await readFile(resolvedLogPath, "utf-8");
  const ciResult = parseCiLog(
    logContents,
    resolvedLogPath,
    options.ciContextLines,
    options.ciMaxBlocks,
  );
  logEvent("INFO", "ci_log_parse_complete", {
    indicators: ciResult.indicators,
    blocks: ciResult.blocks.length,
    truncated: ciResult.blocksTruncated,
  });
  return ciResult;
};

// ---------------------------------------------------------------------------
// Mode: diagnose (original flow)
// ---------------------------------------------------------------------------

const runDiagnoseMode = async (options: Options): Promise<RunOutput> => {
  const codex = new Codex();
  const thread = options.threadId
    ? codex.resumeThread(options.threadId)
    : codex.startThread();
  const runs: RunRecord[] = [];

  const ciResult = await loadCiLog(options);
  const composedPrompt = buildPrompt(options.prompt, ciResult);

  const primaryResult = await thread.run(composedPrompt);
  runs.push({
    basePrompt: options.prompt,
    prompt: composedPrompt,
    result: primaryResult,
    timestamp: new Date().toISOString(),
  });

  if (options.followup) {
    const followupResult = await thread.run(options.followup);
    runs.push({
      prompt: options.followup,
      result: followupResult,
      timestamp: new Date().toISOString(),
    });
  }

  return {
    threadId: thread.id,
    ci: ciResult,
    runs,
  };
};

// ---------------------------------------------------------------------------
// Mode: fix-plan
// ---------------------------------------------------------------------------

const runFixPlanMode = async (options: Options): Promise<RunOutput> => {
  const ciResult = await loadCiLog(options);
  if (!ciResult) {
    throw new Error("fix-plan mode requires a valid --ci-log.");
  }

  // 1. Build the local fix plan (no Codex call needed for the plan itself)
  const plan = buildFixPlan(ciResult, CORRELATION_ID);
  logEvent("INFO", "fix_plan_built", {
    steps: plan.steps.length,
    unmapped: plan.unmappedIndicators,
  });

  // Print the human-readable plan to stdout
  console.log(formatFixPlan(plan));

  // 2. Ask Codex to refine the plan
  const runs: RunRecord[] = [];
  const codexPrompt = buildFixPlanPrompt(ciResult, plan);
  const codex = new Codex();
  const thread = options.threadId
    ? codex.resumeThread(options.threadId)
    : codex.startThread();

  const result = await thread.run(codexPrompt);
  runs.push({
    basePrompt: options.prompt,
    prompt: codexPrompt,
    result,
    timestamp: new Date().toISOString(),
  });

  if (options.followup) {
    const followupResult = await thread.run(options.followup);
    runs.push({
      prompt: options.followup,
      result: followupResult,
      timestamp: new Date().toISOString(),
    });
  }

  return {
    threadId: thread.id,
    ci: ciResult,
    fixPlan: plan,
    runs,
  };
};

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

const main = async (): Promise<void> => {
  try {
    ensureEnv();
    const options = parseArgs(process.argv.slice(2));
    logEvent("INFO", "codex_diagnostics_start", {
      mode: options.mode,
      hasFollowup: Boolean(options.followup),
      hasCiLog: Boolean(options.ciLogPath),
      contextLines: options.ciContextLines,
      maxBlocks: options.ciMaxBlocks,
    });

    const output =
      options.mode === "fix-plan"
        ? await runFixPlanMode(options)
        : await runDiagnoseMode(options);

    const outPath = resolveOutputPath(options.outPath);
    await writeFile(outPath, JSON.stringify(output, null, 2), "utf-8");

    logEvent("INFO", "codex_diagnostics_complete", {
      mode: options.mode,
      threadId: output.threadId,
      outputPath: outPath,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logEvent("ERROR", "codex_diagnostics_failed", { error: message });
    process.exitCode = 1;
  }
};

main();
