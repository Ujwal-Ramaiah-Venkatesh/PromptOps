"""
Hyperparameter Tuner for PromptOps
==================================

Integrates SageMaker Automatic Model Tuning for hyperparameter optimization.
Supports multiple tuning strategies: Random, Bayesian, Hyperband.

Author: ML Engineer - Phase 5 Week 48-49
Date: 2026-05-08
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Hyperparameter Tuner
# ============================================================================

class HyperparameterTuner:
    """
    Manages hyperparameter tuning jobs using SageMaker.

    Supports:
    - Random search
    - Bayesian optimization
    - Hyperband
    - Multi-objective optimization
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize Hyperparameter Tuner.

        Args:
            region: AWS region for SageMaker
        """
        self.region = region
        self.sagemaker_client = None

        # Default tuning strategies
        self.strategies = {
            "random": "Random",
            "bayesian": "Bayesian",
            "hyperband": "Hyperband"
        }

        # Common hyperparameter ranges
        self.hyperparameter_ranges = {
            "xgboost": {
                "max_depth": {"type": "integer", "min": 3, "max": 10},
                "eta": {"type": "continuous", "min": 0.01, "max": 0.3},
                "gamma": {"type": "continuous", "min": 0.0, "max": 5.0},
                "min_child_weight": {"type": "integer", "min": 1, "max": 10},
                "subsample": {"type": "continuous", "min": 0.5, "max": 1.0},
                "alpha": {"type": "continuous", "min": 0.0, "max": 2.0},
                "lambda": {"type": "continuous", "min": 0.0, "max": 2.0}
            },
            "neural_network": {
                "learning_rate": {"type": "continuous", "min": 0.0001, "max": 0.1, "scaling": "logarithmic"},
                "batch_size": {"type": "categorical", "values": ["32", "64", "128", "256"]},
                "num_layers": {"type": "integer", "min": 2, "max": 5},
                "hidden_units": {"type": "integer", "min": 32, "max": 512},
                "dropout_rate": {"type": "continuous", "min": 0.0, "max": 0.5}
            },
            "random_forest": {
                "n_estimators": {"type": "integer", "min": 50, "max": 500},
                "max_depth": {"type": "integer", "min": 3, "max": 20},
                "min_samples_split": {"type": "integer", "min": 2, "max": 20},
                "min_samples_leaf": {"type": "integer", "min": 1, "max": 10}
            }
        }

        # Initialize AWS clients
        self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients."""
        try:
            self.sagemaker_client = boto3.client('sagemaker', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")

    def create_tuning_job(
        self,
        job_name: str,
        model_type: str,
        training_job_definition: Dict[str, Any],
        hyperparameter_ranges: Optional[Dict[str, Any]] = None,
        objective_metric: Optional[Dict[str, str]] = None,
        strategy: str = "bayesian",
        max_jobs: int = 20,
        max_parallel_jobs: int = 2,
        early_stopping: bool = True
    ) -> Dict[str, Any]:
        """
        Create hyperparameter tuning job.

        Args:
            job_name: Unique tuning job name
            model_type: Type of model (xgboost, neural_network, etc.)
            training_job_definition: Base training job configuration
            hyperparameter_ranges: Custom hyperparameter ranges
            objective_metric: Metric to optimize
            strategy: Tuning strategy (random, bayesian, hyperband)
            max_jobs: Maximum number of training jobs
            max_parallel_jobs: Maximum parallel training jobs
            early_stopping: Enable early stopping

        Returns:
            Tuning job information
        """
        logger.info(f"Creating tuning job: {job_name}")

        # Get hyperparameter ranges
        if not hyperparameter_ranges:
            hyperparameter_ranges = self._get_default_ranges(model_type)

        # Get objective metric
        if not objective_metric:
            objective_metric = self._get_default_objective(model_type)

        # Build tuning job config
        tuning_config = {
            "tuning_job_name": job_name,
            "strategy": self.strategies.get(strategy, "Bayesian"),
            "hyperparameter_ranges": hyperparameter_ranges,
            "objective_metric": objective_metric,
            "max_jobs": max_jobs,
            "max_parallel_jobs": max_parallel_jobs,
            "early_stopping": early_stopping,
            "training_job_definition": training_job_definition,
            "created_at": datetime.utcnow().isoformat()
        }

        # Submit to SageMaker
        if self.sagemaker_client:
            try:
                response = self._submit_tuning_job(tuning_config)
                tuning_config["status"] = "InProgress"
                tuning_config["tuning_job_arn"] = response.get("HyperParameterTuningJobArn")
            except Exception as e:
                logger.error(f"Failed to submit tuning job: {e}")
                tuning_config["status"] = "Failed"
                tuning_config["error"] = str(e)
        else:
            logger.warning("SageMaker client not available. Using mock mode.")
            tuning_config["status"] = "Mock"

        return tuning_config

    def _get_default_ranges(self, model_type: str) -> Dict[str, Any]:
        """Get default hyperparameter ranges for model type."""
        if model_type in self.hyperparameter_ranges:
            return self.hyperparameter_ranges[model_type]
        else:
            logger.warning(f"Unknown model type: {model_type}, using XGBoost defaults")
            return self.hyperparameter_ranges["xgboost"]

    def _get_default_objective(self, model_type: str) -> Dict[str, str]:
        """Get default objective metric for model type."""
        # Most models optimize for validation metric
        return {
            "Type": "Maximize",
            "MetricName": "validation:auc"  # Common for classification
        }

    def _submit_tuning_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Submit tuning job to SageMaker."""
        # Convert hyperparameter ranges to SageMaker format
        parameter_ranges = self._format_parameter_ranges(config["hyperparameter_ranges"])

        # Build SageMaker request
        request = {
            "HyperParameterTuningJobName": config["tuning_job_name"],
            "HyperParameterTuningJobConfig": {
                "Strategy": config["strategy"],
                "HyperParameterTuningJobObjective": config["objective_metric"],
                "ResourceLimits": {
                    "MaxNumberOfTrainingJobs": config["max_jobs"],
                    "MaxParallelTrainingJobs": config["max_parallel_jobs"]
                },
                "ParameterRanges": parameter_ranges
            },
            "TrainingJobDefinition": config["training_job_definition"]
        }

        # Add early stopping if enabled
        if config.get("early_stopping"):
            request["HyperParameterTuningJobConfig"]["TrainingJobEarlyStoppingType"] = "Auto"

        response = self.sagemaker_client.create_hyper_parameter_tuning_job(**request)
        return response

    def _format_parameter_ranges(
        self,
        ranges: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Format hyperparameter ranges for SageMaker."""
        formatted = {
            "IntegerParameterRanges": [],
            "ContinuousParameterRanges": [],
            "CategoricalParameterRanges": []
        }

        for param_name, param_config in ranges.items():
            param_type = param_config["type"]

            if param_type == "integer":
                formatted["IntegerParameterRanges"].append({
                    "Name": param_name,
                    "MinValue": str(param_config["min"]),
                    "MaxValue": str(param_config["max"]),
                    "ScalingType": param_config.get("scaling", "Auto")
                })
            elif param_type == "continuous":
                formatted["ContinuousParameterRanges"].append({
                    "Name": param_name,
                    "MinValue": str(param_config["min"]),
                    "MaxValue": str(param_config["max"]),
                    "ScalingType": param_config.get("scaling", "Auto")
                })
            elif param_type == "categorical":
                formatted["CategoricalParameterRanges"].append({
                    "Name": param_name,
                    "Values": param_config["values"]
                })

        return formatted

    def get_tuning_job_status(self, job_name: str) -> Dict[str, Any]:
        """
        Get status of tuning job.

        Args:
            job_name: Tuning job name

        Returns:
            Job status and results
        """
        if not self.sagemaker_client:
            return {
                "status": "Mock",
                "job_name": job_name,
                "message": "SageMaker client not available"
            }

        try:
            response = self.sagemaker_client.describe_hyper_parameter_tuning_job(
                HyperParameterTuningJobName=job_name
            )

            status_info = {
                "job_name": job_name,
                "status": response["HyperParameterTuningJobStatus"],
                "strategy": response["HyperParameterTuningJobConfig"]["Strategy"],
                "objective_metric": response["HyperParameterTuningJobConfig"]["HyperParameterTuningJobObjective"],
                "training_job_status_counters": response.get("TrainingJobStatusCounters", {}),
                "best_training_job": response.get("BestTrainingJob"),
                "created_at": response["CreationTime"].isoformat() if "CreationTime" in response else None,
                "modified_at": response.get("LastModifiedTime").isoformat() if response.get("LastModifiedTime") else None
            }

            return status_info

        except ClientError as e:
            logger.error(f"Failed to get tuning job status: {e}")
            return {
                "status": "Error",
                "job_name": job_name,
                "error": str(e)
            }

    def get_best_hyperparameters(self, job_name: str) -> Dict[str, Any]:
        """
        Get best hyperparameters from completed tuning job.

        Args:
            job_name: Tuning job name

        Returns:
            Best hyperparameters and objective metric value
        """
        status = self.get_tuning_job_status(job_name)

        if status["status"] != "Completed":
            return {
                "status": status["status"],
                "message": f"Tuning job not completed yet: {status['status']}"
            }

        best_job = status.get("best_training_job")
        if not best_job:
            return {
                "status": "Error",
                "message": "No best training job found"
            }

        return {
            "best_training_job_name": best_job["TrainingJobName"],
            "objective_value": best_job["FinalHyperParameterTuningJobObjectiveMetric"]["Value"],
            "objective_metric": best_job["FinalHyperParameterTuningJobObjectiveMetric"]["MetricName"],
            "hyperparameters": best_job["TunedHyperParameters"],
            "training_start_time": best_job.get("TrainingStartTime"),
            "training_end_time": best_job.get("TrainingEndTime")
        }

    def list_training_jobs(
        self,
        tuning_job_name: str,
        status_filter: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List training jobs from tuning job.

        Args:
            tuning_job_name: Tuning job name
            status_filter: Filter by status (Completed, InProgress, Failed)
            max_results: Maximum results to return

        Returns:
            List of training jobs
        """
        if not self.sagemaker_client:
            return []

        try:
            request = {
                "HyperParameterTuningJobName": tuning_job_name,
                "MaxResults": max_results,
                "SortBy": "FinalObjectiveMetricValue",
                "SortOrder": "Descending"
            }

            if status_filter:
                request["StatusEquals"] = status_filter

            response = self.sagemaker_client.list_training_jobs_for_hyper_parameter_tuning_job(**request)

            jobs = []
            for job_summary in response.get("TrainingJobSummaries", []):
                jobs.append({
                    "training_job_name": job_summary["TrainingJobName"],
                    "status": job_summary["TrainingJobStatus"],
                    "tuned_hyperparameters": job_summary.get("TunedHyperParameters", {}),
                    "objective_value": job_summary.get("FinalHyperParameterTuningJobObjectiveMetric", {}).get("Value"),
                    "training_start_time": job_summary.get("TrainingStartTime"),
                    "training_end_time": job_summary.get("TrainingEndTime")
                })

            return jobs

        except ClientError as e:
            logger.error(f"Failed to list training jobs: {e}")
            return []

    def analyze_tuning_results(self, job_name: str) -> Dict[str, Any]:
        """
        Analyze tuning job results and provide insights.

        Args:
            job_name: Tuning job name

        Returns:
            Analysis results with insights
        """
        logger.info(f"Analyzing tuning results for: {job_name}")

        # Get job status
        status = self.get_tuning_job_status(job_name)

        # Get all training jobs
        all_jobs = self.list_training_jobs(job_name, max_results=100)

        if not all_jobs:
            return {
                "status": "Error",
                "message": "No training jobs found"
            }

        # Calculate statistics
        completed_jobs = [j for j in all_jobs if j["status"] == "Completed"]
        objective_values = [j["objective_value"] for j in completed_jobs if j.get("objective_value")]

        analysis = {
            "tuning_job_name": job_name,
            "status": status["status"],
            "total_jobs": len(all_jobs),
            "completed_jobs": len(completed_jobs),
            "failed_jobs": len([j for j in all_jobs if j["status"] == "Failed"]),
            "best_hyperparameters": self.get_best_hyperparameters(job_name),
            "statistics": {}
        }

        if objective_values:
            import numpy as np
            analysis["statistics"] = {
                "best_objective": float(np.max(objective_values)),
                "worst_objective": float(np.min(objective_values)),
                "mean_objective": float(np.mean(objective_values)),
                "std_objective": float(np.std(objective_values)),
                "improvement_over_baseline": 0.0  # Would need baseline to calculate
            }

        # Hyperparameter importance (simplified)
        analysis["hyperparameter_insights"] = self._analyze_hyperparameter_importance(completed_jobs)

        return analysis

    def _analyze_hyperparameter_importance(
        self,
        jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze which hyperparameters had most impact."""
        # Simplified analysis - in production would use more sophisticated methods
        insights = {
            "note": "Simplified analysis - top and bottom performers",
            "top_performers": [],
            "bottom_performers": []
        }

        if len(jobs) >= 5:
            # Sort by objective value
            sorted_jobs = sorted(
                jobs,
                key=lambda x: x.get("objective_value", 0),
                reverse=True
            )

            insights["top_performers"] = [
                {
                    "job": j["training_job_name"],
                    "objective": j.get("objective_value"),
                    "hyperparameters": j.get("tuned_hyperparameters")
                }
                for j in sorted_jobs[:3]
            ]

            insights["bottom_performers"] = [
                {
                    "job": j["training_job_name"],
                    "objective": j.get("objective_value"),
                    "hyperparameters": j.get("tuned_hyperparameters")
                }
                for j in sorted_jobs[-3:]
            ]

        return insights

    def stop_tuning_job(self, job_name: str) -> Dict[str, Any]:
        """
        Stop running tuning job.

        Args:
            job_name: Tuning job name

        Returns:
            Stop result
        """
        if not self.sagemaker_client:
            return {
                "status": "Mock",
                "message": "SageMaker client not available"
            }

        try:
            self.sagemaker_client.stop_hyper_parameter_tuning_job(
                HyperParameterTuningJobName=job_name
            )

            return {
                "status": "Stopping",
                "job_name": job_name,
                "message": f"Tuning job {job_name} is being stopped"
            }

        except ClientError as e:
            logger.error(f"Failed to stop tuning job: {e}")
            return {
                "status": "Error",
                "job_name": job_name,
                "error": str(e)
            }


# ============================================================================
# Testing
# ============================================================================

def test_hyperparameter_tuner():
    """Test hyperparameter tuner."""
    logger.info("Testing Hyperparameter Tuner...")

    tuner = HyperparameterTuner(region='us-east-1')

    # Test 1: Get default hyperparameter ranges
    print("\n=== Test 1: Default Hyperparameter Ranges ===")
    ranges = tuner._get_default_ranges("xgboost")
    print(json.dumps(ranges, indent=2))

    # Test 2: Create mock tuning job configuration
    print("\n=== Test 2: Create Tuning Job Configuration ===")

    training_job_def = {
        "AlgorithmSpecification": {
            "TrainingImage": "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.5-1",
            "TrainingInputMode": "File"
        },
        "RoleArn": "arn:aws:iam::123456789012:role/SageMakerRole",
        "InputDataConfig": [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": "s3://test-bucket/data/train"
                    }
                }
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": "s3://test-bucket/output"
        },
        "ResourceConfig": {
            "InstanceType": "ml.m5.xlarge",
            "InstanceCount": 1,
            "VolumeSizeInGB": 30
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 3600
        }
    }

    tuning_job = tuner.create_tuning_job(
        job_name="test-tuning-churn-model",
        model_type="xgboost",
        training_job_definition=training_job_def,
        strategy="bayesian",
        max_jobs=20,
        max_parallel_jobs=2
    )

    print(json.dumps(tuning_job, indent=2, default=str))


if __name__ == "__main__":
    test_hyperparameter_tuner()
