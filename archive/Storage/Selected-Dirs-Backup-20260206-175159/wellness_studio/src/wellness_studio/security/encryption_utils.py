"""
Wellness Studio - Data Encryption Utilities
Secure encryption/decryption using Fernet (AES-128-CBC)
"""
import base64
import os
import hashlib
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class EncryptionResult:
    """Result of encryption operation"""
    encrypted_data: bytes
    salt: Optional[bytes]
    iv: Optional[bytes]
    algorithm: str


class DataEncryption:
    """
    Secure data encryption using Fernet (AES-128-CBC)
    Supports key rotation and field-level encryption
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize encryption
        
        Args:
            encryption_key: Optional encryption key. If not provided, generates one.
        """
        if encryption_key:
            self.key = encryption_key
        else:
            self.key = Fernet.generate_key()
        
        self.fernet = Fernet(self.key)
        self.key_version = 1
        self.key_history: Dict[int, bytes] = {1: self.key}
    
    def encrypt_string(
        self,
        plaintext: str
    ) -> str:
        """
        Encrypt a string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_string(
        self,
        ciphertext: str
    ) -> str:
        """
        Decrypt a string
        
        Args:
            ciphertext: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        encrypted_bytes = base64.b64decode(ciphertext.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def encrypt_dict(
        self,
        data: Dict[str, Any],
        fields_to_encrypt: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to process
            fields_to_encrypt: List of field names to encrypt. If None, encrypts all string fields.
            
        Returns:
            Dictionary with encrypted fields
        """
        result = {}
        
        for key, value in data.items():
            if fields_to_encrypt and key not in fields_to_encrypt:
                result[key] = value
            elif isinstance(value, str):
                result[key] = self.encrypt_string(value)
            else:
                result[key] = value
        
        return result
    
    def decrypt_dict(
        self,
        data: Dict[str, Any],
        fields_to_decrypt: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to process
            fields_to_decrypt: List of field names to decrypt. If None, decrypts all string fields.
            
        Returns:
            Dictionary with decrypted fields
        """
        result = {}
        
        for key, value in data.items():
            if fields_to_decrypt and key not in fields_to_decrypt:
                result[key] = value
            elif isinstance(value, str):
                try:
                    result[key] = self.decrypt_string(value)
                except Exception:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def encrypt_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Encrypt a file
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted output. If None, appends .enc
            
        Returns:
            Path to encrypted file
        """
        if output_path is None:
            output_path = input_path.with_name(input_path.name + '.enc')
        
        with open(input_path, 'rb') as f:
            plaintext = f.read()
        
        encrypted = self.fernet.encrypt(plaintext)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        return output_path
    
    def decrypt_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Decrypt a file
        
        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output. If None, removes .enc suffix
            
        Returns:
            Path to decrypted file
        """
        if output_path is None:
            if input_path.suffix == '.enc':
                output_path = input_path.with_suffix('')
            else:
                output_path = input_path.with_suffix('.dec')
        
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.fernet.decrypt(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path
    
    def rotate_key(self):
        """
        Rotate encryption key for security
        
        Returns:
            New key
        """
        new_key = Fernet.generate_key()
        self.key_version += 1
        self.key_history[self.key_version] = new_key
        self.key = new_key
        self.fernet = Fernet(new_key)
        
        return new_key
    
    def get_key(self, version: Optional[int] = None) -> bytes:
        """
        Get encryption key
        
        Args:
            version: Key version. If None, returns current key.
            
        Returns:
            Encryption key
        """
        if version is None:
            return self.key
        
        return self.key_history.get(version, self.key)
    
    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: Password string
            salt: Optional salt. If None, generates random salt.
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key, salt
    
    def hash_password(
        self,
        password: str,
        salt: Optional[bytes] = None
    ) -> Tuple[str, bytes]:
        """
        Hash a password using SHA-256
        
        Args:
            password: Password to hash
            salt: Optional salt. If None, generates random salt.
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        hashed = hashlib.sha256(password.encode() + salt).hexdigest()
        
        return hashed, salt
    
    def verify_password(
        self,
        password: str,
        hashed_password: str,
        salt: bytes
    ) -> bool:
        """
        Verify a password against a hash
        
        Args:
            password: Password to verify
            hashed_password: Stored hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches
        """
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == hashed_password
    
    def encrypt_sensitive_field(
        self,
        field_name: str,
        value: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Encrypt a sensitive field with metadata
        
        Args:
            field_name: Name of the field being encrypted
            value: Value to encrypt
            context: Optional context metadata
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        encrypted_value = self.encrypt_string(value)
        
        return {
            'field_name': field_name,
            'encrypted_value': encrypted_value,
            'key_version': self.key_version,
            'encryption_algorithm': 'Fernet (AES-128-CBC)',
            'timestamp': None,  # Would add timestamp here
            'context': context or {}
        }
    
    def decrypt_sensitive_field(
        self,
        encrypted_data: Dict[str, Any]
    ) -> str:
        """
        Decrypt a sensitive field
        
        Args:
            encrypted_data: Dictionary containing encrypted data
            
        Returns:
            Decrypted value
        """
        encrypted_value = encrypted_data['encrypted_value']
        return self.decrypt_string(encrypted_value)
    
    def get_encryption_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about encryption configuration
        
        Returns:
            Encryption metadata
        """
        return {
            'algorithm': 'Fernet (AES-128-CBC)',
            'key_version': self.key_version,
            'key_versions_available': list(self.key_history.keys()),
            'supports_rotation': True
        }


class FieldLevelEncryption:
    """
    Field-level encryption for structured data
    """
    
    def __init__(self, encryption: DataEncryption):
        self.encryption = encryption
        self.encryption_map: Dict[str, list] = {}
    
    def register_fields(
        self,
        data_type: str,
        field_names: list
    ):
        """
        Register fields for encryption by data type
        
        Args:
            data_type: Type identifier (e.g., 'patient_record')
            field_names: List of field names to encrypt
        """
        self.encryption_map[data_type] = field_names
    
    def encrypt_data(
        self,
        data_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Encrypt registered fields in data
        
        Args:
            data_type: Type identifier
            data: Data dictionary
            
        Returns:
            Data with encrypted fields
        """
        if data_type not in self.encryption_map:
            return data
        
        fields = self.encryption_map[data_type]
        return self.encryption.encrypt_dict(data, fields)
    
    def decrypt_data(
        self,
        data_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decrypt registered fields in data
        
        Args:
            data_type: Type identifier
            data: Data dictionary
            
        Returns:
            Data with decrypted fields
        """
        if data_type not in self.encryption_map:
            return data
        
        fields = self.encryption_map[data_type]
        return self.encryption.decrypt_dict(data, fields)
    
    def get_registered_fields(self, data_type: Optional[str] = None) -> Any:
        """
        Get registered field mappings
        
        Args:
            data_type: Optional specific data type
            
        Returns:
            Field mappings for type or all mappings
        """
        if data_type:
            return self.encryption_map.get(data_type, [])
        
        return self.encryption_map
