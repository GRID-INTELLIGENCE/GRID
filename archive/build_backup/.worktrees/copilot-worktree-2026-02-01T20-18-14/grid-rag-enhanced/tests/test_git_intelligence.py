#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path for git_intelligence module (optional)
scripts_dir = Path(__file__).parent.parent / "scripts"
if scripts_dir.exists():
    sys.path.insert(0, str(scripts_dir))

try:
    from git_intelligence import ComplexityEstimator, OllamaClient
except ImportError:
    pytest.skip("git_intelligence not available (scripts/ not present)", allow_module_level=True)


class TestGitIntelligence(unittest.TestCase):
    def test_complexity_estimation_low(self):
        diff = "some small diff"
        staged = ["file1.py"]
        score = ComplexityEstimator.estimate(diff, staged)
        self.assertLessEqual(score, 3)
        self.assertEqual(ComplexityEstimator.select_model(score), "llama3.2:1b")

    def test_complexity_estimation_high(self):
        diff = "line\n" * 300
        staged = ["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"]
        score = ComplexityEstimator.estimate(diff, staged)
        self.assertGreater(score, 6)
        # score will be 3 (file_count) + 5 (diff_lines) = 8
        self.assertEqual(ComplexityEstimator.select_model(score), "codellama:13b")

    @patch("subprocess.run")
    def test_ollama_client_generate(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="AI Response", stderr="")
        client = OllamaClient()
        response = client.generate("test prompt")
        self.assertEqual(response, "AI Response")

    @patch("subprocess.run")
    def test_ollama_client_unavailable(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        client = OllamaClient()
        response = client.generate("test prompt")
        self.assertIn("not installed", response)


if __name__ == "__main__":
    unittest.main()
