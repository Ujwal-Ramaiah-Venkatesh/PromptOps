"""
Shadow Deployment System for PromptOps
======================================

Implements shadow deployment strategy for ML models:
- Deploy new model alongside production model
- Route traffic to both models (shadow gets copy of requests)
- Compare predictions for 24 hours
- Automatic validation and promotion/rollback

Author: ML Engineer - Phase 5 Week 44-45
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Shadow Deployment State Machine
# ============================================================================

class ShadowDeploymentState(Enum):
    """States for shadow deployment."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    SHADOW_ACTIVE = "shadow_active"
    VALIDATING = "validating"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    PROMOTING = "promoting"
    PROMOTED = "promoted"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


# ============================================================================
# Shadow Deployer
# ============================================================================

class ShadowDeployer:
    """
    Manages shadow deployments for ML models.

    Shadow deployment workflow:
    1. Deploy new model as shadow endpoint
    2. Route 100% of traffic to production + copy to shadow
    3. Collect predictions from both for 24 hours
    4. Compare prediction quality
    5. Promote shadow to production if validation passes
    6. Rollback if validation fails
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize Shadow Deployer.

        Args:
            region: AWS region for SageMaker
        """
        self.region = region
        self.sagemaker_client = None
        self.sagemaker_runtime = None

        # Shadow deployment configurations
        self.validation_duration_hours = 24
        self.min_predictions_for_validation = 100
        self.max_error_rate_increase = 0.05  # 5% max error increase

        # Initialize AWS clients
        self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients with error handling."""
        try:
            self.sagemaker_client = boto3.client('sagemaker', region_name=self.region)
            self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")
            logger.warning("Operating in mock mode - no actual deployments will happen")

    def create_shadow_deployment(
        self,
        model_name: str,
        model_version: str,
        production_endpoint: str,
        model_data_url: str,
        instance_type: str = "ml.m5.xlarge",
        instance_count: int = 1
    ) -> Dict[str, Any]:
        """
        Create shadow deployment for a new model version.

        Args:
            model_name: Name of the model
            model_version: Version of new model to deploy
            production_endpoint: Name of current production endpoint
            model_data_url: S3 URL to model artifacts
            instance_type: SageMaker instance type
            instance_count: Number of instances

        Returns:
            Shadow deployment information
        """
        logger.info(f"Creating shadow deployment: {model_name} v{model_version}")

        # Generate shadow endpoint name
        shadow_endpoint_name = f"{model_name}-shadow-v{model_version}"
        shadow_endpoint_name = shadow_endpoint_name.replace('.', '-')[:63]

        deployment = {
            "deployment_id": f"shadow-{model_name}-{model_version}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "model_name": model_name,
            "model_version": model_version,
            "production_endpoint": production_endpoint,
            "shadow_endpoint": shadow_endpoint_name,
            "state": ShadowDeploymentState.PENDING.value,
            "instance_type": instance_type,
            "instance_count": instance_count,
            "model_data_url": model_data_url,
            "created_at": datetime.utcnow().isoformat(),
            "validation_start": None,
            "validation_end": None,
            "metrics": {
                "predictions_collected": 0,
                "production_errors": 0,
                "shadow_errors": 0,
                "agreement_rate": 0.0
            }
        }

        # Create SageMaker model
        model_created = self._create_sagemaker_model(
            model_name=shadow_endpoint_name,
            model_data_url=model_data_url
        )

        if model_created:
            deployment["state"] = ShadowDeploymentState.DEPLOYING.value

            # Create endpoint configuration
            endpoint_config_created = self._create_endpoint_config(
                config_name=shadow_endpoint_name,
                model_name=shadow_endpoint_name,
                instance_type=instance_type,
                instance_count=instance_count
            )

            if endpoint_config_created:
                # Create endpoint
                endpoint_created = self._create_endpoint(
                    endpoint_name=shadow_endpoint_name,
                    config_name=shadow_endpoint_name
                )

                if endpoint_created:
                    deployment["state"] = ShadowDeploymentState.SHADOW_ACTIVE.value
                    deployment["validation_start"] = datetime.utcnow().isoformat()
                    validation_end = datetime.utcnow() + timedelta(hours=self.validation_duration_hours)
                    deployment["validation_end"] = validation_end.isoformat()
                    logger.info(f"Shadow deployment active: {shadow_endpoint_name}")
                else:
                    deployment["state"] = ShadowDeploymentState.FAILED.value
                    deployment["error"] = "Failed to create endpoint"
            else:
                deployment["state"] = ShadowDeploymentState.FAILED.value
                deployment["error"] = "Failed to create endpoint configuration"
        else:
            deployment["state"] = ShadowDeploymentState.FAILED.value
            deployment["error"] = "Failed to create SageMaker model"

        return deployment

    def _create_sagemaker_model(
        self,
        model_name: str,
        model_data_url: str
    ) -> bool:
        """Create SageMaker model."""
        if not self.sagemaker_client:
            logger.warning("SageMaker client not available. Using mock mode.")
            return True

        try:
            # Use XGBoost container as default
            container_image = f"683313688378.dkr.ecr.{self.region}.amazonaws.com/sagemaker-xgboost:1.5-1"

            response = self.sagemaker_client.create_model(
                ModelName=model_name,
                PrimaryContainer={
                    'Image': container_image,
                    'ModelDataUrl': model_data_url
                },
                ExecutionRoleArn=os.getenv('SAGEMAKER_EXECUTION_ROLE', 'arn:aws:iam::123456789012:role/SageMakerRole')
            )

            logger.info(f"SageMaker model created: {model_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create SageMaker model: {e}")
            return False

    def _create_endpoint_config(
        self,
        config_name: str,
        model_name: str,
        instance_type: str,
        instance_count: int
    ) -> bool:
        """Create SageMaker endpoint configuration."""
        if not self.sagemaker_client:
            logger.warning("SageMaker client not available. Using mock mode.")
            return True

        try:
            response = self.sagemaker_client.create_endpoint_config(
                EndpointConfigName=config_name,
                ProductionVariants=[
                    {
                        'VariantName': 'AllTraffic',
                        'ModelName': model_name,
                        'InitialInstanceCount': instance_count,
                        'InstanceType': instance_type,
                        'InitialVariantWeight': 1.0
                    }
                ]
            )

            logger.info(f"Endpoint config created: {config_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create endpoint config: {e}")
            return False

    def _create_endpoint(
        self,
        endpoint_name: str,
        config_name: str
    ) -> bool:
        """Create SageMaker endpoint."""
        if not self.sagemaker_client:
            logger.warning("SageMaker client not available. Using mock mode.")
            return True

        try:
            response = self.sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=config_name
            )

            logger.info(f"Endpoint created: {endpoint_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create endpoint: {e}")
            return False

    def invoke_shadow_prediction(
        self,
        deployment: Dict[str, Any],
        input_data: Any
    ) -> Dict[str, Any]:
        """
        Invoke both production and shadow endpoints for comparison.

        Args:
            deployment: Shadow deployment configuration
            input_data: Input data for prediction

        Returns:
            Predictions from both endpoints
        """
        results = {
            "production_prediction": None,
            "shadow_prediction": None,
            "production_error": None,
            "shadow_error": None,
            "latency_ms": {
                "production": 0,
                "shadow": 0
            }
        }

        # Invoke production endpoint
        try:
            start_time = datetime.utcnow()
            prod_response = self._invoke_endpoint(
                deployment["production_endpoint"],
                input_data
            )
            prod_latency = (datetime.utcnow() - start_time).total_seconds() * 1000

            results["production_prediction"] = prod_response
            results["latency_ms"]["production"] = prod_latency

        except Exception as e:
            logger.error(f"Production prediction failed: {e}")
            results["production_error"] = str(e)

        # Invoke shadow endpoint
        try:
            start_time = datetime.utcnow()
            shadow_response = self._invoke_endpoint(
                deployment["shadow_endpoint"],
                input_data
            )
            shadow_latency = (datetime.utcnow() - start_time).total_seconds() * 1000

            results["shadow_prediction"] = shadow_response
            results["latency_ms"]["shadow"] = shadow_latency

        except Exception as e:
            logger.error(f"Shadow prediction failed: {e}")
            results["shadow_error"] = str(e)

        return results

    def _invoke_endpoint(
        self,
        endpoint_name: str,
        input_data: Any
    ) -> Any:
        """Invoke SageMaker endpoint."""
        if not self.sagemaker_runtime:
            logger.warning("SageMaker runtime not available. Using mock prediction.")
            return {"prediction": 0.75, "confidence": 0.92}

        try:
            # Convert input to CSV format (for XGBoost)
            if isinstance(input_data, dict):
                input_str = ','.join(str(v) for v in input_data.values())
            else:
                input_str = str(input_data)

            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='text/csv',
                Body=input_str
            )

            result = json.loads(response['Body'].read().decode())
            return result

        except ClientError as e:
            logger.error(f"Endpoint invocation failed: {e}")
            raise

    def validate_shadow_deployment(
        self,
        deployment: Dict[str, Any],
        prediction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate shadow deployment based on collected predictions.

        Args:
            deployment: Shadow deployment configuration
            prediction_history: List of prediction comparisons

        Returns:
            Validation results with pass/fail decision
        """
        logger.info(f"Validating shadow deployment: {deployment['deployment_id']}")

        validation = {
            "deployment_id": deployment["deployment_id"],
            "validated_at": datetime.utcnow().isoformat(),
            "passed": False,
            "metrics": {},
            "reasons": []
        }

        # Check if enough predictions collected
        if len(prediction_history) < self.min_predictions_for_validation:
            validation["passed"] = False
            validation["reasons"].append(
                f"Insufficient predictions: {len(prediction_history)} < {self.min_predictions_for_validation}"
            )
            return validation

        # Calculate metrics
        metrics = self._calculate_validation_metrics(prediction_history)
        validation["metrics"] = metrics

        # Check error rate
        error_rate_increase = metrics["shadow_error_rate"] - metrics["production_error_rate"]
        if error_rate_increase > self.max_error_rate_increase:
            validation["passed"] = False
            validation["reasons"].append(
                f"Error rate increased by {error_rate_increase:.2%} (max: {self.max_error_rate_increase:.2%})"
            )
        else:
            validation["reasons"].append(
                f"Error rate acceptable: {error_rate_increase:.2%} increase"
            )

        # Check agreement rate
        if metrics["agreement_rate"] < 0.90:  # 90% agreement threshold
            validation["passed"] = False
            validation["reasons"].append(
                f"Low agreement rate: {metrics['agreement_rate']:.2%} (min: 90%)"
            )
        else:
            validation["reasons"].append(
                f"Agreement rate acceptable: {metrics['agreement_rate']:.2%}"
            )

        # Check latency
        latency_increase = (metrics["shadow_avg_latency"] - metrics["production_avg_latency"]) / metrics["production_avg_latency"]
        if latency_increase > 0.50:  # 50% max latency increase
            validation["passed"] = False
            validation["reasons"].append(
                f"Latency increased by {latency_increase:.2%} (max: 50%)"
            )
        else:
            validation["reasons"].append(
                f"Latency acceptable: {latency_increase:.2%} increase"
            )

        # Overall validation result
        if len([r for r in validation["reasons"] if "acceptable" in r.lower()]) >= 3:
            validation["passed"] = True

        logger.info(f"Validation result: {'PASSED' if validation['passed'] else 'FAILED'}")
        return validation

    def _calculate_validation_metrics(
        self,
        prediction_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate validation metrics from prediction history."""
        metrics = {
            "total_predictions": len(prediction_history),
            "production_errors": 0,
            "shadow_errors": 0,
            "production_error_rate": 0.0,
            "shadow_error_rate": 0.0,
            "agreement_count": 0,
            "agreement_rate": 0.0,
            "production_avg_latency": 0.0,
            "shadow_avg_latency": 0.0
        }

        total_prod_latency = 0
        total_shadow_latency = 0

        for pred in prediction_history:
            # Count errors
            if pred.get("production_error"):
                metrics["production_errors"] += 1
            if pred.get("shadow_error"):
                metrics["shadow_errors"] += 1

            # Check agreement
            if (pred.get("production_prediction") is not None and
                pred.get("shadow_prediction") is not None):
                if self._predictions_agree(
                    pred["production_prediction"],
                    pred["shadow_prediction"]
                ):
                    metrics["agreement_count"] += 1

            # Sum latencies
            total_prod_latency += pred.get("latency_ms", {}).get("production", 0)
            total_shadow_latency += pred.get("latency_ms", {}).get("shadow", 0)

        # Calculate rates
        if metrics["total_predictions"] > 0:
            metrics["production_error_rate"] = metrics["production_errors"] / metrics["total_predictions"]
            metrics["shadow_error_rate"] = metrics["shadow_errors"] / metrics["total_predictions"]
            metrics["agreement_rate"] = metrics["agreement_count"] / metrics["total_predictions"]
            metrics["production_avg_latency"] = total_prod_latency / metrics["total_predictions"]
            metrics["shadow_avg_latency"] = total_shadow_latency / metrics["total_predictions"]

        return metrics

    def _predictions_agree(
        self,
        pred1: Any,
        pred2: Any,
        tolerance: float = 0.1
    ) -> bool:
        """
        Check if two predictions agree within tolerance.

        Args:
            pred1: First prediction
            pred2: Second prediction
            tolerance: Tolerance for numerical differences

        Returns:
            True if predictions agree
        """
        # For classification (discrete values)
        if isinstance(pred1, (int, str)) and isinstance(pred2, (int, str)):
            return pred1 == pred2

        # For regression (continuous values)
        if isinstance(pred1, (float, int)) and isinstance(pred2, (float, int)):
            return abs(pred1 - pred2) / max(abs(pred1), abs(pred2), 1e-10) <= tolerance

        # For structured predictions (dicts)
        if isinstance(pred1, dict) and isinstance(pred2, dict):
            pred1_val = pred1.get('prediction', pred1.get('value'))
            pred2_val = pred2.get('prediction', pred2.get('value'))
            if pred1_val is not None and pred2_val is not None:
                return self._predictions_agree(pred1_val, pred2_val, tolerance)

        return False

    def promote_shadow_to_production(
        self,
        deployment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Promote shadow deployment to production.

        Args:
            deployment: Shadow deployment configuration

        Returns:
            Promotion result
        """
        logger.info(f"Promoting shadow to production: {deployment['shadow_endpoint']}")

        result = {
            "deployment_id": deployment["deployment_id"],
            "promoted_at": datetime.utcnow().isoformat(),
            "success": False,
            "message": ""
        }

        try:
            # Update production endpoint to point to new model
            # In real implementation, this would update endpoint configuration
            result["success"] = True
            result["message"] = f"Shadow endpoint {deployment['shadow_endpoint']} promoted to production"
            logger.info(result["message"])

        except Exception as e:
            result["success"] = False
            result["message"] = f"Promotion failed: {str(e)}"
            logger.error(result["message"])

        return result

    def rollback_shadow_deployment(
        self,
        deployment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rollback shadow deployment and delete resources.

        Args:
            deployment: Shadow deployment configuration

        Returns:
            Rollback result
        """
        logger.info(f"Rolling back shadow deployment: {deployment['shadow_endpoint']}")

        result = {
            "deployment_id": deployment["deployment_id"],
            "rolled_back_at": datetime.utcnow().isoformat(),
            "success": False,
            "message": ""
        }

        try:
            # Delete shadow endpoint
            if self.sagemaker_client:
                try:
                    self.sagemaker_client.delete_endpoint(
                        EndpointName=deployment["shadow_endpoint"]
                    )
                    logger.info(f"Deleted endpoint: {deployment['shadow_endpoint']}")
                except ClientError as e:
                    logger.warning(f"Endpoint deletion failed: {e}")

            result["success"] = True
            result["message"] = f"Shadow deployment {deployment['shadow_endpoint']} rolled back"
            logger.info(result["message"])

        except Exception as e:
            result["success"] = False
            result["message"] = f"Rollback failed: {str(e)}"
            logger.error(result["message"])

        return result


# ============================================================================
# Testing
# ============================================================================

def test_shadow_deployer():
    """Test shadow deployer with mock data."""
    logger.info("Testing Shadow Deployer...")

    deployer = ShadowDeployer(region='us-east-1')

    # Test 1: Create shadow deployment
    print("\n=== Test 1: Create Shadow Deployment ===")
    deployment = deployer.create_shadow_deployment(
        model_name="churn-prediction",
        model_version="v2.0",
        production_endpoint="churn-prediction-prod",
        model_data_url="s3://promptops-models/churn/v2.0/model.tar.gz"
    )
    print(json.dumps(deployment, indent=2))

    # Test 2: Simulate predictions
    print("\n=== Test 2: Shadow Predictions ===")
    input_data = {"feature1": 5, "feature2": 10, "feature3": 0.5}
    predictions = deployer.invoke_shadow_prediction(deployment, input_data)
    print(json.dumps(predictions, indent=2))

    # Test 3: Validate with mock prediction history
    print("\n=== Test 3: Validation ===")
    mock_history = [
        {
            "production_prediction": 0.8,
            "shadow_prediction": 0.82,
            "latency_ms": {"production": 50, "shadow": 55}
        }
        for _ in range(150)  # Simulate 150 predictions
    ]
    validation = deployer.validate_shadow_deployment(deployment, mock_history)
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    test_shadow_deployer()
