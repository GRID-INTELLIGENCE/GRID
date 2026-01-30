"""
Encryption-at-Rest for Personal Data.

AES-256-GCM encryption for sensitive data storage.
Key management via GCP Secret Manager or local secure storage.
"""

import base64
import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    AES-256-GCM encryption for personal data.

    Features:
    - AES-256-GCM (authenticated encryption)
    - PBKDF2 key derivation
    - Salt for each encryption operation
    - Nonce for each encryption operation
    - Tag for authentication
    """

    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM
    SALT_SIZE = 16  # 128 bits
    ITERATIONS = 100000  # PBKDF2 iterations

    def __init__(self, master_key: bytes | None = None):
        """
        Initialize encryption.

        Args:
            master_key: Master encryption key (if None, loads from environment/GCP)
        """
        if master_key is None:
            master_key = self._load_master_key()

        if len(master_key) != self.KEY_SIZE:
            raise ValueError(f"Master key must be {self.KEY_SIZE} bytes")

        self.master_key = master_key
        logger.info("DataEncryption initialized with AES-256-GCM")

    def _load_master_key(self) -> bytes:
        """
        Load master encryption key.

        Priority:
        1. GRID_ENCRYPTION_KEY environment variable (base64 encoded)
        2. GCP Secret Manager
        3. Fail with error
        """
        # Try environment variable
        env_key = os.getenv("GRID_ENCRYPTION_KEY")
        if env_key:
            return base64.b64decode(env_key.encode())

        # Try GCP Secret Manager
        try:
            from .gcp_secrets import get_secret

            secret_key = get_secret("grid-production-wealth-data-encryption", required=False)
            if secret_key:
                return base64.b64decode(secret_key.encode())
        except Exception as e:
            logger.warning(f"Failed to load GCP secret key: {e}")

        raise ValueError(
            "Encryption key not found. Set GRID_ENCRYPTION_KEY environment variable "
            "or configure grid-production-wealth-data-encryption in GCP Secret Manager."
        )

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password or passphrase
            salt: Random salt

        Returns:
            Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str | bytes, associated_data: bytes = b"") -> dict:
        """
        Encrypt data using AES-256-GCM.

        Args:
            plaintext: Data to encrypt (string or bytes)
            associated_data: Additional authenticated data (not encrypted)

        Returns:
            Dictionary with ciphertext, nonce, tag, salt
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Generate salt and nonce
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)

        # Derive key from master key + salt
        key = hashlib.pbkdf2_hmac("sha256", self.master_key, salt, self.ITERATIONS, dklen=self.KEY_SIZE)

        # Encrypt
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)

        # Split ciphertext and tag (GCM appends tag to ciphertext)
        tag = ciphertext[-16:]  # Last 16 bytes is the tag
        actual_ciphertext = ciphertext[:-16]

        return {
            "ciphertext": base64.b64encode(actual_ciphertext).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "tag": base64.b64encode(tag).decode("utf-8"),
            "salt": base64.b64encode(salt).decode("utf-8"),
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2-SHA256",
            "iterations": self.ITERATIONS,
        }

    def decrypt(self, encrypted_data: dict, associated_data: bytes = b"") -> str:
        """
        Decrypt data using AES-256-GCM.

        Args:
            encrypted_data: Dictionary with ciphertext, nonce, tag, salt
            associated_data: Additional authenticated data

        Returns:
            Decrypted plaintext string
        """
        # Decode base64 components
        ciphertext = base64.b64decode(encrypted_data["ciphertext"].encode())
        nonce = base64.b64decode(encrypted_data["nonce"].encode())
        tag = base64.b64decode(encrypted_data["tag"].encode())
        salt = base64.b64decode(encrypted_data["salt"].encode())

        # Derive key
        key = hashlib.pbkdf2_hmac(
            "sha256", self.master_key, salt, encrypted_data.get("iterations", self.ITERATIONS), dklen=self.KEY_SIZE
        )

        # Combine ciphertext and tag
        ciphertext_with_tag = ciphertext + tag

        # Decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data)

        return plaintext.decode("utf-8")

    def encrypt_json(self, data: Any) -> str:
        """
        Encrypt JSON-serializable data.

        Args:
            data: Data to encrypt

        Returns:
            JSON string with encrypted data
        """
        plaintext = json.dumps(data)
        encrypted = self.encrypt(plaintext)
        return json.dumps(encrypted)

    def decrypt_json(self, encrypted_json: str) -> Any:
        """
        Decrypt JSON-encrypted data.

        Args:
            encrypted_json: Encrypted JSON string

        Returns:
            Decrypted data
        """
        encrypted_data = json.loads(encrypted_json)
        decrypted = self.decrypt(encrypted_data)
        return json.loads(decrypted)


class EncryptedStorage:
    """
    Wrapper for storage backends with automatic encryption.

    Encrypts data before writing to storage and decrypts on read.
    """

    def __init__(self, storage_path: str, encryption: DataEncryption):
        """
        Initialize encrypted storage.

        Args:
            storage_path: Path to storage file/database
            encryption: DataEncryption instance
        """
        self.storage_path = storage_path
        self.encryption = encryption
        logger.info(f"EncryptedStorage initialized: {storage_path}")

    def write(self, key: str, data: Any) -> None:
        """
        Write encrypted data to storage.

        Args:
            key: Data identifier
            data: Data to encrypt and store
        """
        encrypted = self.encryption.encrypt_json(data)

        # Store with key prefix
        with open(self.storage_path, "a") as f:
            f.write(f"{key}:{encrypted}\n")

        logger.debug(f"Encrypted and stored: {key}")

    def read(self, key: str) -> Any | None:
        """
        Read and decrypt data from storage.

        Args:
            key: Data identifier

        Returns:
            Decrypted data or None if not found
        """
        try:
            with open(self.storage_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    stored_key, encrypted_json = line.split(":", 1)
                    if stored_key == key:
                        decrypted = self.encryption.decrypt_json(encrypted_json)
                        logger.debug(f"Decrypted: {key}")
                        return decrypted

            return None
        except FileNotFoundError:
            logger.warning(f"Storage file not found: {self.storage_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return None


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.

    Returns:
        Base64-encoded encryption key
    """
    key = os.urandom(32)  # 256 bits
    return base64.b64encode(key).decode("utf-8")


def initialize_encryption() -> DataEncryption:
    """
    Initialize global encryption instance.

    Returns:
        DataEncryption instance
    """
    return DataEncryption()


# Wealth management specific encryption
class WealthDataEncryption:
    """
    Specialized encryption for wealth management data.

    Provides additional metadata and validation for financial data.
    """

    def __init__(self, encryption: DataEncryption):
        """Initialize with DataEncryption instance."""
        self.encryption = encryption
        logger.info("WealthDataEncryption initialized")

    def encrypt_personal_profile(self, profile_data: dict) -> dict:
        """
        Encrypt personal profile data.

        Args:
            profile_data: Personal profile information

        Returns:
            Encrypted profile with metadata
        """
        # Add metadata for audit
        encrypted_profile = self.encryption.encrypt_json(
            {
                "data": profile_data,
                "metadata": {
                    "data_type": "personal_profile",
                    "classification": "PERSONAL_CONFIDENTIAL",
                    "encryption_timestamp": datetime.now(UTC).isoformat(),
                    "encryption_version": "AES-256-GCM-v1",
                },
            }
        )

        return {
            "encrypted_profile": encrypted_profile,
            "classification": "PERSONAL_CONFIDENTIAL",
            "access_required": "authorized_personnel_only",
        }

    def encrypt_asset_data(self, asset_data: list) -> dict:
        """
        Encrypt asset registry data.

        Args:
            asset_data: List of asset information

        Returns:
            Encrypted asset data with metadata
        """
        return {
            "encrypted_assets": self.encryption.encrypt_json(
                {
                    "data": asset_data,
                    "metadata": {
                        "data_type": "asset_registry",
                        "classification": "FINANCIAL_CONFIDENTIAL",
                        "encryption_timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            ),
            "classification": "FINANCIAL_CONFIDENTIAL",
            "access_required": "financial_team_only",
        }
