"""Tests for CLI entrypoints."""

import sys

import pytest
from click.testing import CliRunner

from coinbase.cli import main as click_main
from coinbase.main import main as argparse_main


class TestClickCLI:
    """Tests for Click-based CLI."""

    def test_click_default_output(self) -> None:
        """Test default CLI output without flags."""
        runner = CliRunner()
        result = runner.invoke(click_main)
        assert result.exit_code == 0
        assert "Coinbase CLI running" in result.output
        assert "Crypto scope enabled" not in result.output
        assert "Verbose mode enabled" not in result.output

    def test_click_crypto_flag(self) -> None:
        """Test CLI with --crypto flag."""
        runner = CliRunner()
        result = runner.invoke(click_main, ["--crypto"])
        assert result.exit_code == 0
        assert "Crypto scope enabled" in result.output
        assert "Coinbase CLI running" in result.output
        assert "Verbose mode enabled" not in result.output

    def test_click_verbose_flag(self) -> None:
        """Test CLI with --verbose flag."""
        runner = CliRunner()
        result = runner.invoke(click_main, ["--verbose"])
        assert result.exit_code == 0
        assert "Verbose mode enabled" in result.output
        assert "Coinbase CLI running" in result.output
        assert "Crypto scope enabled" not in result.output

    def test_click_both_flags(self) -> None:
        """Test CLI with both --crypto and --verbose flags."""
        runner = CliRunner()
        result = runner.invoke(click_main, ["--crypto", "--verbose"])
        assert result.exit_code == 0
        assert "Crypto scope enabled" in result.output
        assert "Verbose mode enabled" in result.output
        assert "Coinbase CLI running" in result.output

    def test_click_help(self) -> None:
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(click_main, ["--help"])
        assert result.exit_code == 0
        assert "Enable crypto scope" in result.output
        assert "Enable verbose output" in result.output


class TestArgparseCLI:
    """Tests for argparse-based CLI."""

    def test_argparse_default_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test default CLI output without flags."""
        test_args = ["main.py"]
        with pytest.MonkeyPatch.context() as mpatch:
            mpatch.setattr(sys, "argv", test_args)
            argparse_main()
        captured = capsys.readouterr()
        assert "Coinbase running" in captured.out
        assert "Crypto scope enabled" not in captured.out
        assert "Verbose mode enabled" not in captured.out

    def test_argparse_crypto_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CLI with --crypto flag."""
        test_args = ["main.py", "--crypto"]
        with pytest.MonkeyPatch.context() as mpatch:
            mpatch.setattr(sys, "argv", test_args)
            argparse_main()
        captured = capsys.readouterr()
        assert "Crypto scope enabled" in captured.out
        assert "Coinbase running" in captured.out
        assert "Verbose mode enabled" not in captured.out

    def test_argparse_verbose_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CLI with --verbose flag."""
        test_args = ["main.py", "--verbose"]
        with pytest.MonkeyPatch.context() as mpatch:
            mpatch.setattr(sys, "argv", test_args)
            argparse_main()
        captured = capsys.readouterr()
        assert "Verbose mode enabled" in captured.out
        assert "Coinbase running" in captured.out
        assert "Crypto scope enabled" not in captured.out

    def test_argparse_both_flags(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CLI with both --crypto and --verbose flags."""
        test_args = ["main.py", "--crypto", "--verbose"]
        with pytest.MonkeyPatch.context() as mpatch:
            mpatch.setattr(sys, "argv", test_args)
            argparse_main()
        captured = capsys.readouterr()
        assert "Crypto scope enabled" in captured.out
        assert "Verbose mode enabled" in captured.out
        assert "Coinbase running" in captured.out

    def test_argparse_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CLI help output."""
        test_args = ["main.py", "--help"]
        with pytest.MonkeyPatch.context() as mpatch:
            mpatch.setattr(sys, "argv", test_args)
            with pytest.raises(SystemExit):
                argparse_main()
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "Coinbase crypto project" in captured.out
