/**
 * generate-tokens.js
 *
 * Reads src/tokens/tokens.json and generates src/tokens/tokens.css
 * containing CSS custom properties. This keeps tokens.json as the
 * single source of truth for all design values.
 *
 * Usage: node scripts/generate-tokens.js
 */
const fs = require("fs");
const path = require("path");

const TOKENS_PATH = path.resolve(__dirname, "../src/tokens/tokens.json");
const OUTPUT_PATH = path.resolve(__dirname, "../src/tokens/tokens.css");

function loadTokens() {
  const raw = fs.readFileSync(TOKENS_PATH, "utf-8");
  return JSON.parse(raw);
}

/**
 * Flatten a nested token object into CSS variable declarations.
 * { color: { primary: "#fff" } } => "--color-primary: #fff;"
 */
function flattenTokens(obj, prefix = "") {
  const lines = [];
  for (const [key, value] of Object.entries(obj)) {
    // Skip JSON schema meta-fields
    if (key.startsWith("$")) continue;

    const varName = prefix ? `${prefix}-${key}` : key;
    if (typeof value === "object" && value !== null) {
      lines.push(...flattenTokens(value, varName));
    } else {
      lines.push(`  --${varName}: ${value};`);
    }
  }
  return lines;
}

function generate() {
  const tokens = loadTokens();
  const lines = flattenTokens(tokens);

  const banner = [
    "/* ═══════════════════════════════════════════════════════════════",
    " * AUTO-GENERATED from tokens.json — do not edit manually.",
    " * Run `npm run generate:tokens` to regenerate.",
    " * ═══════════════════════════════════════════════════════════════ */",
    "",
  ];

  // Colors go in .dark scope (dark-first design)
  const colorLines = flattenTokens({ color: tokens.color }, "").map(
    (l) => l.replace("--color-", "--")
  );

  // Non-color tokens go in :root (theme-agnostic)
  const rootTokens = { ...tokens };
  delete rootTokens.color;
  delete rootTokens.$schema;
  delete rootTokens.$description;
  const rootLines = flattenTokens(rootTokens);

  const css = [
    ...banner,
    ":root {",
    ...rootLines,
    "}",
    "",
    ".dark {",
    ...colorLines,
    "}",
    "",
  ].join("\n");

  fs.writeFileSync(OUTPUT_PATH, css, "utf-8");
  const tokenCount = lines.length;
  console.log(
    `Generated ${OUTPUT_PATH} (${tokenCount} tokens from tokens.json)`
  );
}

generate();
