#!/usr/bin/env python3
"""
Test NumPy 2.4.3 compatibility with GRID-specific numerical operations
Tests for embeddings, ranking features, and ML models
"""

import warnings

import numpy as np


def test_embedding_operations():
    """Test embedding operations with NEP 50"""
    print("=== Testing Embedding Operations ===")

    # Simulate sentence-transformers output (typically float32)
    embedding_dim = 384
    test_embedding = np.random.randn(embedding_dim).astype(np.float32)

    print(f"Embedding dtype: {test_embedding.dtype}")
    print(f"Embedding shape: {test_embedding.shape}")
    print(f"Embedding norm: {np.linalg.norm(test_embedding):.6f}")

    # Test similarity calculations (common in RAG)
    query_embedding = np.random.randn(embedding_dim).astype(np.float32)

    # Dot product similarity
    similarity = np.dot(query_embedding, test_embedding)
    print(f"Dot product similarity: {similarity:.6f} (dtype: {similarity.dtype})")

    # Cosine similarity
    cos_sim = similarity / (np.linalg.norm(query_embedding) * np.linalg.norm(test_embedding))
    print(f"Cosine similarity: {cos_sim:.6f} (dtype: {cos_sim.dtype})")

    # Test batch operations
    batch_embeddings = np.random.randn(10, embedding_dim).astype(np.float32)
    batch_similarities = np.dot(batch_embeddings, query_embedding)
    print(f"Batch similarities shape: {batch_similarities.shape}, dtype: {batch_similarities.dtype}")


def test_ranking_features():
    """Test ranking feature extraction with NEP 50"""
    print("\n=== Testing Ranking Features ===")

    # Simulate feature extraction from search/ranking/features.py
    _feature_names = [
        "bm25_score",
        "vector_similarity",
        "rrf_rank",
        "field_match_count",
        "query_doc_len_ratio",
        "field_weight_sum",
        "freshness",
        "popularity",
    ]

    # Create test features with mixed types
    bm25_score = 2.5  # float
    vector_sim = 0.8  # float
    rrf_rank = 5  # int
    field_match = 3  # int
    len_ratio = 0.25  # float
    weight_sum = 1.2  # float
    freshness = 0.9  # float
    popularity = 100  # int

    features = np.array(
        [
            bm25_score,
            vector_sim,
            float(rrf_rank),
            float(field_match),
            len_ratio,
            weight_sum,
            freshness,
            float(popularity),
        ],
        dtype=np.float32,
    )

    print(f"Feature vector dtype: {features.dtype}")
    print(f"Feature vector shape: {features.shape}")
    print(f"Feature values: {features}")

    # Test batch feature matrix
    batch_features = np.random.randn(10, 8).astype(np.float32)
    print(f"Batch features shape: {batch_features.shape}, dtype: {batch_features.dtype}")

    # Test model prediction (simulated)
    predicted_scores = batch_features @ np.random.randn(8).astype(np.float32)
    print(f"Predicted scores shape: {predicted_scores.shape}, dtype: {predicted_scores.dtype}")


def test_ml_model_compatibility():
    """Test ML model training and prediction with NEP 50"""
    print("\n=== Testing ML Model Compatibility ===")

    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import train_test_split

        # Generate training data with different dtypes
        n_samples = 1000
        n_features = 8

        # Features with mixed precision (simulates real data)
        X_uint8 = np.random.randint(0, 100, (n_samples, 2), dtype=np.uint8)  # count features
        X_float32 = np.random.randn(n_samples, n_features - 2).astype(np.float32)  # continuous features
        X = np.hstack([X_uint8, X_float32])

        # Target variable
        y = np.random.randn(n_samples).astype(np.float32)

        print(f"Training features shape: {X.shape}, dtype: {X.dtype}")
        print(f"Target shape: {y.shape}, dtype: {y.dtype}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)

        # Predict
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)

        print(f"Train predictions shape: {train_pred.shape}, dtype: {train_pred.dtype}")
        print(f"Test predictions shape: {test_pred.shape}, dtype: {test_pred.dtype}")

        # Calculate metrics
        train_mse = float(np.mean((train_pred - y_train) ** 2))
        test_mse = float(np.mean((test_pred - y_test) ** 2))

        print(f"Train MSE: {train_mse:.6f}")
        print(f"Test MSE: {test_mse:.6f}")

        print("SUCCESS: sklearn model training completed")

    except ImportError:
        print("WARNING: sklearn not available")
    except Exception as e:
        print(f"ERROR: sklearn compatibility issue: {e}")


def test_precision_critical_operations():
    """Test operations where precision changes could impact results"""
    print("\n=== Testing Precision-Critical Operations ===")

    # Test 1: Similarity calculations with different precisions
    vec1_float32 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    vec2_float32 = np.array([4.0, 5.0, 6.0], dtype=np.float32)

    # Dot product with float32
    dot_float32 = np.dot(vec1_float32, vec2_float32)
    print(f"Float32 dot product: {dot_float32:.6f} (dtype: {dot_float32.dtype})")

    # Same operation with mixed precision
    dot_mixed = np.dot(vec1_float32, np.array([4.0, 5.0, 6.0], dtype=np.float64))
    print(f"Mixed precision dot product: {dot_mixed:.6f} (dtype: {dot_mixed.dtype})")

    # Test 2: Normalization operations
    scores = np.array([0.1, 0.8, 0.3, 0.9, 0.2], dtype=np.float32)

    # Softmax calculation
    exp_scores = np.exp(scores - np.max(scores))
    softmax = exp_scores / np.sum(exp_scores)
    print(f"Softmax result: {softmax}")
    print(f"Softmax sum: {np.sum(softmax):.6f} (should be 1.0)")

    # Test 3: Cumulative operations
    cumsum = np.cumsum(scores)
    print(f"Cumulative sum: {cumsum} (dtype: {cumsum.dtype})")

    # Test 4: Statistical operations
    mean_val = np.mean(scores)
    std_val = np.std(scores)
    print(f"Mean: {mean_val:.6f}, Std: {std_val:.6f}")


def test_overflow_scenarios():
    """Test overflow scenarios that could be affected by NEP 50"""
    print("\n=== Testing Overflow Scenarios ===")

    # Test 1: Integer overflow in uint8
    small_arr = np.array([200, 250, 255], dtype=np.uint8)

    try:
        result = small_arr + 10
        print(f"uint8 + 10: {result} (wrapped around)")
    except OverflowError as e:
        print(f"uint8 + 10 overflow caught: {e}")

    # Test 2: Float overflow
    large_float32 = np.array([1e20, 1e30, 1e38], dtype=np.float32)

    try:
        result = large_float32 * 1e10
        print(f"float32 * 1e10: {result}")
        if np.any(np.isinf(result)):
            print("WARNING: Infinity values detected")
    except OverflowError as e:
        print(f"float32 overflow caught: {e}")

    # Test 3: Critical - document ranking scores
    # Simulate BM25 scores that could overflow
    bm25_scores = np.array([15.2, 23.8, 31.4, 8.9], dtype=np.float32)
    boost_factor = 2.0

    boosted_scores = bm25_scores * boost_factor
    print(f"BM25 boost: {boosted_scores} (dtype: {boosted_scores.dtype})")

    # Test 4: Aggregation operations
    doc_scores = np.random.randint(0, 1000, 100, dtype=np.uint16)
    total_score = np.sum(doc_scores)
    print(f"Total score: {total_score} (dtype: {total_score.dtype})")


def main():
    """Run all GRID-specific compatibility tests"""
    print("GRID NumPy 2.4.3 Compatibility Test Suite")
    print("=" * 50)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_embedding_operations()
        test_ranking_features()
        test_ml_model_compatibility()
        test_precision_critical_operations()
        test_overflow_scenarios()

        if w:
            print(f"\nWARNING: {len(w)} warnings captured:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")

    print("\n" + "=" * 50)
    print("GRID compatibility test completed")


if __name__ == "__main__":
    main()
