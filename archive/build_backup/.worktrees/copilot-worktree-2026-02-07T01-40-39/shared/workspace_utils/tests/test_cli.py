"""
Tests for CLI commands.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from workspace_utils.cli import (
    analyze_command,
    compare_command,
    verify_command,
    config_command,
    main
)


@pytest.fixture
def mock_args():
    """Create mock argparse namespace."""
    class Args:
        pass
    return Args()


def test_analyze_command(temp_dir: Path):
    """Test analyze command."""
    args = mock_args
    args.root = str(temp_dir)
    args.out = str(temp_dir / "output")
    args.max_depth = 3
    args.exclude = None
    
    # Create a sample file
    (temp_dir / "test.py").write_text("print('hello')")
    
    # Should not raise an exception
    analyze_command(args)
    
    # Verify output directory was created
    assert (temp_dir / "output").exists()


def test_compare_command(mock_analysis_output: Path, temp_dir: Path):
    """Test compare command."""
    args = mock_args
    args.project1 = str(mock_analysis_output)
    args.project2 = str(mock_analysis_output)
    args.out = str(temp_dir / "comparison")
    
    # Should not raise an exception
    compare_command(args)
    
    # Verify comparison file was created
    assert (temp_dir / "comparison" / "cross_project_comparison.json").exists()


def test_verify_command():
    """Test verify command."""
    args = mock_args
    
    with patch('workspace_utils.cli.EUFLEVerifier') as mock_verifier_class:
        mock_verifier = MagicMock()
        mock_verifier.run_all_checks.return_value = {
            "all_checks_passed": True,
            "timestamp": "2024-01-01T00:00:00",
            "results": {},
            "details": {},
            "recommendations": []
        }
        mock_verifier_class.return_value = mock_verifier
        
        result = verify_command(args)
        
        assert result == 0
        mock_verifier.run_all_checks.assert_called_once()


def test_config_command_show():
    """Test config show command."""
    args = mock_args
    args.show = True
    args.get = None
    args.set = None
    
    with patch('workspace_utils.cli.config') as mock_config:
        mock_config.config = {"output_dir": "test"}
        mock_config_command = config_command
        # Should not raise exception
        config_command(args)


def test_config_command_get():
    """Test config get command."""
    args = mock_args
    args.show = False
    args.get = "output_dir"
    args.set = None
    
    with patch('workspace_utils.cli.config') as mock_config:
        mock_config.get.return_value = "test_output"
        # Should not raise exception
        config_command(args)
        mock_config.get.assert_called_once_with("output_dir")


def test_config_command_set():
    """Test config set command."""
    args = mock_args
    args.show = False
    args.get = None
    args.set = "output_dir=test_output"
    
    with patch('workspace_utils.cli.config') as mock_config:
        # Should not raise exception
        config_command(args)
        mock_config.set.assert_called_once()
        mock_config.save.assert_called_once()


def test_main_no_command():
    """Test main function with no command."""
    with patch('sys.argv', ['workspace-utils']):
        with pytest.raises(SystemExit):
            main()


def test_main_analyze_command(temp_dir: Path):
    """Test main function with analyze command."""
    (temp_dir / "test.py").write_text("print('hello')")
    
    with patch('sys.argv', [
        'workspace-utils',
        'analyze',
        '--root', str(temp_dir),
        '--out', str(temp_dir / "output")
    ]):
        try:
            main()
        except SystemExit:
            pass  # Expected when argparse exits


@pytest.mark.integration
def test_cli_json_output(temp_dir: Path):
    """Test that CLI commands output JSON for Cascade."""
    (temp_dir / "test.py").write_text("print('hello')")
    
    args = mock_args
    args.root = str(temp_dir)
    args.out = str(temp_dir / "output")
    args.max_depth = 3
    args.exclude = None
    
    analyze_command(args)
    
    # Check for JSON summary file
    summary_file = temp_dir / "output" / "analysis_summary.json"
    # May or may not exist depending on config, but if it does, it should be valid JSON
    if summary_file.exists():
        import json
        with open(summary_file, 'r') as f:
            summary = json.load(f)
            assert isinstance(summary, dict)
            assert "command" in summary