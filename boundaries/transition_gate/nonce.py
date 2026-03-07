"""
Nonce Registry: single-use nonce generation, verification, and persistence.

Each sealed envelope gets a unique nonce. On verification, the nonce is
"burned" (marked as used) so replay attacks are rejected. The registry
persists to a JSON file for durability across process restarts.

Security properties:
- Nonces are UUID4 (128-bit random, cryptographically strong)
- Burn-after-verify: a nonce can only be used once
- Persistence: survives process restarts via JSON file
- Pruning: expired nonces are cleaned up to prevent unbounded growth
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class NonceEntry:
    """Record of a nonce's lifecycle."""

    nonce: str
    created_at: float
    burned: bool = False
    burned_at: float | None = None
    envelope_id: str | None = None
    source: str | None = None

    def is_expired(self, max_age_seconds: float) -> bool:
        """Check if this nonce has exceeded its maximum age."""
        return (time.time() - self.created_at) > max_age_seconds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> NonceEntry:
        return cls(
            nonce=d["nonce"],
            created_at=float(d["created_at"]),
            burned=d.get("burned", False),
            burned_at=d.get("burned_at"),
            envelope_id=d.get("envelope_id"),
            source=d.get("source"),
        )


class NonceRegistry:
    """
    Thread-safe, persistent single-use nonce registry.

    Nonces are generated at seal time and burned at verify time.
    The registry can be backed by a JSON file for durability.

    Args:
        registry_path: Path to the JSON persistence file. If None,
                       operates in-memory only (no persistence).
        max_age_seconds: Maximum age of a nonce before it is considered
                         expired. Default is 600 seconds (10 minutes).
        auto_prune: Whether to automatically prune expired nonces on
                    each operation. Default is True.
    """

    def __init__(
        self,
        registry_path: Path | str | None = None,
        *,
        max_age_seconds: float = 600.0,
        auto_prune: bool = True,
    ):
        self._registry_path = Path(registry_path) if registry_path else None
        self._max_age_seconds = max_age_seconds
        self._auto_prune = auto_prune
        self._lock = threading.Lock()
        self._nonces: dict[str, NonceEntry] = {}
        self._load()

    @property
    def max_age_seconds(self) -> float:
        """Maximum nonce lifetime in seconds."""
        return self._max_age_seconds

    def generate(
        self,
        *,
        envelope_id: str | None = None,
        source: str | None = None,
    ) -> str:
        """
        Generate a new single-use nonce and register it.

        Args:
            envelope_id: Optional envelope ID to associate with this nonce.
            source: Optional source identifier (e.g. "E:\\" partition label).

        Returns:
            The generated nonce string (UUID4 hex).
        """
        nonce = uuid.uuid4().hex
        entry = NonceEntry(
            nonce=nonce,
            created_at=time.time(),
            envelope_id=envelope_id,
            source=source,
        )

        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()
            self._nonces[nonce] = entry
            self._persist_locked()

        return nonce

    def validate(self, nonce: str) -> tuple[bool, str]:
        """
        Check if a nonce is valid (exists, not burned, not expired)
        WITHOUT burning it. Use this for dry-run verification.

        Args:
            nonce: The nonce string to validate.

        Returns:
            Tuple of (is_valid, reason). reason is "valid" on success,
            or a descriptive rejection reason on failure.
        """
        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()

            entry = self._nonces.get(nonce)
            if entry is None:
                return (False, "nonce_unknown")
            if entry.burned:
                return (False, "nonce_already_burned")
            if entry.is_expired(self._max_age_seconds):
                return (False, "nonce_expired")
            return (True, "valid")

    def burn(self, nonce: str) -> tuple[bool, str]:
        """
        Burn a nonce (mark as used). This is the core replay-prevention
        mechanism. A burned nonce can never be used again.

        Args:
            nonce: The nonce string to burn.

        Returns:
            Tuple of (success, reason). success is True if the nonce was
            valid and has now been burned. reason describes the outcome.
        """
        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()

            entry = self._nonces.get(nonce)
            if entry is None:
                return (False, "nonce_unknown")
            if entry.burned:
                return (False, "nonce_already_burned")
            if entry.is_expired(self._max_age_seconds):
                return (False, "nonce_expired")

            entry.burned = True
            entry.burned_at = time.time()
            self._persist_locked()
            return (True, "burned")

    def is_burned(self, nonce: str) -> bool:
        """Check if a specific nonce has been burned."""
        with self._lock:
            entry = self._nonces.get(nonce)
            if entry is None:
                return False
            return entry.burned

    def contains(self, nonce: str) -> bool:
        """Check if a nonce exists in the registry (burned or not)."""
        with self._lock:
            return nonce in self._nonces

    def prune_expired(self) -> int:
        """
        Remove expired nonces from the registry.

        Returns:
            Number of nonces pruned.
        """
        with self._lock:
            count = self._prune_expired_locked()
            if count > 0:
                self._persist_locked()
            return count

    def clear(self) -> None:
        """Clear all nonces from the registry. Use with caution."""
        with self._lock:
            self._nonces.clear()
            self._persist_locked()

    @property
    def count(self) -> int:
        """Total number of nonces in the registry (burned + active)."""
        with self._lock:
            return len(self._nonces)

    @property
    def active_count(self) -> int:
        """Number of nonces that are not burned and not expired."""
        with self._lock:
            return sum(1 for e in self._nonces.values() if not e.burned and not e.is_expired(self._max_age_seconds))

    @property
    def burned_count(self) -> int:
        """Number of burned nonces still in the registry."""
        with self._lock:
            return sum(1 for e in self._nonces.values() if e.burned)

    def get_entry(self, nonce: str) -> NonceEntry | None:
        """Get a copy of the nonce entry, or None if not found."""
        with self._lock:
            entry = self._nonces.get(nonce)
            if entry is None:
                return None
            # Return a copy to prevent external mutation
            return NonceEntry(
                nonce=entry.nonce,
                created_at=entry.created_at,
                burned=entry.burned,
                burned_at=entry.burned_at,
                envelope_id=entry.envelope_id,
                source=entry.source,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire registry to a dict."""
        with self._lock:
            return {
                "max_age_seconds": self._max_age_seconds,
                "nonces": {k: v.to_dict() for k, v in self._nonces.items()},
            }

    # ── Internal methods (must be called with self._lock held) ──

    def _prune_expired_locked(self) -> int:
        """Remove expired nonces. Caller must hold self._lock."""
        expired = [k for k, v in self._nonces.items() if v.is_expired(self._max_age_seconds)]
        for k in expired:
            del self._nonces[k]
        return len(expired)

    def _persist_locked(self) -> None:
        """Write registry to disk. Caller must hold self._lock."""
        if self._registry_path is None:
            return
        try:
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "max_age_seconds": self._max_age_seconds,
                "nonces": {k: v.to_dict() for k, v in self._nonces.items()},
            }
            # Atomic write: write to temp, then rename
            tmp_path = self._registry_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp_path.replace(self._registry_path)
        except OSError:
            # Persist is best-effort; log failures upstream if needed
            pass

    def _load(self) -> None:
        """Load registry from disk if available."""
        if self._registry_path is None or not self._registry_path.exists():
            return
        try:
            with open(self._registry_path, encoding="utf-8") as f:
                data = json.load(f)
            nonces_data = data.get("nonces", {})
            for key, val in nonces_data.items():
                self._nonces[key] = NonceEntry.from_dict(val)
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            # Corrupted registry file — start fresh
            self._nonces = {}
