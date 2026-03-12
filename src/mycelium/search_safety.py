"""
Mycelium Search Safety Integration
Safety validation and PII detection for search results

LIMITATIONS:
    This module provides heuristic-based safety checks for search results.
    It is NOT a production content moderation system. Keyword matching alone
    is insufficient for production safety without classifier context.
    All patterns here are descriptive (nouns/concepts), never imperative.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, List

logger = logging.getLogger(__name__)


class SearchSafetyVerdict(StrEnum):
    """Result of search safety validation."""
    PASS = "pass"
    WARN = "warn"
    REJECT = "reject"


@dataclass
class SearchSafetyReport:
    """Outcome of search safety validation."""
    
    verdict: SearchSafetyVerdict
    reasons: List[str] = field(default_factory=list)
    pii_detected: bool = False
    pii_types: List[str] = field(default_factory=list)
    sanitized_content: str | None = None
    original_length: int = 0
    processing_time_ms: float = 0.0
    
    @property
    def is_safe(self) -> bool:
        """Check if content is safe to process."""
        return self.verdict in (SearchSafetyVerdict.PASS, SearchSafetyVerdict.WARN)


class SearchSafetyGuard:
    """Safety validation for search results in Mycelium."""
    
    def __init__(self):
        """Initialize search safety guard."""
        self._check_count: int = 0
        self._last_check_time: float = 0.0
        
        # PII patterns - descriptive nouns only per Trust Layer Rule 1.1
        self._pii_patterns: dict[str, re.Pattern[str]] = {
            "email_address": re.compile(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.ASCII
            ),
            "phone_number": re.compile(
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
            ),
            "social_security_number": re.compile(
                r"\b\d{3}-\d{2}-\d{4}\b"
            ),
            "credit_card_number": re.compile(
                r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
            ),
            "ip_address": re.compile(
                r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
            ),
        }
        
        # Content safety patterns
        self._dangerous_chars: re.Pattern[str] = re.compile(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
        )
        
        # Search-specific limits
        self.max_content_length = 100_000  # 100KB for search results
        self.pii_scan_limit = 5_000  # First 5KB for PII scanning
    
    def validate_search_result(self, content: str, route: str | None = None) -> SearchSafetyReport:
        """Validate search result content.
        
        Args:
            content: Search result content to validate
            route: Optional file route for context
            
        Returns:
            SearchSafetyReport with validation results
        """
        start = time.monotonic()
        reasons: List[str] = []
        pii_found = False
        pii_types: List[str] = []
        
        # Type check
        if not isinstance(content, str):
            return SearchSafetyReport(
                verdict=SearchSafetyVerdict.REJECT,
                reasons=["Content must be a string"],
                processing_time_ms=self._elapsed_ms(start),
            )
        
        original_length = len(content)
        
        # Length bounds
        if original_length > self.max_content_length:
            return SearchSafetyReport(
                verdict=SearchSafetyVerdict.REJECT,
                reasons=[
                    f"Content exceeds maximum length ({original_length:,} > {self.max_content_length:,})"
                ],
                original_length=original_length,
                processing_time_ms=self._elapsed_ms(start),
            )
        
        if not content.strip():
            return SearchSafetyReport(
                verdict=SearchSafetyVerdict.REJECT,
                reasons=["Content is empty or whitespace-only"],
                original_length=original_length,
                processing_time_ms=self._elapsed_ms(start),
            )
        
        # Sanitize dangerous characters
        sanitized = self._dangerous_chars.sub("", content)
        if len(sanitized) != original_length:
            reasons.append("Control characters removed from content")
        
        # PII detection (warn, don't block - Rule 4.2: non-punitive)
        detected_pii = self._detect_pii_types(sanitized)
        if detected_pii:
            pii_found = True
            pii_types = detected_pii
            reasons.append(
                f"Possible PII detected: {', '.join(detected_pii)}. "
                f"Processing locally only — no data transmitted."
            )
        
        # Update statistics
        self._check_count += 1
        self._last_check_time = time.monotonic()
        
        # Determine verdict
        if pii_found:
            verdict = SearchSafetyVerdict.WARN
        elif reasons:
            verdict = SearchSafetyVerdict.WARN
        else:
            verdict = SearchSafetyVerdict.PASS
        
        return SearchSafetyReport(
            verdict=verdict,
            reasons=reasons,
            pii_detected=pii_found,
            pii_types=pii_types,
            sanitized_content=sanitized,
            original_length=original_length,
            processing_time_ms=self._elapsed_ms(start),
        )
    
    def _detect_pii_types(self, text: str) -> List[str]:
        """Detect PII types in text.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of PII type names found
        """
        scan_text = text[:self.pii_scan_limit]
        found: List[str] = []
        
        for pii_type, pattern in self._pii_patterns.items():
            if pattern.search(scan_text):
                found.append(pii_type)
        
        return found
    
    def _elapsed_ms(self, start: float) -> float:
        """Calculate elapsed milliseconds."""
        return (time.monotonic() - start) * 1000
    
    @property
    def stats(self) -> dict[str, Any]:
        """Get safety check statistics."""
        return {
            "checks_performed": self._check_count,
            "last_check_time": self._last_check_time,
        }


# Module-level convenience
_default_guard = SearchSafetyGuard()


def validate_search_content(content: str, route: str | None = None) -> SearchSafetyReport:
    """Module-level convenience for search content validation."""
    return _default_guard.validate_search_result(content, route)


def detect_search_pii(content: str) -> List[str]:
    """Module-level convenience for PII detection in search content."""
    return _default_guard._detect_pii_types(content)
