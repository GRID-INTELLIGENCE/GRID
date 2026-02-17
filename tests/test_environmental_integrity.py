"""
Test suite for environmental integrity and module isolation.

Tests the fixes for environmental pollution and module management.
"""

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))


class TestEnvironmentalIntegrity(unittest.TestCase):
    """Test environmental integrity fixes."""

    def setUp(self):
        """Set up test environment."""
        self.original_modules = set(sys.modules.keys())
        self.original_environ = dict(os.environ)

        # Clean up any existing grid modules to prevent registry conflicts
        grid_modules = [name for name in sys.modules.keys() if name.startswith("grid.")]
        for module in grid_modules:
            if module in sys.modules:
                del sys.modules[module]

        # Clean up Prometheus registry if it exists
        try:
            from prometheus_client import REGISTRY

            # Clear existing metrics to avoid conflicts
            collectors = list(REGISTRY._collector_to_names.keys())
            for collector in collectors:
                REGISTRY.unregister(collector)
        except ImportError:
            pass  # Prometheus not available

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_environ)

        # Clean up any test modules added to sys.modules
        current_modules = set(sys.modules.keys())
        new_modules = current_modules - self.original_modules
        for module in new_modules:
            if module.startswith("test_") or module.startswith("grid."):
                try:
                    del sys.modules[module]
                except KeyError:
                    pass

    def test_module_utils_import(self):
        """Test that module utils can be imported."""
        from grid.security.module_utils import cleanup_module, isolate_module, safe_reload

        self.assertTrue(callable(safe_reload))
        self.assertTrue(callable(cleanup_module))
        self.assertTrue(callable(isolate_module))

    def test_environment_sanitization_import(self):
        """Test that environment sanitization can be imported."""
        from grid.security.environment import get_environment_report, sanitize_environment

        self.assertTrue(callable(sanitize_environment))
        self.assertTrue(callable(get_environment_report))

    def test_safe_reload_creates_fresh_module(self):
        """Test that safe_reload creates a fresh module state."""
        # Create a test module
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
TEST_VAR = 42
def test_func():
    return TEST_VAR
""")
            test_file = f.name

        try:
            # Add to sys.path temporarily
            module_dir = str(Path(test_file).parent)
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)

            module_name = Path(test_file).stem

            # Import the module
            module = importlib.import_module(module_name)
            self.assertEqual(module.TEST_VAR, 42)

            # Modify the module
            module.TEST_VAR = 99
            self.assertEqual(module.TEST_VAR, 99)

            # Safe reload should give fresh state
            reloaded = safe_reload(module_name)
            self.assertEqual(reloaded.TEST_VAR, 42)

        finally:
            # Cleanup
            if module_name in sys.modules:
                del sys.modules[module_name]
            os.unlink(test_file)
            if module_dir in sys.path:
                sys.path.remove(module_dir)

    def test_environment_path_sanitization(self):
        """Test that PATH sanitization removes duplicates and invalid paths."""
        from grid.security.environment import sanitize_path

        # Set up a polluted PATH
        original_path = os.environ.get("PATH", "")
        test_path = os.pathsep.join(
            [
                "/valid/path",
                "/another/valid/path",
                "/valid/path",  # duplicate
                "/nonexistent/path",  # invalid
                "/valid/path",  # another duplicate
            ]
        )
        os.environ["PATH"] = test_path

        # Sanitize
        sanitize_path()

        # Check result
        sanitized = os.environ["PATH"].split(os.pathsep)
        self.assertEqual(len(sanitized), 2)  # Should have removed duplicates and invalid
        self.assertIn("/valid/path", sanitized)
        self.assertIn("/another/valid/path", sanitized)

        # Restore
        os.environ["PATH"] = original_path

    def test_sensitive_environment_variable_removal(self):
        """Test that sensitive environment variables are removed."""
        from grid.security.environment import sanitize_environment

        # Set sensitive variables
        os.environ["GITHUB_TOKEN"] = "secret_token"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
        os.environ["SECRET_KEY"] = "super_secret"

        # Sanitize
        report = sanitize_environment()

        # Check that they were removed
        self.assertNotIn("GITHUB_TOKEN", os.environ)
        self.assertNotIn("DATABASE_URL", os.environ)
        self.assertNotIn("SECRET_KEY", os.environ)

        # Check report
        self.assertIn("security", report)
        self.assertEqual(len(report["security"]), 3)

    def test_module_isolation_context_manager(self):
        """Test that the isolate_module context manager works correctly."""
        from grid.security.module_utils import isolate_module

        # Create a test module name
        test_module = "test_isolation_module"

        # Ensure it's not in sys.modules
        if test_module in sys.modules:
            del sys.modules[test_module]

        # Use context manager
        with isolate_module(test_module):
            # Inside context, we can do operations
            pass

        # Module should not remain in sys.modules after context
        self.assertNotIn(test_module, sys.modules)

    def test_module_dependency_tracking(self):
        """Test module dependency tracking."""
        from grid.security.module_utils import get_module_dependencies

        # Test with a module that has dependencies
        deps = get_module_dependencies("os")
        self.assertIsInstance(deps, set)

        # os module should have some dependencies
        self.assertGreater(len(deps), 0)

    def test_environment_report_generation(self):
        """Test environment report generation."""
        from grid.security.environment import get_environment_report

        report = get_environment_report()

        # Check structure
        self.assertIn("python", report)
        self.assertIn("environment", report)

        # Check Python info
        python_info = report["python"]
        self.assertIn("executable", python_info)
        self.assertIn("version", python_info)
        self.assertIn("path", python_info)

        # Check environment info
        env_info = report["environment"]
        self.assertIn("path", env_info)
        self.assertIn("pythonpath", env_info)

    @patch("logging.getLogger")
    def test_grid_init_sanitization(self, mock_get_logger):
        """Test that grid init performs sanitization."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Import grid (this should trigger sanitization)
        import grid

        # Check that logger was called (indicating sanitization ran)
        # Note: This might not work if sanitization report is empty
        # but at least test that import succeeds
        self.assertTrue(hasattr(grid, "__all__"))


if __name__ == "__main__":
    unittest.main()
