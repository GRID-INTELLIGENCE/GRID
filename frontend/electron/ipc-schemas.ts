/**
 * IPC Schema Validation — Zod schemas for all Electron IPC contracts.
 *
 * Every IPC handler validates its input against these schemas before
 * executing any logic. This prevents the renderer from sending
 * malformed or malicious payloads through the IPC bridge.
 */
import { z } from "zod";

// ── Shared primitives ────────────────────────────────────────────

const HttpMethod = z.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]);

/** Endpoint must start with "/" and contain only safe URL characters */
const SafeEndpoint = z
  .string()
  .min(1)
  .regex(
    /^\/[\w\-/.?&=%:@+,;~]*$/,
    "Endpoint must start with / and contain only safe URL characters"
  );

// ── GRID API schemas ─────────────────────────────────────────────

export const gridApiSchema = z.object({
  method: HttpMethod,
  endpoint: SafeEndpoint,
  body: z.unknown().optional(),
});

export type GridApiInput = z.infer<typeof gridApiSchema>;

export const gridStreamSchema = z.object({
  method: HttpMethod,
  endpoint: SafeEndpoint,
  body: z.unknown().optional(),
});

export type GridStreamInput = z.infer<typeof gridStreamSchema>;

// ── Ollama API schemas ───────────────────────────────────────────

export const ollamaApiSchema = z.object({
  method: HttpMethod,
  endpoint: SafeEndpoint,
  body: z.unknown().optional(),
});

export type OllamaApiInput = z.infer<typeof ollamaApiSchema>;

const ChatMessage = z.object({
  role: z.enum(["system", "user", "assistant"]),
  content: z.string(),
});

export const ollamaStreamSchema = z.object({
  model: z
    .string()
    .min(1)
    .regex(
      /^[\w.:\-/]+$/,
      "Model name must contain only alphanumerics, dots, colons, hyphens, slashes"
    ),
  messages: z.array(ChatMessage).min(1),
  temperature: z.number().min(0).max(2).optional(),
});

export type OllamaStreamInput = z.infer<typeof ollamaStreamSchema>;

// ── Tool system schemas ──────────────────────────────────────────

export const executeToolSchema = z.object({
  toolId: z.string().min(1),
  arguments: z.record(z.unknown()),
  dryRun: z.boolean().default(false),
});

export type ExecuteToolInput = z.infer<typeof executeToolSchema>;

export const planPreviewSchema = z.object({
  goal: z.string().min(1, "Goal is required"),
  context: z.string().optional(),
  model: z.string().optional(),
});

export type PlanPreviewInput = z.infer<typeof planPreviewSchema>;

// ── Validation helper ────────────────────────────────────────────

export interface ValidationResult<T> {
  success: true;
  data: T;
}

export interface ValidationError {
  success: false;
  error: string;
}

/**
 * Validate IPC input against a zod schema.
 * Returns a discriminated union so callers can handle errors cleanly.
 */
export function validateIpc<T>(
  schema: z.ZodSchema<T>,
  input: unknown
): ValidationResult<T> | ValidationError {
  const result = schema.safeParse(input);
  if (result.success) {
    return { success: true, data: result.data };
  }
  const message = result.error.issues
    .map((i) => `${i.path.join(".")}: ${i.message}`)
    .join("; ");
  return { success: false, error: `IPC validation failed: ${message}` };
}
