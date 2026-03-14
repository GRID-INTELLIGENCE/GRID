"""
Unit tests for SecurePathManager.validate_path().

Covers dangerous pattern blocking, directory traversal detection,
null byte injection, and the regression fix for shell metacharacter
false positives (&&, ;, | removed from path validation).
"""

import tempfile
from pathlib import Path

import pytest

from grid.security.path_manager import SecurePathManager


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathDangerousPatterns:
    """Tests for DANGEROUS_PATTERNS blocking in validate_path()."""

    def test_blocks_tmp_path(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("/tmp/some_dir")
        assert not result.is_valid

    def test_blocks_var_tmp_path(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("/var/tmp/cache")
        assert not result.is_valid


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathTraversal:
    """Tests for directory traversal detection."""

    def test_blocks_dotdot_traversal(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("/home/user/../../../etc/passwd")
        assert not result.is_valid
        # ".." patterns can be caught by either DANGEROUS_PATTERNS or traversal component check
        reason = (result.reason or "").lower()
        assert "dangerous pattern" in reason or "traversal" in reason

    def test_blocks_relative_dotdot(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("../../etc")
        assert not result.is_valid
        assert "traversal" in (result.reason or "").lower()

    def test_allows_double_dots_in_filename(self, tmp_path: Path) -> None:
        """Filenames like 'foo..bar' should NOT trigger traversal detection."""
        target = tmp_path / "foo..bar"
        target.mkdir()
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathNullByte:
    """Tests for null byte injection (CWE-626)."""

    def test_blocks_literal_null_byte(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("/home/user\x00/etc/passwd")
        assert not result.is_valid
        assert "null byte" in (result.reason or "").lower()

    def test_blocks_encoded_null_byte(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("/home/user%00/etc/passwd")
        assert not result.is_valid
        assert "null byte" in (result.reason or "").lower()


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathShellMetacharRegression:
    """Regression tests: shell metacharacters must NOT cause false positives.

    Shell command injection detection is handled by input_sanitizer.py and
    threat_profile.py, not by path validation.
    """

    def test_allows_double_ampersand_in_path(self, tmp_path: Path) -> None:
        """Path like /project&&version/ must be accepted (the original bug)."""
        target = tmp_path / "project&&version"
        target.mkdir()
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid, f"False positive on &&: {result.reason}"

    def test_allows_semicolon_in_path(self, tmp_path: Path) -> None:
        target = tmp_path / "name;v2"
        target.mkdir()
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid, f"False positive on ;: {result.reason}"

    def test_allows_pipe_in_path(self, tmp_path: Path) -> None:
        """Pipe in directory names is valid on Linux filesystems."""
        target = tmp_path / "a|b"
        try:
            target.mkdir()
        except OSError:
            pytest.skip("Filesystem does not support | in directory names")
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid, f"False positive on |: {result.reason}"


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathAcceptance:
    """Tests that valid paths are accepted."""

    def test_valid_directory_accepted(self, tmp_path: Path) -> None:
        target = tmp_path / "valid_project"
        target.mkdir()
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid
        assert result.exists
        assert result.is_directory

    def test_relative_path_resolved_against_base(self, tmp_path: Path) -> None:
        target = tmp_path / "subdir"
        target.mkdir()
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path("subdir")
        assert result.is_valid
        assert result.path.resolve() == target.resolve()

    def test_nonexistent_path_rejected(self, tmp_path: Path) -> None:
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(tmp_path / "does_not_exist")
        assert not result.is_valid
        assert "does not exist" in (result.reason or "").lower()

    def test_file_path_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "file.py"
        target.write_text("# python")
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert not result.is_valid
        assert "not a directory" in (result.reason or "").lower()

    def test_detects_python_files(self, tmp_path: Path) -> None:
        target = tmp_path / "pkg"
        target.mkdir()
        (target / "__init__.py").write_text("")
        manager = SecurePathManager(base_dir=tmp_path)
        result = manager.validate_path(target)
        assert result.is_valid
        assert result.contains_python_files
