"""Smoke tests for CI pipeline verification.

These tests are designed to always pass and verify that the testing
infrastructure is working correctly. They serve as the minimal viable
test suite for CI pipeline stabilization.

Markers:
    - unit: Fast, isolated tests
    - critical: Must pass for CI to be green
"""

import os
import sys

import pytest


class TestEnvironmentSmoke:
    """Verify the test environment is correctly configured."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_python_version(self):
        """Verify Python version is 3.13+."""
        assert sys.version_info >= (3, 13), f"Python 3.13+ required, got {sys.version}"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pythonpath_configured(self):
        """Verify PYTHONPATH includes src directory."""
        # Check that the project root is accessible
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        src_dir = os.path.join(root_dir, "src")
        assert os.path.isdir(src_dir), f"src/ directory not found at {src_dir}"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pytest_working(self):
        """Verify pytest is working (trivial assertion)."""
        assert True, "This test should always pass"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_test_isolation(self):
        """Verify test isolation via environment variables."""
        # These are set in conftest.py
        assert os.environ.get("MOTHERSHIP_ENVIRONMENT") == "test"


class TestCoreImportsSmoke:
    """Verify core dependencies can be imported."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_pytest(self):
        """Verify pytest is importable."""
        import pytest as pt

        assert pt is not None

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_pydantic(self):
        """Verify pydantic is importable."""
        import pydantic

        assert pydantic is not None

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_fastapi(self):
        """Verify fastapi is importable."""
        import fastapi

        assert fastapi is not None

    @pytest.mark.unit
    def test_import_numpy(self):
        """Verify numpy is importable."""
        import numpy as np

        assert np is not None


class TestProjectStructureSmoke:
    """Verify project structure is correct."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pyproject_exists(self):
        """Verify pyproject.toml exists."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        pyproject = os.path.join(root_dir, "pyproject.toml")
        assert os.path.isfile(pyproject), f"pyproject.toml not found at {pyproject}"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_tests_directory_exists(self):
        """Verify tests directory exists."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        tests_dir = os.path.join(root_dir, "tests")
        assert os.path.isdir(tests_dir), f"tests/ directory not found at {tests_dir}"

    @pytest.mark.unit
    def test_conftest_exists(self):
        """Verify conftest.py exists."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        conftest = os.path.join(root_dir, "tests", "conftest.py")
        assert os.path.isfile(conftest), f"conftest.py not found at {conftest}"


class TestArithmeticSmoke:
    """Trivial arithmetic tests to verify test runner is working."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_addition(self):
        """Verify basic addition."""
        assert 1 + 1 == 2

    @pytest.mark.unit
    @pytest.mark.critical
    def test_subtraction(self):
        """Verify basic subtraction."""
        assert 5 - 3 == 2

    @pytest.mark.unit
    def test_multiplication(self):
        """Verify basic multiplication."""
        assert 3 * 4 == 12

    @pytest.mark.unit
    def test_division(self):
        """Verify basic division."""
        assert 10 / 2 == 5
