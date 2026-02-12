"""Async PII Detection Engine with Worker Pool Support

This module provides async PII detection capabilities that integrate with GRID's
safety pipeline. It supports both synchronous (for latency-sensitive paths) and
asynchronous (for high-volume) processing.

Usage:
    # Sync usage (for middleware/request handlers)
    detector = AsyncPIIDetector()
    results = await detector.detect_async(text)

    # Async batch processing
    batch_results = await detector.detect_batch(texts, max_workers=4)
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from safety.observability.logging_setup import get_logger
from safety.observability.metrics import (
    DETECTION_CACHE_HITS,
    DETECTION_CACHE_MISSES,
    PRIVACY_DETECTION_LATENCY,
)
from safety.privacy.cache.result_cache import get_detection_cache

logger = get_logger("safety.privacy.detector")


@dataclass
class AsyncPIIDetection:
    """Async-compatible PII detection result."""

    pii_type: str
    value: str
    start: int
    end: int
    confidence: float
    pattern_name: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pii_type": self.pii_type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "pattern_name": self.pattern_name,
        }


class AsyncPatternMatcher:
    """Async-compatible pattern matcher with compiled regex caching."""

    def __init__(self):
        self._compiled_patterns: dict[str, re.Pattern] = {}
        self._pattern_metadata: dict[str, dict[str, Any]] = {}

    def register_pattern(
        self,
        name: str,
        pattern: str,
        pii_type: str,
        confidence: float = 0.9,
        flags: int = re.IGNORECASE,
    ) -> None:
        """Register a regex pattern for PII detection."""
        try:
            compiled = re.compile(pattern, flags)
            self._compiled_patterns[name] = compiled
            self._pattern_metadata[name] = {
                "pii_type": pii_type,
                "confidence": confidence,
                "pattern": pattern,
            }
            logger.debug(f"Registered pattern: {name} ({pii_type})")
        except re.error as e:
            logger.error(f"Invalid regex pattern '{name}': {e}")
            raise

    async def match(self, text: str, pattern_name: str) -> list[AsyncPIIDetection]:
        """Match text against a specific pattern asynchronously."""
        if pattern_name not in self._compiled_patterns:
            return []

        compiled = self._compiled_patterns[pattern_name]
        metadata = self._pattern_metadata[pattern_name]

        # Run regex matching in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        matches = await loop.run_in_executor(
            None,  # Default executor
            lambda: list(compiled.finditer(text)),
        )

        return [
            AsyncPIIDetection(
                pii_type=metadata["pii_type"],
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=metadata["confidence"],
                pattern_name=pattern_name,
            )
            for match in matches
        ]


class AsyncPIIDetector:
    """High-performance async PII detector with caching and worker pool support."""

    # Default patterns - comprehensive coverage
    DEFAULT_PATTERNS = [
        # PII Types
        ("EMAIL", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL", 0.95),
        ("PHONE_US", r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "PHONE", 0.85),
        ("SSN", r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "SSN", 0.90),
        ("CREDIT_CARD", r"\b(?:\d{4}[-.\s]?){3}\d{4}\b", "CREDIT_CARD", 0.88),
        ("IP_ADDRESS", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP_ADDRESS", 0.75),
        ("IPV6", r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", "IP_ADDRESS", 0.90),
        ("DATE_MDY", r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b", "DATE", 0.70),
        # Secrets/Keys
        ("AWS_KEY", r"(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}", "AWS_KEY", 0.95),
        ("API_KEY", r'(?:api[_-]?key|apikey|api_secret)[":\s=]+\S+', "API_KEY", 0.75),
        ("PASSWORD", r'(?:password|passwd|pwd)[":\s=]+\S+', "PASSWORD", 0.80),
        ("PRIVATE_KEY", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "PRIVATE_KEY", 0.99),
        # Identifiers
        ("IBAN", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "IBAN", 0.85),
        ("US_ZIP", r"\b\d{5}(?:-\d{4})?\b", "US_ZIP", 0.65),
    ]

    def __init__(
        self,
        enable_cache: bool = True,
        max_workers: int = 4,
    ):
        self.matcher = AsyncPatternMatcher()
        self.cache = get_detection_cache() if enable_cache else None
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._enabled_patterns: set[str] = set()

        # Register default patterns
        for name, pattern, pii_type, confidence in self.DEFAULT_PATTERNS:
            self.matcher.register_pattern(name, pattern, pii_type, confidence)
            self._enabled_patterns.add(name)

    def enable_patterns(self, patterns: list[str]) -> None:
        """Enable specific patterns only."""
        self._enabled_patterns = set(p.upper() for p in patterns)

    def disable_patterns(self, patterns: list[str]) -> None:
        """Disable specific patterns."""
        for p in patterns:
            self._enabled_patterns.discard(p.upper())

    def reset_patterns(self) -> None:
        """Reset to all patterns enabled."""
        self._enabled_patterns = set(self.matcher._compiled_patterns.keys())

    def _generate_cache_key(self, text: str, enabled_patterns: frozenset[str]) -> str:
        """Generate cache key for detection results."""
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        patterns_hash = hashlib.sha256(",".join(sorted(enabled_patterns)).encode()).hexdigest()[:8]
        return f"pii:{content_hash}:{patterns_hash}"

    async def detect_async(self, text: str) -> list[AsyncPIIDetection]:
        """Detect PII in text asynchronously with caching."""
        if not text:
            return []

        # Check cache
        if self.cache:
            cached = await self.cache.get(
                text,
                frozenset(self._enabled_patterns),
            )
            if cached is not None:
                logger.debug("cache_hit")
                return [AsyncPIIDetection(**d) for d in cached]

        # Perform detection
        with PRIVACY_DETECTION_LATENCY.time():
            # Run all enabled patterns in parallel
            tasks = [
                self.matcher.match(text, pattern_name)
                for pattern_name in self._enabled_patterns
                if pattern_name in self.matcher._compiled_patterns
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten and filter out exceptions
            detections = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error("pattern_matching_error", error=str(result))
                    continue
                if isinstance(result, list):
                    detections.extend(result)

            # Sort by position and deduplicate
            detections = self._deduplicate(sorted(detections, key=lambda x: x.start))

        # Cache results
        if self.cache:
            await self.cache.set(
                text,
                [d.to_dict() for d in detections],
                frozenset(self._enabled_patterns),
                ttl=3600,
            )

        return detections

    def _deduplicate(self, detections: list[AsyncPIIDetection]) -> list[AsyncPIIDetection]:
        """Remove overlapping detections, keeping highest confidence."""
        if not detections:
            return []

        result = [detections[0]]
        for det in detections[1:]:
            last = result[-1]
            # Check for overlap
            if det.start < last.end:
                # Overlapping - keep higher confidence
                if det.confidence > last.confidence:
                    result[-1] = det
            else:
                result.append(det)

        return result

    async def detect_batch(self, texts: list[str], max_workers: int = 4) -> list[list[AsyncPIIDetection]]:
        """Process multiple texts in parallel using worker pool."""
        semaphore = asyncio.Semaphore(max_workers)

        async def detect_with_limit(text: str) -> list[AsyncPIIDetection]:
            async with semaphore:
                return await self.detect_async(text)

        tasks = [detect_with_limit(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results: list[list[AsyncPIIDetection]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("batch_detection_error", error=str(result))
                valid_results.append([])  # type: ignore[arg-type]
            else:
                valid_results.append(result)  # type: ignore[arg-type]

        return valid_results

    async def close(self) -> None:
        """Cleanup resources."""
        self._executor.shutdown(wait=False)
        if self.cache:
            await self.cache.close()


# Global instance for reuse
detector = AsyncPIIDetector()
