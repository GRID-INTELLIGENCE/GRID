"""
xAI Ethical Guidelines Checker for Wellness Studio
- Basic input validation and safety checks.
- Usage: python ethical_guidelines.py --input "User query here"
"""

import argparse
import json
import re
from typing import Any, Dict

# Load risk framework
with open("risk_management_framework.json", "r") as f:
    RISK_FRAMEWORK = json.load(f)


def check_input_safety(query: str) -> Dict[str, Any]:
    """
    Check query for safety risks.
    Returns: dict with 'risk_level', 'actions', 'safe' (bool)
    """
    query_lower = query.lower()

    # High-risk keywords
    high_risk_keywords = [
        "suicide",
        "self-harm",
        "overdose",
        "die",
        "kill",
        "prescription",
        "medication",
        "diagnosis",
        "therapy",
    ]
    high_risk_count = sum(1 for kw in high_risk_keywords if kw in query_lower)

    # Medium-risk
    medium_risk_keywords = [
        "meditation",
        "anxiety",
        "depression",
        "weight loss",
        "supplement",
        "detox",
        "fasting",
    ]
    medium_risk_count = sum(1 for kw in medium_risk_keywords if kw in query_lower)

    if high_risk_count > 0:
        return {
            "risk_level": "critical",
            "actions": ["block_immediate", "alert_admin"],
            "safe": False,
            "reason": "High-risk content detected (e.g., self-harm or medical).",
        }
    elif medium_risk_count > 0:
        return {
            "risk_level": "medium",
            "actions": ["moderate", "bias_check", "notify_user"],
            "safe": True,
            "reason": "Medium-risk wellness topic; apply disclaimer.",
        }
    else:
        return {
            "risk_level": "low",
            "actions": ["log"],
            "safe": True,
            "reason": "General query.",
        }


def check_bias(text: str) -> Dict[str, Any]:
    """
    Basic bias check for wellness outputs.
    """
    # Simple regex for potential bias (customize as needed)
    bias_patterns = [
        r"\b(only|all)\s+(women|men|girls|boys)\b",  # Gender bias
        r"\b(not for|avoid if)\s+(pregnant|child(ren)?)\b",  # Exclusion
    ]
    biases = [re.search(p, text.lower()) for p in bias_patterns]
    bias_count = sum(1 for b in biases if b)

    return {
        "bias_score": min(bias_count * 0.2, 1.0),
        "has_bias": bias_count > 0,
        "suggestions": "Review for inclusive language." if bias_count > 0 else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xAI Safety Checker")
    parser.add_argument("--input", type=str, required=True, help="Input query to check")
    args = parser.parse_args()

    safety = check_input_safety(args.input)
    bias = check_bias(args.input)

    print("Safety Check:", safety)
    print("Bias Check:", bias)

    if not safety["safe"]:
        print("⚠️  Query blocked for safety reasons.")
    else:
        print("✅ Safe to process with guidelines.")
