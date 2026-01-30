"""CLI tests for GRID.

Note: These tests require the 'click' package.
Tests are skipped if click is not available.
"""

import os
import sys

import pytest

# Skip entire module if click is not available
try:
    from click.testing import CliRunner  # type: ignore[import-not-found]
except ImportError:
    pytest.skip(
        "click package not installed - skipping CLI tests. Install with: pip install click",
        allow_module_level=True,
    )

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# CLI module pending migration from legacy_src/
cli = None


class TestEventCommands:
    @pytest.mark.skipif(cli is None, reason="CLI module pending migration from legacy_src/")
    def test_list_events(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list-events"])
        if result.exit_code != 0:
            pytest.fail(f"CLI failed. Output: {result.output}\nExc: {result.exception}")
        assert result.exit_code == 0
        assert "- event1" in result.output
        assert "- event2" in result.output
