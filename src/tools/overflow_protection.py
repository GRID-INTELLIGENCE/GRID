"""
Overflow protection patches for critical GRID calculations
Adds safety checks to prevent NEP 50 related issues
"""

import warnings
from typing import Any

import numpy as np

# Import safety utilities
try:
    from .numpy_safety import (
        DEFAULT_EMBEDDING_DTYPE,
        DEFAULT_FEATURE_DTYPE,
    )
except ImportError:
    # Fallback for standalone usage
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))
    from numpy_safety import (
        DEFAULT_EMBEDDING_DTYPE,
        DEFAULT_FEATURE_DTYPE,
    )


def safe_feature_extractor_extract(original_extract_func):
    """
    Wrapper for FeatureExtractor.extract() with overflow protection.

    This decorator adds safety checks to the feature extraction process
    to prevent overflow and precision issues.
    """

    def wrapper(self, query_text, doc, candidate, bm25_scores, vector_scores, rrf_rank):
        try:
            # Call original function
            result = original_extract_func(self, query_text, doc, candidate, bm25_scores, vector_scores, rrf_rank)

            # Validate the result
            if isinstance(result, np.ndarray):
                # Check for invalid values
                if np.any(~np.isfinite(result)):
                    warnings.warn(f"Invalid values in features for doc {doc.id}", RuntimeWarning, stacklevel=2)
                    # Replace invalid values
                    result = np.where(np.isfinite(result), result, 0.0)

                # Check for extreme values
                if np.any(np.abs(result) > 1e6):
                    warnings.warn(f"Extreme feature values for doc {doc.id}", RuntimeWarning, stacklevel=2)
                    # Clamp extreme values
                    result = np.clip(result, -1e6, 1e6)

            return result

        except Exception as e:
            warnings.warn(f"Feature extraction failed for doc {doc.id}: {e}", RuntimeWarning, stacklevel=2)
            # Return safe default features
            return np.zeros(8, dtype=DEFAULT_FEATURE_DTYPE)

    return wrapper


def safe_vector_store_query(original_query_func):
    """
    Wrapper for vector store query with similarity safety.
    """

    def wrapper(self, query_embedding, n_results=5, where=None, include=None):
        try:
            # Validate query embedding
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)

            # Check for invalid values
            if np.any(~np.isfinite(query_embedding)):
                warnings.warn("Query embedding contains invalid values", RuntimeWarning, stacklevel=2)
                # Replace with zeros
                query_embedding = np.zeros_like(query_embedding)

            # Normalize to prevent overflow
            norm = np.linalg.norm(query_embedding)
            if norm > 0:
                query_embedding = query_embedding / norm

            # Call original function
            result = original_query_func(self, query_embedding, n_results, where, include)

            # Validate distances
            if "distances" in result and result["distances"]:
                distances = np.array(result["distances"])
                if np.any(~np.isfinite(distances)):
                    warnings.warn("Invalid distances in query results", RuntimeWarning, stacklevel=2)
                    # Replace invalid distances
                    distances = np.where(np.isfinite(distances), distances, 1.0)
                    result["distances"] = distances.tolist()

            return result

        except Exception as e:
            warnings.warn(f"Vector store query failed: {e}", RuntimeWarning, stacklevel=2)
            # Return empty result
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    return wrapper


def safe_ltr_model_train(original_train_func):
    """
    Wrapper for LTRModel.train() with data validation.
    """

    def wrapper(self, features, labels):
        try:
            # Validate features
            if not isinstance(features, np.ndarray):
                features = np.array(features)

            if not isinstance(labels, np.ndarray):
                labels = np.array(labels)

            # Check shapes
            if features.shape[0] != labels.shape[0]:
                raise ValueError(f"Features and labels shape mismatch: {features.shape[0]} vs {labels.shape[0]}")

            # Check for invalid values
            if np.any(~np.isfinite(features)):
                warnings.warn("Features contain invalid values", RuntimeWarning, stacklevel=2)
                features = np.where(np.isfinite(features), features, 0.0)

            if np.any(~np.isfinite(labels)):
                warnings.warn("Labels contain invalid values", RuntimeWarning, stacklevel=2)
                labels = np.where(np.isfinite(labels), labels, 0.0)

            # Check for extreme values
            if np.any(np.abs(features) > 1e6):
                warnings.warn("Features contain extreme values", RuntimeWarning, stacklevel=2)
                features = np.clip(features, -1e6, 1e6)

            # Call original function
            return original_train_func(self, features, labels)

        except Exception as e:
            warnings.warn(f"LTR model training failed: {e}", RuntimeWarning, stacklevel=2)
            # Return error metrics
            return {"train_mse": float("inf"), "n_samples": 0, "error": str(e)}

    return wrapper


def safe_cognitive_unit_to_vector(original_to_vector_func):
    """
    Wrapper for CognitiveUnit.to_vector() with precision safety.
    """

    def wrapper(self, vector_size=32):
        try:
            # Call original function
            result = original_to_vector_func(self, vector_size)

            # Validate result
            if isinstance(result, np.ndarray):
                # Check for invalid values
                if np.any(~np.isfinite(result)):
                    warnings.warn(f"Cognitive unit {self.source_id} has invalid values", RuntimeWarning, stacklevel=2)
                    result = np.where(np.isfinite(result), result, 0.0)

                # Check range (cognitive components should be 0-1)
                if np.any(result < 0) or np.any(result > 1):
                    warnings.warn(
                        f"Cognitive unit {self.source_id} has out-of-range values", RuntimeWarning, stacklevel=2
                    )
                    # Clip to valid range
                    result = np.clip(result, 0.0, 1.0)

            return result

        except Exception as e:
            warnings.warn(f"Cognitive unit vectorization failed: {e}", RuntimeWarning, stacklevel=2)
            # Return zero vector
            return np.zeros(vector_size, dtype=DEFAULT_FEATURE_DTYPE)

    return wrapper


def safe_embedding_provider_embed(original_embed_func):
    """
    Wrapper for embedding providers with output validation.
    """

    def wrapper(self, text):
        try:
            # Call original function
            result = original_embed_func(self, text)

            # Validate embedding
            if isinstance(result, np.ndarray):
                # Check for invalid values
                if np.any(~np.isfinite(result)):
                    warnings.warn("Embedding for text contains invalid values", RuntimeWarning, stacklevel=2)
                    result = np.where(np.isfinite(result), result, 0.0)

                # Normalize to prevent overflow in similarity calculations
                norm = np.linalg.norm(result)
                if norm > 0:
                    result = result / norm

            return result

        except Exception as e:
            warnings.warn(f"Embedding generation failed: {e}", RuntimeWarning, stacklevel=2)
            # Return zero embedding
            return np.zeros(384, dtype=DEFAULT_EMBEDDING_DTYPE)  # Common embedding size

    return wrapper


def safe_pattern_recognition_calculations():
    """
    Safety utilities for pattern recognition calculations.
    """

    def safe_variance_calculation(values):
        """Safe variance calculation with overflow protection."""
        try:
            values = np.array(values, dtype=np.float64)  # Use higher precision for calculation

            if len(values) == 0:
                return 0.0

            mean_val = np.mean(values)
            variance = np.mean((values - mean_val) ** 2)

            # Check for overflow
            if not np.isfinite(variance):
                warnings.warn("Variance calculation overflow", RuntimeWarning, stacklevel=2)
                return 0.0

            return float(variance)

        except Exception as e:
            warnings.warn(f"Variance calculation failed: {e}", RuntimeWarning, stacklevel=2)
            return 0.0

    def safe_load_score_calculation(cognitive_load, optimal_load=5.0):
        """Safe load score calculation with bounds checking."""
        try:
            cognitive_load = float(cognitive_load)
            optimal_load = float(optimal_load)

            # Clamp to reasonable range
            cognitive_load = np.clip(cognitive_load, 0.0, 10.0)

            load_score = 1.0 - abs(cognitive_load - optimal_load) / optimal_load
            return float(np.clip(load_score, 0.0, 1.0))

        except Exception as e:
            warnings.warn(f"Load score calculation failed: {e}", RuntimeWarning, stacklevel=2)
            return 0.5  # Neutral score

    def safe_momentum_score_calculation(base_momentum, engagement, mode_factor=0.2):
        """Safe momentum score calculation."""
        try:
            base_momentum = float(base_momentum)
            engagement = float(np.clip(engagement, 0.0, 1.0))
            mode_factor = float(mode_factor)

            momentum_score = base_momentum + (engagement * mode_factor)
            return float(np.clip(momentum_score, 0.0, 1.0))

        except Exception as e:
            warnings.warn(f"Momentum score calculation failed: {e}", RuntimeWarning, stacklevel=2)
            return 0.5  # Neutral score

    return {
        "safe_variance": safe_variance_calculation,
        "safe_load_score": safe_load_score_calculation,
        "safe_momentum_score": safe_momentum_score_calculation,
    }


def safe_api_response_validation(response_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate API response data for numerical safety.

    Args:
        response_data: Dictionary containing API response data

    Returns:
        Validated response data
    """
    validated_data = response_data.copy()

    def validate_value(value):
        """Recursively validate numeric values."""
        if isinstance(value, dict):
            return {k: validate_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [validate_value(v) for v in value]
        elif isinstance(value, (int, float, np.number)):
            # Check for invalid values
            if not np.isfinite(value):
                warnings.warn(f"Invalid numeric value in API response: {value}", RuntimeWarning, stacklevel=2)
                return 0.0

            # Check for extreme values
            if abs(value) > 1e6:
                warnings.warn(f"Extreme numeric value in API response: {value}", RuntimeWarning, stacklevel=2)
                return np.clip(value, -1e6, 1e6)

            return float(value)
        else:
            return value

    # Validate the entire response
    validated_data = validate_value(validated_data)

    return validated_data


# Patch application functions
def apply_safety_patches():
    """
    Apply safety patches to GRID modules.

    This function should be called during module initialization to
    wrap critical functions with safety checks.
    """
    try:
        # Import modules that need patching
        from cognitive.cognitive_unit import CognitiveUnit
        from search.ranking.features import FeatureExtractor
        from search.ranking.ltr_model import LTRModel
        from tools.rag.vector_store.in_memory_dense import InMemoryDenseVectorStore

        # Apply patches
        FeatureExtractor.extract = safe_feature_extractor_extract(FeatureExtractor.extract)
        InMemoryDenseVectorStore.query = safe_vector_store_query(InMemoryDenseVectorStore.query)
        LTRModel.train = safe_ltr_model_train(LTRModel.train)
        CognitiveUnit.to_vector = safe_cognitive_unit_to_vector(CognitiveUnit.to_vector)

        print("Safety patches applied successfully")

    except ImportError as e:
        print(f"Warning: Could not apply safety patches: {e}")
    except Exception as e:
        print(f"Error applying safety patches: {e}")


# Utility functions for common operations
def safe_divide(numerator, denominator, default=0.0):
    """Safe division with zero-division protection."""
    try:
        if denominator == 0:
            return default
        result = numerator / denominator
        return float(result) if np.isfinite(result) else default
    except Exception:
        return default


def safe_log(value, default=0.0):
    """Safe logarithm with domain protection."""
    try:
        if value <= 0:
            return default
        result = np.log(value)
        return float(result) if np.isfinite(result) else default
    except Exception:
        return default


def safe_exp(value, max_exp=700.0):
    """Safe exponential with overflow protection."""
    try:
        if value > max_exp:  # exp(700) is close to float64 max
            return float("inf")
        result = np.exp(value)
        return float(result) if np.isfinite(result) else float("inf")
    except Exception:
        return float("inf")


# Configuration constants
SAFETY_CONFIG = {
    "max_feature_value": 1e6,
    "max_similarity": 1.0,
    "min_similarity": -1.0,
    "default_embedding_size": 384,
    "default_feature_size": 8,
    "overflow_threshold": 1e30,
    "underflow_threshold": 1e-30,
}
