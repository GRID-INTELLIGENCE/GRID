"""
Transition Gate Toolkit - Comprehensive CLI for sealed envelope operations.

A full-featured toolkit for:
- Sealing artifacts into cryptographically bound envelopes
- Verifying envelopes through the 9-step pipeline
- Testing each security measure independently
- Generating audit reports and compliance documentation
- Interactive demonstrations of security features

Usage:
    python -m boundaries.toolkit --help
    python -m boundaries.toolkit seal --payload-file data.json
    python -m boundaries.toolkit verify --envelope-file envelope.json
    python -m boundaries.toolkit demo --all-steps
    python -m boundaries.toolkit test --scenario replay_attack
"""

__version__ = "1.0.0"
__author__ = "GRID Transition Gate Team"

from boundaries.toolkit.config import ToolkitConfig
from boundaries.toolkit.reports import ReportGenerator

__all__ = ["ToolkitConfig", "ReportGenerator", "__version__"]
