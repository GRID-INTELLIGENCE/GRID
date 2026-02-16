"""
Secure Configuration Management

Handles loading and validation of safety-related settings from environment variables.
"""

import os


class SecureConfig:
    """Secure configuration management with environment variables"""

    def __init__(self):
        self.safety_config = self._load_safety_config()
        self.rate_limiting = self._load_rate_limiting_config()
        self.content_safety = self._load_content_safety_config()

    def _load_safety_config(self) -> dict:
        return {
            "enable_developmental_safety": os.getenv("ENABLE_DEVELOPMENTAL_SAFETY", "true").lower() == "true",
            "min_user_age": int(os.getenv("MIN_USER_AGE", "13")),
            "max_session_length": int(os.getenv("MAX_SESSION_LENGTH", "3600")),
            "sensitive_topics": self._load_sensitive_topics(),
        }

    def _load_rate_limiting_config(self) -> dict:
        return {
            "enabled": os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true",
            "requests_per_minute": int(os.getenv("RATE_LIMIT_REQUESTS", "60")),
            "burst_size": int(os.getenv("RATE_LIMIT_BURST", "10")),
            "window_seconds": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        }

    def _load_content_safety_config(self) -> dict:
        return {
            "blocked_terms": self._load_blocked_terms(),
            "allowed_domains": self._load_allowed_domains(),
            "max_content_length": int(os.getenv("MAX_CONTENT_LENGTH", "10000")),
        }

    def _load_sensitive_topics(self) -> list[str]:
        topics = os.getenv("SENSITIVE_TOPICS", "self_harm,violence,hate_speech,exploitation")
        return [t.strip() for t in topics.split(",") if t.strip()]

    def _load_blocked_terms(self) -> list[str]:
        terms = os.getenv("BLOCKED_TERMS", "dangerous_act,harmful_content,private_key,password_leak")
        return [t.strip() for t in terms.split(",") if t.strip()]

    def _load_allowed_domains(self) -> list[str]:
        domains = os.getenv("ALLOWED_DOMAINS", "localhost,example.com,grid.internal")
        return [d.strip() for d in domains.split(",") if d.strip()]

    @classmethod
    def get_env(cls, key: str, default: str = "") -> str:
        return os.getenv(key, default)

    @classmethod
    def is_dev(cls) -> bool:
        return os.getenv("GRID_ENV", "production").lower() in ("development", "dev", "test")
