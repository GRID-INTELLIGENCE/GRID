"""
Portfolio Data Security
=======================
Full security guardrails for portfolio data as personal sensitive information.

Security Level: CRITICAL
Privacy: Personal Sensitive Information
AI Safety: Full privileges required
"""

import base64
import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

try:
    from cryptography.hazmat.primitives import hashes  # type: ignore
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning(
        "cryptography package not installed. Install with: pip install cryptography. "
        "Encryption will not be available."
    )

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for data access."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    CRITICAL = "CRITICAL"


class AccessLevel(Enum):
    """Access levels for portfolio data."""

    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    ADMIN = "ADMIN"
    AUDIT = "AUDIT"


@dataclass
class SecurityContext:
    """Security context for data access."""

    user_id_hash: str
    access_level: AccessLevel
    timestamp: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None


class PortfolioDataSecurity:
    """
    Full security guardrails for portfolio data.

    Treats portfolio data as personal sensitive information with:
    - Encryption at rest and in transit
    - Access controls
    - Audit logging
    - AI safety privileges
    """

    def __init__(self, encryption_key: bytes | None = None):
        """
        Initialize security module.

        Args:
            encryption_key: Optional 32-byte AES-256 key. If not provided,
                           will try to load from GRID_ENCRYPTION_KEY env var,
                           or generate a new one (not recommended for production).
        """
        self.security_level = SecurityLevel.CRITICAL
        self.encryption_key = self._initialize_encryption_key(encryption_key)
        self.audit_log: list[dict[str, Any]] = []
        self.max_audit_entries = 1000

        if not CRYPTO_AVAILABLE:
            logger.error(
                "SECURITY WARNING: cryptography package not available. "
                "Data encryption is DISABLED. Install with: pip install cryptography"
            )

    def _initialize_encryption_key(self, provided_key: bytes | None = None) -> bytes:
        """
        Initialize encryption key from various sources.

        Priority:
        1. Provided key parameter
        2. GRID_ENCRYPTION_KEY environment variable (base64 encoded)
        3. Generate new key (with warning)

        Returns:
            32-byte encryption key
        """
        # Use provided key
        if provided_key:
            if len(provided_key) != 32:
                raise ValueError("Encryption key must be exactly 32 bytes for AES-256")
            return provided_key

        # Try environment variable
        env_key = os.environ.get("GRID_ENCRYPTION_KEY")
        if env_key:
            try:
                decoded_key = base64.b64decode(env_key)
                if len(decoded_key) != 32:
                    raise ValueError("GRID_ENCRYPTION_KEY must be 32 bytes when decoded")
                return decoded_key
            except Exception as e:
                logger.error(f"Failed to decode GRID_ENCRYPTION_KEY: {e}")
                raise

        # Generate new key (not recommended for production)
        logger.warning(
            "SECURITY WARNING: Generating ephemeral encryption key. "
            "Data encrypted in this session cannot be decrypted later. "
            "Set GRID_ENCRYPTION_KEY environment variable for persistent encryption."
        )
        return secrets.token_bytes(32)

    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a new encryption key for use in GRID_ENCRYPTION_KEY.

        Returns:
            Base64-encoded 32-byte key suitable for environment variable
        """
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode("utf-8")

    def hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID for privacy.

        Args:
            user_id: Original user ID

        Returns:
            Hashed user ID
        """
        # Double hashing for enhanced security
        first_hash = hashlib.sha256(user_id.encode()).hexdigest()
        second_hash = hashlib.sha256(first_hash.encode()).hexdigest()
        return second_hash

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data using AES-256-GCM.

        AES-256-GCM provides:
        - Confidentiality (256-bit encryption)
        - Integrity (authentication tag)
        - Unique nonce per encryption

        Args:
            data: Data to encrypt

        Returns:
            Base64-encoded encrypted data (nonce + ciphertext + tag)

        Raises:
            RuntimeError: If cryptography package is not available
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "Encryption not available. Install cryptography package: pip install cryptography"
            )

        # Generate a unique 12-byte nonce for each encryption
        nonce = secrets.token_bytes(12)

        # Create AESGCM cipher
        aesgcm = AESGCM(self.encryption_key)

        # Encrypt data (includes authentication tag)
        ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)

        # Combine nonce + ciphertext for storage
        encrypted_blob = nonce + ciphertext

        # Return as base64 for safe string storage
        return base64.b64encode(encrypted_blob).decode("utf-8")

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data using AES-256-GCM.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted string

        Raises:
            RuntimeError: If cryptography package is not available
            ValueError: If decryption fails (wrong key or tampered data)
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "Decryption not available. Install cryptography package: pip install cryptography"
            )

        try:
            # Decode from base64
            encrypted_blob = base64.b64decode(encrypted_data)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_blob[:12]
            ciphertext = encrypted_blob[12:]

            # Create AESGCM cipher and decrypt
            aesgcm = AESGCM(self.encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext.decode("utf-8")  # type: ignore

        except Exception as e:
            self._log_security_event(
                "DECRYPTION_FAILED", f"Failed to decrypt data: {type(e).__name__}"
            )
            raise ValueError(f"Decryption failed: {e}") from e

    def validate_access(
        self,
        context: SecurityContext,
        access_level: AccessLevel | None = None,
        user_id: str | None = None,
    ) -> bool:
        """
        Validate access to portfolio data.

        Args:
            context: Security context
            access_level: Required access level (optional)
            user_id: User ID for validation (optional)

        Returns:
            True if access granted
        """
        # Hash user ID if provided
        if user_id is not None:
            user_id_hash = self.hash_user_id(user_id)

            # Verify context matches
            if context.user_id_hash != user_id_hash:
                self._log_security_event("ACCESS_DENIED", "User ID mismatch")
                return False

        # Check access level
        required_level = access_level or context.access_level

        if required_level == AccessLevel.READ_ONLY:
            granted = context.access_level in [
                AccessLevel.READ_ONLY,
                AccessLevel.READ_WRITE,
                AccessLevel.ADMIN,
            ]
        elif required_level == AccessLevel.READ_WRITE:
            granted = context.access_level in [AccessLevel.READ_WRITE, AccessLevel.ADMIN]
        elif required_level == AccessLevel.ADMIN:
            granted = context.access_level == AccessLevel.ADMIN
        else:
            granted = False

        if not granted:
            self._log_security_event(
                "ACCESS_DENIED", f"Insufficient access level: {context.access_level}"
            )
            return False

        self._log_security_event("ACCESS_GRANTED", f"Access level: {required_level.value}")
        return True

    def _log_security_event(
        self, event_type: str, details: str, user_id_hash: str | None = None
    ) -> None:
        """
        Log security event.

        Args:
            event_type: Type of security event
            details: Event details
            user_id_hash: Hashed user ID
        """
        event = {
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "user_id_hash": user_id_hash,
        }

        self.audit_log.append(event)

        # Trim audit log if too large
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries :]

        logger.warning(f"Security Event: {event_type} - {details}")

    def sanitize_portfolio_data(self, portfolio_data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize portfolio data for output.

        Args:
            portfolio_data: Raw portfolio data

        Returns:
            Sanitized portfolio data
        """
        sanitized = {
            "total_positions": portfolio_data.get("total_positions", 0),
            "total_value": portfolio_data.get("total_value", 0.0),
            "total_gain_loss": portfolio_data.get("total_gain_loss", 0.0),
            "gain_loss_percentage": portfolio_data.get("gain_loss_percentage", 0.0),
            "risk_level": portfolio_data.get("risk_level", "UNKNOWN"),
            "recommendation": portfolio_data.get("recommendation", ""),
        }

        # Remove sensitive fields
        if "positions" in portfolio_data:
            sanitized["positions_count"] = len(portfolio_data["positions"])
        else:
            sanitized["positions_count"] = 0

        return sanitized

    def create_security_context(
        self,
        user_id: str,
        access_level: AccessLevel,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SecurityContext:
        """
        Create security context.

        Args:
            user_id: User ID
            access_level: Access level
            ip_address: IP address
            user_agent: User agent

        Returns:
            Security context
        """
        user_id_hash = self.hash_user_id(user_id)
        session_id = secrets.token_hex(16)

        return SecurityContext(
            user_id_hash=user_id_hash,
            access_level=access_level,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

    def get_audit_log(self, user_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            user_id: User ID to filter by
            limit: Max entries to return

        Returns:
            Audit log entries
        """
        if user_id:
            user_id_hash = self.hash_user_id(user_id)
            filtered = [
                entry for entry in self.audit_log if entry.get("user_id_hash") == user_id_hash
            ]
            return filtered[-limit:]

        return self.audit_log[-limit:]


# Singleton instance
_security_instance: PortfolioDataSecurity | None = None


def get_portfolio_security() -> PortfolioDataSecurity:
    """
    Get singleton portfolio security instance.

    Returns:
        PortfolioDataSecurity instance
    """
    global _security_instance
    if _security_instance is None:
        _security_instance = PortfolioDataSecurity()
    return _security_instance


# Example usage
def example_usage() -> None:
    """Example usage of portfolio data security."""
    print("=" * 70)
    print("Portfolio Data Security Demo")
    print("=" * 70)
    print()

    # Initialize security
    security = PortfolioDataSecurity()

    # Hash user ID
    user_id = "user123"
    hashed_id = security.hash_user_id(user_id)
    print(f"User ID: {user_id}")
    print(f"Hashed ID: {hashed_id[:16]}...")
    print()

    # Create security context
    context = security.create_security_context(user_id=user_id, access_level=AccessLevel.READ_WRITE)
    print("Security Context Created")
    print(f"  Access Level: {context.access_level.value}")
    print(f"  Session ID: {context.session_id[:16] if context.session_id else 'None'}...")
    print()

    # Validate access
    granted = security.validate_access(
        user_id=user_id, access_level=AccessLevel.READ_WRITE, context=context
    )
    print(f"Access Granted: {granted}")
    print()

    # Encrypt/decrypt data
    sensitive_data = "Portfolio value: $50,000"
    encrypted = security.encrypt_data(sensitive_data)
    decrypted = security.decrypt_data(encrypted)
    print(f"Original: {sensitive_data}")
    print(f"Encrypted: {encrypted[:32]}...")
    print(f"Decrypted: {decrypted}")
    print()

    # Sanitize portfolio data
    portfolio_data = {
        "total_positions": 5,
        "total_value": 50000.0,
        "total_gain_loss": 5000.0,
        "gain_loss_percentage": 10.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 50, "value": 10000.0},
            {"symbol": "MSFT", "quantity": 30, "value": 15000.0},
        ],
    }

    sanitized = security.sanitize_portfolio_data(portfolio_data)
    print("Sanitized Portfolio Data:")
    print(f"  Total Positions: {sanitized['total_positions']}")
    print(f"  Total Value: ${sanitized['total_value']:,.2f}")
    print(f"  Positions Count: {sanitized['positions_count']}")
    print("  (Individual positions removed for security)")
    print()

    # Get audit log
    audit_log = security.get_audit_log(limit=5)
    print(f"Audit Log Entries: {len(audit_log)}")
    for entry in audit_log:
        print(f"  {entry['event_type']}: {entry['details']}")


if __name__ == "__main__":
    example_usage()
