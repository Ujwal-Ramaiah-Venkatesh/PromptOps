"""
AutoML Integrator for PromptOps
===============================

Integrates SageMaker Autopilot for automated machine learning.
Handles model selection, feature engineering, and hyperparameter tuning automatically.

Author: ML Engineer - Phase 5 Week 48-49
Date: 2026-05-08
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoMLIntegrator:
    """
    Integrates SageMaker Autopilot for automated ML.

    Features:
    - Automatic model selection
    - Automatic feature engineering
    - Automatic hyperparameter tuning
    - Model explainability (SHAP)
    """

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AutoML Integrator."""
        self.region = region
        self.sagemaker_client = None
        self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients."""
        try:
            self.sagemaker_client = boto3.client('sagemaker', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")

    def create_automl_job(
        self,
        job_name: str,
        input_data_s3: str,
        target_column: str,
        output_s3: str,
        role_arn: str,
        problem_type: Optional[str] = None,
        max_candidates: int = 10,
        max_runtime_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Create SageMaker Autopilot job.

        Args:
            job_name: Unique job name
            input_data_s3: S3 path to input data (CSV)
            target_column: Target column name
            output_s3: S3 output path
            role_arn: IAM role ARN
            problem_type: Optional (BinaryClassification, MulticlassClassification, Regression)
            max_candidates: Maximum models to try
            max_runtime_seconds: Maximum runtime

        Returns:
            AutoML job information
        """
        logger.info(f"Creating AutoML job: {job_name}")

        job_config = {
            "job_name": job_name,
            "input_data_s3": input_data_s3,
            "target_column": target_column,
            "output_s3": output_s3,
            "problem_type": problem_type,
            "max_candidates": max_candidates,
            "max_runtime_seconds": max_runtime_seconds,
            "created_at": datetime.utcnow().isoformat(),
            "status": "Pending"
        }

        if not self.sagemaker_client:
            job_config["status"] = "Mock"
            return job_config

        try:
            request = {
                "AutoMLJobName": job_name,
                "InputDataConfig": [
                    {
                        "DataSource": {
                            "S3DataSource": {
                                "S3DataType": "S3Prefix",
                                "S3Uri": input_data_s3
                            }
                        },
                        "TargetAttributeName": target_column
                    }
                ],
                "OutputDataConfig": {
                    "S3OutputPath": output_s3
                },
                "RoleArn": role_arn,
                "AutoMLJobConfig": {
                    "CompletionCriteria": {
                        "MaxCandidates": max_candidates,
                        "MaxRuntimePerTrainingJobInSeconds": max_runtime_seconds
                    }
                }
            }

            if problem_type:
                request["ProblemType"] = problem_type

            response = self.sagemaker_client.create_auto_ml_job(**request)
            job_config["automl_job_arn"] = response["AutoMLJobArn"]
            job_config["status"] = "InProgress"

        except Exception as e:
            logger.error(f"Failed to create AutoML job: {e}")
            job_config["status"] = "Failed"
            job_config["error"] = str(e)

        return job_config

    def get_automl_job_status(self, job_name: str) -> Dict[str, Any]:
        """Get AutoML job status."""
        if not self.sagemaker_client:
            return {"status": "Mock", "job_name": job_name}

        try:
            response = self.sagemaker_client.describe_auto_ml_job(AutoMLJobName=job_name)
            return {
                "job_name": job_name,
                "status": response["AutoMLJobStatus"],
                "best_candidate": response.get("BestCandidate"),
                "created_at": response["CreationTime"].isoformat() if "CreationTime" in response else None
            }
        except ClientError as e:
            logger.error(f"Failed to get AutoML status: {e}")
            return {"status": "Error", "error": str(e)}

    def list_candidates(self, job_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """List candidate models from AutoML job."""
        if not self.sagemaker_client:
            return []

        try:
            response = self.sagemaker_client.list_candidates_for_auto_ml_job(
                AutoMLJobName=job_name,
                MaxResults=max_results,
                SortBy="FinalObjectiveMetricValue",
                SortOrder="Descending"
            )
            return response.get("Candidates", [])
        except ClientError as e:
            logger.error(f"Failed to list candidates: {e}")
            return []


def test_automl_integrator():
    """Test AutoML integrator."""
    logger.info("Testing AutoML Integrator...")

    integrator = AutoMLIntegrator()

    # Test: Create AutoML job
    print("\n=== Test: Create AutoML Job ===")
    job = integrator.create_automl_job(
        job_name="test-automl-churn",
        input_data_s3="s3://test-bucket/data/churn.csv",
        target_column="churn",
        output_s3="s3://test-bucket/output",
        role_arn="arn:aws:iam::123456789012:role/SageMakerRole",
        problem_type="BinaryClassification",
        max_candidates=10
    )
    print(json.dumps(job, indent=2, default=str))


if __name__ == "__main__":
    test_automl_integrator()
