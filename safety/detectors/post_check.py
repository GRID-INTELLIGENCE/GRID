"""
Post-inference safety detector.

Runs after model output is generated, combining:
1. Heuristic pattern checks on the output
2. ML-based classification via ml_detector

Returns (flagged: bool, reason_code: str, evidence: dict).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from safety.detectors.ml_detector import classify as ml_classify
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import POSTCHECK_LATENCY

logger = get_logger("detectors.post_check")

# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------
SEVERITY_MAP: dict[str, str] = {
    "HIGH_RISK_WEAPON": "critical",
    "HIGH_RISK_CHEM_WEAPON": "critical",
    "HIGH_RISK_BIO": "critical",
    "CSAM_BLOCK": "critical",
    "HIGH_RISK_SELF_HARM": "high",
    "HIGH_RISK_CYBER": "high",
    "HIGH_RISK_MANIPULATION": "high",
    "HIGH_RISK_DRUGS": "high",
    "EXPLOIT_JAILBREAK": "medium",
    "DYNAMIC_BLOCKLIST": "medium",
    "DETECTOR_ERROR": "high",
    "HEURISTIC_OUTPUT_UNSAFE": "medium",
}

# ---------------------------------------------------------------------------
# Output heuristic patterns (things model should never output)
# ---------------------------------------------------------------------------
_OUTPUT_BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Detailed synthesis / manufacturing steps in output
    (
        re.compile(
            r"(step\s+\d+[:\.].*?(mix|combine|heat|dissolve|react)\s.*?"
            r"(nitro|ammonium|sulfur|phosph|chlor|acid|base))",
            re.I | re.DOTALL,
        ),
        "HIGH_RISK_CHEM_WEAPON",
    ),
    # Code that looks like malware
    (
        re.compile(
            r"(import\s+(socket|subprocess|ctypes|winreg).*?" r"(reverse.shell|keylog|encrypt.*?ransom|exfiltrat))",
            re.I | re.DOTALL,
        ),
        "HIGH_RISK_CYBER",
    ),
    # PII leakage patterns
    (
        re.compile(
            r"(\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b)",  # SSN-like
            re.I,
        ),
        "PII_LEAKAGE",
    ),
    (
        re.compile(
            r"(\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b.*?password\s*[:=])",
            re.I,
        ),
        "PII_LEAKAGE",
    ),
]

# Threshold above which ML score triggers a flag
_ML_FLAG_THRESHOLD = float(__import__("os").getenv("SAFETY_ML_FLAG_THRESHOLD", "0.65"))


@dataclass
class PostCheckResult:
    flagged: bool
    reason_code: str
    severity: str
    evidence: dict[str, Any] = field(default_factory=dict)


async def post_check(
    model_output: str,
    original_input: str | None = None,
) -> PostCheckResult:
    """
    Run post-inference safety checks on model output.

    Returns a PostCheckResult. If flagged, the output MUST NOT be returned
    to the user.
    """
    start = time.monotonic()

    try:
        if not model_output or not model_output.strip():
            return PostCheckResult(
                flagged=False,
                reason_code="SAFE",
                severity="low",
            )

        evidence: dict[str, Any] = {}

        # 1. Heuristic pattern checks on output
        for pattern, code in _OUTPUT_BLOCK_PATTERNS:
            match = pattern.search(model_output)
            if match:
                severity = SEVERITY_MAP.get(code, "medium")
                evidence["heuristic_match"] = {
                    "pattern": code,
                    "snippet": model_output[max(0, match.start() - 50) : match.end() + 50],
                }
                logger.warning(
                    "postcheck_heuristic_flag",
                    reason_code=code,
                    severity=severity,
                )
                return PostCheckResult(
                    flagged=True,
                    reason_code=code,
                    severity=severity,
                    evidence=evidence,
                )

        # 2. ML-based classification on output
        ml_result = await ml_classify(model_output)
        evidence["ml_detector"] = {
            "score": ml_result.score,
            "label": ml_result.label,
            "confidence": ml_result.confidence,
            "method": ml_result.method,
        }

        if ml_result.label != "SAFE" and ml_result.score >= _ML_FLAG_THRESHOLD:
            severity = SEVERITY_MAP.get(ml_result.label, "medium")
            logger.warning(
                "postcheck_ml_flag",
                reason_code=ml_result.label,
                score=ml_result.score,
                severity=severity,
            )
            return PostCheckResult(
                flagged=True,
                reason_code=ml_result.label,
                severity=severity,
                evidence=evidence,
            )

        # 3. Optional: cross-check input+output coherence
        # (e.g., user asked for safe topic but model produced unsafe content)
        if original_input:
            input_ml = await ml_classify(original_input)
            evidence["input_ml_detector"] = {
                "score": input_ml.score,
                "label": input_ml.label,
                "confidence": input_ml.confidence,
            }
            # If input was safe but output is borderline, flag for review
            if input_ml.label == "SAFE" and ml_result.score >= _ML_FLAG_THRESHOLD * 0.8 and ml_result.label != "SAFE":
                logger.info(
                    "postcheck_coherence_flag",
                    input_label=input_ml.label,
                    output_label=ml_result.label,
                    output_score=ml_result.score,
                )
                return PostCheckResult(
                    flagged=True,
                    reason_code="OUTPUT_COHERENCE_MISMATCH",
                    severity="medium",
                    evidence=evidence,
                )

        return PostCheckResult(
            flagged=False,
            reason_code="SAFE",
            severity="low",
            evidence=evidence,
        )

    except Exception as exc:
        # Fail closed: detector error means flag
        logger.error("postcheck_error", error=str(exc))
        return PostCheckResult(
            flagged=True,
            reason_code="DETECTOR_ERROR",
            severity="high",
            evidence={"error": str(exc)},
        )
    finally:
        elapsed = time.monotonic() - start
        POSTCHECK_LATENCY.observe(elapsed)
