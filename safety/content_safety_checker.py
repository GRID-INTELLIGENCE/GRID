"""
Content Safety Checker

Provides mechanisms for detecting sensitive terms, topics, and age-inappropriate content.
"""

from typing import List, Dict, Any, Optional
import os
import re

from safety.config import SecureConfig

class ContentSafetyChecker:
    def __init__(self, config: Optional[SecureConfig] = None):
        self.config = config or SecureConfig()
        self.sensitive_terms = self.config.content_safety.get("blocked_terms", [])
        self.sensitive_topics = self.config.safety_config.get("sensitive_topics", [])

    def _load_sensitive_terms(self) -> List[str]:
        return self.sensitive_terms

    def _load_sensitive_topics(self) -> List[str]:
        return self.sensitive_topics

    def check_content(self, text: str, user_age: Optional[int] = None) -> Dict[str, Any]:
        """Check text for sensitive or inappropriate content"""
        issues = []

        # Check for sensitive terms
        found_terms = [term for term in self.sensitive_terms if term in text.lower()]
        if found_terms:
            issues.append({
                "type": "sensitive_term_detected",
                "terms": found_terms,
                "severity": "high"
            })

        # Check for sensitive topics (simplified regex match for example)
        for topic in self.sensitive_topics:
            if re.search(rf"\b{topic}\b", text, re.IGNORECASE):
                issues.append({
                    "type": "sensitive_topic_detected",
                    "topic": topic,
                    "severity": "high"
                })

        # Age-appropriate content filtering
        if user_age and user_age < 13:
            if self._contains_mature_content(text):
                issues.append({
                    "type": "age_inappropriate_content",
                    "severity": "high"
                })

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "checks_performed": ["sensitive_terms", "sensitive_topics", "age_appropriateness"]
        }

    def _contains_mature_content(self, text: str) -> bool:
        """Heuristic check for mature content"""
        # Simplified placeholder logic
        mature_keywords = ["adult", "explicit", "violent", "graphic"]
        return any(kw in text.lower() for kw in mature_keywords)

    def validate_user_input(self, text: str) -> bool:
        """Validate user input for safety and security (e.g., injection attempts)"""
        if not isinstance(text, str):
            return False

        # Check for potential injection attempts
        injection_patterns = [
            r"(?i)select\s.*from",
            r"(?i)union\s+select",
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            r"on\w+\s*="
        ]

        if any(re.search(pattern, text) for pattern in injection_patterns):
            return False

        # Check for excessive length
        if len(text) > 10000:  # 10KB max
            return False

        return True
