"""
Unit tests for the model sandbox.
"""

from __future__ import annotations

import asyncio

import pytest

from safety.model.sandbox import SandboxConfig, SandboxResult, run_safe_call


async def _mock_model_call(prompt: str, **kwargs):
    """Mock model call that returns immediately."""
    return {
        "text": f"Response to: {prompt[:50]}",
        "tokens_used": len(prompt.split()),
    }


async def _slow_model_call(prompt: str, **kwargs):
    """Mock model call that takes too long."""
    await asyncio.sleep(5)
    return {"text": "late", "tokens_used": 1}


@pytest.mark.asyncio
class TestSandbox:
    async def test_basic_call(self):
        result = await run_safe_call(
            _mock_model_call,
            prompt="Hello world",
            user_id="test-user",
        )
        assert isinstance(result, SandboxResult)
        assert "Hello world" in result.text
        assert result.latency_seconds >= 0

    async def test_timeout(self):
        config = SandboxConfig(timeout_seconds=0.1)
        with pytest.raises(asyncio.TimeoutError):
            await run_safe_call(
                _slow_model_call,
                prompt="test",
                user_id="test-user",
                config=config,
            )

    async def test_max_tokens_enforced(self):
        config = SandboxConfig(max_tokens=10)

        async def _model(prompt, **kwargs):
            assert kwargs["max_tokens"] <= 10
            return {"text": "ok", "tokens_used": 5}

        result = await run_safe_call(
            _model,
            prompt="test",
            user_id="test-user",
            config=config,
            max_tokens=100,  # Should be clamped to 10
        )
        assert result.text == "ok"

    async def test_tools_stripped_when_disabled(self):
        config = SandboxConfig(allow_tools=False)

        async def _model(prompt, **kwargs):
            assert "tools" not in kwargs
            assert "functions" not in kwargs
            return {"text": "ok", "tokens_used": 1}

        await run_safe_call(
            _model,
            prompt="test",
            user_id="test-user",
            config=config,
            tools=[{"name": "evil_tool"}],
            functions=[{"name": "evil_fn"}],
        )

    async def test_rps_limit(self):
        config = SandboxConfig(max_rps=2.0)
        # First two calls should succeed
        for _ in range(2):
            await run_safe_call(
                _mock_model_call,
                prompt="test",
                user_id="rps-test-user",
                config=config,
            )
        # Third call within same second should fail
        with pytest.raises(RuntimeError, match="RPS limit exceeded"):
            await run_safe_call(
                _mock_model_call,
                prompt="test",
                user_id="rps-test-user",
                config=config,
            )
