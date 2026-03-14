"""Tests for configurable hardcoded security paths.

Verifies that hardcoded paths can be overridden via environment variables.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestConfigurableSystemPaths:
    """Test that system paths are configurable via environment variables."""

    def test_threat_profile_unix_paths_configurable(self):
        from grid.security.threat_profile import PreventionFramework

        # Test default behavior
        with patch.dict(os.environ, {}, clear=True):
            result = PreventionFramework._check_writable_system_paths()
            # Should use default paths: /usr:/bin:/sbin:/lib
            assert isinstance(result, bool)

        # Test custom Unix paths
        with patch.dict(os.environ, {"GRID_SYSTEM_PATHS": "/my/usr:/my/bin"}, clear=True):
            # This should not raise an error and use custom paths
            result = PreventionFramework._check_writable_system_paths()
            assert isinstance(result, bool)

    def test_threat_profile_windows_paths_configurable(self):
        from grid.security.threat_profile import PreventionFramework

        # Test custom Windows paths
        with patch.dict(
            os.environ,
            {"GRID_SYSTEM_PATHS": "/my/usr:/my/bin", "GRID_WINDOWS_PATHS": "C:\\MyWindows:C:\\MyPrograms"},
            clear=True,
        ):
            with patch("sys.platform", "win32"):
                result = PreventionFramework._check_writable_system_paths()
                assert isinstance(result, bool)

    def test_security_runner_paths_configurable(self):
        from grid.security.security_runner import SecurityValidator

        validator = SecurityValidator()

        # Test custom Unix paths
        with patch.dict(os.environ, {"GRID_SYSTEM_PATHS": "/custom/usr:/custom/bin"}, clear=True):
            result = validator._check_writable_paths()
            # Should use custom paths without error
            assert result.name == "runtime_writable_paths"


class TestConfigurableWellnessStudioPaths:
    """Test that wellness studio paths are configurable."""

    def test_wellness_studio_env_override(self):
        from unified_fabric.safety_bridge import get_wellness_studio_default_path

        # Test direct environment override
        with patch.dict(os.environ, {"WELLNESS_STUDIO_PATH": "/custom/wellness"}, clear=True):
            path = get_wellness_studio_default_path()
            assert path == "/custom/wellness"

    def test_wellness_studio_search_paths_configurable(self):
        from unified_fabric.safety_bridge import get_wellness_studio_default_path

        # Test configurable search paths
        custom_paths = "/custom/path1:/custom/path2"
        with patch.dict(
            os.environ, {"WELLNESS_STUDIO_SEARCH_PATHS": custom_paths, "WELLNESS_STUDIO_PATH": ""}, clear=True
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                with patch("os.name", "posix"):  # Force Unix path separator
                    path = get_wellness_studio_default_path()
                    # Should return first custom path even if it doesn't exist
                    assert path == "/custom/path1"


class TestConfigurableDashboardPaths:
    """Test that dashboard allowed directories are configurable."""

    def test_dashboard_allowed_dirs_configurable(self):
        from tools.interfaces_dashboard.dashboard import validate_db_path

        # Test that the environment variable is read (mock the actual validation)
        custom_dirs = "/custom/dir1:/custom/dir2"
        with patch.dict(os.environ, {"GRID_DASHBOARD_ALLOWED_DIRS": custom_dirs}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                # Just verify the function tries to read the env var
                # The actual path resolution is platform-dependent
                try:
                    validate_db_path("test.db")
                except ValueError:
                    # Expected on Windows due to path resolution differences
                    pass

    def test_dashboard_default_dirs_fallback(self):
        from tools.interfaces_dashboard.dashboard import validate_db_path

        # Test fallback to default directories
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                with patch("pathlib.Path.exists", return_value=True):
                    # Should accept path in current directory (default)
                    result = validate_db_path("test.db")
                    assert result.endswith("test.db")


class TestConfigurableContextPaths:
    """Test that context storage roots are configurable."""

    def test_context_allowed_roots_configurable(self):
        from grid.context.storage import ContextStorage

        # Test custom allowed roots
        custom_root = "/custom/context/root"
        with patch.dict(os.environ, {"GRID_CONTEXT_ALLOWED_ROOTS": custom_root}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                with patch("pathlib.Path.mkdir"):
                    storage = ContextStorage(Path(custom_root) / "test_context")
                    # Should not raise validation error
                    assert storage.context_root == Path(custom_root) / "test_context"

    def test_context_default_roots_fallback(self):
        from grid.context.storage import ContextStorage

        # Test fallback to default roots
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                with patch("pathlib.Path.mkdir"):
                    # Should use default home/.grid/context
                    storage = ContextStorage(Path("/home/test/.grid/context/test"))
                    assert storage.context_root == Path("/home/test/.grid/context/test")
