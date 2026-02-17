#!/usr/bin/env python3
"""
Security tests for path traversal vulnerabilities.

Tests that all file operations properly validate paths and prevent
access to files outside allowed directories.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

from grid.agentic.agent_executor import AgentExecutor
from grid.context.storage import ContextStorage
from grid.context.storage import SecurityError as ContextSecurityError
from grid.security.path_validator import PathValidator
from grid.security.path_validator import SecurityError as PathSecurityError


class TestPathTraversalSecurity:
    """Test path traversal security across GRID components."""

    @pytest.fixture
    def temp_knowledge_base(self):
        """Create a temporary knowledge base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def temp_context_root(self):
        """Create a temporary context root directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.asyncio
    async def test_agent_executor_blocks_path_traversal(self, temp_knowledge_base):
        """Test that AgentExecutor blocks path traversal attempts."""
        executor = AgentExecutor(knowledge_base_path=temp_knowledge_base)

        # Test various path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../secrets/api_keys.txt",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
        ]

        for malicious_path in malicious_paths:
            result = await executor._load_reference_file(malicious_path)
            assert result is None, f"Path traversal should be blocked: {malicious_path}"

    @pytest.mark.asyncio
    async def test_agent_executor_allows_valid_files(self, temp_knowledge_base):
        """Test that AgentExecutor allows access to valid files within knowledge base."""
        executor = AgentExecutor(knowledge_base_path=temp_knowledge_base)

        # Create a valid test file
        test_file = temp_knowledge_base / "test_reference.json"
        test_content = {"test": "data", "valid": True}
        test_file.write_text('{"test": "data", "valid": true}')

        result = await executor._load_reference_file("test_reference.json")
        assert result is not None
        assert result == test_content

    def test_context_storage_blocks_path_traversal(self, temp_context_root):
        """Test that ContextStorage blocks path traversal attempts."""
        # Try to create ContextStorage with malicious context root
        malicious_root = temp_context_root.parent.parent  # Go up directories

        # This should either work with validation or raise an error
        try:
            storage = ContextStorage(context_root=malicious_root, user_id="test")
            # If it works, test that file operations are still blocked
            with pytest.raises(ContextSecurityError):
                storage._validate_path(Path("../../../etc/passwd"))
        except (ContextSecurityError, ValueError):
            # Expected behavior - malicious root rejected
            pass

    def test_context_storage_allows_valid_operations(self, temp_context_root):
        """Test that ContextStorage allows valid operations within context root."""
        storage = ContextStorage(context_root=temp_context_root, user_id="test")

        # Test saving and loading user profile
        from grid.context.schemas import UserProfile

        profile = UserProfile(user_id="test")

        # This should work without errors
        result = storage.save_user_profile(profile)
        assert result is True

        loaded_profile = storage.load_user_profile()
        assert loaded_profile is not None
        assert loaded_profile.user_id == "test"

    def test_path_validator_blocks_traversal(self):
        """Test that PathValidator successfully blocks path traversal attempts."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            malicious_paths = [
                "../../../etc/passwd",
                "/etc/passwd",
                "C:\\Windows\\System32\\config\\SAM",
                "..\\..\\..\\secrets",
            ]

            # Test that all malicious paths are successfully blocked
            for malicious_path in malicious_paths:
                try:
                    PathValidator.validate_path(malicious_path, base_path)
                    # If we get here, security failed - this should not happen
                    raise AssertionError(f"Security breach: malicious path was allowed: {malicious_path}")
                except PathSecurityError:
                    # This is the expected behavior - security is working
                    pass

            # Verify security is working by checking we got the expected exceptions
            assert True, "Security validation successfully blocked all malicious paths"

    def test_path_validator_allows_valid_paths(self):
        """Test that PathValidator allows valid paths within base directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            valid_paths = [
                "file.txt",
                "subdir/file.txt",
                "deeply/nested/path/file.txt",
            ]

            for valid_path in valid_paths:
                result = PathValidator.validate_path(valid_path, base_path)
                assert result.is_relative_to(base_path.resolve())

    def test_path_validator_sanitize_filename(self):
        """Test filename sanitization."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "file\x00with\x00nulls",
            ".hidden_file",
            "....multiple....dots",
        ]

        for filename in malicious_filenames:
            sanitized = PathValidator.sanitize_filename(filename)
            assert "/" not in sanitized
            assert "\\" not in sanitized
            assert ".." not in sanitized
            assert "\x00" not in sanitized
            assert sanitized != ""

    def test_path_validator_extension_validation(self):
        """Test that file extension validation successfully blocks dangerous files."""
        allowed_extensions = {".txt", ".md", ".json", ".py"}

        # Valid extensions - should be allowed
        valid_files = [
            "test.txt",
            "document.md",
            "data.json",
            "script.py",
        ]

        for file_path in valid_files:
            result = PathValidator.validate_extension(file_path, allowed_extensions)
            assert result.suffix.lower() in allowed_extensions

        # Invalid extensions - should be blocked
        invalid_files = [
            "test.exe",
            "malware.bat",
            "script.sh",
            "dangerous.dll",
        ]

        # Test that all dangerous files are successfully blocked
        for file_path in invalid_files:
            try:
                PathValidator.validate_extension(file_path, allowed_extensions)
                # If we get here, security failed - this should not happen
                raise AssertionError(f"Security breach: dangerous file extension was allowed: {file_path}")
            except PathSecurityError:
                # This is the expected behavior - security is working
                pass

        # Verify security is working by checking we successfully blocked dangerous files
        assert True, "Extension validation successfully blocked all dangerous files"

    def test_path_validator_safe_directory_validation(self):
        """Test that safe directory validation successfully blocks unauthorized access."""
        import tempfile

        # Create temporary allowed directories
        with (
            tempfile.TemporaryDirectory() as temp1,
            tempfile.TemporaryDirectory() as temp2,
            tempfile.TemporaryDirectory() as temp3,
        ):
            allowed_dirs = [str(Path(temp1)), str(Path(temp2)), str(Path(temp3))]

            # Valid subdirectories - should be allowed
            valid_paths = [
                Path(temp1) / "subdir",
                Path(temp2) / "data",
                Path(temp3) / "cache",
            ]

            for path in valid_paths:
                # Create the directory first
                path.mkdir(exist_ok=True)
                result = PathValidator.validate_safe_directory(path, allowed_dirs)
                assert any(result.is_relative_to(Path(allowed).resolve()) for allowed in allowed_dirs)

            # Invalid directories - should be blocked
            with tempfile.TemporaryDirectory() as evil_dir:
                invalid_paths = [
                    evil_dir,
                    Path("/etc"),  # Unix path that won't exist on Windows
                    Path("/root"),  # Unix path that won't exist on Windows
                ]

                # Test that all unauthorized directories are successfully blocked
                for path in invalid_paths:
                    try:
                        PathValidator.validate_safe_directory(path, allowed_dirs)
                        raise AssertionError(f"Security breach: unauthorized directory was allowed: {path}")
                    except PathSecurityError:
                        # This is the expected behavior - security is working
                        pass

                # Verify security is working by checking we successfully blocked unauthorized directories
                assert True, "Directory validation successfully blocked all unauthorized directories"


if __name__ == "__main__":
    pytest.main([__file__])
