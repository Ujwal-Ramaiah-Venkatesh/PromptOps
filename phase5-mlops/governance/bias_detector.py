"""
Bias Detector for PromptOps
============================

Detects and quantifies bias in ML models using fairness metrics.
Implements metrics from Fairlearn: demographic parity, equalized odds, etc.

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Union
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Bias Detector
# ============================================================================

class BiasDetector:
    """
    Detects bias in ML model predictions using fairness metrics.

    Fairness Metrics:
    - Demographic Parity: P(ŷ=1|A=a) ≈ P(ŷ=1|A=b)
    - Equalized Odds: TPR and FPR equal across groups
    - Equal Opportunity: TPR equal across groups
    - Predictive Parity: PPV equal across groups

    Protected Attributes: gender, race, age_group, etc.
    """

    def __init__(self):
        """Initialize Bias Detector."""
        self.fairness_thresholds = {
            "demographic_parity": 0.80,  # Ratio should be >= 0.80
            "equalized_odds_tpr": 0.80,
            "equalized_odds_fpr": 1.25,  # Ratio should be <= 1.25
            "equal_opportunity": 0.80,
            "predictive_parity": 0.80
        }

    def detect_bias(
        self,
        model_name: str,
        model_version: str,
        predictions: List[int],
        true_labels: List[int],
        protected_attributes: Dict[str, List[str]],
        positive_outcome: int = 1
    ) -> Dict[str, Any]:
        """
        Comprehensive bias detection across all fairness metrics.

        Args:
            model_name: Model name
            model_version: Model version
            predictions: Model predictions (0/1)
            true_labels: Ground truth labels (0/1)
            protected_attributes: Dict of protected attributes
                                  {"gender": ["M", "F", "M", ...], "age_group": [...]}
            positive_outcome: Positive class label (default: 1)

        Returns:
            Bias detection report
        """
        logger.info(f"Detecting bias for {model_name}:{model_version}")

        report = {
            "model": f"{model_name}:{model_version}",
            "num_samples": len(predictions),
            "protected_attributes": list(protected_attributes.keys()),
            "fairness_metrics": {},
            "bias_detected": False,
            "violations": []
        }

        # Check each protected attribute
        for attr_name, attr_values in protected_attributes.items():
            logger.info(f"Checking bias for attribute: {attr_name}")

            # Get unique groups
            groups = list(set(attr_values))

            if len(groups) < 2:
                logger.warning(f"Attribute {attr_name} has fewer than 2 groups, skipping")
                continue

            # Compute metrics for this attribute
            metrics = self._compute_fairness_metrics(
                predictions=predictions,
                true_labels=true_labels,
                attribute_values=attr_values,
                groups=groups,
                positive_outcome=positive_outcome
            )

            # Check for violations
            violations = self._check_fairness_violations(attr_name, groups, metrics)

            report["fairness_metrics"][attr_name] = {
                "groups": groups,
                "metrics": metrics,
                "violations": violations
            }

            if violations:
                report["bias_detected"] = True
                report["violations"].extend(violations)

        return report

    def _compute_fairness_metrics(
        self,
        predictions: List[int],
        true_labels: List[int],
        attribute_values: List[str],
        groups: List[str],
        positive_outcome: int
    ) -> Dict[str, Any]:
        """Compute fairness metrics for a protected attribute."""

        # Group data by attribute value
        group_data = defaultdict(lambda: {"predictions": [], "labels": []})

        for pred, label, attr_val in zip(predictions, true_labels, attribute_values):
            group_data[attr_val]["predictions"].append(pred)
            group_data[attr_val]["labels"].append(label)

        # Compute metrics for each group
        group_metrics = {}

        for group in groups:
            preds = group_data[group]["predictions"]
            labels = group_data[group]["labels"]

            if not preds:
                continue

            # Basic metrics
            positive_rate = sum(1 for p in preds if p == positive_outcome) / len(preds)

            # Confusion matrix
            tp = sum(1 for p, l in zip(preds, labels) if p == positive_outcome and l == positive_outcome)
            fp = sum(1 for p, l in zip(preds, labels) if p == positive_outcome and l != positive_outcome)
            tn = sum(1 for p, l in zip(preds, labels) if p != positive_outcome and l != positive_outcome)
            fn = sum(1 for p, l in zip(preds, labels) if p != positive_outcome and l == positive_outcome)

            # Rates
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0  # True Positive Rate / Recall
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # False Positive Rate
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0  # Positive Predictive Value / Precision

            group_metrics[group] = {
                "sample_size": len(preds),
                "positive_rate": round(positive_rate, 4),
                "true_positive_rate": round(tpr, 4),
                "false_positive_rate": round(fpr, 4),
                "positive_predictive_value": round(ppv, 4),
                "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn}
            }

        # Compute pairwise ratios
        pairwise_ratios = self._compute_pairwise_ratios(group_metrics, groups)

        return {
            "by_group": group_metrics,
            "pairwise_ratios": pairwise_ratios
        }

    def _compute_pairwise_ratios(
        self,
        group_metrics: Dict[str, Dict[str, float]],
        groups: List[str]
    ) -> Dict[str, Any]:
        """Compute pairwise fairness ratios between groups."""

        ratios = {
            "demographic_parity": [],
            "equalized_odds_tpr": [],
            "equalized_odds_fpr": [],
            "equal_opportunity": [],
            "predictive_parity": []
        }

        for i, group1 in enumerate(groups):
            for group2 in groups[i+1:]:
                if group1 not in group_metrics or group2 not in group_metrics:
                    continue

                metrics1 = group_metrics[group1]
                metrics2 = group_metrics[group2]

                # Demographic Parity (positive rate ratio)
                ratio_dp = self._safe_ratio(metrics1["positive_rate"], metrics2["positive_rate"])
                ratios["demographic_parity"].append({
                    "groups": f"{group1} vs {group2}",
                    "ratio": ratio_dp
                })

                # Equalized Odds - TPR
                ratio_tpr = self._safe_ratio(metrics1["true_positive_rate"], metrics2["true_positive_rate"])
                ratios["equalized_odds_tpr"].append({
                    "groups": f"{group1} vs {group2}",
                    "ratio": ratio_tpr
                })

                # Equalized Odds - FPR
                ratio_fpr = self._safe_ratio(metrics1["false_positive_rate"], metrics2["false_positive_rate"])
                ratios["equalized_odds_fpr"].append({
                    "groups": f"{group1} vs {group2}",
                    "ratio": ratio_fpr
                })

                # Equal Opportunity (same as TPR)
                ratios["equal_opportunity"].append({
                    "groups": f"{group1} vs {group2}",
                    "ratio": ratio_tpr
                })

                # Predictive Parity (PPV ratio)
                ratio_ppv = self._safe_ratio(metrics1["positive_predictive_value"], metrics2["positive_predictive_value"])
                ratios["predictive_parity"].append({
                    "groups": f"{group1} vs {group2}",
                    "ratio": ratio_ppv
                })

        return ratios

    def _safe_ratio(self, value1: float, value2: float) -> float:
        """Compute ratio safely, handling zeros."""
        if value2 == 0:
            return 1.0 if value1 == 0 else float('inf')

        ratio = value1 / value2
        # Return min(ratio, 1/ratio) to get ratio in [0, 1]
        normalized_ratio = min(ratio, 1.0 / ratio) if ratio > 0 else 0
        return round(normalized_ratio, 4)

    def _check_fairness_violations(
        self,
        attr_name: str,
        groups: List[str],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for fairness metric violations."""

        violations = []

        pairwise = metrics["pairwise_ratios"]

        # Check demographic parity
        for comparison in pairwise["demographic_parity"]:
            if comparison["ratio"] < self.fairness_thresholds["demographic_parity"]:
                violations.append({
                    "attribute": attr_name,
                    "metric": "demographic_parity",
                    "groups": comparison["groups"],
                    "ratio": comparison["ratio"],
                    "threshold": self.fairness_thresholds["demographic_parity"],
                    "severity": "high" if comparison["ratio"] < 0.70 else "medium"
                })

        # Check equalized odds (TPR)
        for comparison in pairwise["equalized_odds_tpr"]:
            if comparison["ratio"] < self.fairness_thresholds["equalized_odds_tpr"]:
                violations.append({
                    "attribute": attr_name,
                    "metric": "equalized_odds_tpr",
                    "groups": comparison["groups"],
                    "ratio": comparison["ratio"],
                    "threshold": self.fairness_thresholds["equalized_odds_tpr"],
                    "severity": "high" if comparison["ratio"] < 0.70 else "medium"
                })

        # Check equal opportunity
        for comparison in pairwise["equal_opportunity"]:
            if comparison["ratio"] < self.fairness_thresholds["equal_opportunity"]:
                violations.append({
                    "attribute": attr_name,
                    "metric": "equal_opportunity",
                    "groups": comparison["groups"],
                    "ratio": comparison["ratio"],
                    "threshold": self.fairness_thresholds["equal_opportunity"],
                    "severity": "high" if comparison["ratio"] < 0.70 else "medium"
                })

        return violations

    def get_bias_summary(self, bias_report: Dict[str, Any]) -> str:
        """Generate human-readable bias summary."""

        if not bias_report["bias_detected"]:
            return "No significant bias detected. Model meets fairness thresholds across all protected attributes."

        lines = ["⚠️ Bias detected in the following areas:\n"]

        violations_by_severity = defaultdict(list)
        for violation in bias_report["violations"]:
            violations_by_severity[violation["severity"]].append(violation)

        if violations_by_severity["high"]:
            lines.append("HIGH SEVERITY:")
            for v in violations_by_severity["high"]:
                lines.append(
                    f"  • {v['metric']} for {v['attribute']} ({v['groups']}): "
                    f"ratio {v['ratio']:.2f} < threshold {v['threshold']:.2f}"
                )
            lines.append("")

        if violations_by_severity["medium"]:
            lines.append("MEDIUM SEVERITY:")
            for v in violations_by_severity["medium"]:
                lines.append(
                    f"  • {v['metric']} for {v['attribute']} ({v['groups']}): "
                    f"ratio {v['ratio']:.2f} < threshold {v['threshold']:.2f}"
                )

        lines.append("\nRecommendations:")
        lines.append("  1. Re-train model with balanced samples across groups")
        lines.append("  2. Apply fairness constraints during training")
        lines.append("  3. Use post-processing fairness adjustments")

        return "\n".join(lines)


# ============================================================================
# Testing
# ============================================================================

def test_bias_detector():
    """Test bias detector."""
    logger.info("Testing Bias Detector...")

    detector = BiasDetector()

    # Generate test data
    np.random.seed(42)

    # Scenario: Biased loan approval model
    num_samples = 200

    # Protected attribute: gender
    genders = ["Male"] * 120 + ["Female"] * 80

    # Biased predictions (higher approval rate for males)
    predictions = []
    true_labels = []

    for gender in genders:
        if gender == "Male":
            # 70% approval for males
            pred = 1 if np.random.random() < 0.70 else 0
            label = 1 if np.random.random() < 0.65 else 0
        else:
            # 45% approval for females (biased)
            pred = 1 if np.random.random() < 0.45 else 0
            label = 1 if np.random.random() < 0.62 else 0

        predictions.append(pred)
        true_labels.append(label)

    # Test 1: Detect bias
    print("\n=== Test 1: Detect Bias (Gender) ===")
    bias_report = detector.detect_bias(
        model_name="loan-approval",
        model_version="v1",
        predictions=predictions,
        true_labels=true_labels,
        protected_attributes={"gender": genders}
    )
    print(json.dumps(bias_report, indent=2))

    # Test 2: Bias summary
    print("\n=== Test 2: Bias Summary ===")
    summary = detector.get_bias_summary(bias_report)
    print(summary)

    # Test 3: Multiple protected attributes
    print("\n=== Test 3: Multiple Protected Attributes ===")
    age_groups = ["18-30"] * 60 + ["31-50"] * 80 + ["51+"] * 60

    multi_attr_report = detector.detect_bias(
        model_name="loan-approval",
        model_version="v1",
        predictions=predictions,
        true_labels=true_labels,
        protected_attributes={
            "gender": genders,
            "age_group": age_groups
        }
    )
    print(f"Bias detected: {multi_attr_report['bias_detected']}")
    print(f"Total violations: {len(multi_attr_report['violations'])}")


if __name__ == "__main__":
    test_bias_detector()
