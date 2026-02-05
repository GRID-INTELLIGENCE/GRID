
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class MultiDimAnomalyDetector:
    """Isolation Forest-based multi-dimensional anomaly detection."""

    def __init__(self, contamination: float = 0.01, n_estimators: int = 100):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> "MultiDimAnomalyDetector":
        """Fit the anomaly detector on training data."""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """Predict anomalies with confidence scores."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        X_scaled = self.scaler.transform(X)
        anomaly_scores = -self.model.score_samples(X_scaled)
        predictions = self.model.predict(X_scaled)

        return {
            "is_anomaly": predictions == -1,
            "anomaly_score": anomaly_scores,
            "confidence": 1 / (1 + np.exp(-anomaly_scores)),  # Sigmoid to [0,1]
        }
