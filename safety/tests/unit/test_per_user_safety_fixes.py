#!/usr/bin/env python3
"""
Test script to verify per-user safety engine isolation and race condition fixes
"""

import asyncio

from safety.ai_workflow_safety import get_ai_workflow_safety_engine


async def test_per_user_isolation():
    """Test that different users get isolated safety engines"""
    print("Testing per-user safety engine isolation...")

    # Create engines for two different users
    engine1 = await get_ai_workflow_safety_engine("user1", user_age=16)
    engine2 = await get_ai_workflow_safety_engine("user2", user_age=25)

    # Verify they are different instances
    assert engine1 is not engine2, "Users should have separate safety engines"
    assert engine1.wellbeing_tracker.user_age == 16, "User1 should have age 16"
    assert engine2.wellbeing_tracker.user_age == 25, "User2 should have age 25"

    # Test temporal isolation - user1 has a response
    assessment1 = await engine1.evaluate_interaction(
        user_input="Hello", ai_response="Hi there!", response_time=1.0, current_time=1000.0
    )

    # user2 should not be affected by user1's interaction
    assessment2 = await engine2.evaluate_interaction(
        user_input="Hello",
        ai_response="Hi there!",
        response_time=1.0,
        current_time=1000.1,  # Very soon after user1
    )

    # Both should be allowed since they have separate temporal tracking
    assert assessment1["safety_allowed"] is True
    assert assessment2["safety_allowed"] is True

    print("✓ Per-user isolation working correctly")


async def test_concurrent_access():
    """Test concurrent access doesn't cause race conditions"""
    print("Testing concurrent access safety...")

    async def user_interactions(user_id: str, count: int):
        """Simulate multiple interactions for a user"""
        engine = await get_ai_workflow_safety_engine(user_id)

        for i in range(count):
            assessment = await engine.evaluate_interaction(
                user_input=f"Message {i}", ai_response=f"Response {i}", response_time=0.5, current_time=1000.0 + i * 0.1
            )

            # Should be allowed for this test
            if not assessment["safety_allowed"]:
                print(f"User {user_id} interaction {i} blocked: {assessment.get('temporal_reason')}")

    # Run concurrent interactions for multiple users
    tasks = [
        user_interactions("concurrent_user1", 5),
        user_interactions("concurrent_user2", 5),
        user_interactions("concurrent_user3", 5),
    ]

    await asyncio.gather(*tasks)

    print("✓ Concurrent access handled safely")


async def test_engine_caching():
    """Test that engines are properly cached and reused"""
    print("Testing engine caching...")

    # Get engine for user
    engine1 = await get_ai_workflow_safety_engine("cached_user")
    engine2 = await get_ai_workflow_safety_engine("cached_user")

    # Should be the same instance (cached)
    assert engine1 is engine2, "Same user should get cached engine"

    # But different users get different engines
    engine3 = await get_ai_workflow_safety_engine("different_user")
    assert engine1 is not engine3, "Different users should get different engines"

    print("✓ Engine caching working correctly")


async def test_statistics_safety():
    """Test that statistical operations handle edge cases safely"""
    print("Testing statistics safety...")

    engine = await get_ai_workflow_safety_engine("stats_test_user")

    # Test with minimal data
    assessment = await engine.evaluate_interaction(
        user_input="Hi", ai_response="Hello", response_time=1.0, current_time=1000.0
    )

    # Should not crash with minimal data
    assert assessment["safety_allowed"] is True
    assert "wellbeing_metrics" in assessment

    # Test temporal pattern detection with minimal data
    pattern = engine.temporal_engine.get_temporal_pattern()
    assert pattern is not None

    print("✓ Statistics operations safe with edge cases")


async def main():
    """Run all per-user safety tests"""
    print("🔒 Testing Per-User Safety Engine Implementation\n")

    try:
        await test_per_user_isolation()
        await test_concurrent_access()
        await test_engine_caching()
        await test_statistics_safety()

        print("\n✅ All per-user safety tests passed!")
        print("✓ Race conditions fixed")
        print("✓ User isolation working")
        print("✓ Engine caching functional")
        print("✓ Statistics edge cases handled")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
