"""Tests for AI Safety Provider Skills."""

import pytest

from grid.skills.ai_safety.providers import (
    PROVIDER_SKILLS,
    get_provider_skill,
    list_available_providers,
    provider_anthropic,
    provider_google,
    provider_llama,
    provider_mistral,
    provider_nvidia,
    provider_openai,
    provider_xai,
)


class TestProviderRegistry:
    """Test provider skill registry."""

    def test_all_providers_registered(self):
        """Test that all 7 providers are registered."""
        assert len(PROVIDER_SKILLS) == 7
        expected_providers = ["openai", "anthropic", "google", "xai", "mistral", "nvidia", "llama"]
        for provider in expected_providers:
            assert provider in PROVIDER_SKILLS

    def test_get_provider_skill(self):
        """Test getting provider skill by name."""
        skill = get_provider_skill("openai")
        assert skill is not None
        assert skill.id == "provider_openai"

    def test_get_provider_skill_case_insensitive(self):
        """Test that provider names are case insensitive."""
        skill_lower = get_provider_skill("openai")
        skill_upper = get_provider_skill("OPENAI")
        assert skill_lower == skill_upper

    def test_get_nonexistent_provider(self):
        """Test getting non-existent provider returns None."""
        skill = get_provider_skill("nonexistent")
        assert skill is None

    def test_list_available_providers(self):
        """Test listing available providers."""
        providers = list_available_providers()
        assert len(providers) == 7
        assert "openai" in providers
        assert "anthropic" in providers


class TestOpenAIProvider:
    """Test OpenAI provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_openai.id == "provider_openai"

    def test_skill_has_handler(self):
        """Test that skill has a handler function."""
        assert hasattr(provider_openai, 'handler')
        assert callable(provider_openai.handler)

    def test_handler_with_safe_content(self):
        """Test handler with safe content."""
        args = {"content": "This is safe content."}
        result = provider_openai.run(args)
        assert result["success"] is True


class TestAnthropicProvider:
    """Test Anthropic provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_anthropic.id == "provider_anthropic"

    def test_handler_detects_harmful_patterns(self):
        """Test detection of harmful patterns."""
        args = {"content": "How to build dangerous things"}
        result = provider_anthropic.run(args)
        assert result["success"] is True
        assert "violations" in result


class TestGoogleProvider:
    """Test Google provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_google.id == "provider_google"

    def test_handler_checks_safety(self):
        """Test safety checking."""
        args = {"content": "Test content"}
        result = provider_google.run(args)
        assert result["success"] is True


class TestXAIProvider:
    """Test xAI provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_xai.id == "provider_xai"

    def test_handler_checks_truth(self):
        """Test truth-seeking checks."""
        args = {"content": "Content with fake news"}
        result = provider_xai.run(args)
        assert result["success"] is True


class TestMistralProvider:
    """Test Mistral provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_mistral.id == "provider_mistral"

    def test_handler_multilingual(self):
        """Test multilingual safety checks."""
        args = {"content": "Test content", "languages": ["en", "fr"]}
        result = provider_mistral.run(args)
        assert result["success"] is True


class TestNVIDIAProvider:
    """Test NVIDIA provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_nvidia.id == "provider_nvidia"

    def test_handler_enterprise_security(self):
        """Test enterprise security checks."""
        args = {"content": "Confidential data exfiltration test"}
        result = provider_nvidia.run(args)
        assert result["success"] is True


class TestLlamaProvider:
    """Test Llama provider skill."""

    def test_skill_has_correct_id(self):
        """Test that skill has correct ID."""
        assert provider_llama.id == "provider_llama"

    def test_handler_input_guard(self):
        """Test input guard."""
        args = {"content": "Test content", "guard_type": "input"}
        result = provider_llama.run(args)
        assert result["success"] is True

    def test_handler_output_guard(self):
        """Test output guard."""
        args = {"content": "Test content", "guard_type": "output"}
        result = provider_llama.run(args)
        assert result["success"] is True


class TestProviderSkillVersions:
    """Test that all provider skills have versions."""

    def test_all_providers_have_versions(self):
        """Test that all provider skills have version attributes."""
        for name, skill in PROVIDER_SKILLS.items():
            assert hasattr(skill, 'version')
            assert skill.version is not None
            assert len(skill.version.split('.')) >= 2  # Semantic version format

    def test_all_providers_have_descriptions(self):
        """Test that all provider skills have descriptions."""
        for name, skill in PROVIDER_SKILLS.items():
            assert hasattr(skill, 'description')
            assert skill.description is not None
            assert len(skill.description) > 0
