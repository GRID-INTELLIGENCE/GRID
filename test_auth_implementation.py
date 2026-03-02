#!/usr/bin/env python3
"""Test script for signature-based authentication and narrowed accessibility scope."""

import asyncio
import time
from src.search.guardrail.policy import GuardrailPolicy
from src.search.guardrail.orchestrator import GuardrailOrchestrator
from src.search.guardrail.auth import AuthSignature


def test_signature_based_auth():
    """Test signature-based authentication for profile activation."""
    print("Testing signature-based authentication...")

    # Create policy with default profiles
    policy = GuardrailPolicy.default()

    # Test 1: Basic profile should activate without authentication
    print("\nTest 1: Basic profile activation (no auth required)")
    success = policy.activate_profile("basic", user_role="basic")
    print(f"Basic profile activation: {'SUCCESS' if success else 'FAILED'}")
    assert success, "Basic profile should activate without auth"
    assert policy.active_profile == "basic"

    # Test 2: Developer profile with valid signature
    print("\nTest 2: Developer profile with valid signature")
    user_id = "test_user_123"
    timestamp = int(time.time())

    # Create valid signature
    auth_sig = policy.create_profile_signature("developer", user_id, timestamp)
    assert auth_sig is not None, "Should create signature for developer profile"

    # Try to activate with valid signature
    success = policy.activate_profile(
        "developer",
        user_id=user_id,
        auth_signature=auth_sig,
        user_role="developer"
    )
    print(f"Developer profile with valid sig: {'SUCCESS' if success else 'FAILED'}")
    assert success, "Developer profile should activate with valid signature"
    assert policy.active_profile == "developer"

    # Test 3: Developer profile with invalid signature (wrong timestamp)
    print("\nTest 3: Developer profile with invalid signature (expired)")
    old_timestamp = timestamp - 600  # 10 minutes ago (expired)
    invalid_sig = policy.create_profile_signature("developer", user_id, old_timestamp)

    success = policy.activate_profile(
        "developer",
        user_id=user_id,
        auth_signature=invalid_sig,
        user_role="developer"
    )
    print(f"Developer profile with expired sig: {'SUCCESS' if success else 'FAILED'}")
    assert not success, "Developer profile should reject expired signature"
    assert policy.active_profile != "developer"


def test_narrowed_accessibility_scope():
    """Test narrowed accessibility scope based on roles and permissions."""
    print("\n\nTesting narrowed accessibility scope...")

    policy = GuardrailPolicy.default()

    # Test 1: Basic user trying to access developer profile
    print("\nTest 1: Basic user accessing developer profile")
    success = policy.activate_profile("developer", user_role="basic")
    print(f"Basic user -> developer: {'ALLOWED' if success else 'DENIED'}")
    assert not success, "Basic user should not access developer profile"
    assert policy.active_profile is None

    # Test 2: Developer user accessing developer profile (allowed)
    print("\nTest 2: Developer user accessing developer profile")
    user_id = "dev_user_456"
    timestamp = int(time.time())
    auth_sig = policy.create_profile_signature("developer", user_id, timestamp)

    success = policy.activate_profile(
        "developer",
        user_id=user_id,
        auth_signature=auth_sig,
        user_role="developer"
    )
    print(f"Developer user -> developer: {'ALLOWED' if success else 'DENIED'}")
    assert success, "Developer user should access developer profile"

    # Test 3: Manager accessing any profile (should be narrowed appropriately)
    print("\nTest 3: Manager accessing restricted profile")
    success = policy.activate_profile("admin", user_role="manager")  # admin not in default profiles
    print(f"Manager -> admin (non-existent): {'ALLOWED' if success else 'DENIED'}")
    assert not success, "Manager should not access non-existent profiles"

    # Test 4: Explicit permissions override role restrictions
    print("\nTest 4: Explicit permissions override")
    user_permissions = {"admin"}  # Explicitly grant admin access
    success = policy.activate_profile(
        "manager",
        user_permissions=user_permissions,
        user_role="basic"  # Low role but explicit permission
    )
    print(f"Basic user with admin permission -> manager: {'ALLOWED' if success else 'DENIED'}")
    # This should work since manager is allowed for users with admin permission


async def test_orchestrator_integration():
    """Test orchestrator integration with auth."""
    print("\n\nTesting orchestrator integration...")

    orchestrator = GuardrailOrchestrator()

    # Test activation through orchestrator
    user_id = "test_user_789"
    timestamp = int(time.time())
    auth_sig = orchestrator.policy.create_profile_signature("designer", user_id, timestamp)

    success = orchestrator.activate_profile(
        "designer",
        user_id=user_id,
        auth_signature=auth_sig,
        user_role="designer"
    )
    print(f"Orchestrator designer activation: {'SUCCESS' if success else 'FAILED'}")
    assert success, "Orchestrator should activate designer profile with valid auth"
    assert orchestrator.policy.active_profile == "designer"


if __name__ == "__main__":
    test_signature_based_auth()
    test_narrowed_accessibility_scope()
    asyncio.run(test_orchestrator_integration())
    print("\n✅ All tests passed! Signature-based auth and narrowed accessibility scope working correctly.")
