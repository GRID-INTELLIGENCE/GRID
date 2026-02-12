"""Crypto-related functionality."""


class CryptoScope:
    """Crypto scope manager."""

    def __init__(self, enabled: bool = False) -> None:
        """Initialize crypto scope."""
        self.enabled = enabled
        self._data: dict[str, str] = {}

    def enable(self) -> None:
        """Enable crypto scope."""
        self.enabled = True

    def disable(self) -> None:
        """Disable crypto scope."""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if crypto scope is enabled."""
        return self.enabled

    def set_data(self, key: str, value: str) -> None:
        """Set crypto data."""
        if not self.enabled:
            raise RuntimeError("Crypto scope is not enabled")
        self._data[key] = value

    def get_data(self, key: str) -> str | None:
        """Get crypto data."""
        if not self.enabled:
            raise RuntimeError("Crypto scope is not enabled")
        return self._data.get(key)

    def clear_data(self) -> None:
        """Clear all crypto data."""
        self._data.clear()
