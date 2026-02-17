"""Comprehensive tests for AI Safety Provider edge cases and API mocking."""

from __future__ import annotations

import sys
from unittest.mock import Mock, patch

from grid.skills.ai_safety.base import SafetyCategory, ThreatLevel
from grid.skills.ai_safety.providers.openai import (
    check_openai_safety,
    map_openai_category,
    map_openai_score,
)


class TestOpenAIMappingFunctions:
    """Test OpenAI category and score mapping functions."""

    def test_map_openai_category_hate(self):
        """Test mapping hate category."""
        result = map_openai_category("hate")
        assert result == SafetyCategory.HARASSMENT

    def test_map_openai_category_violence(self):
        """Test mapping violence category."""
        result = map_openai_category("violence")
        assert result == SafetyCategory.HARMFUL_CONTENT

    def test_map_openai_category_self_harm(self):
        """Test mapping self-harm category."""
        result = map_openai_category("self-harm")
        assert result == SafetyCategory.MENTAL_HEALTH_RISK

    def test_map_openai_category_unknown(self):
        """Test mapping unknown category defaults to harmful_content."""
        result = map_openai_category("unknown_category")
        assert result == SafetyCategory.HARMFUL_CONTENT

    def test_map_openai_score_critical(self):
        """Test mapping critical score."""
        result = map_openai_score(0.85)
        assert result == ThreatLevel.CRITICAL

    def test_map_openai_score_high(self):
        """Test mapping high score."""
        result = map_openai_score(0.65)
        assert result == ThreatLevel.HIGH

    def test_map_openai_score_medium(self):
        """Test mapping medium score."""
        result = map_openai_score(0.45)
        assert result == ThreatLevel.MEDIUM

    def test_map_openai_score_low(self):
        """Test mapping low score."""
        result = map_openai_score(0.25)
        assert result == ThreatLevel.LOW

    def test_map_openai_score_none(self):
        """Test mapping none score."""
        result = map_openai_score(0.1)
        assert result == ThreatLevel.NONE


class TestOpenAIAPIEdgeCases:
    """Test OpenAI API edge cases with mocking."""

    @patch("grid.skills.ai_safety.providers.openai.get_config")
    def test_check_openai_safety_disabled_provider(self, mock_get_config):
        """Test check when provider is disabled."""
        mock_config = Mock()
        mock_config.is_provider_enabled.return_value = False
        mock_get_config.return_value = mock_config

        violations = check_openai_safety("test content")
        assert violations == []

    @patch("grid.skills.ai_safety.providers.openai.get_config")
    def test_check_openai_safety_no_api_key(self, mock_get_config):
        """Test check when API key is not available."""
        mock_config = Mock()
        mock_config.is_provider_enabled.return_value = True
        mock_config.get_provider_api_key.return_value = None
        mock_get_config.return_value = mock_config

        violations = check_openai_safety("test content")
        assert violations == []

    @patch("grid.skills.ai_safety.providers.openai.get_config")
    def test_check_openai_safety_import_error(self, mock_get_config):
        """Test check when requests is not available."""
        mock_config = Mock()
        mock_config.is_provider_enabled.return_value = True
        mock_config.get_provider_api_key.return_value = "test_key"
        mock_get_config.return_value = mock_config

        with patch.dict(sys.modules, {"requests": None}):
            violations = check_openai_safety("test content")
            assert violations == []
