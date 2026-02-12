import pytest
import sys
from pathlib import Path

# Ensure the correct src is in Python path (not work/GRID/src)
src_path = Path(__file__).parent.parent.parent / "src"
work_grid_src_path = Path(__file__).parent.parent.parent / "work" / "GRID" / "src"

# Remove work/GRID/src from path if it exists
if str(work_grid_src_path) in sys.path:
    sys.path.remove(str(work_grid_src_path))

# Add our src to the beginning
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from grid.services.inference import InferenceService

@pytest.mark.asyncio
async def test_local_model_processing():
    service = InferenceService()
    from grid.models.inference import InferenceRequest
    request = InferenceRequest(prompt="Test prompt", model="local-model")
    result = await service._call_local_model(request)
    assert "response" in result.result
    assert result.model == "local-model"

@pytest.mark.asyncio
async def test_openai_model_processing():
    service = InferenceService()
    from grid.models.inference import InferenceRequest
    request = InferenceRequest(prompt="Test prompt", model="gpt-3.5-turbo")
    result = await service._call_openai_model(request)
    assert "response" in result.result
    assert "gpt-3.5-turbo" in result.model
