/**
 * Shared keyword extraction utility.
 *
 * Used by use-mycelium.ts (highlights) and MyceliumDemo.tsx (keyword pills).
 * Single source of truth for stop-word filtering and frequency counting.
 */

const STOP_WORDS = new Set([
  "the",
  "a",
  "an",
  "and",
  "or",
  "but",
  "in",
  "on",
  "at",
  "to",
  "for",
  "of",
  "with",
  "by",
  "from",
  "is",
  "are",
  "was",
  "were",
  "be",
  "been",
  "have",
  "has",
  "had",
  "do",
  "does",
  "did",
  "will",
  "it",
  "this",
  "that",
  "each",
  "its",
  "not",
  "as",
  "such",
  "all",
  "no",
  "than",
  "like",
  "during",
  "using",
  "without",
  "must",
  "also",
  "into",
  "may",
  "can",
]);

/**
 * Extract the top N keywords from text by frequency.
 * Filters stop words and words with 3 or fewer characters.
 */
export function extractKeywords(text: string, topN: number): string[] {
  const counts = new Map<string, number>();
  for (const w of text.split(/\s+/)) {
    const clean = w.toLowerCase().replace(/[^a-z]/g, "");
    if (clean.length > 3 && !STOP_WORDS.has(clean)) {
      counts.set(clean, (counts.get(clean) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
    .map(([word]) => word);
}
