"""
SageMaker Training Job Generator for PromptOps
==============================================

Converts ML intent JSON from the parser into executable SageMaker training jobs.
Handles 5 model types: classification, regression, NLP, time-series, CV.

Author: ML Engineer - Phase 5 Week 42-43
Date: 2026-05-07
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


# ============================================================================
# SageMaker Training Job Generator
# ============================================================================

class SageMakerTrainingGenerator:
    """
    Generates SageMaker training job configurations from ML intent parameters.
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize SageMaker Training Generator.

        Args:
            region: AWS region for SageMaker
        """
        self.region = region
        self.sagemaker_client = None
        self.s3_client = None

        # Model type configurations
        self.model_configs = {
            "classification": {
                "algorithm": "xgboost",
                "framework_version": "1.5-1",
                "instance_type": "ml.m5.xlarge",
                "hyperparameters": {
                    "objective": "binary:logistic",
                    "eval_metric": "auc",
                    "num_round": "100"
                }
            },
            "regression": {
                "algorithm": "xgboost",
                "framework_version": "1.5-1",
                "instance_type": "ml.m5.xlarge",
                "hyperparameters": {
                    "objective": "reg:squarederror",
                    "eval_metric": "rmse",
                    "num_round": "100"
                }
            },
            "nlp": {
                "algorithm": "huggingface",
                "framework_version": "4.17",
                "pytorch_version": "1.10",
                "instance_type": "ml.g4dn.xlarge",
                "hyperparameters": {
                    "model_name": "distilbert-base-uncased",
                    "epochs": "3",
                    "learning_rate": "2e-5"
                }
            },
            "time_series": {
                "algorithm": "forecasting-deepar",
                "framework_version": "1.0-1",
                "instance_type": "ml.c5.2xlarge",
                "hyperparameters": {
                    "time_freq": "D",
                    "epochs": "100",
                    "prediction_length": "30"
                }
            },
            "computer_vision": {
                "algorithm": "image-classification",
                "framework_version": "1.0-1",
                "instance_type": "ml.p3.2xlarge",
                "hyperparameters": {
                    "num_layers": "18",
                    "epochs": "30",
                    "learning_rate": "0.001"
                }
            }
        }

        # Initialize AWS clients (lazy loading)
        self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients with error handling."""
        try:
            self.sagemaker_client = boto3.client('sagemaker', region_name=self.region)
            self.s3_client = boto3.client('s3', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")
            logger.warning("Operating in mock mode - no actual jobs will be submitted")

    def generate_training_config(
        self,
        intent_params: Dict[str, Any],
        s3_data_path: str,
        s3_output_path: str,
        role_arn: str
    ) -> Dict[str, Any]:
        """
        Generate SageMaker training job configuration from intent parameters.

        Args:
            intent_params: Parsed ML intent parameters from classifier
            s3_data_path: S3 path to training data
            s3_output_path: S3 path for model artifacts
            role_arn: IAM role ARN for SageMaker execution

        Returns:
            SageMaker training job configuration
        """
        logger.info(f"Generating training config for intent: {intent_params.get('model_type', 'unknown')}")

        # Extract parameters
        model_type = self._determine_model_type(intent_params)
        model_name = intent_params.get('model_type', 'unknown')
        time_range = intent_params.get('time_range', '90_days')

        # Get base config for model type
        base_config = self.model_configs.get(model_type, self.model_configs["classification"])

        # Generate unique job name
        job_name = self._generate_job_name(model_name, model_type)

        # Build training job configuration
        training_config = {
            "TrainingJobName": job_name,
            "RoleArn": role_arn,
            "AlgorithmSpecification": self._build_algorithm_spec(base_config),
            "InputDataConfig": self._build_input_config(s3_data_path, model_type),
            "OutputDataConfig": {
                "S3OutputPath": s3_output_path
            },
            "ResourceConfig": {
                "InstanceType": base_config["instance_type"],
                "InstanceCount": 1,
                "VolumeSizeInGB": 30
            },
            "StoppingCondition": {
                "MaxRuntimeInSeconds": 86400  # 24 hours
            },
            "HyperParameters": self._merge_hyperparameters(
                base_config["hyperparameters"],
                intent_params
            ),
            "Tags": self._generate_tags(intent_params, model_type)
        }

        logger.info(f"Training config generated: {job_name}")
        return training_config

    def _determine_model_type(self, intent_params: Dict[str, Any]) -> str:
        """
        Determine SageMaker model type from intent parameters.

        Args:
            intent_params: Intent parameters from classifier

        Returns:
            Model type string (classification, regression, nlp, time_series, computer_vision)
        """
        model_type_str = intent_params.get('model_type', '').lower()

        # Classification patterns
        if any(kw in model_type_str for kw in ['churn', 'fraud', 'classification', 'classifier']):
            return "classification"

        # Regression patterns
        if any(kw in model_type_str for kw in ['price', 'pricing', 'forecast', 'regression', 'revenue']):
            return "regression"

        # NLP patterns
        if any(kw in model_type_str for kw in ['sentiment', 'nlp', 'text', 'language', 'review']):
            return "nlp"

        # Time series patterns
        if any(kw in model_type_str for kw in ['time_series', 'timeseries', 'demand', 'sales_forecast']):
            return "time_series"

        # Computer vision patterns
        if any(kw in model_type_str for kw in ['image', 'vision', 'cv', 'detection', 'recognition']):
            return "computer_vision"

        # Default to classification
        logger.warning(f"Unknown model type: {model_type_str}, defaulting to classification")
        return "classification"

    def _generate_job_name(self, model_name: str, model_type: str) -> str:
        """
        Generate unique SageMaker training job name.

        Args:
            model_name: Model name from intent
            model_type: Model type

        Returns:
            Unique job name (max 63 chars, alphanumeric + hyphens)
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')

        # Clean model name
        clean_name = ''.join(c if c.isalnum() else '-' for c in model_name.lower())
        clean_name = clean_name[:20]  # Limit length

        job_name = f"promptops-{model_type[:10]}-{clean_name}-{timestamp}"

        # Ensure max 63 chars
        if len(job_name) > 63:
            job_name = job_name[:63]

        return job_name

    def _build_algorithm_spec(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build AlgorithmSpecification for SageMaker.

        Args:
            base_config: Base model configuration

        Returns:
            Algorithm specification dict
        """
        algorithm = base_config["algorithm"]

        # Map algorithm to container image
        algorithm_images = {
            "xgboost": f"683313688378.dkr.ecr.{self.region}.amazonaws.com/sagemaker-xgboost:{base_config['framework_version']}",
            "huggingface": f"763104351884.dkr.ecr.{self.region}.amazonaws.com/huggingface-pytorch-training:{base_config['framework_version']}-transformers{base_config.get('pytorch_version', '1.10')}-gpu-py38-cu111-ubuntu20.04",
            "forecasting-deepar": f"522234722520.dkr.ecr.{self.region}.amazonaws.com/forecasting-deepar:1",
            "image-classification": f"811284229777.dkr.ecr.{self.region}.amazonaws.com/image-classification:1"
        }

        return {
            "TrainingImage": algorithm_images.get(algorithm, algorithm_images["xgboost"]),
            "TrainingInputMode": "File"
        }

    def _build_input_config(self, s3_data_path: str, model_type: str) -> List[Dict[str, Any]]:
        """
        Build InputDataConfig for SageMaker.

        Args:
            s3_data_path: S3 path to training data
            model_type: Model type

        Returns:
            List of input data channel configurations
        """
        # For most algorithms, we need train channel
        input_config = [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": f"{s3_data_path}/train",
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "ContentType": "text/csv" if model_type != "nlp" else "application/json",
                "CompressionType": "None"
            }
        ]

        # Add validation channel
        input_config.append({
            "ChannelName": "validation",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"{s3_data_path}/validation",
                    "S3DataDistributionType": "FullyReplicated"
                }
            },
            "ContentType": "text/csv" if model_type != "nlp" else "application/json",
            "CompressionType": "None"
        })

        return input_config

    def _merge_hyperparameters(
        self,
        base_params: Dict[str, str],
        intent_params: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Merge base hyperparameters with intent-specific parameters.

        Args:
            base_params: Base hyperparameters from model config
            intent_params: Intent parameters from classifier

        Returns:
            Merged hyperparameters (all values as strings)
        """
        merged = base_params.copy()

        # Override with intent-specific parameters if present
        if 'hyperparameters' in intent_params:
            for key, value in intent_params['hyperparameters'].items():
                merged[key] = str(value)

        return merged

    def _generate_tags(self, intent_params: Dict[str, Any], model_type: str) -> List[Dict[str, str]]:
        """
        Generate tags for SageMaker training job.

        Args:
            intent_params: Intent parameters
            model_type: Model type

        Returns:
            List of tag dictionaries
        """
        return [
            {"Key": "Project", "Value": "PromptOps"},
            {"Key": "Phase", "Value": "Phase5-MLOps"},
            {"Key": "ModelType", "Value": model_type},
            {"Key": "CreatedBy", "Value": "PromptOps-ML-Agent"},
            {"Key": "CreatedAt", "Value": datetime.utcnow().isoformat()}
        ]

    def submit_training_job(self, training_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit training job to SageMaker.

        Args:
            training_config: Training job configuration

        Returns:
            Response from SageMaker with job ARN and status
        """
        if not self.sagemaker_client:
            logger.warning("SageMaker client not initialized. Returning mock response.")
            return {
                "status": "mock_mode",
                "job_name": training_config["TrainingJobName"],
                "job_arn": f"arn:aws:sagemaker:{self.region}:123456789012:training-job/{training_config['TrainingJobName']}",
                "message": "AWS credentials not configured. Job not actually submitted."
            }

        try:
            logger.info(f"Submitting training job: {training_config['TrainingJobName']}")

            response = self.sagemaker_client.create_training_job(**training_config)

            return {
                "status": "submitted",
                "job_name": training_config["TrainingJobName"],
                "job_arn": response["TrainingJobArn"],
                "message": "Training job submitted successfully"
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Failed to submit training job: {error_code} - {error_msg}")

            return {
                "status": "failed",
                "job_name": training_config["TrainingJobName"],
                "error": error_msg,
                "error_code": error_code
            }

    def get_training_status(self, job_name: str) -> Dict[str, Any]:
        """
        Get status of training job.

        Args:
            job_name: SageMaker training job name

        Returns:
            Job status information
        """
        if not self.sagemaker_client:
            return {
                "status": "mock_mode",
                "job_name": job_name,
                "message": "AWS credentials not configured"
            }

        try:
            response = self.sagemaker_client.describe_training_job(TrainingJobName=job_name)

            return {
                "status": response["TrainingJobStatus"],
                "job_name": job_name,
                "secondary_status": response.get("SecondaryStatus"),
                "failure_reason": response.get("FailureReason"),
                "model_artifacts": response.get("ModelArtifacts", {}).get("S3ModelArtifacts"),
                "training_time_seconds": response.get("TrainingTimeInSeconds"),
                "billable_time_seconds": response.get("BillableTimeInSeconds")
            }

        except ClientError as e:
            logger.error(f"Failed to get training status: {e}")
            return {
                "status": "error",
                "job_name": job_name,
                "error": str(e)
            }


# ============================================================================
# Testing
# ============================================================================

def test_sagemaker_generator():
    """Test SageMaker training generator with sample intent."""
    logger.info("Testing SageMaker Training Generator...")

    generator = SageMakerTrainingGenerator(region='us-east-1')

    # Sample intent parameters (from ML intent classifier)
    intent_params = {
        "model_type": "churn_prediction",
        "time_range": "90_days",
        "data_source": "user_activity",
        "hyperparameters": {
            "max_depth": "6",
            "eta": "0.3"
        }
    }

    # Generate training config
    config = generator.generate_training_config(
        intent_params=intent_params,
        s3_data_path="s3://promptops-ml-data/churn/input",
        s3_output_path="s3://promptops-ml-models/churn/output",
        role_arn="arn:aws:iam::123456789012:role/PromptOpsSageMakerRole"
    )

    print("\n=== Generated Training Configuration ===")
    print(json.dumps(config, indent=2))

    # Test job submission (will be mock if no AWS credentials)
    result = generator.submit_training_job(config)
    print("\n=== Submission Result ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_sagemaker_generator()
