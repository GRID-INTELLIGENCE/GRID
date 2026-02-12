"""
AI Safety Denylist Engine for wellness_studio
Server categorization and safety enforcement with structured logging
"""

from pathlib import Path
import sys

# Add parent scripts path for core modules
_scripts_path = Path(__file__).parent.parent.parent.parent / "scripts"
if _scripts_path.exists():
    sys.path.insert(0, str(_scripts_path))

from server_denylist_manager import (  # type: ignore
    ServerDenylistManager,
    ServerCategory,
    DenylistReason,
)
from safety_aware_server_manager import SafetyAwareServerManager  # type: ignore
from init_safety_logging import (  # type: ignore
    SafetyLogger,
    SafetyEvent,
    EventType,
    Severity,
    RiskLevel,
    create_safety_event,
    calculate_safety_score,
    determine_risk_level,
    init_safety_logging,
)

__all__ = [
    "ServerDenylistManager",
    "ServerCategory",
    "DenylistReason",
    "SafetyAwareServerManager",
    "SafetyLogger",
    "SafetyEvent",
    "EventType",
    "Severity",
    "RiskLevel",
    "create_safety_event",
    "calculate_safety_score",
    "determine_risk_level",
    "init_safety_logging",
]

__version__ = "1.0.0"
