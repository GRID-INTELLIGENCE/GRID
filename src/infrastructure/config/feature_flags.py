"""Feature flags for parasitic leak remediation phases."""

import os

FEATURE_FLAGS = {
    "eventbus_refactor": os.getenv("EVENTBUS_REFACTOR", "false").lower() == "true",
    "db_engine_disposal": os.getenv("DB_ENGINE_DISPOSAL", "false").lower() == "true",
    "parasite_guard_integration": os.getenv("PARASITE_GUARD_INTEGRATION", "false").lower() == "true",
}

__all__ = ["FEATURE_FLAGS"]
