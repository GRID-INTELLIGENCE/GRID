"""
Project GUARDIAN: Safety Canary Utility.
Injects and detects hidden markers in AI responses to identify adversarial recycling.
"""

import re
import random
from typing import List

# These are invisible or rare UTF-8 sequences that won't disrupt UI but are easy to regex
# Zero-width Joiner + specific sequence
CANARY_TOKENS = [
    "\u200D\u2062\u2063\u200D",  # Variant A
    "\u200D\u2064\u2061\u200D",  # Variant B
    "\u200D\uFEFF\u200D",        # Variant C (ZWJ + BOM + ZWJ)
]

# Combined regex for fast detection
CANARY_REGEX = re.compile("|".join(CANARY_TOKENS))

class SafetyCanary:
    """Utility for response watermarking and detection."""

    @staticmethod
    def inject(text: str) -> str:
        """Inject a random canary token into the text."""
        token = random.choice(CANARY_TOKENS)
        # Append to the end of the string
        return f"{text}{token}"

    @staticmethod
    def has_canary(text: str) -> bool:
        """Check if the text contains any canary token."""
        if not text:
            return False
        return bool(CANARY_REGEX.search(text))

# Global Instance
safety_canary = SafetyCanary()
