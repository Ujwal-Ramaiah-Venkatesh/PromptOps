"""
Performance Monitor for PromptOps ML Models
===========================================

Real-time monitoring of ML model performance metrics:
- Accuracy, precision, recall, F1 (classification)
- MAE, RMSE, R² (regression)
- Latency (p50, p95, p99)
- Throughput (requests/second)
- Error rates

Author: ML Engineer - Phase 5 Week 46-47
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Performance Monitor
# ============================================================================

class PerformanceMonitor:
    """
    Monitors ML model performance in real-time.

    Tracks:
    - Prediction metrics (accuracy, error rates)
    - Latency metrics (p50, p95, p99)
    - Throughput (requests/second)
    - Resource utilization
    """

    def __init__(
        self,
        model_name: str,
        endpoint_name: str,
        region: str = 'us-east-1',
        window_size: int = 1000
    ):
        """
        Initialize Performance Monitor.

        Args:
            model_name: Name of model being monitored
            endpoint_name: SageMaker endpoint name
            region: AWS region
            window_size: Size of sliding window for metrics
        """
        self.model_name = model_name
        self.endpoint_name = endpoint_name
        self.region = region
        self.window_size = window_size

        # CloudWatch client
        self.cloudwatch = None
        self._init_cloudwatch()

        # In-memory sliding windows for real-time metrics
        self.prediction_window = deque(maxlen=window_size)
        self.latency_window = deque(maxlen=window_size)
        self.error_window = deque(maxlen=window_size)

        # Cumulative metrics
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = datetime.utcnow()

    def _init_cloudwatch(self):
        """Initialize CloudWatch client."""
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            logger.info(f"CloudWatch client initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch: {e}")

    def record_prediction(
        self,
        prediction: Any,
        ground_truth: Optional[Any] = None,
        latency_ms: float = 0.0,
        error: bool = False
    ):
        """
        Record a single prediction for monitoring.

        Args:
            prediction: Model prediction
            ground_truth: Optional ground truth label
            latency_ms: Prediction latency in milliseconds
            error: Whether prediction resulted in error
        """
        self.total_requests += 1

        # Record prediction
        self.prediction_window.append({
            "prediction": prediction,
            "ground_truth": ground_truth,
            "timestamp": datetime.utcnow(),
            "latency_ms": latency_ms,
            "error": error
        })

        # Record latency
        if latency_ms > 0:
            self.latency_window.append(latency_ms)

        # Record error
        if error:
            self.total_errors += 1
            self.error_window.append(1)
        else:
            self.error_window.append(0)

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dictionary of current metrics
        """
        metrics = {
            "model_name": self.model_name,
            "endpoint_name": self.endpoint_name,
            "timestamp": datetime.utcnow().isoformat(),
            "window_size": len(self.prediction_window),
            "total_requests": self.total_requests,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600
        }

        # Throughput metrics
        metrics["throughput"] = self._calculate_throughput()

        # Latency metrics
        metrics["latency"] = self._calculate_latency_metrics()

        # Error metrics
        metrics["errors"] = self._calculate_error_metrics()

        # Prediction quality metrics (if ground truth available)
        if any(p.get("ground_truth") is not None for p in self.prediction_window):
            metrics["quality"] = self._calculate_quality_metrics()

        return metrics

    def _calculate_throughput(self) -> Dict[str, float]:
        """Calculate throughput metrics."""
        if len(self.prediction_window) < 2:
            return {"requests_per_second": 0.0, "requests_per_minute": 0.0}

        # Calculate time span
        first_timestamp = self.prediction_window[0]["timestamp"]
        last_timestamp = self.prediction_window[-1]["timestamp"]
        duration_seconds = (last_timestamp - first_timestamp).total_seconds()

        if duration_seconds == 0:
            return {"requests_per_second": 0.0, "requests_per_minute": 0.0}

        rps = len(self.prediction_window) / duration_seconds
        rpm = rps * 60

        return {
            "requests_per_second": round(rps, 2),
            "requests_per_minute": round(rpm, 2),
            "window_duration_seconds": round(duration_seconds, 2)
        }

    def _calculate_latency_metrics(self) -> Dict[str, float]:
        """Calculate latency percentiles."""
        if not self.latency_window:
            return {
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "mean_ms": 0.0,
                "max_ms": 0.0
            }

        latencies = np.array(list(self.latency_window))

        return {
            "p50_ms": float(np.percentile(latencies, 50)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "mean_ms": float(np.mean(latencies)),
            "max_ms": float(np.max(latencies)),
            "min_ms": float(np.min(latencies))
        }

    def _calculate_error_metrics(self) -> Dict[str, Any]:
        """Calculate error rate metrics."""
        if not self.error_window:
            return {
                "error_rate": 0.0,
                "error_count": 0,
                "success_rate": 1.0
            }

        errors = np.array(list(self.error_window))
        error_count = int(np.sum(errors))
        error_rate = float(np.mean(errors))

        return {
            "error_rate": error_rate,
            "error_count": error_count,
            "success_rate": 1.0 - error_rate,
            "total_errors": self.total_errors,
            "total_errors_rate": self.total_errors / max(self.total_requests, 1)
        }

    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate prediction quality metrics."""
        # Extract predictions and ground truth
        predictions = []
        ground_truths = []

        for pred_data in self.prediction_window:
            if pred_data.get("ground_truth") is not None:
                predictions.append(pred_data["prediction"])
                ground_truths.append(pred_data["ground_truth"])

        if not predictions:
            return {"no_ground_truth": True}

        # Try classification metrics first
        try:
            pred_array = np.array(predictions)
            gt_array = np.array(ground_truths)

            # Check if classification (discrete values)
            if len(np.unique(gt_array)) <= 20:  # Assume classification if ≤20 unique values
                correct = np.sum(pred_array == gt_array)
                accuracy = correct / len(predictions)

                return {
                    "type": "classification",
                    "accuracy": float(accuracy),
                    "correct_predictions": int(correct),
                    "total_predictions": len(predictions)
                }
            else:
                # Regression metrics
                mae = float(np.mean(np.abs(pred_array - gt_array)))
                rmse = float(np.sqrt(np.mean((pred_array - gt_array) ** 2)))

                # R² score
                ss_res = np.sum((gt_array - pred_array) ** 2)
                ss_tot = np.sum((gt_array - np.mean(gt_array)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

                return {
                    "type": "regression",
                    "mae": mae,
                    "rmse": rmse,
                    "r2_score": float(r2),
                    "total_predictions": len(predictions)
                }

        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
            return {"error": str(e)}

    def get_cloudwatch_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: int = 300
    ) -> Dict[str, Any]:
        """
        Get metrics from CloudWatch for SageMaker endpoint.

        Args:
            start_time: Start time for metrics (default: 1 hour ago)
            end_time: End time for metrics (default: now)
            period: Period in seconds (default: 300 = 5 minutes)

        Returns:
            CloudWatch metrics
        """
        if not self.cloudwatch:
            logger.warning("CloudWatch not available")
            return {"error": "CloudWatch not available"}

        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()

        try:
            # SageMaker endpoint metrics
            metrics_to_fetch = [
                "Invocations",
                "ModelLatency",
                "OverheadLatency",
                "Invocation4XXErrors",
                "Invocation5XXErrors"
            ]

            cloudwatch_metrics = {}

            for metric_name in metrics_to_fetch:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/SageMaker',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'EndpointName', 'Value': self.endpoint_name},
                        {'Name': 'VariantName', 'Value': 'AllTraffic'}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period,
                    Statistics=['Average', 'Sum', 'Maximum']
                )

                cloudwatch_metrics[metric_name] = response.get('Datapoints', [])

            return {
                "endpoint_name": self.endpoint_name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "period_seconds": period,
                "metrics": cloudwatch_metrics
            }

        except ClientError as e:
            logger.error(f"Failed to fetch CloudWatch metrics: {e}")
            return {"error": str(e)}

    def check_performance_degradation(
        self,
        baseline_metrics: Dict[str, Any],
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Check if current performance has degraded compared to baseline.

        Args:
            baseline_metrics: Baseline metrics to compare against
            thresholds: Custom thresholds (optional)

        Returns:
            Degradation check results
        """
        if not thresholds:
            thresholds = {
                "accuracy_drop": 0.05,  # 5% accuracy drop
                "error_rate_increase": 0.05,  # 5% error rate increase
                "latency_increase": 0.30,  # 30% latency increase
            }

        current_metrics = self.get_current_metrics()

        degradation = {
            "degraded": False,
            "checks": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Check accuracy degradation (if available)
        if "quality" in current_metrics and "quality" in baseline_metrics:
            if current_metrics["quality"].get("type") == "classification":
                current_acc = current_metrics["quality"].get("accuracy", 1.0)
                baseline_acc = baseline_metrics["quality"].get("accuracy", 1.0)
                accuracy_drop = baseline_acc - current_acc

                check = {
                    "metric": "accuracy",
                    "current": current_acc,
                    "baseline": baseline_acc,
                    "change": -accuracy_drop,
                    "threshold": thresholds["accuracy_drop"],
                    "degraded": accuracy_drop > thresholds["accuracy_drop"]
                }
                degradation["checks"].append(check)

                if check["degraded"]:
                    degradation["degraded"] = True

        # Check error rate increase
        current_error_rate = current_metrics["errors"].get("error_rate", 0.0)
        baseline_error_rate = baseline_metrics.get("errors", {}).get("error_rate", 0.0)
        error_rate_increase = current_error_rate - baseline_error_rate

        check = {
            "metric": "error_rate",
            "current": current_error_rate,
            "baseline": baseline_error_rate,
            "change": error_rate_increase,
            "threshold": thresholds["error_rate_increase"],
            "degraded": error_rate_increase > thresholds["error_rate_increase"]
        }
        degradation["checks"].append(check)

        if check["degraded"]:
            degradation["degraded"] = True

        # Check latency increase
        current_p95 = current_metrics["latency"].get("p95_ms", 0.0)
        baseline_p95 = baseline_metrics.get("latency", {}).get("p95_ms", 0.0)

        if baseline_p95 > 0:
            latency_increase = (current_p95 - baseline_p95) / baseline_p95

            check = {
                "metric": "latency_p95",
                "current": current_p95,
                "baseline": baseline_p95,
                "change": latency_increase,
                "threshold": thresholds["latency_increase"],
                "degraded": latency_increase > thresholds["latency_increase"]
            }
            degradation["checks"].append(check)

            if check["degraded"]:
                degradation["degraded"] = True

        return degradation

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        metrics = self.get_current_metrics()

        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics exported to: {filepath}")

    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        self.prediction_window.clear()
        self.latency_window.clear()
        self.error_window.clear()
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = datetime.utcnow()
        logger.info("Metrics reset")


# ============================================================================
# Testing
# ============================================================================

def test_performance_monitor():
    """Test performance monitor with simulated data."""
    logger.info("Testing Performance Monitor...")

    monitor = PerformanceMonitor(
        model_name="churn-prediction",
        endpoint_name="churn-prediction-prod",
        window_size=100
    )

    # Simulate 150 predictions
    print("\n=== Simulating Predictions ===")
    np.random.seed(42)

    for i in range(150):
        # Simulate prediction
        ground_truth = np.random.randint(0, 2)
        prediction = ground_truth if np.random.random() < 0.85 else 1 - ground_truth

        # Simulate latency (normal distribution around 50ms)
        latency = max(10, np.random.normal(50, 10))

        # Simulate error (2% error rate)
        error = np.random.random() < 0.02

        monitor.record_prediction(
            prediction=prediction,
            ground_truth=ground_truth,
            latency_ms=latency,
            error=error
        )

    # Get current metrics
    print("\n=== Current Metrics ===")
    metrics = monitor.get_current_metrics()
    print(json.dumps(metrics, indent=2))

    # Check degradation
    print("\n=== Checking Performance Degradation ===")
    baseline_metrics = {
        "quality": {"type": "classification", "accuracy": 0.90},
        "errors": {"error_rate": 0.01},
        "latency": {"p95_ms": 55.0}
    }

    degradation = monitor.check_performance_degradation(baseline_metrics)
    print(json.dumps(degradation, indent=2))


if __name__ == "__main__":
    test_performance_monitor()
