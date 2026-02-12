"""
Tests for configuration manager.
"""

import pytest
import json
from pathlib import Path
from workspace_utils.config import ConfigManager, DEFAULT_CONFIG


def test_config_manager_defaults(temp_dir: Path):
    """Test ConfigManager with default configuration."""
    config_file = temp_dir / "test_config.json"
    config = ConfigManager(config_file=config_file)
    
    assert config.get("workspace_root") is not None
    assert config.get("output_dir") is not None
    assert isinstance(config.get("excluded_dirs"), list)
    assert len(config.get("excluded_dirs")) > 0


def test_config_manager_load_from_file(mock_config_file: Path):
    """Test loading configuration from file."""
    config = ConfigManager(config_file=mock_config_file)
    
    assert config.get("output_dir") == "__TEST_OUTPUT__"
    assert config.get("max_file_size_mb") == 5
    assert config.get("max_recursion_depth") == 6


def test_config_manager_save(temp_dir: Path):
    """Test saving configuration to file."""
    config_file = temp_dir / "test_config.json"
    config = ConfigManager(config_file=config_file)
    
    config.set("test_key", "test_value")
    config.save()
    
    assert config_file.exists()
    with open(config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config["test_key"] == "test_value"


def test_config_manager_get():
    """Test getting configuration values."""
    from workspace_utils.config import config
    
    # Test simple key
    workspace_root = config.get("workspace_root")
    assert workspace_root is not None
    
    # Test nested key
    json_output = config.get("cascade_integration.json_output")
    assert isinstance(json_output, bool)


def test_config_manager_get_output_dir():
    """Test getting output directory path."""
    from workspace_utils.config import config
    
    output_dir = config.get_output_dir()
    assert isinstance(output_dir, Path)


def test_config_manager_is_cascade_enabled():
    """Test checking if Cascade integration is enabled."""
    from workspace_utils.config import config
    
    enabled = config.is_cascade_enabled()
    assert isinstance(enabled, bool)


def test_config_manager_should_output_json():
    """Test checking if JSON output should be used."""
    from workspace_utils.config import config
    
    should_json = config.should_output_json()
    assert isinstance(should_json, bool)