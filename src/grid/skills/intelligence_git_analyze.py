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
    from scripts.git_intelligence import ComplexityEstimator, OllamaClient

    _INTELLIGENCE_AVAILABLE = True
except ImportError:
    _INTELLIGENCE_AVAILABLE = False


def _analyze_git(args: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze current git changes with AI."""
    if not _INTELLIGENCE_AVAILABLE:
        return {
            "skill": "intelligence.git_analyze",
            "status": "error",
            "error": "Git intelligence module not available",
        }

    import subprocess

    try:
        # Initialize clients
        ollama_client = OllamaClient()
        estimator = ComplexityEstimator(ollama_client)

        # Check if Ollama is available
        if not ollama_client.is_available():
            return {
                "skill": "intelligence.git_analyze",
                "status": "offline",
                "error": "Ollama not available",
                "message": "Install Ollama: curl https://ollama.ai/install.sh | sh",
            }

        # Get git changes
        result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, timeout=30)  # noqa: S607 partial path is intentional
        if result.returncode != 0:
            return {
                "skill": "intelligence.git_analyze",
                "status": "error",
                "error": "Failed to get git diff",
            }

        # Get staged files
        result_files = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=30,  # noqa: S607 partial path is intentional
        )
        staged_files = result_files.stdout.strip().split("\n") if result_files.returncode == 0 else []

        # Run complexity analysis
        complexity_score = estimator.estimate(result.stdout, staged_files)
        model = estimator.select_model(complexity_score)

        # Normalize output
        return {
            "skill": "intelligence.git_analyze",
            "status": "analyzed",
            "complexity": complexity_score,
            "model": model,
            "analysis": f"Analyzed {len(staged_files)} staged files",
            "message": f"Complexity: {complexity_score:.2f}/10 (using {model})",
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
