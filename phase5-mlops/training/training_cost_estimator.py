"""
Training Cost Estimator for PromptOps
=====================================

Estimates SageMaker training costs using AWS Pricing API.
Helps PMs make informed decisions about model training budgets.

Author: ML Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Training Cost Estimator
# ============================================================================

class TrainingCostEstimator:
    """
    Estimates SageMaker training costs based on instance type and duration.
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize Training Cost Estimator.

        Args:
            region: AWS region for pricing
        """
        self.region = region

        # SageMaker instance pricing (USD per hour) - us-east-1
        # Source: AWS SageMaker Pricing (as of May 2026)
        self.instance_pricing = {
            # General Purpose
            "ml.m5.large": 0.134,
            "ml.m5.xlarge": 0.269,
            "ml.m5.2xlarge": 0.538,
            "ml.m5.4xlarge": 1.075,
            "ml.m5.12xlarge": 3.226,
            "ml.m5.24xlarge": 6.451,

            # Compute Optimized
            "ml.c5.xlarge": 0.238,
            "ml.c5.2xlarge": 0.476,
            "ml.c5.4xlarge": 0.952,
            "ml.c5.9xlarge": 2.142,
            "ml.c5.18xlarge": 4.284,

            # Memory Optimized
            "ml.r5.large": 0.156,
            "ml.r5.xlarge": 0.312,
            "ml.r5.2xlarge": 0.624,
            "ml.r5.4xlarge": 1.248,
            "ml.r5.12xlarge": 3.744,

            # GPU Instances
            "ml.p2.xlarge": 1.26,
            "ml.p2.8xlarge": 10.08,
            "ml.p2.16xlarge": 20.16,
            "ml.p3.2xlarge": 4.284,
            "ml.p3.8xlarge": 17.136,
            "ml.p3.16xlarge": 34.272,
            "ml.g4dn.xlarge": 0.736,
            "ml.g4dn.2xlarge": 1.052,
            "ml.g4dn.4xlarge": 1.686,
            "ml.g4dn.8xlarge": 3.045,
            "ml.g4dn.12xlarge": 5.435,
            "ml.g4dn.16xlarge": 6.090
        }

        # Storage pricing (USD per GB-month)
        self.storage_price_per_gb = 0.10  # EBS storage

    def estimate_training_cost(
        self,
        instance_type: str,
        instance_count: int,
        training_duration_hours: float,
        storage_gb: int = 30
    ) -> Dict[str, Any]:
        """
        Estimate total training cost.

        Args:
            instance_type: SageMaker instance type
            instance_count: Number of instances
            training_duration_hours: Estimated training duration in hours
            storage_gb: Storage volume size in GB

        Returns:
            Cost breakdown and total estimate
        """
        logger.info(
            f"Estimating cost: {instance_type} x{instance_count} "
            f"for {training_duration_hours}h"
        )

        # Get instance price
        instance_price = self.instance_pricing.get(instance_type)
        if not instance_price:
            logger.warning(f"Unknown instance type: {instance_type}, using default")
            instance_price = 0.269  # Default to ml.m5.xlarge

        # Calculate compute cost
        compute_cost = instance_price * instance_count * training_duration_hours

        # Calculate storage cost (prorated for training duration)
        hours_per_month = 730
        storage_cost = (storage_gb * self.storage_price_per_gb *
                       training_duration_hours / hours_per_month * instance_count)

        # Total cost
        total_cost = compute_cost + storage_cost

        # Build cost breakdown
        cost_estimate = {
            "instance_type": instance_type,
            "instance_count": instance_count,
            "instance_price_per_hour": instance_price,
            "training_duration_hours": training_duration_hours,
            "storage_gb": storage_gb,
            "compute_cost_usd": round(compute_cost, 2),
            "storage_cost_usd": round(storage_cost, 2),
            "total_cost_usd": round(total_cost, 2),
            "cost_per_hour": round(total_cost / training_duration_hours, 2),
            "region": self.region,
            "estimated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Estimated total cost: ${cost_estimate['total_cost_usd']}")
        return cost_estimate

    def estimate_from_job_config(
        self,
        job_config: Dict[str, Any],
        estimated_duration_hours: float
    ) -> Dict[str, Any]:
        """
        Estimate cost from SageMaker job configuration.

        Args:
            job_config: SageMaker training job config
            estimated_duration_hours: Estimated training duration

        Returns:
            Cost estimate
        """
        resource_config = job_config.get("ResourceConfig", {})

        return self.estimate_training_cost(
            instance_type=resource_config.get("InstanceType", "ml.m5.xlarge"),
            instance_count=resource_config.get("InstanceCount", 1),
            training_duration_hours=estimated_duration_hours,
            storage_gb=resource_config.get("VolumeSizeInGB", 30)
        )

    def compare_instance_costs(
        self,
        instance_types: list,
        training_duration_hours: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compare costs across different instance types.

        Args:
            instance_types: List of instance types to compare
            training_duration_hours: Training duration for comparison

        Returns:
            Cost comparison
        """
        comparison = {
            "duration_hours": training_duration_hours,
            "instances": []
        }

        for instance_type in instance_types:
            estimate = self.estimate_training_cost(
                instance_type=instance_type,
                instance_count=1,
                training_duration_hours=training_duration_hours
            )
            comparison["instances"].append({
                "instance_type": instance_type,
                "total_cost_usd": estimate["total_cost_usd"],
                "compute_cost_usd": estimate["compute_cost_usd"]
            })

        # Sort by cost
        comparison["instances"] = sorted(
            comparison["instances"],
            key=lambda x: x["total_cost_usd"]
        )

        return comparison

    def recommend_instance_type(
        self,
        model_type: str,
        dataset_size_gb: float,
        budget_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Recommend instance type based on model type and dataset size.

        Args:
            model_type: Model type (classification, regression, nlp, time_series, cv)
            dataset_size_gb: Dataset size in GB
            budget_usd: Optional budget constraint

        Returns:
            Instance recommendation
        """
        logger.info(f"Recommending instance for {model_type}, {dataset_size_gb}GB dataset")

        # Define recommendations based on model type and data size
        recommendations = {
            "classification": self._recommend_classification_instance(dataset_size_gb),
            "regression": self._recommend_regression_instance(dataset_size_gb),
            "nlp": self._recommend_nlp_instance(dataset_size_gb),
            "time_series": self._recommend_timeseries_instance(dataset_size_gb),
            "computer_vision": self._recommend_cv_instance(dataset_size_gb)
        }

        recommended = recommendations.get(model_type, recommendations["classification"])

        # Estimate cost for recommendation
        estimated_duration = self._estimate_training_duration(model_type, dataset_size_gb)
        cost_estimate = self.estimate_training_cost(
            instance_type=recommended["instance_type"],
            instance_count=1,
            training_duration_hours=estimated_duration
        )

        # Check budget constraint
        within_budget = True
        if budget_usd is not None:
            within_budget = cost_estimate["total_cost_usd"] <= budget_usd

        return {
            "model_type": model_type,
            "dataset_size_gb": dataset_size_gb,
            "recommended_instance": recommended["instance_type"],
            "reasoning": recommended["reasoning"],
            "estimated_duration_hours": estimated_duration,
            "estimated_cost_usd": cost_estimate["total_cost_usd"],
            "budget_usd": budget_usd,
            "within_budget": within_budget
        }

    def _recommend_classification_instance(self, dataset_size_gb: float) -> Dict[str, str]:
        """Recommend instance for classification models."""
        if dataset_size_gb < 1:
            return {
                "instance_type": "ml.m5.large",
                "reasoning": "Small dataset (<1GB), general purpose instance sufficient"
            }
        elif dataset_size_gb < 10:
            return {
                "instance_type": "ml.m5.xlarge",
                "reasoning": "Medium dataset (1-10GB), balanced compute/memory"
            }
        else:
            return {
                "instance_type": "ml.m5.4xlarge",
                "reasoning": "Large dataset (>10GB), requires more compute"
            }

    def _recommend_regression_instance(self, dataset_size_gb: float) -> Dict[str, str]:
        """Recommend instance for regression models."""
        return self._recommend_classification_instance(dataset_size_gb)

    def _recommend_nlp_instance(self, dataset_size_gb: float) -> Dict[str, str]:
        """Recommend instance for NLP models."""
        if dataset_size_gb < 5:
            return {
                "instance_type": "ml.g4dn.xlarge",
                "reasoning": "Small NLP dataset, GPU-accelerated for transformer models"
            }
        else:
            return {
                "instance_type": "ml.g4dn.4xlarge",
                "reasoning": "Large NLP dataset, requires more GPU memory"
            }

    def _recommend_timeseries_instance(self, dataset_size_gb: float) -> Dict[str, str]:
        """Recommend instance for time series models."""
        if dataset_size_gb < 5:
            return {
                "instance_type": "ml.c5.2xlarge",
                "reasoning": "Time series with compute optimization"
            }
        else:
            return {
                "instance_type": "ml.c5.4xlarge",
                "reasoning": "Large time series, needs compute power"
            }

    def _recommend_cv_instance(self, dataset_size_gb: float) -> Dict[str, str]:
        """Recommend instance for computer vision models."""
        if dataset_size_gb < 10:
            return {
                "instance_type": "ml.p3.2xlarge",
                "reasoning": "CV training requires GPU, V100 for medium datasets"
            }
        else:
            return {
                "instance_type": "ml.p3.8xlarge",
                "reasoning": "Large CV dataset, multi-GPU training"
            }

    def _estimate_training_duration(self, model_type: str, dataset_size_gb: float) -> float:
        """
        Estimate training duration in hours.

        Args:
            model_type: Model type
            dataset_size_gb: Dataset size

        Returns:
            Estimated duration in hours
        """
        # Simple heuristic: 0.5 hours per GB for most models
        base_duration = dataset_size_gb * 0.5

        # Adjust by model type
        multipliers = {
            "classification": 1.0,
            "regression": 1.0,
            "nlp": 2.0,  # NLP takes longer
            "time_series": 1.5,
            "computer_vision": 3.0  # CV takes longest
        }

        multiplier = multipliers.get(model_type, 1.0)
        estimated = base_duration * multiplier

        # Minimum 0.5 hours, maximum 24 hours
        return max(0.5, min(estimated, 24.0))


# ============================================================================
# Testing
# ============================================================================

def test_cost_estimator():
    """Test training cost estimator."""
    logger.info("Testing Training Cost Estimator...")

    estimator = TrainingCostEstimator(region='us-east-1')

    # Test 1: Simple cost estimate
    print("\n=== Test 1: Simple Cost Estimate ===")
    cost = estimator.estimate_training_cost(
        instance_type="ml.m5.xlarge",
        instance_count=1,
        training_duration_hours=2.0
    )
    print(json.dumps(cost, indent=2))

    # Test 2: Instance comparison
    print("\n=== Test 2: Instance Comparison ===")
    comparison = estimator.compare_instance_costs(
        instance_types=["ml.m5.large", "ml.m5.xlarge", "ml.m5.2xlarge"],
        training_duration_hours=1.0
    )
    print(json.dumps(comparison, indent=2))

    # Test 3: Instance recommendation
    print("\n=== Test 3: Instance Recommendation ===")
    recommendation = estimator.recommend_instance_type(
        model_type="classification",
        dataset_size_gb=5.0,
        budget_usd=10.0
    )
    print(json.dumps(recommendation, indent=2))


if __name__ == "__main__":
    test_cost_estimator()
