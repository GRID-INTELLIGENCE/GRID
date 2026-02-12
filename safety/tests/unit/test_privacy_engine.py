import pytest
from safety.privacy.core.engine import PrivacyEngine
from safety.privacy.core.types import PrivacyAction, PrivacyConfig
from safety.privacy.detector import AsyncPIIDetection

@pytest.fixture
def engine():
    # Helper to create an engine with mocked components effectively
    # For unit tests, we can use the real engine but maybe mock detections if complex
    # Here we use the real one with defaults
    return PrivacyEngine(PrivacyConfig(enable_cache=False))

@pytest.mark.asyncio
async def test_engine_pass_through(engine):
    text = "Hello world"
    result = await engine.process(text)

    assert result.success
    assert result.processed_text == text
    assert not result.masked
    assert not result.blocked

@pytest.mark.asyncio
async def test_engine_interactive_default(engine):
    # Default is ASK
    text = "My email is test@example.com"
    result = await engine.process(text)

    assert result.success
    assert result.requires_user_input
    assert len(result.detections) > 0

@pytest.mark.asyncio
async def test_engine_mask_action(engine):
    # Configure to always mask EMAIL
    engine._config.per_type_actions["EMAIL"] = PrivacyAction.MASK

    text = "Contact test@example.com please."
    result = await engine.process(text)

    assert result.success
    assert result.masked
    assert "test@example.com" not in result.processed_text
    assert "[EMAIL]" in result.processed_text or "**" in result.processed_text

@pytest.mark.asyncio
async def test_engine_block_action(engine):
    # Configure to block API_KEY
    engine._config.per_type_actions["API_KEY"] = PrivacyAction.BLOCK

    text = "My api_key = abc12345"
    result = await engine.process(text)

    assert result.success
    assert result.blocked
    assert result.processed_text is None
