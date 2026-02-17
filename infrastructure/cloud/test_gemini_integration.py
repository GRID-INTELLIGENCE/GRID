"""
Integration tests for Gemini Studio Cloud Client.

Run tests:
    pytest grid/infra/cloud/test_gemini_integration.py -v

For live API tests (requires GEMINI_API_KEY):
    pytest grid/infra/cloud/test_gemini_integration.py -v --live
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from . import (
    GeminiCloudClient,
    GeminiEnvironment,
    GeminiResponse,
)
from . import (
    GeminiConfig as CloudConfig,
)
from .gemini_client import (
    GeminiAuthError,
    GeminiConfig,
    GeminiModel,
    GeminiStudioClient,
    GenerationResult,
)
from .gemini_config import (
    DeploymentStage,
    GeminiAuthSettings,
    GeminiSettings,
)


# Fixtures
@pytest.fixture
def mock_config() -> GeminiConfig:
    """Create a test configuration."""
    return GeminiConfig(
        api_key="test-api-key-12345",
        project_id="test-project",
        model=GeminiModel.GEMINI_1_5_FLASH.value,
        max_retries=2,
        base_delay=0.1,
        timeout=10.0,
    )


@pytest.fixture
def mock_client(mock_config: GeminiConfig) -> GeminiStudioClient:
    """Create a test client with mock config."""
    return GeminiStudioClient(config=mock_config)


@pytest.fixture
def mock_response_data() -> dict[str, Any]:
    """Standard mock response from Gemini API."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello! I'm Gemini, a large language model."}],
                    "role": "model",
                },
                "finishReason": "STOP",
                "safetyRatings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "probability": "NEGLIGIBLE",
                    }
                ],
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 15,
            "totalTokenCount": 25,
        },
    }


# Configuration Tests
class TestGeminiConfig:
    """Tests for GeminiConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = GeminiConfig()
        assert config.model == GeminiModel.GEMINI_1_5_PRO.value
        assert config.max_retries == 3
        assert config.temperature == 0.7

    def test_config_from_env(self) -> None:
        """Test configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "env-api-key",
                "GEMINI_PROJECT_ID": "env-project",
                "GEMINI_MODEL": "gemini-1.5-flash",
            },
        ):
            config = GeminiConfig()
            assert config.api_key == "env-api-key"
            assert config.project_id == "env-project"

    def test_config_validation_no_key(self) -> None:
        """Test validation fails without API key."""
        config = GeminiConfig(api_key="")
        assert config.validate() is False

    def test_config_validation_with_key(self) -> None:
        """Test validation passes with API key."""
        config = GeminiConfig(api_key="test-key")
        assert config.validate() is True


class TestGeminiSettings:
    """Tests for GeminiSettings from gemini_config.py."""

    def test_settings_defaults(self) -> None:
        """Test default settings values."""
        settings = GeminiSettings()
        assert settings.enabled is True
        assert settings.deployment_stage == DeploymentStage.NOT_DEPLOYED

    def test_settings_is_deployed(self) -> None:
        """Test is_deployed property."""
        settings = GeminiSettings(deployment_stage=DeploymentStage.NOT_DEPLOYED)
        assert settings.is_deployed is False

        settings = GeminiSettings(deployment_stage=DeploymentStage.PRODUCTION)
        assert settings.is_deployed is True

    def test_settings_to_dict(self) -> None:
        """Test settings serialization."""
        settings = GeminiSettings()
        data = settings.to_dict()
        assert "enabled" in data
        assert "deployment_stage" in data
        assert "auth" in data

    def test_auth_settings_configured(self) -> None:
        """Test auth settings is_configured property."""
        auth = GeminiAuthSettings(api_key="test-key")
        assert auth.is_configured is True

        auth = GeminiAuthSettings(api_key="", use_adc=True, project_id="proj")
        assert auth.is_configured is True


# Client Tests
class TestGeminiStudioClient:
    """Tests for GeminiStudioClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_client: GeminiStudioClient) -> None:
        """Test client initializes correctly."""
        assert mock_client._initialized is False
        await mock_client.initialize()
        assert mock_client._initialized is True
        await mock_client.close()

    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_config: GeminiConfig) -> None:
        """Test client as async context manager."""
        async with GeminiStudioClient(config=mock_config) as client:
            assert client._initialized is True
        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_generate_dry_run(self) -> None:
        """Test generate in dry run mode (no API key)."""
        config = GeminiConfig(api_key="")
        client = GeminiStudioClient(config=config)

        with pytest.raises(GeminiAuthError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_config: GeminiConfig, mock_response_data: dict[str, Any]) -> None:
        """Test successful generation."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.aclose = AsyncMock()
            MockClient.return_value = mock_instance

            async with GeminiStudioClient(config=mock_config) as client:
                result = await client.generate("Hello, Gemini!")

            assert result.text == "Hello! I'm Gemini, a large language model."
            assert result.finish_reason == "STOP"
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 15

    @pytest.mark.asyncio
    async def test_generate_rate_limit_retry(self, mock_config: GeminiConfig) -> None:
        """Test retry on rate limit."""
        mock_config.max_retries = 2
        mock_config.base_delay = 0.01

        with patch("httpx.AsyncClient") as MockClient:
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.json.return_value = {"error": {"message": "Rate limit exceeded"}}

            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"candidates": [{"content": {"parts": [{"text": "Success!"}]}}]}

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(side_effect=[mock_response_429, mock_response_200])
            mock_instance.aclose = AsyncMock()
            MockClient.return_value = mock_instance

            async with GeminiStudioClient(config=mock_config) as client:
                result = await client.generate("Test")

            assert result.text == "Success!"
            assert mock_instance.post.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_auth_error_no_retry(self, mock_config: GeminiConfig) -> None:
        """Test auth errors don't retry."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.aclose = AsyncMock()
            MockClient.return_value = mock_instance

            async with GeminiStudioClient(config=mock_config) as client:
                with pytest.raises(GeminiAuthError):
                    await client.generate("Test")

            # Auth errors should not retry
            assert mock_instance.post.call_count == 1

    def test_health_check(self, mock_config: GeminiConfig) -> None:
        """Test health check output."""
        client = GeminiStudioClient(config=mock_config)
        health = client.health_check()

        assert health["initialized"] is False
        assert health["dry_run"] is False
        assert health["has_api_key"] is True
        assert health["model"] == mock_config.model

    @pytest.mark.asyncio
    async def test_chat(self, mock_config: GeminiConfig, mock_response_data: dict[str, Any]) -> None:
        """Test multi-turn chat."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.aclose = AsyncMock()
            MockClient.return_value = mock_instance

            async with GeminiStudioClient(config=mock_config) as client:
                messages = [
                    {"role": "user", "content": "Hello!"},
                    {"role": "model", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ]
                result = await client.chat(messages)

            assert result.text is not None
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs["json"]
            assert len(payload["contents"]) == 3

    def test_dry_run_forbidden_in_production(self) -> None:
        """Dry-run should fail fast in production by default."""
        with patch.dict(os.environ, {"MOTHERSHIP_ENVIRONMENT": "production"}, clear=False):
            with pytest.raises(RuntimeError):
                GeminiStudioClient(config=GeminiConfig(api_key=""))

    def test_dry_run_allowed_in_production_with_override(self) -> None:
        """Allow explicit production override for dry-run mode."""
        with patch.dict(
            os.environ,
            {
                "MOTHERSHIP_ENVIRONMENT": "production",
                "GEMINI_STUDIO_ALLOW_DRY_RUN_IN_PRODUCTION": "true",
            },
            clear=False,
        ):
            client = GeminiStudioClient(config=GeminiConfig(api_key=""))
            assert client._dry_run is True


# Cloud Client Tests (from __init__.py)
class TestGeminiCloudClient:
    """Tests for GeminiCloudClient from __init__.py."""

    def test_client_from_env(self) -> None:
        """Test client creation from environment."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            client = GeminiCloudClient.from_env()
            assert client.config.api_key == "test-key"

    def test_production_blocks_mock_or_pending_modes(self) -> None:
        """Production should reject mock/pending modes unless explicitly allowed."""
        with pytest.raises(RuntimeError):
            GeminiCloudClient(
                config=CloudConfig(
                    environment=GeminiEnvironment.PRODUCTION,
                    pending_deployment=True,
                    mock_responses=False,
                    allow_mock_in_production=False,
                )
            )

    def test_production_allows_mock_with_explicit_override(self) -> None:
        """Production override should allow controlled mock mode."""
        client = GeminiCloudClient(
            config=CloudConfig(
                environment=GeminiEnvironment.PRODUCTION,
                pending_deployment=True,
                mock_responses=False,
                allow_mock_in_production=True,
            )
        )
        assert client.config.allow_mock_in_production is True

    @pytest.mark.asyncio
    async def test_mock_response(self) -> None:
        """Test mock response generation."""
        config = CloudConfig(mock_responses=True)
        client = GeminiCloudClient(config=config)

        response = await client.generate_content("Test prompt")
        assert response.success is True
        assert response.text is not None
        assert "[MOCK]" in response.text
        assert response.origin == "mock"

    @pytest.mark.asyncio
    async def test_pending_deployment_mock(self) -> None:
        """Test pending deployment returns mock."""
        config = CloudConfig(pending_deployment=True)
        client = GeminiCloudClient(config=config)

        response = await client.generate_content("Test")
        assert response.success is True
        assert response.text is not None
        assert "[MOCK]" in response.text
        assert response.origin == "mock"

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health check endpoint."""
        config = CloudConfig(mock_responses=True)
        client = GeminiCloudClient(config=config)

        health = await client.health_check()
        assert "config_valid" in health
        assert "mock_mode" in health
        assert health["mock_mode"] is True

    def test_gemini_response_from_api(self) -> None:
        """Test GeminiResponse parsing."""
        api_data = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Test response"}]},
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 5,
                "candidatesTokenCount": 10,
                "totalTokenCount": 15,
            },
        }

        response = GeminiResponse.from_api_response(api_data, latency=100.0)
        assert response.success is True
        assert response.text == "Test response"
        assert response.usage["total_tokens"] == 15

    def test_gemini_response_error(self) -> None:
        """Test error response creation."""
        response = GeminiResponse.error_response("Test error", 500)
        assert response.success is False
        assert response.error == "Test error"
        assert response.status_code == 500


# GenerationResult Tests
class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_token_properties(self) -> None:
        """Test token count properties."""
        result = GenerationResult(
            text="Test",
            model="gemini-1.5-pro",
            usage={"prompt_token_count": 10, "candidates_token_count": 20},
        )
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 20
        assert result.total_tokens == 30

    def test_token_properties_no_usage(self) -> None:
        """Test token properties with no usage data."""
        result = GenerationResult(text="Test", model="gemini-1.5-pro")
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0


# Live API Tests (only run with --live flag)
@pytest.mark.live
class TestLiveAPI:
    """Live API tests - require GEMINI_API_KEY environment variable."""

    @pytest.fixture
    def api_key(self) -> str:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            pytest.skip("GEMINI_API_KEY not set")
        return key

    @pytest.mark.asyncio
    async def test_live_generate(self, api_key: str) -> None:
        """Test live generation."""
        config = GeminiConfig(api_key=api_key, model=GeminiModel.GEMINI_1_5_FLASH.value)

        async with GeminiStudioClient(config=config) as client:
            result = await client.generate("Say hello in exactly 3 words.")

        assert result.text
        assert result.finish_reason == "STOP"
        print(f"\nLive response: {result.text}")

    @pytest.mark.asyncio
    async def test_live_stream(self, api_key: str) -> None:
        """Test live streaming."""
        config = GeminiConfig(api_key=api_key, model=GeminiModel.GEMINI_1_5_FLASH.value)

        chunks = []
        async with GeminiStudioClient(config=config) as client:
            async for chunk in client.stream("Count from 1 to 5."):
                chunks.append(chunk)

        full_text = "".join(chunks)
        assert full_text
        print(f"\nStreamed response: {full_text}")


def pytest_configure(config: Any) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "live: mark test as live API test")
