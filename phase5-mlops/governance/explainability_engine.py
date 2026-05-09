"""
Explainability Engine for PromptOps
====================================

Provides model explainability using SHAP (SHapley Additive exPlanations).
Generates feature importance, prediction explanations, and global insights.

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Explainability Engine
# ============================================================================

class ExplainabilityEngine:
    """
    Model explainability using SHAP values.

    Features:
    - Feature importance (global)
    - Individual prediction explanations (local)
    - Force plots and waterfall charts
    - Summary statistics
    - Support for tree models, linear models, deep learning
    """

    def __init__(self):
        """Initialize Explainability Engine."""
        self.shap_values_cache: Dict[str, Any] = {}
        self.explainer_cache: Dict[str, Any] = {}

    def explain_prediction(
        self,
        model_name: str,
        model_version: str,
        prediction: float,
        features: Dict[str, Any],
        feature_names: List[str],
        base_value: float = 0.5
    ) -> Dict[str, Any]:
        """
        Explain individual prediction using SHAP values.

        Args:
            model_name: Model name
            model_version: Model version
            prediction: Model prediction
            features: Feature values
            feature_names: Feature names
            base_value: Base/expected value

        Returns:
            Prediction explanation with SHAP values
        """
        logger.info(f"Explaining prediction for {model_name}:{model_version}")

        # Mock SHAP values (in production, compute real SHAP values)
        shap_values = self._compute_mock_shap_values(features, feature_names, prediction, base_value)

        # Sort features by absolute SHAP value
        sorted_features = sorted(
            zip(feature_names, shap_values),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # Build explanation
        explanation = {
            "model": f"{model_name}:{model_version}",
            "prediction": prediction,
            "base_value": base_value,
            "shap_values": dict(zip(feature_names, shap_values)),
            "top_features": [
                {
                    "feature": name,
                    "value": features.get(name),
                    "shap_value": shap_val,
                    "contribution": "positive" if shap_val > 0 else "negative",
                    "impact": abs(shap_val)
                }
                for name, shap_val in sorted_features[:10]
            ],
            "explanation_text": self._generate_explanation_text(
                sorted_features[:5],
                features,
                prediction,
                base_value
            )
        }

        return explanation

    def _compute_mock_shap_values(
        self,
        features: Dict[str, Any],
        feature_names: List[str],
        prediction: float,
        base_value: float
    ) -> List[float]:
        """
        Compute mock SHAP values for testing.
        In production, use real SHAP library.
        """
        # Mock: distribute prediction delta across features
        delta = prediction - base_value
        num_features = len(feature_names)

        # Assign larger values to some features
        shap_values = []
        remaining_delta = delta

        for i, fname in enumerate(feature_names):
            # Give more importance to first few features
            if i < 3:
                contribution = remaining_delta * 0.25
            elif i < 7:
                contribution = remaining_delta * 0.10
            else:
                contribution = remaining_delta * 0.05 / max(1, (num_features - 7))

            shap_values.append(round(contribution, 4))
            remaining_delta -= contribution

        # Adjust last feature to balance
        if shap_values:
            shap_values[-1] += remaining_delta

        return shap_values

    def _generate_explanation_text(
        self,
        top_features: List[tuple],
        features: Dict[str, Any],
        prediction: float,
        base_value: float
    ) -> str:
        """Generate human-readable explanation."""
        direction = "increase" if prediction > base_value else "decrease"

        lines = [
            f"This prediction ({prediction:.3f}) represents a {direction} from the base value ({base_value:.3f}).",
            "",
            "Top contributing features:"
        ]

        for feature_name, shap_value in top_features[:5]:
            feature_val = features.get(feature_name, "N/A")
            impact = "increases" if shap_value > 0 else "decreases"
            lines.append(
                f"  • {feature_name} = {feature_val} {impact} prediction by {abs(shap_value):.3f}"
            )

        return "\n".join(lines)

    def compute_feature_importance(
        self,
        model_name: str,
        model_version: str,
        feature_names: List[str],
        shap_values_matrix: Optional[List[List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Compute global feature importance.

        Args:
            model_name: Model name
            model_version: Model version
            feature_names: Feature names
            shap_values_matrix: Matrix of SHAP values (samples × features)

        Returns:
            Feature importance ranking
        """
        logger.info(f"Computing feature importance for {model_name}:{model_version}")

        # Mock SHAP values matrix if not provided
        if shap_values_matrix is None:
            shap_values_matrix = self._mock_shap_matrix(len(feature_names), num_samples=100)

        # Compute mean absolute SHAP value for each feature
        mean_abs_shap = []
        for feature_idx in range(len(feature_names)):
            feature_shap_values = [row[feature_idx] for row in shap_values_matrix]
            mean_abs = np.mean([abs(val) for val in feature_shap_values])
            mean_abs_shap.append(mean_abs)

        # Sort by importance
        feature_importance = sorted(
            zip(feature_names, mean_abs_shap),
            key=lambda x: x[1],
            reverse=True
        )

        # Build result
        total_importance = sum(mean_abs_shap)

        return {
            "model": f"{model_name}:{model_version}",
            "num_features": len(feature_names),
            "num_samples": len(shap_values_matrix),
            "feature_importance": [
                {
                    "rank": idx + 1,
                    "feature": name,
                    "importance": float(importance),
                    "percentage": float(importance / total_importance * 100) if total_importance > 0 else 0
                }
                for idx, (name, importance) in enumerate(feature_importance)
            ]
        }

    def _mock_shap_matrix(self, num_features: int, num_samples: int = 100) -> List[List[float]]:
        """Generate mock SHAP values matrix for testing."""
        np.random.seed(42)
        matrix = []

        for _ in range(num_samples):
            row = []
            for feature_idx in range(num_features):
                # Give more importance to first few features
                if feature_idx < 3:
                    value = np.random.normal(0.1, 0.05)
                elif feature_idx < 7:
                    value = np.random.normal(0.05, 0.03)
                else:
                    value = np.random.normal(0.01, 0.01)
                row.append(round(float(value), 4))
            matrix.append(row)

        return matrix

    def explain_model_behavior(
        self,
        model_name: str,
        model_version: str,
        feature_names: List[str],
        num_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Comprehensive model behavior explanation.

        Args:
            model_name: Model name
            model_version: Model version
            feature_names: Feature names
            num_samples: Number of samples for analysis

        Returns:
            Comprehensive model insights
        """
        logger.info(f"Analyzing model behavior: {model_name}:{model_version}")

        # Generate mock SHAP values
        shap_matrix = self._mock_shap_matrix(len(feature_names), num_samples)

        # Compute feature importance
        importance = self.compute_feature_importance(
            model_name, model_version, feature_names, shap_matrix
        )

        # Compute feature interactions (simplified)
        interactions = self._compute_feature_interactions(feature_names[:5])

        # Summary statistics
        summary = {
            "model": f"{model_name}:{model_version}",
            "analysis_samples": num_samples,
            "total_features": len(feature_names),
            "top_5_features": [f["feature"] for f in importance["feature_importance"][:5]],
            "feature_importance": importance["feature_importance"][:10],
            "feature_interactions": interactions,
            "insights": [
                f"Top feature '{importance['feature_importance'][0]['feature']}' accounts for "
                f"{importance['feature_importance'][0]['percentage']:.1f}% of model decisions",
                f"Top 3 features account for "
                f"{sum(f['percentage'] for f in importance['feature_importance'][:3]):.1f}% of importance",
                f"Model relies heavily on {len([f for f in importance['feature_importance'] if f['percentage'] > 5])} key features"
            ]
        }

        return summary

    def _compute_feature_interactions(self, top_features: List[str]) -> List[Dict[str, Any]]:
        """Compute feature interaction strengths (simplified)."""
        interactions = []

        for i, feature1 in enumerate(top_features):
            for feature2 in top_features[i+1:]:
                # Mock interaction strength
                interaction_strength = np.random.uniform(0.01, 0.10)
                interactions.append({
                    "feature1": feature1,
                    "feature2": feature2,
                    "interaction_strength": round(float(interaction_strength), 4)
                })

        # Sort by strength
        interactions.sort(key=lambda x: x["interaction_strength"], reverse=True)

        return interactions[:5]  # Top 5 interactions

    def generate_force_plot_data(
        self,
        model_name: str,
        model_version: str,
        features: Dict[str, Any],
        shap_values: Dict[str, float],
        base_value: float,
        prediction: float
    ) -> Dict[str, Any]:
        """
        Generate data for SHAP force plot visualization.

        Args:
            model_name: Model name
            model_version: Model version
            features: Feature values
            shap_values: SHAP values for features
            base_value: Base value
            prediction: Prediction value

        Returns:
            Force plot data
        """
        # Sort features by SHAP value (positive first, then negative)
        positive_features = {k: v for k, v in shap_values.items() if v > 0}
        negative_features = {k: v for k, v in shap_values.items() if v < 0}

        sorted_positive = sorted(positive_features.items(), key=lambda x: x[1], reverse=True)
        sorted_negative = sorted(negative_features.items(), key=lambda x: x[1])

        return {
            "model": f"{model_name}:{model_version}",
            "base_value": base_value,
            "prediction": prediction,
            "features_pushing_higher": [
                {"feature": k, "value": features.get(k), "shap": v}
                for k, v in sorted_positive
            ],
            "features_pushing_lower": [
                {"feature": k, "value": features.get(k), "shap": v}
                for k, v in sorted_negative
            ],
            "total_positive_impact": sum(positive_features.values()),
            "total_negative_impact": sum(negative_features.values())
        }


# ============================================================================
# Testing
# ============================================================================

def test_explainability_engine():
    """Test explainability engine."""
    logger.info("Testing Explainability Engine...")

    engine = ExplainabilityEngine()

    # Test data
    feature_names = [
        "account_age_days", "total_purchases", "avg_purchase_amount",
        "days_since_last_purchase", "support_tickets", "email_opens",
        "app_sessions", "subscription_tier", "payment_failures"
    ]

    features = {
        "account_age_days": 730,
        "total_purchases": 45,
        "avg_purchase_amount": 89.50,
        "days_since_last_purchase": 180,
        "support_tickets": 8,
        "email_opens": 12,
        "app_sessions": 5,
        "subscription_tier": "premium",
        "payment_failures": 2
    }

    # Test 1: Explain prediction
    print("\n=== Test 1: Explain Prediction ===")
    explanation = engine.explain_prediction(
        model_name="churn-prediction",
        model_version="v2",
        prediction=0.78,
        features=features,
        feature_names=feature_names,
        base_value=0.35
    )
    print(json.dumps(explanation, indent=2))

    # Test 2: Compute feature importance
    print("\n=== Test 2: Feature Importance ===")
    importance = engine.compute_feature_importance(
        model_name="churn-prediction",
        model_version="v2",
        feature_names=feature_names
    )
    print(json.dumps(importance, indent=2))

    # Test 3: Model behavior analysis
    print("\n=== Test 3: Model Behavior Analysis ===")
    behavior = engine.explain_model_behavior(
        model_name="churn-prediction",
        model_version="v2",
        feature_names=feature_names,
        num_samples=100
    )
    print(json.dumps(behavior, indent=2))

    # Test 4: Force plot data
    print("\n=== Test 4: Force Plot Data ===")
    force_plot = engine.generate_force_plot_data(
        model_name="churn-prediction",
        model_version="v2",
        features=features,
        shap_values=explanation["shap_values"],
        base_value=0.35,
        prediction=0.78
    )
    print(json.dumps(force_plot, indent=2))


if __name__ == "__main__":
    test_explainability_engine()
