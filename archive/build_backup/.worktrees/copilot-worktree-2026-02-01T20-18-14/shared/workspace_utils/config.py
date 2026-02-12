"""
Shared configuration management for workspace utilities.

Centralizes settings across all workspace utility scripts for consistency
and Cascade integration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default workspace root
WORKSPACE_ROOT = Path(os.getenv("PROJECT_ROOT", "e:\\")).resolve()

# Default output directory for analysis artifacts
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "analysis_outputs"

# Default configuration file
CONFIG_FILE = WORKSPACE_ROOT / "workspace_utils_config.json"

# Default settings
DEFAULT_CONFIG = {
    "workspace_root": str(WORKSPACE_ROOT),
    "output_dir": str(DEFAULT_OUTPUT_DIR),
    "max_file_size_mb": 5,
    "max_recursion_depth": 6,
    "excluded_dirs": [
        ".git", "node_modules", "venv", ".venv", "build", "dist",
        "vendor", ".cache", "__pycache__", ".pytest_cache", ".mypy_cache",
        "target", "bin", "obj", ".idea", ".vscode", "analysis_outputs"
    ],
    "log_level": "INFO",
    "output_format": "json",  # For Cascade parsing
    "cascade_integration": {
        "enable_terminal_tracking": True,
        "json_output": True,
        "context_retention": True
    }
}


class ConfigManager:
    """Manages workspace utility configuration with Cascade integration."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults for missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
        return self.config
    
    def save(self):
        """Save current configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot-notation support."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value with dot-notation support."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def get_output_dir(self) -> Path:
        """Get output directory path."""
        return Path(self.get("output_dir", DEFAULT_OUTPUT_DIR))
    
    def get_workspace_root(self) -> Path:
        """Get workspace root path."""
        return Path(self.get("workspace_root", WORKSPACE_ROOT))
    
    def get_excluded_dirs(self) -> list:
        """Get list of excluded directories."""
        return self.get("excluded_dirs", DEFAULT_CONFIG["excluded_dirs"])
    
    def is_cascade_enabled(self) -> bool:
        """Check if Cascade integration is enabled."""
        return self.get("cascade_integration.enable_terminal_tracking", True)
    
    def should_output_json(self) -> bool:
        """Check if JSON output format should be used (for Cascade parsing)."""
        return self.get("cascade_integration.json_output", True)


# Global configuration instance
config = ConfigManager()