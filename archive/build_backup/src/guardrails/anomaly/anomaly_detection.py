"""
Anomaly Detection Engine for Guardrails

Detects anomalous module behavior using statistical and machine learning methods
inspired by financial market anomaly detection and time series analysis.
"""

import math
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import defaultdict


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    
    # Statistical anomalies
    STATISTICAL_OUTLIER = "statistical_outlier"      # Z-score based outlier
    SEASONAL_ANOMALY = "seasonal_anomaly"           # Deviation from seasonal pattern
    TREND_BREAK = "trend_break"                     # Sudden trend change
    
    # Velocity anomalies (inspired by market volatility)
    VELOCITY_SPIKE = "velocity_spike"               # Sudden change in rate
    VOLATILITY_CLUSTER = "volatility_cluster"       # Period of high variance
    MOMENTUM_SHIFT = "momentum_shift"               # Change in momentum direction
    
    # Behavioral anomalies
    PATTERN_BREAK = "pattern_break"                 # Break from established pattern
    BEHAVIOR_DRIFT = "behavior_drift"               # Gradual behavior change
    REGIME_CHANGE = "regime_change"                 # Fundamental shift in behavior
    
    # Cross-sectional anomalies (inspired by peer analysis)
    PEER_DEVIATION = "peer_deviation"               # Deviation from peer group
    CLUSTER_ANOMALY = "cluster_anomaly"               # Anomaly within cluster
    CATEGORY_OUTLIER = "category_outlier"             # Outlier in category
    
    # Structural anomalies
    ARCHITECTURE_DRIFT = "architecture_drift"         # Architectural pattern change
    DEPENDENCY_SHIFT = "dependency_shift"             # Major dependency change
    INTERFACE_BREAK = "interface_break"               # Breaking interface change


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    
    anomaly_type: AnomalyType
    module_name: str
    timestamp: datetime
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 to 1.0
    
    # Detection details
    metric_name: str
    expected_value: float
    actual_value: float
    deviation: float  # Standard deviations or percentage
    
    # Context
    historical_context: Dict[str, Any]
    peer_comparison: Optional[Dict[str, float]]
    
    # Recommendation
    suggested_action: str
    auto_remediation_available: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'anomaly_type': self.anomaly_type.value,
            'module_name': self.module_name,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'confidence': self.confidence,
            'metric_name': self.metric_name,
            'expected_value': self.expected_value,
            'actual_value': self.actual_value,
            'deviation': self.deviation,
            'historical_context': self.historical_context,
            'peer_comparison': self.peer_comparison,
            'suggested_action': self.suggested_action,
            'auto_remediation_available': self.auto_remediation_available
        }


class StatisticalDetector:
    """Statistical anomaly detection methods."""
    
    @staticmethod
    def z_score_detection(
        values: List[float],
        threshold: float = 2.5
    ) -> List[Tuple[int, float, float]]:
        """
        Detect outliers using Z-score method.
        
        Args:
            values: List of metric values
            threshold: Z-score threshold (typically 2.5-3.0)
            
        Returns:
            List of (index, value, z_score) for anomalies
        """
        if len(values) < 3:
            return []
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return []
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold:
                anomalies.append((i, value, z_score))
        
        return anomalies
    
    @staticmethod
    def moving_average_detection(
        values: List[float],
        window: int = 7,
        threshold_std: float = 2.0
    ) -> List[Tuple[int, float, float]]:
        """
        Detect anomalies using moving average.
        
        Args:
            values: List of metric values
            window: Moving average window size
            threshold_std: Standard deviation threshold
            
        Returns:
            List of (index, value, deviation) for anomalies
        """
        if len(values) < window + 1:
            return []
        
        anomalies = []
        
        for i in range(window, len(values)):
            window_values = values[i-window:i]
            ma = statistics.mean(window_values)
            std = statistics.stdev(window_values) if len(window_values) > 1 else 0
            
            if std > 0:
                deviation = abs(values[i] - ma) / std
                if deviation > threshold_std:
                    anomalies.append((i, values[i], deviation))
        
        return anomalies
    
    @staticmethod
    def interquartile_range_detection(
        values: List[float],
        k: float = 1.5
    ) -> List[Tuple[int, float, str]]:
        """
        Detect outliers using IQR method (robust to extreme values).
        
        Args:
            values: List of metric values
            k: IQR multiplier (1.5 for outliers, 3.0 for extreme outliers)
            
        Returns:
            List of (index, value, type) where type is 'outlier' or 'extreme'
        """
        if len(values) < 4:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        
        iqr = q3 - q1
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        extreme_lower = q1 - 3 * iqr
        extreme_upper = q3 + 3 * iqr
        
        anomalies = []
        for i, value in enumerate(values):
            if value < extreme_lower or value > extreme_upper:
                anomalies.append((i, value, 'extreme'))
            elif value < lower_bound or value > upper_bound:
                anomalies.append((i, value, 'outlier'))
        
        return anomalies


class VelocityDetector:
    """Detect velocity and momentum based anomalies."""
    
    @staticmethod
    def detect_velocity_spike(
        values: List[float],
        timestamps: List[datetime],
        spike_threshold: float = 3.0
    ) -> List[Tuple[int, float, float]]:
        """
        Detect sudden velocity spikes (rate of change anomalies).
        
        Inspired by: Stock market volatility spikes, music streaming surges
        """
        if len(values) < 3:
            return []
        
        # Calculate velocities (rate of change)
        velocities = []
        for i in range(1, len(values)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            if time_diff > 0:
                velocity = (values[i] - values[i-1]) / time_diff
                velocities.append((i, velocity))
        
        if len(velocities) < 2:
            return []
        
        # Calculate velocity statistics
        velocity_values = [v[1] for v in velocities]
        mean_velocity = statistics.mean(velocity_values)
        std_velocity = statistics.stdev(velocity_values) if len(velocity_values) > 1 else 1
        
        if std_velocity == 0:
            std_velocity = 1
        
        # Detect spikes
        spikes = []
        for idx, velocity in velocities:
            z_score = abs((velocity - mean_velocity) / std_velocity)
            if z_score > spike_threshold:
                spikes.append((idx, velocity, z_score))
        
        return spikes
    
    @staticmethod
    def detect_momentum_shift(
        values: List[float],
        window: int = 5
    ) -> Optional[Tuple[int, str, float]]:
        """
        Detect momentum direction changes.
        
        Returns: (index, direction, strength) or None
        """
        if len(values) < window * 2:
            return None
        
        # Calculate momentum in recent window vs previous window
        recent = values[-window:]
        previous = values[-window*2:-window]
        
        recent_trend = (recent[-1] - recent[0]) / len(recent)
        previous_trend = (previous[-1] - previous[0]) / len(previous)
        
        # Detect significant direction change
        if recent_trend * previous_trend < 0:  # Opposite directions
            strength = abs(recent_trend - previous_trend)
            direction = "up" if recent_trend > 0 else "down"
            return (len(values) - 1, direction, strength)
        
        return None
    
    @staticmethod
    def detect_volatility_clustering(
        values: List[float],
        window: int = 10,
        threshold: float = 2.0
    ) -> List[Tuple[int, float]]:
        """
        Detect periods of high volatility (clustering).
        
        Inspired by: Financial market volatility clustering (GARCH models)
        """
        if len(values) < window + 1:
            return []
        
        # Calculate rolling volatility (standard deviation)
        volatilities = []
        for i in range(window, len(values)):
            window_values = values[i-window:i]
            vol = statistics.stdev(window_values) if len(window_values) > 1 else 0
            volatilities.append((i, vol))
        
        # Calculate mean volatility
        vol_values = [v[1] for v in volatilities]
        mean_vol = statistics.mean(vol_values)
        std_vol = statistics.stdev(vol_values) if len(vol_values) > 1 else 1
        
        if std_vol == 0:
            std_vol = 1
        
        # Detect high volatility periods
        clusters = []
        for idx, vol in volatilities:
            z_score = (vol - mean_vol) / std_vol
            if z_score > threshold:
                clusters.append((idx, vol))
        
        return clusters


class PeerGroupAnalyzer:
    """Analyze modules against their peer groups."""
    
    @staticmethod
    def calculate_peer_deviation(
        module_value: float,
        peer_values: List[float],
        metric_name: str
    ) -> Tuple[float, str]:
        """
        Calculate how much a module deviates from its peer group.
        
        Returns:
            (deviation_score, severity)
        """
        if not peer_values:
            return (0.0, "unknown")
        
        peer_mean = statistics.mean(peer_values)
        peer_std = statistics.stdev(peer_values) if len(peer_values) > 1 else 1
        
        if peer_std == 0:
            peer_std = 1
        
        deviation = abs(module_value - peer_mean) / peer_std
        
        # Determine severity
        if deviation > 3.0:
            severity = "critical"
        elif deviation > 2.0:
            severity = "high"
        elif deviation > 1.5:
            severity = "medium"
        else:
            severity = "low"
        
        return (deviation, severity)
    
    @staticmethod
    def find_peer_group(
        module_name: str,
        all_modules: Dict[str, Dict[str, Any]],
        similarity_func: Optional[Callable] = None
    ) -> List[str]:
        """
        Find peer group for a module based on similarity.
        
        Default similarity: same lifecycle stage and similar complexity
        """
        if module_name not in all_modules:
            return []
        
        module = all_modules[module_name]
        peers = []
        
        for other_name, other_data in all_modules.items():
            if other_name == module_name:
                continue
            
            # Simple similarity: same lifecycle stage
            if (module.get('lifecycle_stage') == other_data.get('lifecycle_stage')):
                peers.append(other_name)
        
        return peers


class AnomalyDetectionEngine:
    """
    Main anomaly detection engine combining multiple detection methods.
    """
    
    def __init__(self):
        self.statistical_detector = StatisticalDetector()
        self.velocity_detector = VelocityDetector()
        self.peer_analyzer = PeerGroupAnalyzer()
        
        # Detection configuration
        self.enabled_detectors = {
            'statistical_outlier': True,
            'velocity_spike': True,
            'momentum_shift': True,
            'volatility_cluster': True,
            'peer_deviation': True,
            'trend_break': True
        }
        
        # Thresholds
        self.thresholds = {
            'z_score': 2.5,
            'velocity_spike': 3.0,
            'volatility': 2.0,
            'peer_deviation': 2.0
        }
    
    def detect_anomalies(
        self,
        module_name: str,
        metric_history: Dict[str, List[float]],
        timestamps: List[datetime],
        peer_modules: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Anomaly]:
        """
        Detect all types of anomalies for a module.
        
        Args:
            module_name: Name of the module
            metric_history: Dict of metric_name -> list of values
            timestamps: Corresponding timestamps
            peer_modules: Optional dict of peer module data
            
        Returns:
            List of detected Anomaly objects
        """
        anomalies = []
        
        for metric_name, values in metric_history.items():
            # Statistical outliers
            if self.enabled_detectors['statistical_outlier']:
                stat_anomalies = self._detect_statistical_anomalies(
                    module_name, metric_name, values, timestamps
                )
                anomalies.extend(stat_anomalies)
            
            # Velocity anomalies
            if self.enabled_detectors['velocity_spike']:
                vel_anomalies = self._detect_velocity_anomalies(
                    module_name, metric_name, values, timestamps
                )
                anomalies.extend(vel_anomalies)
            
            # Peer deviation
            if self.enabled_detectors['peer_deviation'] and peer_modules:
                peer_anomalies = self._detect_peer_anomalies(
                    module_name, metric_name, values, peer_modules
                )
                anomalies.extend(peer_anomalies)
        
        # Sort by severity and confidence
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        anomalies.sort(key=lambda a: (severity_order.get(a.severity, 4), -a.confidence))
        
        return anomalies
    
    def _detect_statistical_anomalies(
        self,
        module_name: str,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime]
    ) -> List[Anomaly]:
        """Detect statistical anomalies using multiple methods."""
        anomalies = []
        
        # Z-score detection
        z_anomalies = self.statistical_detector.z_score_detection(
            values, self.thresholds['z_score']
        )
        
        for idx, value, z_score in z_anomalies:
            severity = "critical" if z_score > 3.5 else "high" if z_score > 3.0 else "medium"
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                module_name=module_name,
                timestamp=timestamps[idx] if idx < len(timestamps) else datetime.now(timezone.utc),
                severity=severity,
                confidence=min(z_score / 4.0, 1.0),
                metric_name=metric_name,
                expected_value=statistics.mean(values[:idx] + values[idx+1:]),
                actual_value=value,
                deviation=z_score,
                historical_context={
                    'mean': statistics.mean(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'sample_size': len(values)
                },
                peer_comparison=None,
                suggested_action=f"Investigate unexpected {metric_name} value"
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_velocity_anomalies(
        self,
        module_name: str,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime]
    ) -> List[Anomaly]:
        """Detect velocity-based anomalies."""
        anomalies = []
        
        # Velocity spikes
        spikes = self.velocity_detector.detect_velocity_spike(
            values, timestamps, self.thresholds['velocity_spike']
        )
        
        for idx, velocity, z_score in spikes:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.VELOCITY_SPIKE,
                module_name=module_name,
                timestamp=timestamps[idx] if idx < len(timestamps) else datetime.now(timezone.utc),
                severity="high" if z_score > 4.0 else "medium",
                confidence=min(z_score / 5.0, 1.0),
                metric_name=f"{metric_name}_velocity",
                expected_value=0.0,
                actual_value=velocity,
                deviation=z_score,
                historical_context={'recent_values': values[max(0, idx-5):idx]},
                peer_comparison=None,
                suggested_action="Monitor for rapid changes in module behavior"
            )
            anomalies.append(anomaly)
        
        # Momentum shifts
        momentum = self.velocity_detector.detect_momentum_shift(values)
        if momentum:
            idx, direction, strength = momentum
            anomaly = Anomaly(
                anomaly_type=AnomalyType.MOMENTUM_SHIFT,
                module_name=module_name,
                timestamp=timestamps[-1],
                severity="medium",
                confidence=min(strength * 10, 1.0),
                metric_name=f"{metric_name}_momentum",
                expected_value=0.0,
                actual_value=1.0 if direction == "up" else -1.0,
                deviation=strength,
                historical_context={'direction': direction},
                peer_comparison=None,
                suggested_action=f"Module showing {direction}ward momentum shift"
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_peer_anomalies(
        self,
        module_name: str,
        metric_name: str,
        values: List[float],
        peer_modules: Dict[str, Dict[str, Any]]
    ) -> List[Anomaly]:
        """Detect anomalies based on peer group comparison."""
        anomalies = []
        
        current_value = values[-1] if values else 0
        
        # Find peer values for the same metric
        peer_values = []
        for peer_name, peer_data in peer_modules.items():
            if peer_name != module_name:
                peer_metric_history = peer_data.get('metric_history', {})
                peer_values_list = peer_metric_history.get(metric_name, [])
                if peer_values_list:
                    peer_values.append(peer_values_list[-1])
        
        if peer_values:
            deviation, severity = self.peer_analyzer.calculate_peer_deviation(
                current_value, peer_values, metric_name
            )
            
            if severity in ['medium', 'high', 'critical']:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.PEER_DEVIATION,
                    module_name=module_name,
                    timestamp=datetime.now(timezone.utc),
                    severity=severity,
                    confidence=min(deviation / 3.0, 1.0),
                    metric_name=metric_name,
                    expected_value=statistics.mean(peer_values),
                    actual_value=current_value,
                    deviation=deviation,
                    historical_context={'peer_count': len(peer_values)},
                    peer_comparison={
                        'peer_mean': statistics.mean(peer_values),
                        'peer_std': statistics.stdev(peer_values) if len(peer_values) > 1 else 0
                    },
                    suggested_action="Review module for differences from peer group norms"
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def configure_detector(
        self,
        detector_name: str,
        enabled: bool,
        threshold: Optional[float] = None
    ) -> None:
        """Configure a specific detector."""
        if detector_name in self.enabled_detectors:
            self.enabled_detectors[detector_name] = enabled
        
        if threshold and detector_name in self.thresholds:
            self.thresholds[detector_name] = threshold


def quick_anomaly_check(
    module_name: str,
    recent_values: List[float],
    baseline_values: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Quick anomaly check for rapid validation.
    
    Args:
        module_name: Name of module to check
        recent_values: Recent metric values
        baseline_values: Optional baseline for comparison
        
    Returns:
        List of anomaly summaries
    """
    if not recent_values:
        return []
    
    engine = AnomalyDetectionEngine()
    timestamps = [datetime.now(timezone.utc) - timedelta(hours=i) for i in range(len(recent_values))]
    timestamps.reverse()
    
    metric_history = {'metric': recent_values}
    
    anomalies = engine.detect_anomalies(
        module_name,
        metric_history,
        timestamps
    )
    
    return [a.to_dict() for a in anomalies]


# Example usage and testing
if __name__ == "__main__":
    # Test data simulating module metrics
    test_values = [10, 11, 10, 12, 11, 10, 45, 11, 10, 12]  # 45 is outlier
    test_timestamps = [datetime.now(timezone.utc) - timedelta(hours=i) for i in range(len(test_values))]
    test_timestamps.reverse()
    
    engine = AnomalyDetectionEngine()
    
    metric_history = {'dependents': test_values}
    
    anomalies = engine.detect_anomalies(
        "test_module",
        metric_history,
        test_timestamps
    )
    
    print(f"Detected {len(anomalies)} anomalies:")
    for anomaly in anomalies:
        print(f"  - {anomaly.anomaly_type.value}: {anomaly.severity} "
              f"(confidence: {anomaly.confidence:.2f})")
