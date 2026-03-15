#!/usr/bin/env python3
"""
Test GRID-specific operations that might be affected by NEP 50
Focus on pattern recognition, cognitive calculations, and scoring
"""

import numpy as np


def test_pattern_recognition_calculations():
    """Test pattern recognition calculations from cognitive/patterns/recognition.py"""
    print("=== Testing Pattern Recognition Calculations ===")

    # Test 1: Flow score calculation (line 233)
    cognitive_load = np.array([3.0, 5.0, 7.0], dtype=np.float32)  # Different loads
    engagement = 0.8
    focus_score = 0.9
    time_distortion = 0.1

    # Original calculation: 1.0 - abs(cognitive_load - 5.0) / 5.0
    for load in cognitive_load:
        load_score = 1.0 - abs(float(load) - 5.0) / 5.0
        flow_score = (load_score + engagement + focus_score + time_distortion) / 4.0
        print(f"Load {load}: load_score={load_score:.3f}, flow_score={flow_score:.3f}")

    # Test 2: Momentum score calculations (lines 413, 416, 419)
    engagement = 0.7

    # Espresso mode
    momentum_espresso = 0.8 + (engagement * 0.2)
    print(f"Espresso momentum: {momentum_espresso:.3f}")

    # Americano mode
    momentum_americano = 0.5 + (engagement * 0.3)
    print(f"Americano momentum: {momentum_americano:.3f}")

    # Cold Brew mode
    momentum_coldbrew = 0.3 + (engagement * 0.2)
    print(f"Cold Brew momentum: {momentum_coldbrew:.3f}")

    # Test 3: Variance calculations (line 463-464)
    distances = np.array([1.2, 1.5, 1.8, 2.1, 1.4], dtype=np.float32)
    avg_dist = float(np.mean(distances))
    variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
    consistency = 1.0 - min(variance / (avg_dist**2 + 1), 1.0)

    print(f"Distances variance: {variance:.6f}, consistency: {consistency:.3f}")

    # Test with numpy variance for comparison
    np_variance = np.var(distances)
    print(f"NumPy variance: {np_variance:.6f}")


def test_cognitive_unit_operations():
    """Test cognitive unit vector operations"""
    print("\n=== Testing Cognitive Unit Operations ===")

    # Test component vectors (from cognitive_unit.py)
    vision_vector = np.array([0.5, 0.7, 0.3], dtype=np.float32)  # hue, luminance, saturation
    sound_vector = np.array([0.4, 0.6], dtype=np.float32)  # mel, amplitude
    locomotion_vector = np.array([0.8, 0.2], dtype=np.float32)  # heading, speed

    # Concatenate components
    components = np.concatenate([vision_vector, sound_vector, locomotion_vector])
    print(f"Combined components: {components} (dtype: {components.dtype})")

    # Pad to vector size
    vector_size = 32
    result = np.zeros(vector_size, dtype=np.float32)
    result[: len(components)] = components
    print(f"Padded vector shape: {result.shape}, dtype: {result.dtype}")

    # Test centroid calculation - pad to same length first
    max_len = max(len(vision_vector), len(sound_vector), len(locomotion_vector))
    padded_units = []
    for vec in [vision_vector, sound_vector, locomotion_vector]:
        padded = np.zeros(max_len, dtype=np.float32)
        padded[: len(vec)] = vec
        padded_units.append(padded)

    centroid = np.mean(padded_units, axis=0)
    print(f"Centroid: {centroid[:7]} (dtype: {centroid.dtype})")  # Show only relevant part


def test_embedding_precision():
    """Test embedding operations with different precisions"""
    print("\n=== Testing Embedding Precision ===")

    # Test FAISS-style float32 operations
    embeddings = np.random.randn(100, 384).astype(np.float32)
    query_embedding = np.random.randn(384).astype(np.float32)

    # Normalize for cosine similarity
    faiss_norm_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    faiss_norm_query = query_embedding / np.linalg.norm(query_embedding)

    # Dot product similarity
    similarities = np.dot(faiss_norm_embeddings, faiss_norm_query)
    print(f"Similarities shape: {similarities.shape}, dtype: {similarities.dtype}")
    print(f"Max similarity: {np.max(similarities):.6f}")

    # Test with mixed precision
    query_float64 = query_embedding.astype(np.float64)
    mixed_similarities = np.dot(embeddings, query_float64)
    print(f"Mixed precision similarities dtype: {mixed_similarities.dtype}")

    # Check for differences
    max_diff = np.max(np.abs(similarities - mixed_similarities))
    print(f"Max difference between float32 and mixed: {max_diff:.10f}")


def test_scoring_functions():
    """Test various scoring functions for NEP 50 impact"""
    print("\n=== Testing Scoring Functions ===")

    # Test 1: Softmax calculations
    scores = np.array([2.3, 1.8, 0.5, 3.1], dtype=np.float32)

    # Manual softmax
    exp_scores = np.exp(scores - np.max(scores))
    softmax_manual = exp_scores / np.sum(exp_scores)

    # NumPy softmax
    softmax_numpy = np.exp(scores) / np.sum(np.exp(scores))

    print(f"Manual softmax: {softmax_manual}")
    print(f"NumPy softmax: {softmax_numpy}")
    print(f"Softmax difference: {np.max(np.abs(softmax_manual - softmax_numpy)):.10f}")

    # Test 2: Normalization operations
    raw_scores = np.array([15, 23, 8, 31, 12], dtype=np.uint8)

    # Min-max normalization
    min_val, max_val = np.min(raw_scores), np.max(raw_scores)
    normalized = (raw_scores - min_val) / (max_val - min_val)

    print(f"Raw scores: {raw_scores} (dtype: {raw_scores.dtype})")
    print(f"Normalized: {normalized} (dtype: {normalized.dtype})")

    # Test 3: Statistical operations with different dtypes
    data_uint8 = np.random.randint(0, 100, 50, dtype=np.uint8)
    data_float32 = data_uint8.astype(np.float32)

    stats_uint8 = {"mean": np.mean(data_uint8), "std": np.std(data_uint8), "var": np.var(data_uint8)}

    stats_float32 = {"mean": np.mean(data_float32), "std": np.std(data_float32), "var": np.var(data_float32)}

    print(f"Uint8 stats: mean={stats_uint8['mean']:.3f}, std={stats_uint8['std']:.3f}")
    print(f"Float32 stats: mean={stats_float32['mean']:.3f}, std={stats_float32['std']:.3f}")

    mean_diff = abs(stats_uint8["mean"] - stats_float32["mean"])
    std_diff = abs(stats_uint8["std"] - stats_float32["std"])
    print(f"Statistics differences: mean={mean_diff:.6f}, std={std_diff:.6f}")


def test_critical_boundary_conditions():
    """Test boundary conditions that could be affected by NEP 50"""
    print("\n=== Testing Critical Boundary Conditions ===")

    # Test 1: Small value operations
    small_values = np.array([1e-10, 1e-8, 1e-6], dtype=np.float32)

    # Multiplication that might underflow
    result = small_values * 1e-5
    print(f"Small value multiplication: {result}")
    print(f"Any underflows: {np.any(result == 0)}")

    # Test 2: Large value operations
    large_values = np.array([1e6, 1e8, 1e10], dtype=np.float32)

    # Division that might cause issues
    result = large_values / 1e3
    print(f"Large value division: {result}")
    print(f"Any overflows: {np.any(np.isinf(result))}")

    # Test 3: Integer boundary conditions
    uint8_near_max = np.array([250, 251, 252, 253, 254, 255], dtype=np.uint8)

    # Addition that wraps around
    wrapped = uint8_near_max + 10
    print(f"Uint8 wrap-around: {wrapped}")

    # Test 4: Precision-dependent comparisons
    a = np.float32(1.0 / 3.0)
    b = 1.0 / 3.0  # Python float

    comparison_result = a == b
    print(f"float32(1/3) == 1/3: {comparison_result}")
    print(f"float32(1/3): {a:.10f}")
    print(f"Python float 1/3: {b:.10f}")

    # Test 5: Cumulative operations
    values = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

    cumsum_float32 = np.cumsum(values)
    cumsum_float64 = np.cumsum(values.astype(np.float64))

    print(f"Float32 cumsum: {cumsum_float32}")
    print(f"Float64 cumsum: {cumsum_float64}")
    print(f"Cumsum difference: {np.max(np.abs(cumsum_float32 - cumsum_float64.astype(np.float32))):.10f}")


def main():
    """Run all GRID-specific NEP 50 tests"""
    print("GRID NEP 50 Impact Assessment")
    print("=" * 50)

    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_pattern_recognition_calculations()
        test_cognitive_unit_operations()
        test_embedding_precision()
        test_scoring_functions()
        test_critical_boundary_conditions()

        if w:
            print(f"\nWARNING: {len(w)} warnings captured:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")

    print("\n" + "=" * 50)
    print("NEP 50 impact assessment completed")


if __name__ == "__main__":
    main()
