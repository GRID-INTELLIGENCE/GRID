"""
NumPy dtype safety utilities for GRID 2.4.3 compatibility
Provides safe numerical operations with explicit dtype handling
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np


class DTypeError(Exception):
    """Raised when dtype operations could cause precision loss or overflow."""

    pass


def safe_float32_conversion(
    value: np.ndarray | float | int | list, name: str = "value", allow_overflow: bool = False
) -> np.ndarray:
    """
    Safely convert to float32 with overflow checking.

    Args:
        value: Input value, array, or list
        name: Variable name for error messages
        allow_overflow: Whether to allow overflow (with warning)

    Returns:
        float32 array

    Raises:
        DTypeError: If conversion would cause overflow and not allowed
    """
    if isinstance(value, (int, float)):
        value = np.array([value])
    elif isinstance(value, list):
        value = np.array(value)

    # Check for existing infinities or NaNs
    if np.any(~np.isfinite(value)) and not allow_overflow:
        raise DTypeError(f"{name} contains NaN or infinite values")

    # Convert to float32
    result = value.astype(np.float32)

    # Check for overflow during conversion
    if not allow_overflow and np.any(np.isinf(result)) and not np.any(np.isinf(value)):
        raise DTypeError(f"{name} overflow during float32 conversion")

    # Warn about precision loss
    if np.any(value != result.astype(value.dtype)) and not allow_overflow:
        warnings.warn(f"Precision loss in {name} during float32 conversion", RuntimeWarning, stacklevel=2)

    return result


def safe_uint_conversion(
    value: np.ndarray | int | list, target_dtype: type = np.uint32, name: str = "value", allow_overflow: bool = False
) -> np.ndarray:
    """
    Safely convert to unsigned integer with overflow checking.

    Args:
        value: Input value, array, or list
        target_dtype: Target unsigned integer dtype
        name: Variable name for error messages
        allow_overflow: Whether to allow overflow (with warning)

    Returns:
        Unsigned integer array

    Raises:
        DTypeError: If conversion would cause overflow and not allowed
    """
    if isinstance(value, int):
        value = np.array([value])
    elif isinstance(value, list):
        value = np.array(value)

    # Check if values are negative
    if np.any(value < 0):
        raise DTypeError(f"{name} contains negative values, cannot convert to {target_dtype.__name__}")

    # Get max value for target dtype
    max_val = np.iinfo(target_dtype).max

    # Check for overflow
    if np.any(value > max_val):
        if allow_overflow:
            warnings.warn(f"{name} overflow in {target_dtype.__name__} conversion", RuntimeWarning, stacklevel=2)
        else:
            raise DTypeError(f"{name} exceeds {target_dtype.__name__} maximum ({max_val})")

    return value.astype(target_dtype)


def safe_similarity_calculation(
    vec1: np.ndarray, vec2: np.ndarray, dtype: type = np.float32, normalize: bool = True
) -> float:
    """
    Safely calculate cosine similarity with overflow protection.

    Args:
        vec1: First vector
        vec2: Second vector
        dtype: Precision for calculation
        normalize: Whether to normalize vectors first

    Returns:
        Cosine similarity score
    """
    # Ensure same dtype
    vec1 = vec1.astype(dtype)
    vec2 = vec2.astype(dtype)

    if normalize:
        # Safe normalization
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        vec1 = vec1 / norm1
        vec2 = vec2 / norm2

    # Calculate similarity
    similarity = np.dot(vec1, vec2)

    # Clamp to valid range
    similarity = np.clip(similarity, -1.0, 1.0)

    return float(similarity)


def safe_batch_similarity(
    embeddings: np.ndarray, query: np.ndarray, dtype: type = np.float32, max_batch_size: int = 10000
) -> np.ndarray:
    """
    Safely calculate batch similarities with memory management.

    Args:
        embeddings: Matrix of embeddings (n, d)
        query: Query vector (d,)
        dtype: Precision for calculation
        max_batch_size: Maximum batch size to prevent memory issues

    Returns:
        Array of similarities
    """
    n_embeddings = embeddings.shape[0]

    if n_embeddings > max_batch_size:
        # Process in batches
        similarities = []
        for i in range(0, n_embeddings, max_batch_size):
            batch = embeddings[i : i + max_batch_size]
            batch_sim = safe_batch_similarity(batch, query, dtype, max_batch_size)
            similarities.append(batch_sim)
        return np.concatenate(similarities)

    # Safe batch calculation
    embeddings = embeddings.astype(dtype)
    query = query.astype(dtype)

    # Normalize
    embeddings_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
    query_norm = query / (np.linalg.norm(query) + 1e-8)

    # Calculate similarities
    similarities = np.dot(embeddings_norm, query_norm)

    # Clamp to valid range
    similarities = np.clip(similarities, -1.0, 1.0)

    return similarities


def safe_feature_extraction(
    features: list[float | int], dtype: type = np.float32, feature_names: list[str] | None = None
) -> np.ndarray:
    """
    Safely extract features with dtype validation.

    Args:
        features: List of feature values
        dtype: Target dtype
        feature_names: Optional names for error reporting

    Returns:
        Feature vector
    """
    try:
        features_array = np.array(features, dtype=dtype)

        # Check for invalid values
        if dtype == np.float32 or dtype == np.float64:
            if np.any(~np.isfinite(features_array)):
                if feature_names:
                    invalid_indices = np.where(~np.isfinite(features_array))[0]
                    invalid_names = [feature_names[i] for i in invalid_indices]
                    raise DTypeError(f"Invalid values in features: {invalid_names}")
                else:
                    raise DTypeError("Features contain NaN or infinite values")

        return features_array

    except (ValueError, OverflowError) as e:
        raise DTypeError(f"Feature extraction failed: {e}")


def safe_normalization(
    values: np.ndarray, method: str = "minmax", dtype: type = np.float32, epsilon: float = 1e-8
) -> np.ndarray:
    """
    Safely normalize values with overflow protection.

    Args:
        values: Input values
        method: Normalization method ('minmax', 'zscore', 'l2')
        dtype: Output dtype
        epsilon: Small value to prevent division by zero

    Returns:
        Normalized values
    """
    values = values.astype(dtype)

    if method == "minmax":
        min_val = np.min(values)
        max_val = np.max(values)

        if max_val - min_val < epsilon:
            return np.zeros_like(values)

        return (values - min_val) / (max_val - min_val + epsilon)

    elif method == "zscore":
        mean_val = np.mean(values)
        std_val = np.std(values)

        if std_val < epsilon:
            return np.zeros_like(values)

        return (values - mean_val) / (std_val + epsilon)

    elif method == "l2":
        norm = np.linalg.norm(values)

        if norm < epsilon:
            return np.zeros_like(values)

        return values / (norm + epsilon)

    else:
        raise ValueError(f"Unknown normalization method: {method}")


def safe_softmax(
    scores: np.ndarray, dtype: type = np.float32, temperature: float = 1.0, epsilon: float = 1e-8
) -> np.ndarray:
    """
    Safely calculate softmax with numerical stability.

    Args:
        scores: Input scores
        dtype: Output dtype
        temperature: Softmax temperature
        epsilon: Small value for numerical stability

    Returns:
        Softmax probabilities
    """
    scores = scores.astype(dtype) / temperature

    # Numerical stability: subtract max
    scores = scores - np.max(scores)

    # Calculate softmax
    exp_scores = np.exp(scores)
    sum_exp = np.sum(exp_scores)

    if sum_exp < epsilon:
        # Return uniform distribution
        return np.ones_like(scores) / len(scores)

    return exp_scores / (sum_exp + epsilon)


def validate_numerical_input(
    value: Any,
    name: str,
    expected_dtype: type | None = None,
    min_val: float | None = None,
    max_val: float | None = None,
    allow_nan: bool = False,
    allow_inf: bool = False,
) -> np.ndarray:
    """
    Comprehensive input validation for numerical operations.

    Args:
        value: Input value
        name: Variable name for errors
        expected_dtype: Expected numpy dtype
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_nan: Whether to allow NaN values
        allow_inf: Whether to allow infinite values

    Returns:
        Validated numpy array
    """
    try:
        result = np.array(value)

        # Check dtype
        if expected_dtype is not None:
            result = result.astype(expected_dtype)

        # Check for invalid values
        if not allow_nan and np.any(np.isnan(result)):
            raise DTypeError(f"{name} contains NaN values")

        if not allow_inf and np.any(np.isinf(result)):
            raise DTypeError(f"{name} contains infinite values")

        # Check range
        if min_val is not None and np.any(result < min_val):
            raise DTypeError(f"{name} contains values below minimum ({min_val})")

        if max_val is not None and np.any(result > max_val):
            raise DTypeError(f"{name} contains values above maximum ({max_val})")

        return result

    except Exception as e:
        raise DTypeError(f"Input validation failed for {name}: {e}")


# Convenience constants for common operations
DEFAULT_EMBEDDING_DTYPE = np.float32
DEFAULT_FEATURE_DTYPE = np.float32
DEFAULT_COUNT_DTYPE = np.uint32
DEFAULT_SCORE_DTYPE = np.float32

# Common dtype combinations
EMBEDDING_CONFIG = {"dtype": DEFAULT_EMBEDDING_DTYPE, "allow_overflow": False, "normalize": True}

FEATURE_CONFIG = {"dtype": DEFAULT_FEATURE_DTYPE, "validate_range": True, "min_val": -1e6, "max_val": 1e6}

COUNT_CONFIG = {"dtype": DEFAULT_COUNT_DTYPE, "allow_overflow": False, "max_value": np.iinfo(DEFAULT_COUNT_DTYPE).max}
