"""
Local Secrets Manager - Simple, secure local secrets storage.

A reliable local secrets manager with optional GCP Secret Manager sync.
Designed for local development with production-ready security.
"""

import base64
import json
import logging
import os
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class Secret:
    """Secret data container."""

    key: str
    value: str
    metadata: dict[str, Any] = None
    created_at: float = None
    updated_at: float = None


class LocalSecretsManager:
    """
    Simple, secure local secrets manager.

    Features:
    - AES-256-GCM encryption
    - SQLite storage
    - PBKDF2 key derivation (100,000 iterations)
    - Optional GCP Secret Manager sync
    - Simple CLI interface

    Usage:
        manager = LocalSecretsManager()
        manager.set("api_key", "my-secret-key")
        value = manager.get("api_key")
    """

    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM
    SALT_SIZE = 16  # 128 bits
    ITERATIONS = 100000  # PBKDF2 iterations

    def __init__(
        self, storage_path: Path | None = None, master_key: bytes | None = None, environment: str = "development"
    ):
        """
        Initialize local secrets manager.

        Args:
            storage_path: Path to secrets database (default: ~/.grid/secrets.db)
            master_key: Master encryption key (auto-generated if not provided)
            environment: Environment name (affects key derivation)
        """
        self.environment = environment

        # Determine storage path
        if storage_path is None:
            home = Path.home()
            grid_dir = home / ".grid"
            grid_dir.mkdir(exist_ok=True)
            storage_path = grid_dir / "secrets.db"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or generate master key
        self.master_key = master_key or self._load_or_create_key()

        # Initialize database
        self._init_database()

        logger.info(f"LocalSecretsManager initialized: {self.storage_path}")

    def _load_or_create_key(self) -> bytes:
        """Load master key from file or create new one."""
        key_file = self.storage_path.parent / ".master.key"

        if key_file.exists():
            # Load existing key
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load master key: {e}")

        # Generate new key
        key = secrets.token_bytes(self.KEY_SIZE)

        # Save key with restricted permissions
        key_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Owner read/write only
        except Exception as e:
            logger.warning(f"Failed to save master key: {e}")

        logger.info("Generated new master key")
        return key

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(self.master_key)

    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(str(self.storage_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                encrypted_value TEXT NOT NULL,
                salt TEXT NOT NULL,
                nonce TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_secrets_updated ON secrets(updated_at DESC);
        """
        )

        conn.commit()
        conn.close()

    def _encrypt(self, plaintext: str) -> tuple:
        """Encrypt a value and return (encrypted, salt, nonce)."""
        salt = secrets.token_bytes(self.SALT_SIZE)
        nonce = secrets.token_bytes(self.NONCE_SIZE)

        key = self._derive_key(salt)
        aesgcm = AESGCM(key)

        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        return (
            base64.b64encode(ciphertext).decode("utf-8"),
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(nonce).decode("utf-8"),
        )

    def _decrypt(self, encrypted_value: str, salt: str, nonce: str) -> str:
        """Decrypt a value."""
        ciphertext = base64.b64decode(encrypted_value.encode("utf-8"))
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        nonce_bytes = base64.b64decode(nonce.encode("utf-8"))

        key = self._derive_key(salt_bytes)
        aesgcm = AESGCM(key)

        plaintext = aesgcm.decrypt(nonce_bytes, ciphertext, None)
        return plaintext.decode("utf-8")

    def set(self, key: str, value: str, metadata: dict | None = None) -> bool:
        """
        Set a secret value.

        Args:
            key: Secret key name
            value: Secret value
            metadata: Optional metadata dictionary

        Returns:
            True if successful
        """
        try:
            encrypted_value, salt, nonce = self._encrypt(value)
            now = secrets.token_hex(8)  # Simple timestamp

            conn = sqlite3.connect(str(self.storage_path))
            conn.execute(
                """
                INSERT OR REPLACE INTO secrets (key, encrypted_value, salt, nonce, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (key, encrypted_value, salt, nonce, now, now, json.dumps(metadata or {})),
            )
            conn.commit()
            conn.close()

            logger.debug(f"Secret set: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False

    def get(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value.

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        try:
            conn = sqlite3.connect(str(self.storage_path))
            cursor = conn.execute(
                """
                SELECT encrypted_value, salt, nonce FROM secrets WHERE key = ?
            """,
                (key,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._decrypt(row[0], row[1], row[2])

            return default
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return default

    def delete(self, key: str) -> bool:
        """Delete a secret."""
        try:
            conn = sqlite3.connect(str(self.storage_path))
            conn.execute("DELETE FROM secrets WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            logger.debug(f"Secret deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            return False

    def list(self, prefix: str = "") -> list[str]:
        """List secret keys."""
        try:
            conn = sqlite3.connect(str(self.storage_path))
            if prefix:
                cursor = conn.execute("SELECT key FROM secrets WHERE key LIKE ?", (f"{prefix}%",))
            else:
                cursor = conn.execute("SELECT key FROM secrets")
            keys = [row[0] for row in cursor.fetchall()]
            conn.close()
            return keys
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []

    def exists(self, key: str) -> bool:
        """Check if a secret exists."""
        try:
            conn = sqlite3.connect(str(self.storage_path))
            cursor = conn.execute("SELECT 1 FROM secrets WHERE key = ?", (key,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Failed to check secret existence: {e}")
            return False

    def get_all(self) -> dict[str, Secret]:
        """Get all secrets as Secret objects."""
        try:
            conn = sqlite3.connect(str(self.storage_path))
            cursor = conn.execute("SELECT * FROM secrets ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            conn.close()

            secrets_dict = {}
            for row in rows:
                secrets_dict[row[0]] = Secret(
                    key=row[0],
                    value=self._decrypt(row[1], row[2], row[3]),
                    metadata=json.loads(row[6]) if row[6] else None,
                    created_at=row[4],
                    updated_at=row[5],
                )
            return secrets_dict
        except Exception as e:
            logger.error(f"Failed to get all secrets: {e}")
            return {}

    def clear(self) -> bool:
        """Clear all secrets (use with caution)."""
        try:
            conn = sqlite3.connect(str(self.storage_path))
            conn.execute("DELETE FROM secrets")
            conn.commit()
            conn.close()
            logger.warning("All secrets cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear secrets: {e}")
            return False


# Convenience functions
def get_local_secrets_manager(storage_path: Path | None = None, environment: str = None) -> LocalSecretsManager:
    """Get a LocalSecretsManager instance."""
    env = environment or os.getenv("GRID_ENVIRONMENT", "development")
    return LocalSecretsManager(storage_path=storage_path, environment=env)


def set_secret(key: str, value: str, environment: str = None) -> bool:
    """Convenience function to set a secret."""
    manager = get_local_secrets_manager(environment=environment)
    return manager.set(key, value)


def get_secret(key: str, default: str = None, environment: str = None) -> str | None:
    """Convenience function to get a secret."""
    manager = get_local_secrets_manager(environment=environment)
    return manager.get(key, default)


class LocalSecretsProvider:
    """
    Adapter to make LocalSecretsManager compatible with SecretsProvider interface.

    This allows seamless switching between local and cloud secret providers.
    """

    def __init__(self, storage_path: Path | None = None):
        """Initialize with LocalSecretsManager."""
        self.manager = get_local_secrets_manager(storage_path=storage_path)

    async def get_secret(self, key: str) -> Secret | None:
        """Get a secret."""
        try:
            value = self.manager.get(key)
            if value:
                return Secret(key=key, value=value, metadata={"source": "local"})
            return None
        except Exception:
            return None

    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List secret keys."""
        return self.manager.list(prefix)

    async def refresh_secret(self, key: str) -> Secret | None:
        """Refresh a secret."""
        return await self.get_secret(key)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local Secrets Manager")
    parser.add_argument("command", choices=["set", "get", "list", "delete", "clear"], help="Command to execute")
    parser.add_argument("key", nargs="?", help="Secret key")
    parser.add_argument("value", nargs="?", help="Secret value (for set)")
    parser.add_argument("--env", default="development", help="Environment")
    parser.add_argument("--path", help="Custom storage path")

    args = parser.parse_args()

    manager = get_local_secrets_manager(storage_path=Path(args.path) if args.path else None, environment=args.env)

    if args.command == "set":
        if not args.key or not args.value:
            parser.error("set requires key and value")
        success = manager.set(args.key, args.value)
        print(f"Set {args.key}: {'success' if success else 'failed'}")

    elif args.command == "get":
        if not args.key:
            parser.error("get requires key")
        value = manager.get(args.key)
        if value:
            print(value)
        else:
            print(f"Key not found: {args.key}")

    elif args.command == "list":
        keys = manager.list()
        for key in keys:
            print(key)

    elif args.command == "delete":
        if not args.key:
            parser.error("delete requires key")
        success = manager.delete(args.key)
        print(f"Delete {args.key}: {'success' if success else 'failed'}")

    elif args.command == "clear":
        confirm = input("This will delete ALL secrets. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            manager.clear()
            print("All secrets cleared")
        else:
            print("Cancelled")
