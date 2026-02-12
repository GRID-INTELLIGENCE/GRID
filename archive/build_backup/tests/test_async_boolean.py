"""
Test suite for async_boolean module.

Covers the deny_request coroutine with pytest-asyncio.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from async_boolean import deny_request  # type: ignore


class TestDenyRequest:
    """Test cases for deny_request function."""

    @pytest.mark.asyncio
    async def test_deny_request_returns_zero(self):
        """Step 3️⃣: Verify the coroutine returns exactly 0."""
        result = await deny_request()
        assert result == 0, f"Expected 0, got {result}"

    @pytest.mark.asyncio
    async def test_deny_request_is_coroutine(self):
        """Verify deny_request returns a coroutine object."""
        coroutine = deny_request()
        assert asyncio.iscoroutine(coroutine), "deny_request should return a coroutine"
        await coroutine

    @pytest.mark.asyncio
    async def test_deny_request_multiple_calls(self):
        """Verify deny_request can be called multiple times."""
        results = await asyncio.gather(
            deny_request(),
            deny_request(),
            deny_request(),
        )
        assert all(r == 0 for r in results), "All calls should return 0"


def test_deny_request_with_asyncio_run():
    """Step 2️⃣: Execute the coroutine directly with asyncio.run."""
    result = asyncio.run(deny_request())
    assert result == 0
    print("✅ Assertion passed – function returns 0")
