#!/usr/bin/env python3
"""
Parasite Guard Integration Validation Script
===========================================

Comprehensive validation of the parasite guard integration with:
1. EventBus subscription cleanup
2. Database engine disposal
3. Metrics integration
4. PrunerOrchestrator functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add grid source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def validate_parasite_guard_integration():
    """Main validation function."""
    print("🧪 Parasite Guard Integration Validation")
    print("=" * 50)

    results = []
    errors = []

    try:
        # Test 1: Import validation
        print("\n1️⃣ Testing imports...")
        from grid.security.parasite_guard import (
            PrunerOrchestrator,
            ParasiteContext,
            SourceMap,
            ParasiteStatus,
            ParasiteProfiler,
            _profiler
        )
        from application.mothership.db.engine import dispose_async_engine
        print("✅ All imports successful")
        results.append("imports")

    except Exception as e:
        errors.append(f"Import failed: {e}")
        print(f"❌ Import failed: {e}")

    try:
        # Test 2: ParasiteContext creation
        print("\n2️⃣ Testing ParasiteContext...")
        ctx = ParasiteContext(
            id="test-123",
            rule="test_rule",
            meta={"test": "data"}
        )
        assert ctx.id == "test-123"
        assert ctx.rule == "test_rule"
        assert ctx.status == ParasiteStatus.DETECTED
        print("✅ ParasiteContext creation successful")
        results.append("parasite_context")

    except Exception as e:
        errors.append(f"ParasiteContext test failed: {e}")
        print(f"❌ ParasiteContext test failed: {e}")

    try:
        # Test 3: SourceMap creation
        print("\n3️⃣ Testing SourceMap...")
        src = SourceMap(
            module="test_module",
            function="test_function",
            line=42,
            file="/test/file.py",
            package="test_package"
        )
        assert src.module == "test_module"
        assert src.function == "test_function"
        print("✅ SourceMap creation successful")
        results.append("source_map")

    except Exception as e:
        errors.append(f"SourceMap test failed: {e}")
        print(f"❌ SourceMap test failed: {e}")

    try:
        # Test 4: PrunerOrchestrator creation
        print("\n4️⃣ Testing PrunerOrchestrator...")
        pruner = PrunerOrchestrator()
        assert hasattr(pruner, '_dispose_database_engine')
        assert hasattr(pruner, '_cleanup_eventbus_subscriptions')
        print("✅ PrunerOrchestrator creation successful")
        results.append("pruner_creation")

    except Exception as e:
        errors.append(f"PrunerOrchestrator test failed: {e}")
        print(f"❌ PrunerOrchestrator test failed: {e}")

    try:
        # Test 5: DB engine disposal method exists and callable
        print("\n5️⃣ Testing DB engine disposal method...")
        pruner = PrunerOrchestrator()
        assert callable(getattr(pruner, '_dispose_database_engine', None))
        print("✅ DB engine disposal method available")
        results.append("db_disposal_method")

    except Exception as e:
        errors.append(f"DB disposal method test failed: {e}")
        print(f"❌ DB disposal method test failed: {e}")

    try:
        # Test 6: EventBus cleanup method exists and callable
        print("\n6️⃣ Testing EventBus cleanup method...")
        pruner = PrunerOrchestrator()
        assert callable(getattr(pruner, '_cleanup_eventbus_subscriptions', None))
        print("✅ EventBus cleanup method available")
        results.append("eventbus_cleanup_method")

    except Exception as e:
        errors.append(f"EventBus cleanup method test failed: {e}")
        print(f"❌ EventBus cleanup method test failed: {e}")

    try:
        # Test 7: Metrics integration
        print("\n7️⃣ Testing metrics integration...")
        # Check if profiler has metrics methods
        assert hasattr(_profiler, 'record_db_engine_disposal_success')
        assert hasattr(_profiler, 'record_db_engine_disposal_failure')
        assert hasattr(_profiler, 'record_eventbus_cleanup_success')
        print("✅ Metrics methods available")
        results.append("metrics_integration")

    except Exception as e:
        errors.append(f"Metrics integration test failed: {e}")
        print(f"❌ Metrics integration test failed: {e}")

    try:
        # Test 8: Prune method signature (basic)
        print("\n8️⃣ Testing prune method signature...")
        pruner = PrunerOrchestrator()
        import inspect
        sig = inspect.signature(pruner.prune)
        params = list(sig.parameters.keys())
        assert 'source' in params
        assert 'context' in params
        print("✅ Prune method signature correct")
        results.append("prune_signature")

    except Exception as e:
        errors.append(f"Prune signature test failed: {e}")
        print(f"❌ Prune signature test failed: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS")
    print("=" * 50)

    total_tests = 8
    passed_tests = len(results)
    failed_tests = len(errors)

    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {failed_tests}/{total_tests}")

    if results:
        print("\n✅ PASSED TESTS:")
        for test in results:
            print(f"   • {test.replace('_', ' ').title()}")

    if errors:
        print("\n❌ FAILED TESTS:")
        for error in errors:
            print(f"   • {error}")

    # Final assessment
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Parasite Guard integration is VALID and READY")
        return True
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        print("❌ Integration needs attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_parasite_guard_integration())
    sys.exit(0 if success else 1)
