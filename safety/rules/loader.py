import json
import yaml
from pathlib import Path
from typing import List, Dict, Any


def load_rules(rule_file_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """
    Load safety rules from JSON or YAML file.

    Args:
        rule_file_path: Path to the rule file. If None, checks registry.json then defaults.yaml.

    Returns:
        List of rule dictionaries.
    """
    if rule_file_path is None:
        # Check Project GUARDIAN registry first, then fallback to defaults
        p_json = Path(__file__).parent / "registry.json"
        p_yaml = Path(__file__).parent / "defaults.yaml"
        rule_file_path = p_json if p_json.exists() else p_yaml

    path = Path(rule_file_path)
    if not path.exists():
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
            return data.get('rules', [])
    except Exception as e:
        # Use simple print as fallback if logging not ready
        print(f"Failed to load rules from {path}: {e}")
        return []
