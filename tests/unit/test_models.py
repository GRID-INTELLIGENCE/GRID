import pytest
from tests.utils.path_manager import PathManager

# Setup paths atomically to prevent race conditions
PathManager.setup_test_paths(__file__)

from grid.services.inference import InferenceService

@pytest.mark.asyncio
async def test_local_model_processing() -> None:
    service = InferenceService()
    from grid.models.inference import InferenceRequest
    request = InferenceRequest(prompt="Test prompt", model="local-model")
    result = await service._call_local_model(request)
    assert "response" in result.result
    assert result.model == "local-model"

@pytest.mark.asyncio
async def test_openai_model_processing() -> None:
    service = InferenceService()
    from grid.models.inference import InferenceRequest
    request = InferenceRequest(prompt="Test prompt", model="gpt-3.5-turbo")
    result = await service._call_openai_model(request)
    assert "response" in result.result
    assert "gpt-3.5-turbo" in result.model
