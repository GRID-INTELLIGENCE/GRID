"""
ML-based content classifier for safety detection.

Uses sentence-transformers for embedding and scikit-learn for classification.
The classifier is loaded from a joblib file at startup. If no model file
exists, falls back to a cosine-similarity threshold against known-bad
exemplars.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from safety.observability.logging_setup import get_logger

logger = get_logger("detectors.ml_detector")

# ---------------------------------------------------------------------------
# Lazy-loaded models (heavy imports deferred)
# ---------------------------------------------------------------------------
_embedding_model: Any = None
_classifier: Any = None
_fallback_embeddings: np.ndarray | None = None

# Known-bad exemplars for the fallback cosine-similarity approach
_KNOWN_BAD_EXEMPLARS: list[tuple[str, str]] = [
    ("instructions to create explosives or weapons", "HIGH_RISK_WEAPON"),
    ("how to synthesize dangerous chemical compounds", "HIGH_RISK_CHEM_WEAPON"),
    ("steps to create biological weapons or pathogens", "HIGH_RISK_BIO"),
    ("detailed instructions for hacking or cyber attacks", "HIGH_RISK_CYBER"),
    ("content sexualizing or exploiting minors", "CSAM_BLOCK"),
    ("detailed methods of self-harm or suicide", "HIGH_RISK_SELF_HARM"),
    (
        "instructions to manipulate or deceive vulnerable people",
        "HIGH_RISK_MANIPULATION",
    ),
    ("instructions for producing illegal drugs", "HIGH_RISK_DRUGS"),
]

_MODEL_NAME = os.getenv("SAFETY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_CLASSIFIER_PATH = os.getenv("SAFETY_CLASSIFIER_PATH", "safety/models/safety_classifier.joblib")
_COSINE_THRESHOLD = float(os.getenv("SAFETY_COSINE_THRESHOLD", "0.72"))


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Result from the ML detector."""

    score: float  # 0.0 (safe) to 1.0 (unsafe)
    label: str  # reason code or "SAFE"
    confidence: float
    method: str  # "classifier" or "cosine_fallback"


def _load_embedding_model() -> Any:
    """Lazy-load the sentence-transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer(_MODEL_NAME)
            logger.info("embedding_model_loaded", model=_MODEL_NAME)
        except Exception as exc:
            logger.error("embedding_model_load_failed", error=str(exc))
            raise
    return _embedding_model


def _load_classifier() -> Any | None:
    """Lazy-load the sklearn classifier from joblib. Returns None if not found."""
    global _classifier
    if _classifier is not None:
        return _classifier
    path = Path(_CLASSIFIER_PATH)
    if not path.exists():
        logger.info("classifier_not_found", path=str(path), fallback="cosine_similarity")
        return None
    try:
        import joblib

        _classifier = joblib.load(path)
        logger.info("classifier_loaded", path=str(path))
        return _classifier
    except Exception as exc:
        logger.error("classifier_load_failed", path=str(path), error=str(exc))
        return None


def _get_fallback_embeddings() -> np.ndarray:
    """Compute and cache embeddings for known-bad exemplars."""
    global _fallback_embeddings
    if _fallback_embeddings is None:
        model = _load_embedding_model()
        texts = [ex[0] for ex in _KNOWN_BAD_EXEMPLARS]
        embeddings = model.encode(texts, normalize_embeddings=True)
        _fallback_embeddings = embeddings
    return _fallback_embeddings  # type: ignore[reportReturnStatementType]


async def classify(text: str) -> DetectionResult:
    """
    Classify text as safe or unsafe using ML.

    Tries the trained classifier first; falls back to cosine similarity
    against known-bad exemplars.
    """
    if not text or not text.strip():
        return DetectionResult(score=0.0, label="SAFE", confidence=1.0, method="empty_input")

    try:
        model = _load_embedding_model()
        embedding = model.encode([text], normalize_embeddings=True)[0]

        # Try trained classifier first
        clf = _load_classifier()
        if clf is not None:
            prediction = clf.predict([embedding])[0]
            probas = clf.predict_proba([embedding])[0]
            max_proba = float(np.max(probas))
            label = str(prediction)
            score = 1.0 - max_proba if label == "SAFE" else max_proba
            return DetectionResult(
                score=score,
                label=label,
                confidence=max_proba,
                method="classifier",
            )

        # Fallback: cosine similarity against known-bad exemplars
        bad_embeddings = _get_fallback_embeddings()
        similarities = [
            float(np.dot(embedding, bad_emb) / (np.linalg.norm(embedding) * np.linalg.norm(bad_emb) + 1e-9))
            for bad_emb in bad_embeddings
        ]
        max_idx = int(np.argmax(similarities))
        return DetectionResult(
            score=similarities[max_idx],
            label=_KNOWN_BAD_EXEMPLARS[max_idx][1],
            confidence=similarities[max_idx],
            method="cosine_fallback",
        )

    except Exception as exc:
        logger.error("ml_detector_error", error=str(exc))
        # Fail closed: if ML detection fails, flag as suspicious
        return DetectionResult(
            score=0.9,
            label="DETECTOR_ERROR",
            confidence=0.0,
            method="error_failsafe",
        )
