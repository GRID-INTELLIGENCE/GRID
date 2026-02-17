"""
Model management for The Chase
"""


from typing import Dict

class OverwatchModels:
    """Model management for OVERWATCH"""

    MODELS: Dict[str, Dict[str, object]] = {
        "gemini_3_flash": {
            "capabilities": ["reasoning", "speed"],
            "use_case": "agentic_workflows"
        }
    }
