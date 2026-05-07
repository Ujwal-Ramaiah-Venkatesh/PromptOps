"""
Prediction Quality Comparator for PromptOps
===========================================

Compares prediction quality between model versions using statistical tests.
Supports classification and regression metrics with statistical significance.

Author: ML Engineer - Phase 5 Week 44-45
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Prediction Quality Comparator
# ============================================================================

class PredictionComparator:
    """
    Compares prediction quality between two model versions.

    Supports:
    - Classification metrics (accuracy, precision, recall, F1)
    - Regression metrics (MAE, RMSE, R²)
    - Statistical significance tests
    - Prediction agreement analysis
    """

    def __init__(self):
        """Initialize Prediction Comparator."""
        self.significance_level = 0.05  # p-value threshold

    def compare_predictions(
        self,
        production_predictions: List[Dict[str, Any]],
        candidate_predictions: List[Dict[str, Any]],
        ground_truth: Optional[List[Any]] = None,
        model_type: str = "classification"
    ) -> Dict[str, Any]:
        """
        Compare predictions from production and candidate models.

        Args:
            production_predictions: Predictions from production model
            candidate_predictions: Predictions from candidate model
            ground_truth: Optional ground truth labels for evaluation
            model_type: Type of model (classification or regression)

        Returns:
            Comparison results with metrics and statistical tests
        """
        logger.info(f"Comparing {len(production_predictions)} predictions")

        comparison = {
            "model_type": model_type,
            "total_predictions": len(production_predictions),
            "compared_at": datetime.utcnow().isoformat(),
            "production_metrics": {},
            "candidate_metrics": {},
            "agreement_metrics": {},
            "statistical_tests": {},
            "recommendation": ""
        }

        # Extract prediction values
        prod_values = [p.get("prediction", p.get("value")) for p in production_predictions]
        cand_values = [p.get("prediction", p.get("value")) for p in candidate_predictions]

        # Agreement analysis
        comparison["agreement_metrics"] = self._calculate_agreement(
            prod_values,
            cand_values,
            model_type
        )

        # If ground truth available, calculate performance metrics
        if ground_truth:
            if model_type == "classification":
                comparison["production_metrics"] = self._classification_metrics(
                    prod_values,
                    ground_truth
                )
                comparison["candidate_metrics"] = self._classification_metrics(
                    cand_values,
                    ground_truth
                )
                comparison["statistical_tests"] = self._mcnemar_test(
                    prod_values,
                    cand_values,
                    ground_truth
                )

            elif model_type == "regression":
                comparison["production_metrics"] = self._regression_metrics(
                    prod_values,
                    ground_truth
                )
                comparison["candidate_metrics"] = self._regression_metrics(
                    cand_values,
                    ground_truth
                )
                comparison["statistical_tests"] = self._paired_t_test(
                    prod_values,
                    cand_values,
                    ground_truth
                )

        # Generate recommendation
        comparison["recommendation"] = self._generate_recommendation(comparison)

        return comparison

    def _calculate_agreement(
        self,
        predictions1: List[Any],
        predictions2: List[Any],
        model_type: str
    ) -> Dict[str, Any]:
        """Calculate agreement metrics between two sets of predictions."""
        if len(predictions1) != len(predictions2):
            return {"error": "Prediction lists have different lengths"}

        agreement_metrics = {
            "total_predictions": len(predictions1),
            "exact_agreement_count": 0,
            "exact_agreement_rate": 0.0,
            "disagreement_count": 0,
            "disagreement_rate": 0.0
        }

        exact_matches = 0
        differences = []

        for p1, p2 in zip(predictions1, predictions2):
            if model_type == "classification":
                # Exact match for classification
                if p1 == p2:
                    exact_matches += 1
            else:
                # Within tolerance for regression
                if p1 is not None and p2 is not None:
                    diff = abs(float(p1) - float(p2))
                    differences.append(diff)
                    # Consider "agreement" if within 10% relative error
                    rel_error = diff / max(abs(float(p1)), 1e-10)
                    if rel_error <= 0.10:
                        exact_matches += 1

        agreement_metrics["exact_agreement_count"] = exact_matches
        agreement_metrics["exact_agreement_rate"] = exact_matches / len(predictions1)
        agreement_metrics["disagreement_count"] = len(predictions1) - exact_matches
        agreement_metrics["disagreement_rate"] = 1.0 - agreement_metrics["exact_agreement_rate"]

        if model_type == "regression" and differences:
            agreement_metrics["mean_absolute_difference"] = float(np.mean(differences))
            agreement_metrics["median_absolute_difference"] = float(np.median(differences))
            agreement_metrics["max_absolute_difference"] = float(np.max(differences))

        return agreement_metrics

    def _classification_metrics(
        self,
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> Dict[str, float]:
        """Calculate classification metrics."""
        if len(predictions) != len(ground_truth):
            return {"error": "Prediction and ground truth lengths don't match"}

        # Convert to binary for simplicity (can be extended for multiclass)
        y_true = np.array(ground_truth)
        y_pred = np.array(predictions)

        # Basic metrics
        correct = np.sum(y_true == y_pred)
        accuracy = correct / len(y_true)

        # Confusion matrix elements
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        # Precision, recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn)
        }

    def _regression_metrics(
        self,
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> Dict[str, float]:
        """Calculate regression metrics."""
        if len(predictions) != len(ground_truth):
            return {"error": "Prediction and ground truth lengths don't match"}

        y_true = np.array([float(y) for y in ground_truth])
        y_pred = np.array([float(y) for y in predictions])

        # Mean Absolute Error
        mae = float(np.mean(np.abs(y_true - y_pred)))

        # Root Mean Squared Error
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

        # R² Score
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Mean Absolute Percentage Error
        mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100)

        return {
            "mae": mae,
            "rmse": rmse,
            "r2_score": float(r2),
            "mape": mape
        }

    def _mcnemar_test(
        self,
        predictions1: List[Any],
        predictions2: List[Any],
        ground_truth: List[Any]
    ) -> Dict[str, Any]:
        """
        Perform McNemar's test for classification models.

        Tests if there's a statistically significant difference between two models.
        """
        y_true = np.array(ground_truth)
        y_pred1 = np.array(predictions1)
        y_pred2 = np.array(predictions2)

        # Contingency table
        correct1 = (y_pred1 == y_true)
        correct2 = (y_pred2 == y_true)

        # Count disagreements
        model1_correct_model2_wrong = np.sum(correct1 & ~correct2)
        model1_wrong_model2_correct = np.sum(~correct1 & correct2)

        # McNemar's test statistic
        if model1_correct_model2_wrong + model1_wrong_model2_correct == 0:
            return {
                "test_name": "McNemar's Test",
                "statistic": 0.0,
                "p_value": 1.0,
                "significant": False,
                "message": "Models perform identically"
            }

        # Chi-square test with continuity correction
        statistic = ((abs(model1_correct_model2_wrong - model1_wrong_model2_correct) - 1) ** 2 /
                    (model1_correct_model2_wrong + model1_wrong_model2_correct))

        p_value = 1 - stats.chi2.cdf(statistic, df=1)

        return {
            "test_name": "McNemar's Test",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": bool(p_value < self.significance_level),
            "contingency": {
                "model1_correct_model2_wrong": int(model1_correct_model2_wrong),
                "model1_wrong_model2_correct": int(model1_wrong_model2_correct)
            },
            "message": (
                "Candidate model is significantly different"
                if p_value < self.significance_level
                else "No significant difference between models"
            )
        }

    def _paired_t_test(
        self,
        predictions1: List[Any],
        predictions2: List[Any],
        ground_truth: List[Any]
    ) -> Dict[str, Any]:
        """
        Perform paired t-test for regression models.

        Tests if there's a statistically significant difference in errors.
        """
        y_true = np.array([float(y) for y in ground_truth])
        y_pred1 = np.array([float(y) for y in predictions1])
        y_pred2 = np.array([float(y) for y in predictions2])

        # Calculate absolute errors
        errors1 = np.abs(y_true - y_pred1)
        errors2 = np.abs(y_true - y_pred2)

        # Paired t-test
        statistic, p_value = stats.ttest_rel(errors1, errors2)

        mean_error_diff = float(np.mean(errors1 - errors2))

        return {
            "test_name": "Paired t-test",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": bool(p_value < self.significance_level),
            "mean_error_difference": mean_error_diff,
            "message": (
                f"Candidate model has {'lower' if mean_error_diff > 0 else 'higher'} error "
                f"({'significant' if p_value < self.significance_level else 'not significant'})"
            )
        }

    def _generate_recommendation(self, comparison: Dict[str, Any]) -> str:
        """Generate deployment recommendation based on comparison results."""
        recommendations = []

        # Check agreement rate
        agreement_rate = comparison["agreement_metrics"].get("exact_agreement_rate", 0)
        if agreement_rate < 0.80:
            recommendations.append(
                f"⚠️ Low agreement rate ({agreement_rate:.1%}). Models make different predictions."
            )

        # Check performance if ground truth available
        if comparison["candidate_metrics"]:
            model_type = comparison["model_type"]

            if model_type == "classification":
                prod_acc = comparison["production_metrics"].get("accuracy", 0)
                cand_acc = comparison["candidate_metrics"].get("accuracy", 0)
                accuracy_improvement = cand_acc - prod_acc

                if accuracy_improvement > 0.02:  # 2% improvement
                    recommendations.append(
                        f"✅ Candidate model shows {accuracy_improvement:.1%} accuracy improvement. Recommend deployment."
                    )
                elif accuracy_improvement < -0.02:  # 2% degradation
                    recommendations.append(
                        f"❌ Candidate model shows {abs(accuracy_improvement):.1%} accuracy degradation. Do not deploy."
                    )
                else:
                    recommendations.append(
                        f"⚠️ Similar performance ({accuracy_improvement:+.1%}). Consider other factors (latency, cost)."
                    )

            elif model_type == "regression":
                prod_rmse = comparison["production_metrics"].get("rmse", float('inf'))
                cand_rmse = comparison["candidate_metrics"].get("rmse", float('inf'))
                rmse_improvement = (prod_rmse - cand_rmse) / prod_rmse

                if rmse_improvement > 0.05:  # 5% improvement
                    recommendations.append(
                        f"✅ Candidate model shows {rmse_improvement:.1%} RMSE improvement. Recommend deployment."
                    )
                elif rmse_improvement < -0.05:  # 5% degradation
                    recommendations.append(
                        f"❌ Candidate model shows {abs(rmse_improvement):.1%} RMSE degradation. Do not deploy."
                    )
                else:
                    recommendations.append(
                        f"⚠️ Similar performance ({rmse_improvement:+.1%}). Consider other factors."
                    )

        # Check statistical significance
        if comparison["statistical_tests"]:
            if comparison["statistical_tests"]["significant"]:
                recommendations.append(
                    f"📊 Statistical test shows significant difference (p={comparison['statistical_tests']['p_value']:.4f})"
                )
            else:
                recommendations.append(
                    f"📊 No statistically significant difference detected"
                )

        return " ".join(recommendations) if recommendations else "Insufficient data for recommendation"


# ============================================================================
# Testing
# ============================================================================

def test_prediction_comparator():
    """Test prediction comparator with mock data."""
    logger.info("Testing Prediction Comparator...")

    comparator = PredictionComparator()

    # Test 1: Classification comparison with ground truth
    print("\n=== Test 1: Classification Comparison ===")

    # Simulate 100 predictions
    np.random.seed(42)
    ground_truth = np.random.randint(0, 2, 100).tolist()

    # Production model: 85% accuracy
    production_preds = []
    for gt in ground_truth:
        pred = gt if np.random.random() < 0.85 else 1 - gt
        production_preds.append({"prediction": pred})

    # Candidate model: 88% accuracy
    candidate_preds = []
    for gt in ground_truth:
        pred = gt if np.random.random() < 0.88 else 1 - gt
        candidate_preds.append({"prediction": pred})

    comparison = comparator.compare_predictions(
        production_predictions=production_preds,
        candidate_predictions=candidate_preds,
        ground_truth=ground_truth,
        model_type="classification"
    )

    print(json.dumps(comparison, indent=2))

    # Test 2: Regression comparison
    print("\n=== Test 2: Regression Comparison ===")

    # Ground truth
    ground_truth_reg = np.linspace(0, 100, 100).tolist()

    # Production model: mean error ~5
    production_preds_reg = [
        {"prediction": gt + np.random.normal(0, 5)}
        for gt in ground_truth_reg
    ]

    # Candidate model: mean error ~3
    candidate_preds_reg = [
        {"prediction": gt + np.random.normal(0, 3)}
        for gt in ground_truth_reg
    ]

    comparison_reg = comparator.compare_predictions(
        production_predictions=production_preds_reg,
        candidate_predictions=candidate_preds_reg,
        ground_truth=ground_truth_reg,
        model_type="regression"
    )

    print(json.dumps(comparison_reg, indent=2))


if __name__ == "__main__":
    test_prediction_comparator()
