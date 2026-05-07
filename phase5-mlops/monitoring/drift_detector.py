"""
Drift Detector for PromptOps ML Models
======================================

Detects two types of drift:
1. Prediction Drift: Distribution of predictions changes
2. Concept Drift: Relationship between features and target changes

Uses statistical tests and Evidently AI approach.

Author: ML Engineer - Phase 5 Week 46-47
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Drift Detector
# ============================================================================

class DriftDetector:
    """
    Detects drift in ML model predictions and data distributions.

    Supports:
    - Prediction drift: Changes in prediction distribution
    - Concept drift: Changes in feature-target relationship
    - Statistical tests: KS test, chi-square, PSI, JS divergence
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize Drift Detector.

        Args:
            significance_level: P-value threshold for statistical tests
        """
        self.significance_level = significance_level

    def detect_prediction_drift(
        self,
        reference_predictions: List[Any],
        current_predictions: List[Any],
        prediction_type: str = "classification"
    ) -> Dict[str, Any]:
        """
        Detect drift in prediction distribution.

        Args:
            reference_predictions: Baseline predictions (training/validation)
            current_predictions: Current production predictions
            prediction_type: "classification" or "regression"

        Returns:
            Drift detection results
        """
        logger.info(f"Detecting prediction drift ({prediction_type})")

        results = {
            "drift_type": "prediction_drift",
            "prediction_type": prediction_type,
            "reference_size": len(reference_predictions),
            "current_size": len(current_predictions),
            "detected_at": datetime.utcnow().isoformat(),
            "drift_detected": False,
            "drift_score": 0.0,
            "tests": []
        }

        if prediction_type == "classification":
            results["tests"] = self._detect_classification_drift(
                reference_predictions,
                current_predictions
            )
        else:  # regression
            results["tests"] = self._detect_regression_drift(
                reference_predictions,
                current_predictions
            )

        # Overall drift detection
        significant_tests = [t for t in results["tests"] if t.get("drift_detected", False)]
        if significant_tests:
            results["drift_detected"] = True
            results["drift_score"] = np.mean([t.get("drift_score", 0) for t in significant_tests])

        return results

    def _detect_classification_drift(
        self,
        reference: List[Any],
        current: List[Any]
    ) -> List[Dict[str, Any]]:
        """Detect drift in classification predictions."""
        tests = []

        # Chi-square test
        try:
            # Get unique classes
            all_classes = sorted(set(reference + current))

            # Count occurrences
            ref_counts = [reference.count(c) for c in all_classes]
            curr_counts = [current.count(c) for c in all_classes]

            # Normalize to proportions
            ref_total = sum(ref_counts)
            curr_total = sum(curr_counts)

            ref_props = [c / ref_total for c in ref_counts]
            curr_props = [c / curr_total for c in curr_counts]

            # Chi-square test
            observed = curr_counts
            expected = [p * curr_total for p in ref_props]

            chi2_stat, p_value = stats.chisquare(observed, expected)

            tests.append({
                "test_name": "chi_square",
                "statistic": float(chi2_stat),
                "p_value": float(p_value),
                "drift_detected": bool(p_value < self.significance_level),
                "drift_score": float(chi2_stat / len(all_classes)),  # Normalized
                "reference_distribution": dict(zip(all_classes, ref_props)),
                "current_distribution": dict(zip(all_classes, curr_props))
            })

        except Exception as e:
            logger.error(f"Chi-square test failed: {e}")

        # Jensen-Shannon divergence
        try:
            all_classes = sorted(set(reference + current))
            ref_counts = np.array([reference.count(c) for c in all_classes])
            curr_counts = np.array([current.count(c) for c in all_classes])

            # Normalize
            ref_dist = ref_counts / ref_counts.sum()
            curr_dist = curr_counts / curr_counts.sum()

            js_div = jensenshannon(ref_dist, curr_dist)

            tests.append({
                "test_name": "jensen_shannon_divergence",
                "divergence": float(js_div),
                "drift_detected": bool(js_div > 0.1),  # Threshold: 0.1
                "drift_score": float(js_div),
                "threshold": 0.1
            })

        except Exception as e:
            logger.error(f"Jensen-Shannon divergence failed: {e}")

        # Population Stability Index (PSI)
        try:
            psi = self._calculate_psi(reference, current)

            tests.append({
                "test_name": "population_stability_index",
                "psi": float(psi),
                "drift_detected": bool(psi > 0.1),  # PSI > 0.1 indicates shift
                "drift_score": float(psi),
                "interpretation": (
                    "no_shift" if psi < 0.1 else
                    "moderate_shift" if psi < 0.25 else
                    "significant_shift"
                )
            })

        except Exception as e:
            logger.error(f"PSI calculation failed: {e}")

        return tests

    def _detect_regression_drift(
        self,
        reference: List[Any],
        current: List[Any]
    ) -> List[Dict[str, Any]]:
        """Detect drift in regression predictions."""
        tests = []

        ref_array = np.array([float(x) for x in reference])
        curr_array = np.array([float(x) for x in current])

        # Kolmogorov-Smirnov test
        try:
            ks_stat, p_value = stats.ks_2samp(ref_array, curr_array)

            tests.append({
                "test_name": "kolmogorov_smirnov",
                "statistic": float(ks_stat),
                "p_value": float(p_value),
                "drift_detected": bool(p_value < self.significance_level),
                "drift_score": float(ks_stat),
                "reference_mean": float(np.mean(ref_array)),
                "current_mean": float(np.mean(curr_array)),
                "reference_std": float(np.std(ref_array)),
                "current_std": float(np.std(curr_array))
            })

        except Exception as e:
            logger.error(f"KS test failed: {e}")

        # Wasserstein distance (Earth Mover's Distance)
        try:
            wasserstein = stats.wasserstein_distance(ref_array, curr_array)

            # Normalize by reference std
            normalized_wasserstein = wasserstein / (np.std(ref_array) + 1e-10)

            tests.append({
                "test_name": "wasserstein_distance",
                "distance": float(wasserstein),
                "normalized_distance": float(normalized_wasserstein),
                "drift_detected": bool(normalized_wasserstein > 0.1),
                "drift_score": float(normalized_wasserstein),
                "threshold": 0.1
            })

        except Exception as e:
            logger.error(f"Wasserstein distance failed: {e}")

        return tests

    def _calculate_psi(
        self,
        reference: List[Any],
        current: List[Any],
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).

        PSI = sum((current_pct - reference_pct) * ln(current_pct / reference_pct))
        """
        # Get bins from reference distribution
        ref_array = np.array(reference)
        curr_array = np.array(current)

        # Create bins
        _, bin_edges = np.histogram(ref_array, bins=bins)

        # Calculate proportions
        ref_counts, _ = np.histogram(ref_array, bins=bin_edges)
        curr_counts, _ = np.histogram(curr_array, bins=bin_edges)

        # Add small constant to avoid division by zero
        epsilon = 1e-10
        ref_props = (ref_counts + epsilon) / (len(reference) + epsilon * bins)
        curr_props = (curr_counts + epsilon) / (len(current) + epsilon * bins)

        # Calculate PSI
        psi = np.sum((curr_props - ref_props) * np.log(curr_props / ref_props))

        return float(psi)

    def detect_concept_drift(
        self,
        reference_data: Dict[str, List[Any]],
        current_data: Dict[str, List[Any]],
        model_type: str = "classification"
    ) -> Dict[str, Any]:
        """
        Detect concept drift (change in feature-target relationship).

        Args:
            reference_data: {"features": [...], "predictions": [...], "ground_truth": [...]}
            current_data: {"features": [...], "predictions": [...], "ground_truth": [...]}
            model_type: "classification" or "regression"

        Returns:
            Concept drift detection results
        """
        logger.info(f"Detecting concept drift ({model_type})")

        results = {
            "drift_type": "concept_drift",
            "model_type": model_type,
            "reference_size": len(reference_data.get("predictions", [])),
            "current_size": len(current_data.get("predictions", [])),
            "detected_at": datetime.utcnow().isoformat(),
            "drift_detected": False,
            "drift_score": 0.0,
            "tests": []
        }

        # Check if ground truth available
        if "ground_truth" not in reference_data or "ground_truth" not in current_data:
            results["error"] = "Ground truth required for concept drift detection"
            return results

        # Compare model performance on reference vs current data
        if model_type == "classification":
            ref_accuracy = self._calculate_accuracy(
                reference_data["predictions"],
                reference_data["ground_truth"]
            )
            curr_accuracy = self._calculate_accuracy(
                current_data["predictions"],
                current_data["ground_truth"]
            )

            accuracy_drop = ref_accuracy - curr_accuracy

            results["tests"].append({
                "test_name": "accuracy_comparison",
                "reference_accuracy": ref_accuracy,
                "current_accuracy": curr_accuracy,
                "accuracy_drop": accuracy_drop,
                "drift_detected": accuracy_drop > 0.05,  # 5% threshold
                "drift_score": accuracy_drop
            })

            if accuracy_drop > 0.05:
                results["drift_detected"] = True
                results["drift_score"] = accuracy_drop

        else:  # regression
            ref_rmse = self._calculate_rmse(
                reference_data["predictions"],
                reference_data["ground_truth"]
            )
            curr_rmse = self._calculate_rmse(
                current_data["predictions"],
                current_data["ground_truth"]
            )

            rmse_increase = (curr_rmse - ref_rmse) / (ref_rmse + 1e-10)

            results["tests"].append({
                "test_name": "rmse_comparison",
                "reference_rmse": ref_rmse,
                "current_rmse": curr_rmse,
                "rmse_increase": rmse_increase,
                "drift_detected": rmse_increase > 0.10,  # 10% threshold
                "drift_score": rmse_increase
            })

            if rmse_increase > 0.10:
                results["drift_detected"] = True
                results["drift_score"] = rmse_increase

        return results

    def _calculate_accuracy(
        self,
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> float:
        """Calculate classification accuracy."""
        correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        return correct / len(predictions) if predictions else 0.0

    def _calculate_rmse(
        self,
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> float:
        """Calculate RMSE for regression."""
        pred_array = np.array([float(p) for p in predictions])
        gt_array = np.array([float(g) for g in ground_truth])
        return float(np.sqrt(np.mean((pred_array - gt_array) ** 2)))

    def detect_feature_drift(
        self,
        reference_features: np.ndarray,
        current_features: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect drift in feature distributions.

        Args:
            reference_features: Reference feature matrix (n_samples x n_features)
            current_features: Current feature matrix (n_samples x n_features)
            feature_names: Optional feature names

        Returns:
            Feature drift detection results
        """
        logger.info("Detecting feature drift")

        n_features = reference_features.shape[1]
        if not feature_names:
            feature_names = [f"feature_{i}" for i in range(n_features)]

        results = {
            "drift_type": "feature_drift",
            "n_features": n_features,
            "detected_at": datetime.utcnow().isoformat(),
            "drift_detected": False,
            "drifted_features": [],
            "feature_tests": []
        }

        # Test each feature independently
        for i, feature_name in enumerate(feature_names):
            ref_feature = reference_features[:, i]
            curr_feature = current_features[:, i]

            # KS test for continuous features
            ks_stat, p_value = stats.ks_2samp(ref_feature, curr_feature)

            feature_test = {
                "feature_name": feature_name,
                "feature_index": i,
                "ks_statistic": float(ks_stat),
                "p_value": float(p_value),
                "drift_detected": p_value < self.significance_level,
                "reference_mean": float(np.mean(ref_feature)),
                "current_mean": float(np.mean(curr_feature)),
                "mean_change": float(np.mean(curr_feature) - np.mean(ref_feature))
            }

            results["feature_tests"].append(feature_test)

            if feature_test["drift_detected"]:
                results["drifted_features"].append(feature_name)
                results["drift_detected"] = True

        results["drift_score"] = len(results["drifted_features"]) / n_features

        return results

    def generate_drift_report(
        self,
        prediction_drift: Optional[Dict[str, Any]] = None,
        concept_drift: Optional[Dict[str, Any]] = None,
        feature_drift: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate human-readable drift detection report.

        Args:
            prediction_drift: Prediction drift results
            concept_drift: Concept drift results
            feature_drift: Feature drift results

        Returns:
            Formatted report
        """
        report = []
        report.append("=" * 70)
        report.append("DRIFT DETECTION REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append("")

        # Prediction drift
        if prediction_drift:
            report.append("PREDICTION DRIFT:")
            report.append(f"  Status: {'⚠️ DETECTED' if prediction_drift['drift_detected'] else '✓ No drift'}")
            report.append(f"  Score: {prediction_drift['drift_score']:.4f}")
            report.append(f"  Tests run: {len(prediction_drift['tests'])}")
            for test in prediction_drift['tests']:
                if test.get('drift_detected'):
                    report.append(f"    - {test['test_name']}: DRIFT DETECTED")
            report.append("")

        # Concept drift
        if concept_drift:
            report.append("CONCEPT DRIFT:")
            report.append(f"  Status: {'⚠️ DETECTED' if concept_drift['drift_detected'] else '✓ No drift'}")
            report.append(f"  Score: {concept_drift['drift_score']:.4f}")
            for test in concept_drift.get('tests', []):
                report.append(f"    - {test['test_name']}: {test}")
            report.append("")

        # Feature drift
        if feature_drift:
            report.append("FEATURE DRIFT:")
            report.append(f"  Status: {'⚠️ DETECTED' if feature_drift['drift_detected'] else '✓ No drift'}")
            report.append(f"  Drifted features: {len(feature_drift['drifted_features'])}/{feature_drift['n_features']}")
            if feature_drift['drifted_features']:
                report.append(f"  Features with drift: {', '.join(feature_drift['drifted_features'][:5])}")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)


# ============================================================================
# Testing
# ============================================================================

def test_drift_detector():
    """Test drift detector with simulated data."""
    logger.info("Testing Drift Detector...")

    detector = DriftDetector(significance_level=0.05)

    # Test 1: Classification prediction drift (no drift)
    print("\n=== Test 1: Classification Prediction Drift (No Drift) ===")
    np.random.seed(42)

    reference_preds = np.random.choice([0, 1], size=1000, p=[0.7, 0.3]).tolist()
    current_preds = np.random.choice([0, 1], size=1000, p=[0.68, 0.32]).tolist()  # Slight change

    drift_result = detector.detect_prediction_drift(
        reference_preds,
        current_preds,
        prediction_type="classification"
    )
    print(json.dumps(drift_result, indent=2))

    # Test 2: Classification prediction drift (with drift)
    print("\n=== Test 2: Classification Prediction Drift (With Drift) ===")

    reference_preds_drift = np.random.choice([0, 1], size=1000, p=[0.7, 0.3]).tolist()
    current_preds_drift = np.random.choice([0, 1], size=1000, p=[0.3, 0.7]).tolist()  # Significant change

    drift_result_2 = detector.detect_prediction_drift(
        reference_preds_drift,
        current_preds_drift,
        prediction_type="classification"
    )
    print(json.dumps(drift_result_2, indent=2))

    # Test 3: Concept drift
    print("\n=== Test 3: Concept Drift Detection ===")

    # Reference: 90% accuracy
    ref_ground_truth = np.random.randint(0, 2, 1000).tolist()
    ref_predictions = [gt if np.random.random() < 0.90 else 1-gt for gt in ref_ground_truth]

    # Current: 80% accuracy (concept drift)
    curr_ground_truth = np.random.randint(0, 2, 1000).tolist()
    curr_predictions = [gt if np.random.random() < 0.80 else 1-gt for gt in curr_ground_truth]

    concept_drift = detector.detect_concept_drift(
        reference_data={
            "predictions": ref_predictions,
            "ground_truth": ref_ground_truth
        },
        current_data={
            "predictions": curr_predictions,
            "ground_truth": curr_ground_truth
        },
        model_type="classification"
    )
    print(json.dumps(concept_drift, indent=2))

    # Generate report
    print("\n=== Drift Report ===")
    report = detector.generate_drift_report(
        prediction_drift=drift_result_2,
        concept_drift=concept_drift
    )
    print(report)


if __name__ == "__main__":
    test_drift_detector()
