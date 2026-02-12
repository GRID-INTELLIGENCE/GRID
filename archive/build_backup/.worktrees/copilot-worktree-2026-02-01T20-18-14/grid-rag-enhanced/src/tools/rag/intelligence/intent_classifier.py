"""
Intent Classifier for Intelligent RAG.

This module provides intent classification for user queries, allowing the RAG
system to choose different retrieval and generation strategies based on the
user's goal (e.g., finding a definition vs. understanding an implementation).
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

import torch
from transformers import pipeline

# Set up logging
logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Supported query intents for the GRID RAG system."""

    DEFINITION = "definition"  # "What is X?", "Explain the concept of Y"
    IMPLEMENTATION = "implementation"  # "How does X work?", "Show me the logic for Y"
    USAGE = "usage"  # "How do I use X?", "Give me an example of Y"
    DEBUGGING = "debugging"  # "Why is X failing?", "Fix the error in Y"
    ARCHITECTURE = "architecture"  # "How is the system structured?", "Workflow for X"
    COMPARISON = "comparison"  # "Difference between X and Y", "X vs Y"
    LOCATION = "location"  # "Where is X defined?", "Find the file for Y"
    RELATIONSHIP = "relationship"  # "How does X interact with Y?", "Dependencies of X"
    OTHER = "other"  # General chat or unclassified


@dataclass
class IntentResult:
    """Result of an intent classification."""

    intent: Intent
    confidence: float
    all_scores: Dict[str, float]
    query: str


class IntentClassifier:
    """
    Classifies user queries into specific intents using zero-shot classification.

    This allows the RAG system to understand if a user is looking for code,
    documentation, or architectural overviews without requiring a task-specific
    fine-tuned model for every new intent.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/nli-deberta-v3-small",
        device: Optional[str] = None,
        use_gpu: bool = True,
    ):
        """
        Initialize the intent classifier.

        Args:
            model_name: The transformer model to use for zero-shot classification.
            device: Specific device ('cpu', 'cuda', 'mps'). Defaults to auto-detection.
            use_gpu: Whether to attempt to use GPU if available.
        """
        self.model_name = model_name

        # Determine device
        if device is None:
            if use_gpu and torch.cuda.is_available():
                self.device = 0  # First CUDA device
            elif use_gpu and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = -1  # CPU
        else:
            self.device = device

        logger.info(f"Initializing IntentClassifier with {model_name} on {self.device}")

        try:
            # Use the zero-shot-classification pipeline for flexibility
            self.classifier = pipeline("zero-shot-classification", model=model_name, device=self.device)
        except Exception as e:
            logger.error(f"Failed to load intent classification model: {e}")
            self.classifier = None

        # Map display names/descriptions to Intent enum for better zero-shot performance
        self.label_map = {
            "explaining a concept or definition": Intent.DEFINITION,
            "understanding code implementation or logic": Intent.IMPLEMENTATION,
            "using a feature or looking for examples": Intent.USAGE,
            "debugging an error or fixing a bug": Intent.DEBUGGING,
            "high-level architecture and system structure": Intent.ARCHITECTURE,
            "comparing two different components": Intent.COMPARISON,
            "finding the file path or location of code": Intent.LOCATION,
            "system relationships and dependencies": Intent.RELATIONSHIP,
            "general conversation or other": Intent.OTHER,
        }
        self.candidate_labels = list(self.label_map.keys())

    def classify(self, query: str) -> IntentResult:
        """
        Classify the intent of a query.

        Args:
            query: The user's input string.

        Returns:
            IntentResult containing the detected intent and confidence scores.
        """
        if not query or not query.strip():
            return IntentResult(Intent.OTHER, 0.0, {}, query)

        if self.classifier is None:
            # Fallback to simple rule-based classification if model failed to load
            return self._fallback_classify(query)

        try:
            result = self.classifier(query, candidate_labels=self.candidate_labels, multi_label=False)

            # Map back to Enum
            top_label = result["labels"][0]
            top_score = result["scores"][0]

            all_scores = {
                self.label_map[label].value: score for label, score in zip(result["labels"], result["scores"])
            }

            return IntentResult(
                intent=self.label_map[top_label], confidence=top_score, all_scores=all_scores, query=query
            )

        except Exception as e:
            logger.error(f"Error during intent classification: {e}")
            return self._fallback_classify(query)

    def _fallback_classify(self, query: str) -> IntentResult:
        """Simple keyword-based fallback for intent detection."""
        query_lower = query.lower()

        # Simple heuristics
        if any(w in query_lower for w in ["what is", "define", "meaning", "explain"]):
            intent = Intent.DEFINITION
        elif any(w in query_lower for w in ["how does", "logic", "source", "implement"]):
            intent = Intent.IMPLEMENTATION
        elif any(w in query_lower for w in ["example", "how to use", "usage", "sample"]):
            intent = Intent.USAGE
        elif any(w in query_lower for w in ["error", "fix", "bug", "fail", "why"]):
            intent = Intent.DEBUGGING
        elif any(w in query_lower for w in ["where is", "path", "find file", "location"]):
            intent = Intent.LOCATION
        elif any(w in query_lower for w in ["structure", "architecture", "design", "layout"]):
            intent = Intent.ARCHITECTURE
        else:
            intent = Intent.OTHER

        return IntentResult(intent=intent, confidence=0.5, all_scores={intent.value: 0.5}, query=query)


if __name__ == "__main__":
    # Quick test harness
    logging.basicConfig(level=logging.INFO)
    classifier = IntentClassifier()

    test_queries = [
        "What is the GRID architecture?",
        "How does the indexer handle .agentignore files?",
        "Show me an example of using the RAGEngine",
        "Why am I getting a ConnectionError with Ollama?",
        "Where is the database configuration defined?",
        "Hi there!",
    ]

    print("\n--- Intent Classification Test ---")
    for q in test_queries:
        res = classifier.classify(q)
        print(f"Query: '{q}'")
        print(f"Intent: {res.intent.value} ({res.confidence:.2%})")
        print("-" * 30)
