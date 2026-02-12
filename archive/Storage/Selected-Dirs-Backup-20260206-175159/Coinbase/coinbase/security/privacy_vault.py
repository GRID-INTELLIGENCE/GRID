"""
Privacy Vault
=============
Security and privacy - Vault pattern.

Reference: Vault - Encrypt and protect user data
"""

import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EncryptedData:
    """Encrypted data wrapper."""

    original: str
    hashed: str
    algorithm: str = "SHA-256"


class PrivacyVault:
    """
    Encrypt user data like a Vault.

    Protects user privacy with hashing.
    """

    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """
        Hash user ID for privacy.

        Args:
            user_id: Original user ID

        Returns:
            Hashed user ID (SHA-256)
        """
        return hashlib.sha256(user_id.encode()).hexdigest()

    @staticmethod
    def hash_data(data: str) -> EncryptedData:
        """
        Hash arbitrary data.

        Args:
            data: Data to hash

        Returns:
            EncryptedData with original and hashed values
        """
        return EncryptedData(
            original=data, hashed=hashlib.sha256(data.encode()).hexdigest(), algorithm="SHA-256"
        )

    @staticmethod
    def parameterized_query(query: str, params: tuple) -> tuple[str, tuple]:
        """
        Ensure parameterized query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Tuple of (query, params)

        Raises:
            ValueError: If query contains dangerous keywords
        """
        # Validate query pattern
        if not query.strip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
            raise ValueError("Invalid query type")

        # Check for dangerous keywords
        dangerous = ["DROP", "TRUNCATE", "ALTER"]
        for keyword in dangerous:
            if keyword in query.upper():
                raise ValueError(f"Dangerous keyword: {keyword}")

        # Check for SQL injection patterns
        injection_patterns = ["'", "--", "/*", "*/", "xp_", "sp_"]
        for pattern in injection_patterns:
            if pattern in query:
                raise ValueError(f"Potential SQL injection: {pattern}")

        return query, params

    @staticmethod
    def validate_query(query: str) -> bool:
        """
        Validate query safety.

        Args:
            query: SQL query string

        Returns:
            True if safe
        """
        try:
            PrivacyVault.parameterized_query(query, ())
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_input(value: str) -> str:
        """
        Sanitize user input.

        Args:
            value: Input string

        Returns:
            Sanitized string
        """
        # Remove dangerous characters
        dangerous = ["'", ";", "--", "/*", "*/"]
        for char in dangerous:
            value = value.replace(char, "")

        return value.strip()


# Example usage
def example_usage() -> None:
    """Example usage of PrivacyVault."""
    vault = PrivacyVault()

    # Hash user ID
    hashed_id = vault.hash_user_id("user123")
    print(f"Hashed ID: {hashed_id[:16]}...")

    # Validate query
    query1 = "SELECT * FROM portfolio_positions WHERE user_id_hash = ?"
    is_safe1 = vault.validate_query(query1)
    print(f"Query 1 safe: {is_safe1}")

    query2 = "DROP TABLE portfolio_positions"
    is_safe2 = vault.validate_query(query2)
    print(f"Query 2 safe: {is_safe2}")


if __name__ == "__main__":
    example_usage()
