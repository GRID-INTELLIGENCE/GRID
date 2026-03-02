"""Learning-to-Rank model using scikit-learn GradientBoosting."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingRegressor

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    GradientBoostingRegressor = Any  # type: ignore

try:
    import joblib

    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class LTRModel:
    """Pointwise learning-to-rank model.

    Uses GradientBoostingRegressor to predict relevance scores from
    the 8-dimensional feature vectors produced by FeatureExtractor.

    Upgradeable to pairwise LambdaMART via lightgbm.LGBMRanker when
    sufficient labelled training data is available.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 4,
    ) -> None:
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for LTRModel")

        self._model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
        )
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def train(self, features: np.ndarray, labels: np.ndarray) -> dict[str, float]:
        """Fit the model on (features, relevance_labels).

        Args:
            features: (n_samples, n_features) matrix
            labels: (n_samples,) relevance scores (higher = more relevant)

        Returns:
            Training metrics dict.
        """
        if features.shape[0] == 0:
            raise ValueError("Cannot train on empty feature set")

        self._model.fit(features, labels)
        self._is_fitted = True

        train_pred = self._model.predict(features)
        mse = float(np.mean((train_pred - labels) ** 2))
        return {"train_mse": mse, "n_samples": features.shape[0]}

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict relevance scores for the given feature matrix."""
        if not self._is_fitted:
            raise RuntimeError("LTR model has not been trained or loaded")
        return self._model.predict(features)

    def save(self, path: str | Path) -> None:
        if not HAS_JOBLIB:
            raise ImportError("joblib is required for model persistence")
        if not self._is_fitted:
            raise RuntimeError("Cannot save an unfitted model")
        joblib.dump(self._model, str(path))
        logger.info("LTR model saved to %s", path)

    def load(self, path: str | Path) -> None:
        if not HAS_JOBLIB:
            raise ImportError("joblib is required for model persistence")
        self._model = joblib.load(str(path))
        self._is_fitted = True
        logger.info("LTR model loaded from %s", path)

    def feature_importances(self) -> dict[str, float]:
        if not self._is_fitted:
            return {}
        from .features import FEATURE_NAMES

        importances = self._model.feature_importances_
        return dict(zip(FEATURE_NAMES, [float(v) for v in importances], strict=False))
