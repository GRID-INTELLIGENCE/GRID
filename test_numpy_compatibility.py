#!/usr/bin/env python3
"""
Test script to verify NumPy 2.4.3 / NEP 50 compatibility
Tests for precision preservation and type promotion changes
"""

import warnings

import numpy as np


def test_nep50_precision_preservation():
    """Test NEP 50 precision preservation behavior"""
    print("=== Testing NEP 50 Precision Preservation ===")

    # Test 1: uint8 precision preservation
    arr_uint8 = np.arange(100, dtype=np.uint8)
    value = arr_uint8[10]

    print(f"Original array dtype: {arr_uint8.dtype}")
    print(f"Extracted value: {value} (dtype: {value.dtype if hasattr(value, 'dtype') else type(value)})")

    # Test multiplication - should preserve uint8 precision
    result_old_behavior = value * 100
    print(f"value * 100 result: {result_old_behavior} (dtype: {result_old_behavior.dtype})")

    # Test array operation - should also preserve uint8
    result_array = arr_uint8 * 100
    print(f"arr_uint8 * 100 result dtype: {result_array.dtype}")

    # Test 2: float32 precision preservation
    arr_float32 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    float_value = arr_float32[0]

    print(f"\nFloat32 array dtype: {arr_float32.dtype}")
    print(f"Float32 value: {float_value}")

    # Test comparison behavior change
    comparison_result = np.float32(1 / 3) == 1 / 3
    print(f"np.float32(1/3) == 1/3: {comparison_result} (should be True in NumPy 2.0+)")

    # Test 3: Error cases for overflow
    try:
        overflow_result = np.array([1], np.uint8) * 1000
        print(f"uint8 * 1000: {overflow_result} (dtype: {overflow_result.dtype})")
    except Exception as e:
        print(f"uint8 * 1000 failed as expected: {e}")

    # Test 4: Complex precision promotion
    complex_result = np.multiply(np.array([1.0], dtype=np.float32), 2.0)
    print(f"float32 * 2.0 result dtype: {complex_result.dtype}")


def test_scalar_performance():
    """Test scalar operation performance improvements"""
    print("\n=== Testing Scalar Performance ===")

    import time

    # Test scalar vs array performance
    scalar_val = 1.5
    array_val = np.array([1.5])

    # Time scalar operations
    start = time.perf_counter()
    for _ in range(10000):
        _result = np.sin(scalar_val)
    scalar_time = time.perf_counter() - start

    # Time array operations
    start = time.perf_counter()
    for _ in range(10000):
        _result = np.sin(array_val)
    array_time = time.perf_counter() - start

    print(f"Scalar operation time: {scalar_time:.6f}s")
    print(f"Array operation time: {array_time:.6f}s")
    print(f"Performance ratio (array/scalar): {array_time / scalar_time:.2f}x")


def test_ml_compatibility():
    """Test compatibility with ML libraries"""
    print("\n=== Testing ML Library Compatibility ===")

    try:
        from sklearn.ensemble import RandomForestClassifier

        # Test with different dtypes
        X_uint8 = np.random.randint(0, 100, (100, 5), dtype=np.uint8)
        y = np.random.randint(0, 2, 100)

        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_uint8, y)

        print("SUCCESS: sklearn with uint8 data")

        # Test prediction
        pred = clf.predict(X_uint8[:5])
        print(f"Prediction shape: {pred.shape}, dtype: {pred.dtype}")

    except ImportError:
        print("WARNING: sklearn not available")
    except Exception as e:
        print(f"ERROR: sklearn compatibility issue: {e}")


def test_pydantic_integration():
    """Test Pydantic integration with NumPy arrays"""
    print("\n=== Testing Pydantic Integration ===")

    try:
        from pydantic import BaseModel

        class Model(BaseModel):
            values: list[float]
            array_field: list[list[float]]

        # Test with numpy arrays
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        model = Model(values=arr.tolist(), array_field=[arr.tolist()])

        print("SUCCESS: Pydantic model creation")
        print(f"Model values: {model.values}")

    except ImportError:
        print("WARNING: Pydantic not available")
    except Exception as e:
        print(f"ERROR: Pydantic integration issue: {e}")


def main():
    """Run all compatibility tests"""
    print("NumPy 2.4.3 / NEP 50 Compatibility Test Suite")
    print("=" * 50)

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_nep50_precision_preservation()
        test_scalar_performance()
        test_ml_compatibility()
        test_pydantic_integration()

        if w:
            print(f"\nWARNING: {len(w)} warnings captured:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")

    print("\n" + "=" * 50)
    print("Compatibility test completed")


if __name__ == "__main__":
    main()
