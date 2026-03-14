#!/usr/bin/env python3
"""
Comprehensive edge case tests for NumPy 2.4.3 NEP 50 in GRID
Tests for scenarios that could cause precision or overflow issues
"""

import warnings

import numpy as np


def test_mixed_precision_edge_cases():
    """Test edge cases in mixed precision operations"""
    print("=== Testing Mixed Precision Edge Cases ===")

    # Test 1: Very small differences in similarity calculations
    vec1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    vec2 = np.array([1.0000001, 2.0000001, 3.0000001], dtype=np.float32)

    # Different precision calculations
    dot_float32 = np.dot(vec1, vec2)
    dot_mixed = np.dot(vec1.astype(np.float64), vec2.astype(np.float64))

    print(f"Float32 dot product: {dot_float32:.10f}")
    print(f"Float64 dot product: {dot_mixed:.10f}")
    print(f"Relative difference: {abs(dot_float32 - dot_mixed) / dot_mixed:.2e}")

    # Test 2: Cumulative operations with precision loss
    small_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

    cumsum_float32 = np.cumsum(small_values)
    cumsum_float64 = np.cumsum(small_values.astype(np.float64))

    print(f"Cumsum precision loss: {abs(cumsum_float32[-1] - cumsum_float64[-1]):.10f}")

    # Test 3: Matrix operations with different precisions
    mat_float32 = np.random.randn(10, 10).astype(np.float32)
    mat_float64 = mat_float32.astype(np.float64)

    eigenvals_32 = np.linalg.eigvals(mat_float32)
    eigenvals_64 = np.linalg.eigvals(mat_float64)

    max_eigen_diff = np.max(np.abs(eigenvals_32 - eigenvals_64))
    print(f"Eigenvalue precision difference: {max_eigen_diff:.2e}")


def test_embedding_similarity_edge_cases():
    """Test edge cases in embedding similarity calculations"""
    print("\n=== Testing Embedding Similarity Edge Cases ===")

    # Test 1: Near-identical vectors
    base_vec = np.random.randn(384).astype(np.float32)
    similar_vec = base_vec + np.random.randn(384).astype(np.float32) * 0.001

    # Cosine similarity
    cos_sim = np.dot(base_vec, similar_vec) / (np.linalg.norm(base_vec) * np.linalg.norm(similar_vec))
    print(f"Near-identical cosine similarity: {cos_sim:.10f}")

    # Test 2: Orthogonal vectors
    orth_vec1 = np.random.randn(384).astype(np.float32)
    orth_vec2 = np.random.randn(384).astype(np.float32)

    # Make orthogonal (Gram-Schmidt simplified)
    orth_vec2 = orth_vec2 - np.dot(orth_vec2, orth_vec1) * orth_vec1 / np.dot(orth_vec1, orth_vec1)
    orth_sim = np.dot(orth_vec1, orth_vec2) / (np.linalg.norm(orth_vec1) * np.linalg.norm(orth_vec2))
    print(f"Orthogonal cosine similarity: {orth_sim:.10f}")

    # Test 3: Zero vectors
    zero_vec = np.zeros(384, dtype=np.float32)
    try:
        zero_sim = np.dot(base_vec, zero_vec) / (np.linalg.norm(base_vec) * np.linalg.norm(zero_vec))
        print(f"Zero vector similarity: {zero_sim:.10f}")
    except Exception as e:
        print(f"Zero vector error (expected): {e}")

    # Test 4: Very large embeddings (potential overflow)
    large_embeddings = np.random.randn(1000, 1024).astype(np.float32) * 100
    query = np.random.randn(1024).astype(np.float32) * 100

    similarities = np.dot(large_embeddings, query)
    print(f"Large embedding similarities - max: {np.max(similarities):.2e}, min: {np.min(similarities):.2e}")
    print(f"Any infinities: {np.any(np.isinf(similarities))}")


def test_ranking_and_scoring_edge_cases():
    """Test edge cases in ranking and scoring systems"""
    print("\n=== Testing Ranking and Scoring Edge Cases ===")

    # Test 1: BM25 score edge cases
    # Very high term frequency
    tf = np.array([100, 1000, 10000], dtype=np.float32)
    idf = np.array([2.0, 1.5, 1.0], dtype=np.float32)

    bm25_scores = tf * idf
    print(f"High TF BM25 scores: {bm25_scores}")
    print(f"Any BM25 overflows: {np.any(np.isinf(bm25_scores))}")

    # Test 2: Feature vector edge cases
    # Mix of very large and very small features
    features = np.array([[1e-10, 1e10, 0.5, 1000], [1e-8, 1e8, 0.3, 100], [1e-6, 1e6, 0.7, 10]], dtype=np.float32)

    # Normalize features
    feature_norms = np.linalg.norm(features, axis=1, keepdims=True)
    normalized_features = features / (feature_norms + 1e-8)  # Add epsilon to avoid division by zero

    print(f"Feature normalization successful: {not np.any(np.isnan(normalized_features))}")

    # Test 3: Learning-to-rank edge cases
    # Extreme relevance labels
    relevance_labels = np.array([0, 1, 2, 3, 4], dtype=np.uint8)
    predicted_scores = np.array([0.1, 0.9, 2.1, 3.5, 4.2], dtype=np.float32)

    # Calculate MSE
    mse = np.mean((predicted_scores - relevance_labels.astype(np.float32)) ** 2)
    print(f"Extreme relevance MSE: {mse:.6f}")

    # Test 4: Ranking with ties
    scores_with_ties = np.array([0.8, 0.8, 0.6, 0.6, 0.6, 0.4], dtype=np.float32)

    # Stable sorting (preserve order for ties)
    indices = np.argsort(-scores_with_ties, kind="stable")
    print(f"Tie handling - indices: {indices}")


def test_cognitive_computation_edge_cases():
    """Test edge cases in cognitive computations"""
    print("\n=== Testing Cognitive Computation Edge Cases ===")

    # Test 1: Temporal resonance calculations
    # Very small time differences
    time_diffs = np.array([1e-6, 1e-5, 1e-4, 1e-3], dtype=np.float32)

    # Resonance frequency calculation
    frequencies = 1.0 / (time_diffs + 1e-9)  # Add epsilon
    print(f"Temporal frequencies: {frequencies}")
    print(f"Any frequency overflows: {np.any(np.isinf(frequencies))}")

    # Test 2: Cognitive load calculations
    # Edge case: zero or negative loads
    load_values = np.array([0.0, 0.1, 0.5, 1.0, 2.0], dtype=np.float32)

    # Load score calculation (from pattern recognition)
    load_scores = 1.0 - np.abs(load_values - 1.0) / 1.0  # Optimal at 1.0
    load_scores = np.clip(load_scores, 0.0, 1.0)
    print(f"Load scores: {load_scores}")

    # Test 3: Component vector edge cases
    # All zero components
    zero_vision = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    zero_sound = np.array([0.0, 0.0], dtype=np.float32)
    zero_locomotion = np.array([0.0, 0.0], dtype=np.float32)

    combined_zero = np.concatenate([zero_vision, zero_sound, zero_locomotion])
    zero_norm = np.linalg.norm(combined_zero)
    print(f"Zero component norm: {zero_norm}")

    # Test 4: Maximum value components
    max_vision = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    max_sound = np.array([1.0, 1.0], dtype=np.float32)
    max_locomotion = np.array([1.0, 1.0], dtype=np.float32)

    combined_max = np.concatenate([max_vision, max_sound, max_locomotion])
    max_norm = np.linalg.norm(combined_max)
    print(f"Maximum component norm: {max_norm}")


def test_overflow_and_underflow_scenarios():
    """Test specific overflow and underflow scenarios"""
    print("\n=== Testing Overflow and Underflow Scenarios ===")

    # Test 1: Integer overflow in counting operations
    counter_uint8 = np.array([250, 251, 252, 253, 254, 255], dtype=np.uint8)
    increment = 10

    # This should wrap around
    result_uint8 = counter_uint8 + increment
    print(f"Uint8 overflow: {counter_uint8} + {increment} = {result_uint8}")

    # Test with uint16
    counter_uint16 = counter_uint8.astype(np.uint16)
    result_uint16 = counter_uint16 + increment
    print(f"Uint16 safe: {counter_uint16} + {increment} = {result_uint16}")

    # Test 2: Floating point overflow in similarity
    large_vec = np.array([1e38, 1e38, 1e38], dtype=np.float32)
    similarity = np.dot(large_vec, large_vec)
    print(f"Large vector similarity: {similarity}")
    print(f"Similarity is infinite: {np.isinf(similarity)}")

    # Test 3: Underflow in small probability calculations
    tiny_probs = np.array([1e-20, 1e-30, 1e-40], dtype=np.float32)

    # Log probability
    log_probs = np.log(tiny_probs + 1e-50)  # Add epsilon
    print(f"Log probabilities: {log_probs}")
    print(f"Any negative infinities: {np.any(np.isneginf(log_probs))}")

    # Test 4: Matrix multiplication overflow
    large_matrix = np.random.randn(100, 100).astype(np.float32) * 1e10
    vector = np.random.randn(100).astype(np.float32) * 1e10

    try:
        result = np.dot(large_matrix, vector)
        print("Large matrix-vector multiplication successful")
        print(f"Result range: [{np.min(result):.2e}, {np.max(result):.2e}]")
    except Exception as e:
        print(f"Matrix multiplication error: {e}")


def test_api_boundary_conditions():
    """Test boundary conditions in API responses"""
    print("\n=== Testing API Boundary Conditions ===")

    # Test 1: JSON serialization edge cases
    # NaN and Inf values (should not appear in API responses)
    problematic_values = np.array([np.nan, np.inf, -np.inf, 1.0, 2.0], dtype=np.float32)

    # Filter out problematic values
    valid_mask = np.isfinite(problematic_values)
    clean_values = problematic_values[valid_mask]

    print(f"Original values: {problematic_values}")
    print(f"Clean values: {clean_values}")
    print(f"Values filtered: {len(problematic_values) - len(clean_values)}")

    # Test 2: Pagination calculations
    total_items = np.array([1000], dtype=np.uint32)
    page_size = np.array([0, 1, 10, 100, 1000, 10000], dtype=np.uint32)

    for size in page_size:
        if size > 0:
            num_pages = np.ceil(total_items / size).astype(np.uint32)
            print(f"Page size {size}: {num_pages} pages")
        else:
            print("Page size 0: Invalid")

    # Test 3: Rate limiting calculations
    request_counts = np.array([10, 50, 100, 500, 1000], dtype=np.uint16)
    rate_limit = 100

    # Calculate remaining capacity
    remaining = np.maximum(0, rate_limit - request_counts)
    print(f"Rate limit remaining: {remaining}")

    # Test 4: Scoring precision in responses
    # Ensure scores are within reasonable range
    raw_scores = np.random.randn(100).astype(np.float32)

    # Sigmoid to bound between 0 and 1
    bounded_scores = 1.0 / (1.0 + np.exp(-raw_scores))
    print(f"Score range: [{np.min(bounded_scores):.6f}, {np.max(bounded_scores):.6f}]")
    print(f"All scores valid: {np.all((bounded_scores >= 0.0) & (bounded_scores <= 1.0))}")


def main():
    """Run all edge case tests"""
    print("GRID NumPy 2.4.3 Edge Case Test Suite")
    print("=" * 50)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_mixed_precision_edge_cases()
        test_embedding_similarity_edge_cases()
        test_ranking_and_scoring_edge_cases()
        test_cognitive_computation_edge_cases()
        test_overflow_and_underflow_scenarios()
        test_api_boundary_conditions()

        if w:
            print(f"\nWARNING: {len(w)} warnings captured:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")

    print("\n" + "=" * 50)
    print("Edge case testing completed")


if __name__ == "__main__":
    main()
