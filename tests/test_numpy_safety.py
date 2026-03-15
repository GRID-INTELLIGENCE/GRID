#!/usr/bin/env python3
"""
Test NumPy safety utilities for GRID
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import warnings

import numpy as np

from tools.numpy_safety import (
    DEFAULT_COUNT_DTYPE,
    DEFAULT_EMBEDDING_DTYPE,
    DEFAULT_FEATURE_DTYPE,
    DTypeError,
    safe_batch_similarity,
    safe_feature_extraction,
    safe_float32_conversion,
    safe_normalization,
    safe_similarity_calculation,
    safe_softmax,
    safe_uint_conversion,
    validate_numerical_input,
)


def test_safe_float32_conversion():
    """Test safe float32 conversion"""
    print("=== Testing Safe Float32 Conversion ===")

    # Test normal conversion
    values = [1.0, 2.5, 3.7]
    result = safe_float32_conversion(values)
    print(f"Normal conversion: {result} (dtype: {result.dtype})")

    # Test large values (should warn)
    try:
        large_values = [1e20, 1e30, 1e40]
        result = safe_float32_conversion(large_values, allow_overflow=True)
        print(f"Large values (with overflow allowed): {result}")
    except DTypeError as e:
        print(f"Large values error: {e}")

    # Test NaN/Inf rejection
    try:
        bad_values = [1.0, np.nan, 2.0]
        result = safe_float32_conversion(bad_values)
        print(f"NaN values: {result}")
    except DTypeError as e:
        print(f"NaN rejection: {e}")


def test_safe_uint_conversion():
    """Test safe unsigned integer conversion"""
    print("\n=== Testing Safe UInt Conversion ===")

    # Test normal conversion
    values = [100, 200, 300]
    result = safe_uint_conversion(values, np.uint32)
    print(f"Normal conversion: {result} (dtype: {result.dtype})")

    # Test overflow
    try:
        large_values = [100, 200, 5000000000]  # Exceeds uint32 max
        result = safe_uint_conversion(large_values, np.uint32, allow_overflow=True)
        print(f"Overflow (allowed): {result}")
    except DTypeError as e:
        print(f"Overflow error: {e}")

    # Test negative values
    try:
        neg_values = [-1, 0, 1]
        result = safe_uint_conversion(neg_values, np.uint32)
        print(f"Negative values: {result}")
    except DTypeError as e:
        print(f"Negative rejection: {e}")


def test_safe_similarity():
    """Test safe similarity calculations"""
    print("\n=== Testing Safe Similarity Calculation ===")

    # Test normal similarity
    vec1 = np.array([1.0, 2.0, 3.0], dtype=DEFAULT_EMBEDDING_DTYPE)
    vec2 = np.array([1.1, 2.1, 3.1], dtype=DEFAULT_EMBEDDING_DTYPE)

    similarity = safe_similarity_calculation(vec1, vec2)
    print(f"Normal similarity: {similarity:.6f}")

    # Test zero vectors
    zero_vec = np.zeros(3, dtype=DEFAULT_EMBEDDING_DTYPE)
    similarity = safe_similarity_calculation(vec1, zero_vec)
    print(f"Zero vector similarity: {similarity:.6f}")

    # Test batch similarity
    embeddings = np.random.randn(100, 10).astype(DEFAULT_EMBEDDING_DTYPE)
    query = np.random.randn(10).astype(DEFAULT_EMBEDDING_DTYPE)

    similarities = safe_batch_similarity(embeddings, query)
    print(
        f"Batch similarities: shape={similarities.shape}, range=[{np.min(similarities):.3f}, {np.max(similarities):.3f}]"
    )


def test_safe_feature_extraction():
    """Test safe feature extraction"""
    print("\n=== Testing Safe Feature Extraction ===")

    # Test normal features
    features = [0.5, 1.2, 0.8, 2.1, 0.3]
    feature_names = ["bm25", "vector_sim", "freshness", "popularity", "relevance"]

    result = safe_feature_extraction(features, DEFAULT_FEATURE_DTYPE, feature_names)
    print(f"Normal features: {result} (dtype: {result.dtype})")

    # Test with invalid values
    try:
        bad_features = [0.5, np.nan, 0.8, 2.1, 0.3]
        result = safe_feature_extraction(bad_features, DEFAULT_FEATURE_DTYPE, feature_names)
        print(f"Features with NaN: {result}")
    except DTypeError as e:
        print(f"NaN detection: {e}")


def test_safe_normalization():
    """Test safe normalization"""
    print("\n=== Testing Safe Normalization ===")

    # Test minmax normalization
    values = np.array([10, 20, 30, 40, 50], dtype=DEFAULT_FEATURE_DTYPE)
    normalized = safe_normalization(values, method="minmax")
    print(f"Minmax normalized: {normalized}")

    # Test z-score normalization
    normalized = safe_normalization(values, method="zscore")
    print(f"Z-score normalized: mean={np.mean(normalized):.3f}, std={np.std(normalized):.3f}")

    # Test constant values
    constant_values = np.array([5, 5, 5, 5, 5], dtype=DEFAULT_FEATURE_DTYPE)
    normalized = safe_normalization(constant_values, method="minmax")
    print(f"Constant values: {normalized}")


def test_safe_softmax():
    """Test safe softmax calculation"""
    print("\n=== Testing Safe Softmax ===")

    # Test normal scores
    scores = np.array([2.0, 1.0, 0.5], dtype=DEFAULT_FEATURE_DTYPE)
    softmax = safe_softmax(scores)
    print(f"Normal softmax: {softmax} (sum: {np.sum(softmax):.6f})")

    # Test extreme scores
    extreme_scores = np.array([1000, 1, 2], dtype=DEFAULT_FEATURE_DTYPE)
    softmax = safe_softmax(extreme_scores)
    print(f"Extreme softmax: {softmax} (sum: {np.sum(softmax):.6f})")

    # Test temperature
    softmax = safe_softmax(scores, temperature=0.5)
    print(f"Temperature softmax (T=0.5): {softmax}")


def test_input_validation():
    """Test comprehensive input validation"""
    print("\n=== Testing Input Validation ===")

    # Test normal validation
    values = [1.0, 2.0, 3.0]
    validated = validate_numerical_input(values, "test", expected_dtype=DEFAULT_FEATURE_DTYPE)
    print(f"Normal validation: {validated}")

    # Test range validation
    try:
        out_of_range = [0.5, 1.5, 2.5]
        validated = validate_numerical_input(out_of_range, "test", min_val=1.0, max_val=2.0)
        print(f"Range validation: {validated}")
    except DTypeError as e:
        print(f"Range error: {e}")

    # Test NaN validation
    try:
        nan_values = [1.0, np.nan, 2.0]
        validated = validate_numerical_input(nan_values, "test", allow_nan=False)
        print(f"NaN validation: {validated}")
    except DTypeError as e:
        print(f"NaN error: {e}")


def test_real_world_scenarios():
    """Test safety utilities with real-world scenarios"""
    print("\n=== Testing Real-World Scenarios ===")

    # Scenario 1: Embedding similarity with potential overflow
    print("Scenario 1: Large embedding similarities")
    large_embeddings = np.random.randn(1000, 384).astype(DEFAULT_EMBEDDING_DTYPE) * 100
    query = np.random.randn(384).astype(DEFAULT_EMBEDDING_DTYPE) * 100

    try:
        similarities = safe_batch_similarity(large_embeddings, query)
        print(f"  Large embeddings processed: shape={similarities.shape}")
        print(f"  Similarity range: [{np.min(similarities):.3f}, {np.max(similarities):.3f}]")
    except DTypeError as e:
        print(f"  Large embeddings error: {e}")

    # Scenario 2: Feature extraction with mixed types
    print("Scenario 2: Mixed feature extraction")
    mixed_features = [0.8, 2, 0.5, 100, 0.3]  # float, int, float, int, float
    feature_names = ["similarity", "count", "freshness", "popularity", "score"]

    try:
        features = safe_feature_extraction(mixed_features, DEFAULT_FEATURE_DTYPE, feature_names)
        print(f"  Mixed features: {features}")
    except DTypeError as e:
        print(f"  Mixed features error: {e}")

    # Scenario 3: Counting operations with potential overflow
    print("Scenario 3: Counting operations")
    document_counts = [1000, 2000, 3000, 4000, 5000]

    try:
        counts = safe_uint_conversion(document_counts, DEFAULT_COUNT_DTYPE, "document_counts")
        print(f"  Document counts: {counts}")

        # Test increment
        incremented = counts + 100
        print(f"  Incremented counts: {incremented}")
    except DTypeError as e:
        print(f"  Counting error: {e}")


def main():
    """Run all safety utility tests"""
    print("GRID NumPy Safety Utilities Test Suite")
    print("=" * 50)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_safe_float32_conversion()
        test_safe_uint_conversion()
        test_safe_similarity()
        test_safe_feature_extraction()
        test_safe_normalization()
        test_safe_softmax()
        test_input_validation()
        test_real_world_scenarios()

        if w:
            print(f"\nWARNING: {len(w)} warnings captured:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")

    print("\n" + "=" * 50)
    print("Safety utilities testing completed")


if __name__ == "__main__":
    main()
