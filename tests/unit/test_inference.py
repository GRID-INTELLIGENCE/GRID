from tests.utils.path_manager import PathManager

# Setup paths atomically to prevent race conditions
PathManager.setup_test_paths(__file__)

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
