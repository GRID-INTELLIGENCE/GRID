/**
 * generate-tokens.js
 *
 * Reads src/tokens/tokens.json and generates src/tokens/tokens.css
 * containing CSS custom properties. This keeps tokens.json as the
 * single source of truth for all design values.
 *
 * Supports multi-theme: themes.dark, themes.light, themes.mycelium
 * are emitted as scoped CSS classes. All other tokens go in :root.
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

  const banner = [
    "/* ═══════════════════════════════════════════════════════════════",
    " * AUTO-GENERATED from tokens.json — do not edit manually.",
    " * Run `npm run generate:tokens` to regenerate.",
    " * ═══════════════════════════════════════════════════════════════ */",
    "",
  ];

  // Theme-scoped color tokens
  const themes = tokens.themes || {};
  const themeBlocks = [];
  for (const [themeName, themeColors] of Object.entries(themes)) {
    const colorLines = flattenTokens(themeColors).map((l) =>
      l.replace(/^  --/, "  --")
    );
    themeBlocks.push(`.${themeName} {`, ...colorLines, "}", "");
  }

  // Non-theme tokens go in :root (theme-agnostic)
  const rootTokens = { ...tokens };
  delete rootTokens.themes;
  delete rootTokens.$schema;
  delete rootTokens.$description;
  const rootLines = flattenTokens(rootTokens);

  const css = [
    ...banner,
    ":root {",
    ...rootLines,
    "}",
    "",
    ...themeBlocks,
  ].join("\n");

  fs.writeFileSync(OUTPUT_PATH, css, "utf-8");
  const themeCount = Object.keys(themes).length;
  const rootCount = rootLines.length;
  console.log(
    `Generated ${OUTPUT_PATH} (${rootCount} root tokens, ${themeCount} themes from tokens.json)`
  );
}

generate();
