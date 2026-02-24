/**
 * Synthesis Web Worker
 *
 * Offloads text processing from the main thread for the local bridge fallback.
 * Handles sentence splitting, keyword extraction, and basic text statistics.
 */

interface WorkerRequest {
  type: "split-sentences" | "extract-keywords" | "text-stats";
  text: string;
}

interface SplitSentencesResult {
  type: "split-sentences";
  sentences: string[];
}

interface ExtractKeywordsResult {
  type: "extract-keywords";
  keywords: string[];
}

interface TextStatsResult {
  type: "text-stats";
  chars: number;
  words: number;
  sentences: number;
  readingMinutes: number;
}

type WorkerResponse =
  | SplitSentencesResult
  | ExtractKeywordsResult
  | TextStatsResult;

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function extractKeywords(text: string): string[] {
  const stopWords = new Set([
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "and",
    "but",
    "or",
    "not",
    "no",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
  ]);

  const words = text.toLowerCase().match(/\b[a-z]{3,}\b/g) ?? [];
  const freq = new Map<string, number>();

  for (const word of words) {
    if (!stopWords.has(word)) {
      freq.set(word, (freq.get(word) ?? 0) + 1);
    }
  }

  return [...freq.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([word]) => word);
}

function computeStats(text: string): TextStatsResult {
  const chars = text.length;
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const sentences = splitSentences(text).length;
  const readingMinutes = Math.max(1, Math.ceil(words / 238));

  return { type: "text-stats", chars, words, sentences, readingMinutes };
}

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const { type, text } = event.data;
  let response: WorkerResponse;

  switch (type) {
    case "split-sentences":
      response = { type: "split-sentences", sentences: splitSentences(text) };
      break;
    case "extract-keywords":
      response = { type: "extract-keywords", keywords: extractKeywords(text) };
      break;
    case "text-stats":
      response = computeStats(text);
      break;
  }

  self.postMessage(response);
};
