"""
Skill: intelligence.git_analyze

AI-powered analysis of git changes using GRID's intelligence module.
Analyzes staged/unstaged changes, estimates complexity, and suggests actions.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from .base import SimpleSkill

# Import after path is set
try:
    from scripts.git_intelligence import GitIntelligence

    _INTELLIGENCE_AVAILABLE = True
except ImportError:
    _INTELLIGENCE_AVAILABLE = False


def _analyze_git(args: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze current git changes with AI."""
    verbose = args.get("verbose", False)

    if not _INTELLIGENCE_AVAILABLE:
        return {
            "skill": "intelligence.git_analyze",
            "status": "error",
            "error": "GitIntelligence module not available",
        }

    try:
        intel = GitIntelligence(verbose=verbose)

        # Check if Ollama is available
        if not intel.client.is_available():
            return {
                "skill": "intelligence.git_analyze",
                "status": "offline",
                "error": "Ollama not available",
                "message": "Install Ollama: curl https://ollama.ai/install.sh | sh",
            }

        # Run analysis
        result = intel.analyze()

        # Normalize output
        return {
            "skill": "intelligence.git_analyze",
            "status": result.get("status", "analyzed"),
            "complexity": result.get("complexity", 0),
            "model": result.get("model", "unknown"),
            "analysis": result.get("analysis", ""),
            "message": result.get("message", ""),
        }

    except Exception as e:
        return {
            "skill": "intelligence.git_analyze",
            "status": "error",
            "error": str(e),
        }


# Register skill
intelligence_git_analyze = SimpleSkill(
    id="intelligence.git_analyze",
    name="Git Intelligence Analysis",
    description="Analyze git changes with AI-powered complexity estimation and suggestions",
    handler=_analyze_git,
)
