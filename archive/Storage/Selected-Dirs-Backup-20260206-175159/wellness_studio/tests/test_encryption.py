"""
Comprehensive tests for Data Encryption utilities
Tests encryption/decryption, key management, and field-level encryption
"""
import pytest
import tempfile
from pathlib import Path
from wellness_studio.security import (
    DataEncryption,
    FieldLevelEncryption,
    EncryptionResult
)


class TestDataEncryption:
    """Test data encryption functionality"""
    
    @pytest.fixture
    def encryption(self):
        """Create encryption instance"""
        return DataEncryption()
    
    def test_encrypt_string(self, encryption):
        """Test encrypting a string"""
        plaintext = "sensitive_data_123"
        encrypted = encryption.encrypt_string(plaintext)
        
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
    
    def test_decrypt_string(self, encryption):
        """Test decrypting a string"""
        plaintext = "sensitive_data_123"
        encrypted = encryption.encrypt_string(plaintext)
        decrypted = encryption.decrypt_string(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_roundtrip(self, encryption):
        """Test encryption/decryption roundtrip"""
        test_strings = [
            "simple text",
            "numbers 12345",
            "special chars !@#$%",
            "unicode 你好世界",
            "multi\nline\ntext"
        ]
        
        for text in test_strings:
            encrypted = encryption.encrypt_string(text)
            decrypted = encryption.decrypt_string(encrypted)
            assert decrypted == text
    
    def test_encrypt_dict_all_fields(self, encryption):
        """Test encrypting all fields in a dictionary"""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }
        
        encrypted = encryption.encrypt_dict(data)
        
        assert encrypted["name"] != data["name"]
        assert encrypted["ssn"] != data["ssn"]
        assert encrypted["email"] != data["email"]
    
    def test_encrypt_dict_specific_fields(self, encryption):
        """Test encrypting specific fields in a dictionary"""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com",
            "age": 35
        }
        
        encrypted = encryption.encrypt_dict(data, fields_to_encrypt=["ssn", "email"])
        
        assert encrypted["name"] == data["name"]  # Not encrypted
        assert encrypted["ssn"] != data["ssn"]  # Encrypted
        assert encrypted["email"] != data["email"]  # Encrypted
        assert encrypted["age"] == data["age"]  # Not encrypted (not string)
    
    def test_decrypt_dict(self, encryption):
        """Test decrypting a dictionary"""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }
        
        encrypted = encryption.encrypt_dict(data)
        decrypted = encryption.decrypt_dict(encrypted)
        
        assert decrypted["name"] == data["name"]
        assert decrypted["ssn"] == data["ssn"]
        assert decrypted["email"] == data["email"]
    
    def test_encrypt_file(self, encryption):
        """Test encrypting a file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "test.txt"
            input_file.write_text("sensitive file content")
            
            encrypted_file = encryption.encrypt_file(input_file)
            
            assert encrypted_file.exists()
            assert encrypted_file.name == "test.txt.enc"
            assert ".enc" in encrypted_file.suffixes
            encrypted_content = encrypted_file.read_text()
            assert encrypted_content != "sensitive file content"
    
    def test_decrypt_file(self, encryption):
        """Test decrypting a file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "test.txt"
            input_file.write_text("sensitive file content")
            
            encrypted_file = encryption.encrypt_file(input_file)
            decrypted_file = encryption.decrypt_file(encrypted_file)
            
            assert decrypted_file.exists()
            decrypted_content = decrypted_file.read_text()
            assert decrypted_content == "sensitive file content"
    
    def test_key_rotation(self, encryption):
        """Test key rotation"""
        old_key = encryption.key
        
        new_key = encryption.rotate_key()
        
        assert new_key != old_key
        assert encryption.key == new_key
        assert encryption.key_version == 2
    
    def test_key_history(self, encryption):
        """Test key history tracking"""
        initial_key = encryption.key
        initial_version = encryption.key_version
        
        encryption.rotate_key()
        encryption.rotate_key()
        
        assert encryption.key_version == initial_version + 2
        assert len(encryption.key_history) == 3
        assert 1 in encryption.key_history
        assert 2 in encryption.key_history
        assert 3 in encryption.key_history
    
    def test_get_key_by_version(self, encryption):
        """Test retrieving key by version"""
        initial_key = encryption.key
        encryption.rotate_key()
        
        retrieved_key = encryption.get_key(1)
        
        assert retrieved_key == initial_key
    
    def test_derive_key_from_password(self, encryption):
        """Test deriving key from password"""
        password = "secure_password_123"
        
        key, salt = encryption.derive_key_from_password(password)
        
        assert key is not None
        assert salt is not None
        assert isinstance(key, bytes)
        assert isinstance(salt, bytes)
    
    def test_derive_key_with_salt(self, encryption):
        """Test deriving key with provided salt"""
        password = "secure_password_123"
        salt = b"fixed_salt_value"
        
        key1, _ = encryption.derive_key_from_password(password, salt)
        key2, _ = encryption.derive_key_from_password(password, salt)
        
        assert key1 == key2
    
    def test_hash_password(self, encryption):
        """Test password hashing"""
        password = "secure_password_123"
        
        hashed, salt = encryption.hash_password(password)
        
        assert hashed is not None
        assert salt is not None
        assert hashed != password
        assert len(salt) == 32
    
    def test_verify_password(self, encryption):
        """Test password verification"""
        password = "secure_password_123"
        hashed, salt = encryption.hash_password(password)
        
        assert encryption.verify_password(password, hashed, salt) is True
        assert encryption.verify_password("wrong_password", hashed, salt) is False
    
    def test_encrypt_sensitive_field(self, encryption):
        """Test encrypting sensitive field with metadata"""
        result = encryption.encrypt_sensitive_field(
            field_name="ssn",
            value="123-45-6789",
            context={"purpose": "medical_record"}
        )
        
        assert "field_name" in result
        assert "encrypted_value" in result
        assert "key_version" in result
        assert result["field_name"] == "ssn"
        assert result["encrypted_value"] != "123-45-6789"
    
    def test_decrypt_sensitive_field(self, encryption):
        """Test decrypting sensitive field"""
        encrypted = encryption.encrypt_sensitive_field(
            field_name="ssn",
            value="123-45-6789"
        )
        
        decrypted = encryption.decrypt_sensitive_field(encrypted)
        
        assert decrypted == "123-45-6789"
    
    def test_get_encryption_metadata(self, encryption):
        """Test getting encryption metadata"""
        metadata = encryption.get_encryption_metadata()
        
        assert "algorithm" in metadata
        assert "key_version" in metadata
        assert "supports_rotation" in metadata
        assert metadata["supports_rotation"] is True
    
    def test_empty_string_encryption(self, encryption):
        """Test encrypting empty string"""
        plaintext = ""
        encrypted = encryption.encrypt_string(plaintext)
        decrypted = encryption.decrypt_string(encrypted)
        
        assert decrypted == plaintext
    
    def test_large_string_encryption(self, encryption):
        """Test encrypting large string"""
        plaintext = "x" * 10000
        encrypted = encryption.encrypt_string(plaintext)
        decrypted = encryption.decrypt_string(encrypted)
        
        assert decrypted == plaintext
    
    def test_unicode_encryption(self, encryption):
        """Test encrypting unicode characters"""
        plaintext = "Hello 世界 🌍 Привет مرحبا"
        encrypted = encryption.encrypt_string(plaintext)
        decrypted = encryption.decrypt_string(encrypted)
        
        assert decrypted == plaintext
    
    def test_invalid_decryption(self, encryption):
        """Test decrypting invalid data"""
        with pytest.raises(Exception):
            encryption.decrypt_string("invalid_encrypted_data")


class TestFieldLevelEncryption:
    """Test field-level encryption for structured data"""
    
    @pytest.fixture
    def encryption(self):
        """Create encryption instance"""
        return DataEncryption()
    
    @pytest.fixture
    def field_encryption(self, encryption):
        """Create field-level encryption"""
        return FieldLevelEncryption(encryption)
    
    def test_register_fields(self, field_encryption):
        """Test registering fields for encryption"""
        field_encryption.register_fields(
            data_type="patient_record",
            field_names=["ssn", "email", "phone"]
        )
        
        fields = field_encryption.get_registered_fields("patient_record")
        
        assert "ssn" in fields
        assert "email" in fields
        assert "phone" in fields
    
    def test_encrypt_data_with_registered_fields(self, field_encryption):
        """Test encrypting data with registered fields"""
        field_encryption.register_fields(
            data_type="patient_record",
            field_names=["ssn", "email"]
        )
        
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com",
            "age": 35
        }
        
        encrypted = field_encryption.encrypt_data("patient_record", data)
        
        assert encrypted["name"] == data["name"]  # Not encrypted
        assert encrypted["ssn"] != data["ssn"]  # Encrypted
        assert encrypted["email"] != data["email"]  # Encrypted
        assert encrypted["age"] == data["age"]  # Not encrypted
    
    def test_decrypt_data_with_registered_fields(self, field_encryption):
        """Test decrypting data with registered fields"""
        field_encryption.register_fields(
            data_type="patient_record",
            field_names=["ssn", "email"]
        )
        
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com",
            "age": 35
        }
        
        encrypted = field_encryption.encrypt_data("patient_record", data)
        decrypted = field_encryption.decrypt_data("patient_record", encrypted)
        
        assert decrypted["name"] == data["name"]
        assert decrypted["ssn"] == data["ssn"]
        assert decrypted["email"] == data["email"]
        assert decrypted["age"] == data["age"]
    
    def test_encrypt_data_unregistered_type(self, field_encryption):
        """Test encrypting data with unregistered type"""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789"
        }
        
        encrypted = field_encryption.encrypt_data("unknown_type", data)
        
        assert encrypted == data  # No changes
    
    def test_get_all_registered_fields(self, field_encryption):
        """Test getting all registered field mappings"""
        field_encryption.register_fields("patient_record", ["ssn", "email"])
        field_encryption.register_fields("user_profile", ["password"])
        
        all_mappings = field_encryption.get_registered_fields()
        
        assert "patient_record" in all_mappings
        assert "user_profile" in all_mappings
        assert "ssn" in all_mappings["patient_record"]
        assert "password" in all_mappings["user_profile"]
