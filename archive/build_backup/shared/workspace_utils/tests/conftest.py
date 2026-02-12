"""
Pytest configuration and fixtures for workspace_utils tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_dir: Path) -> Path:
    """Create a sample Python file for testing."""
    test_file = temp_dir / "test_module.py"
    test_file.write_text("""
def hello_world():
    '''A simple function.'''
    return "Hello, World!"

class TestClass:
    '''A test class.'''
    def method(self):
        return "method result"
""")
    return test_file


@pytest.fixture
def sample_js_file(temp_dir: Path) -> Path:
    """Create a sample JavaScript file for testing."""
    test_file = temp_dir / "test_module.js"
    test_file.write_text("""
/**
 * A test function
 */
export function helloWorld() {
    return "Hello, World!";
}

const testClass = {
    method: function() {
        return "method result";
    }
};
""")
    return test_file


@pytest.fixture
def sample_repo_structure(temp_dir: Path) -> Path:
    """Create a sample repository structure for testing."""
    # Create Python module
    (temp_dir / "src" / "app").mkdir(parents=True)
    (temp_dir / "src" / "app" / "__init__.py").write_text("")
    (temp_dir / "src" / "app" / "main.py").write_text("""
import os
from pathlib import Path

def main():
    '''Main entry point.'''
    print("Hello from main")

if __name__ == "__main__":
    main()
""")
    
    # Create JavaScript module
    (temp_dir / "frontend" / "src").mkdir(parents=True)
    (temp_dir / "frontend" / "src" / "index.js").write_text("""
export const App = () => {
    return "Hello from App";
};
""")
    
    # Create excluded directory
    (temp_dir / "__pycache__").mkdir()
    (temp_dir / "__pycache__" / "test.pyc").write_bytes(b"fake pyc")
    
    return temp_dir


@pytest.fixture
def mock_config_file(temp_dir: Path) -> Path:
    """Create a mock configuration file."""
    config_file = temp_dir / "workspace_utils_config.json"
    config_file.write_text("""{
    "output_dir": "__TEST_OUTPUT__",
    "max_file_size_mb": 5,
    "max_recursion_depth": 6,
    "excluded_dirs": [".git", "node_modules", "__pycache__"],
    "cascade_integration": {
        "enable_terminal_tracking": true,
        "json_output": true
    }
}""")
    return config_file