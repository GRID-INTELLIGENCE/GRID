from tests.utils.path_manager import PathManager

# Setup paths atomically to prevent race conditions
PathManager.setup_test_paths(__file__)

import pytest

from grid.services.inference import InferenceService


def test_inference_service_validation() -> None:
    service = InferenceService()
    # Valid request
    from grid.models.inference import InferenceRequest

    valid_request = InferenceRequest(prompt="Valid", max_tokens=100)
    assert service._validate_request(valid_request) is True
    # Invalid prompt
    invalid_request = InferenceRequest(prompt="", max_tokens=100)
    assert service._validate_request(invalid_request) is False
    # Invalid token count
    invalid_tokens_request = InferenceRequest(prompt="Test", max_tokens=5000)
    assert service._validate_request(invalid_tokens_request) is False


def test_cache_key_generation() -> None:
    service = InferenceService()
    from grid.models.inference import InferenceRequest

    request = InferenceRequest(prompt="Hello world", model="gpt-4", max_tokens=500, temperature=0.7)
    key = service._generate_cache_key(request)
    assert "Hello world" in key
    assert "gpt-4" in key
    assert "500" in key
    assert "0.7" in key


@pytest.mark.asyncio
async def test_inference_response_marks_placeholder_origin() -> None:
    service = InferenceService()
    from grid.models.inference import InferenceRequest

    response = await service.process(InferenceRequest(prompt="Hello", model="gpt-4"))

    assert response.metadata is not None
    assert response.metadata.get("origin") == "placeholder"
    assert response.metadata.get("simulated") is True


def test_inference_service_blocks_placeholder_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOTHERSHIP_ENVIRONMENT", "production")
    monkeypatch.delenv("INFERENCE_ALLOW_PLACEHOLDER_IN_PRODUCTION", raising=False)

    with pytest.raises(RuntimeError):
        InferenceService()
