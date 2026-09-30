"""
Cost Anomaly Detection Engine
==============================

ML-powered anomaly detection for cloud cost optimization.

Algorithms:
- Z-score (statistical)
- IQR (Interquartile Range)
- Isolation Forest (ML)
- Moving Average deviation

Author: PromptOps Team - Q3 2026
Date: July 9, 2026
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import IsolationForest
from scipy import stats


class AnomalyMethod(Enum):
    """Anomaly detection methods"""
    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    MOVING_AVERAGE = "moving_average"


class AnomalySeverity(Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Detected anomaly"""
    timestamp: datetime
    value: float
    expected_value: float
    deviation: float
    deviation_percentage: float
    severity: AnomalySeverity
    method: AnomalyMethod
    confidence: float
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class AnomalyDetectionConfig:
    """Configuration for anomaly detection"""
    # Z-score parameters
    z_score_threshold: float = 3.0

    # IQR parameters
    iqr_multiplier: float = 1.5

    # Isolation Forest parameters
    contamination: float = 0.1
    n_estimators: int = 100

    # Moving average parameters
    window_size: int = 7
    std_multiplier: float = 2.0

    # Severity thresholds (deviation percentage)
    low_threshold: float = 20.0
    medium_threshold: float = 50.0
    high_threshold: float = 100.0


class CostAnomalyDetector:
    """
    Cost anomaly detection engine using multiple ML algorithms.

    Features:
    - Multi-algorithm detection (Z-score, IQR, Isolation Forest, MA)
    - Severity classification
    - Confidence scoring
    - Historical baseline learning
    - Real-time detection

    Example:
        detector = CostAnomalyDetector()
        anomalies = detector.detect_anomalies(cost_data, method=AnomalyMethod.Z_SCORE)
    """

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        """Initialize detector with configuration"""
        self.config = config or AnomalyDetectionConfig()
        self.isolation_forest: Optional[IsolationForest] = None
        self.baseline_stats: Dict = {}

    def detect_anomalies(
        self,
        data: List[Dict],
        method: AnomalyMethod = AnomalyMethod.Z_SCORE,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[Anomaly]:
        """
        Detect anomalies in cost data.

        Args:
            data: List of {timestamp, value} dicts
            method: Detection method to use
            resource_id: Optional resource identifier
            resource_type: Optional resource type (ec2, rds, etc.)

        Returns:
            List of detected anomalies
        """
        if len(data) < 2:
            return []

        # Extract timestamps and values
        timestamps = [d['timestamp'] for d in data]
        values = np.array([d['value'] for d in data])

        # Select detection method
        if method == AnomalyMethod.Z_SCORE:
            anomaly_indices = self._detect_z_score(values)
        elif method == AnomalyMethod.IQR:
            anomaly_indices = self._detect_iqr(values)
        elif method == AnomalyMethod.ISOLATION_FOREST:
            anomaly_indices = self._detect_isolation_forest(values)
        elif method == AnomalyMethod.MOVING_AVERAGE:
            anomaly_indices = self._detect_moving_average(values)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Calculate expected values
        expected_values = self._calculate_expected_values(values, method)

        # Build anomaly objects
        anomalies = []
        for idx in anomaly_indices:
            value = values[idx]
            expected = expected_values[idx]
            deviation = abs(value - expected)
            deviation_pct = (deviation / expected * 100) if expected > 0 else 0

            anomaly = Anomaly(
                timestamp=timestamps[idx],
                value=value,
                expected_value=expected,
                deviation=deviation,
                deviation_percentage=deviation_pct,
                severity=self._classify_severity(deviation_pct),
                method=method,
                confidence=self._calculate_confidence(values, idx, method),
                resource_id=resource_id,
                resource_type=resource_type,
            )
            anomalies.append(anomaly)

        return sorted(anomalies, key=lambda x: x.deviation_percentage, reverse=True)

    def detect_multi_method(
        self,
        data: List[Dict],
        methods: Optional[List[AnomalyMethod]] = None,
        consensus_threshold: int = 2
    ) -> List[Anomaly]:
        """
        Detect anomalies using multiple methods with consensus.

        Args:
            data: Cost data points
            methods: Methods to use (default: all)
            consensus_threshold: Minimum methods that must agree

        Returns:
            Anomalies detected by multiple methods
        """
        if methods is None:
            methods = list(AnomalyMethod)

        # Detect with each method
        all_detections = {}
        for method in methods:
            anomalies = self.detect_anomalies(data, method)
            for anomaly in anomalies:
                key = anomaly.timestamp.isoformat()
                if key not in all_detections:
                    all_detections[key] = []
                all_detections[key].append(anomaly)

        # Filter by consensus
        consensus_anomalies = []
        for timestamp_key, detections in all_detections.items():
            if len(detections) >= consensus_threshold:
                # Use the highest severity detection
                best = max(detections, key=lambda x: (
                    x.deviation_percentage,
                    x.confidence
                ))
                best.confidence = len(detections) / len(methods)
                consensus_anomalies.append(best)

        return sorted(consensus_anomalies, key=lambda x: x.deviation_percentage, reverse=True)

    def learn_baseline(self, data: List[Dict], resource_id: str):
        """
        Learn baseline statistics for a resource.

        Args:
            data: Historical cost data
            resource_id: Resource identifier
        """
        values = np.array([d['value'] for d in data])

        self.baseline_stats[resource_id] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'median': np.median(values),
            'q1': np.percentile(values, 25),
            'q3': np.percentile(values, 75),
            'min': np.min(values),
            'max': np.max(values),
            'samples': len(values),
            'last_updated': datetime.utcnow(),
        }

    # ========================================================================
    # Detection Methods
    # ========================================================================

    def _detect_z_score(self, values: np.ndarray) -> List[int]:
        """Detect anomalies using Z-score method"""
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return []

        z_scores = np.abs((values - mean) / std)
        return np.where(z_scores > self.config.z_score_threshold)[0].tolist()

    def _detect_iqr(self, values: np.ndarray) -> List[int]:
        """Detect anomalies using Interquartile Range method"""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        lower_bound = q1 - self.config.iqr_multiplier * iqr
        upper_bound = q3 + self.config.iqr_multiplier * iqr

        return np.where((values < lower_bound) | (values > upper_bound))[0].tolist()

    def _detect_isolation_forest(self, values: np.ndarray) -> List[int]:
        """Detect anomalies using Isolation Forest ML algorithm"""
        if len(values) < 10:
            return []

        # Train or retrain model
        X = values.reshape(-1, 1)
        self.isolation_forest = IsolationForest(
            contamination=self.config.contamination,
            n_estimators=self.config.n_estimators,
            random_state=42
        )
        predictions = self.isolation_forest.fit_predict(X)

        # -1 indicates anomaly
        return np.where(predictions == -1)[0].tolist()

    def _detect_moving_average(self, values: np.ndarray) -> List[int]:
        """Detect anomalies using moving average deviation"""
        if len(values) < self.config.window_size:
            return []

        # Calculate moving average and std
        moving_avg = np.convolve(
            values,
            np.ones(self.config.window_size) / self.config.window_size,
            mode='valid'
        )

        # Pad to original length
        padding = len(values) - len(moving_avg)
        moving_avg = np.pad(moving_avg, (padding, 0), mode='edge')

        # Calculate moving std
        moving_std = np.array([
            np.std(values[max(0, i - self.config.window_size):i + 1])
            for i in range(len(values))
        ])

        # Detect deviations
        deviations = np.abs(values - moving_avg)
        threshold = self.config.std_multiplier * moving_std

        return np.where(deviations > threshold)[0].tolist()

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _calculate_expected_values(
        self,
        values: np.ndarray,
        method: AnomalyMethod
    ) -> np.ndarray:
        """Calculate expected values based on method"""
        if method == AnomalyMethod.Z_SCORE:
            return np.full_like(values, np.mean(values))

        elif method == AnomalyMethod.IQR:
            return np.full_like(values, np.median(values))

        elif method == AnomalyMethod.ISOLATION_FOREST:
            return np.full_like(values, np.mean(values))

        elif method == AnomalyMethod.MOVING_AVERAGE:
            if len(values) < self.config.window_size:
                return np.full_like(values, np.mean(values))

            moving_avg = np.convolve(
                values,
                np.ones(self.config.window_size) / self.config.window_size,
                mode='valid'
            )
            padding = len(values) - len(moving_avg)
            return np.pad(moving_avg, (padding, 0), mode='edge')

        return np.full_like(values, np.mean(values))

    def _classify_severity(self, deviation_pct: float) -> AnomalySeverity:
        """Classify anomaly severity based on deviation percentage"""
        if deviation_pct >= self.config.high_threshold:
            return AnomalySeverity.CRITICAL
        elif deviation_pct >= self.config.medium_threshold:
            return AnomalySeverity.HIGH
        elif deviation_pct >= self.config.low_threshold:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _calculate_confidence(
        self,
        values: np.ndarray,
        index: int,
        method: AnomalyMethod
    ) -> float:
        """Calculate confidence score for anomaly detection"""
        value = values[index]
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return 0.5

        # Calculate normalized deviation
        z_score = abs((value - mean) / std)

        # Convert to confidence (0-1)
        # Higher z-score = higher confidence
        confidence = min(z_score / 5.0, 1.0)

        return round(confidence, 3)

    def get_baseline_stats(self, resource_id: str) -> Optional[Dict]:
        """Get baseline statistics for a resource"""
        return self.baseline_stats.get(resource_id)

    def clear_baseline(self, resource_id: Optional[str] = None):
        """Clear baseline statistics"""
        if resource_id:
            self.baseline_stats.pop(resource_id, None)
        else:
            self.baseline_stats.clear()


# ============================================================================
# Utility Functions
# ============================================================================

def generate_sample_cost_data(
    days: int = 30,
    base_cost: float = 1000.0,
    noise: float = 50.0,
    anomaly_days: Optional[List[int]] = None
) -> List[Dict]:
    """
    Generate sample cost data for testing.

    Args:
        days: Number of days
        base_cost: Base daily cost
        noise: Random noise amplitude
        anomaly_days: Days to inject anomalies

    Returns:
        List of cost data points
    """
    data = []
    start_date = datetime.utcnow() - timedelta(days=days)

    for day in range(days):
        cost = base_cost + np.random.normal(0, noise)

        # Inject anomalies
        if anomaly_days and day in anomaly_days:
            cost *= np.random.uniform(2.0, 4.0)

        data.append({
            'timestamp': start_date + timedelta(days=day),
            'value': round(cost, 2)
        })

    return data


def analyze_anomalies(anomalies: List[Anomaly]) -> Dict:
    """
    Analyze detected anomalies and generate summary.

    Returns:
        Summary statistics and insights
    """
    if not anomalies:
        return {
            'total_anomalies': 0,
            'severity_breakdown': {},
            'total_excess_cost': 0.0,
            'avg_deviation': 0.0,
            'avg_confidence': 0.0
        }

    # Severity breakdown
    severity_counts = {}
    for anomaly in anomalies:
        severity = anomaly.severity.value
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Calculate metrics
    total_excess = sum(a.deviation for a in anomalies)
    avg_deviation = np.mean([a.deviation_percentage for a in anomalies])
    avg_confidence = np.mean([a.confidence for a in anomalies])

    return {
        'total_anomalies': len(anomalies),
        'severity_breakdown': severity_counts,
        'total_excess_cost': round(total_excess, 2),
        'avg_deviation': round(avg_deviation, 2),
        'avg_confidence': round(avg_confidence, 3),
        'highest_anomaly': {
            'timestamp': anomalies[0].timestamp.isoformat(),
            'deviation_pct': round(anomalies[0].deviation_percentage, 2),
            'value': anomalies[0].value,
            'expected': anomalies[0].expected_value
        } if anomalies else None
    }
