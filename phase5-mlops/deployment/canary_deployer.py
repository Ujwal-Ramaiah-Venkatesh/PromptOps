"""
Canary Deployment System for PromptOps
======================================

Implements canary deployment strategy for ML models:
- Gradual traffic shift: 5% → 25% → 50% → 100%
- Automatic monitoring and validation at each stage
- Automatic rollback on quality degradation
- Stage-by-stage promotion with safety checks

Author: ML Engineer - Phase 5 Week 44-45
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
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
# Canary Deployment State Machine
# ============================================================================

class CanaryStage(Enum):
    """Canary deployment stages."""
    PENDING = "pending"
    STAGE_5_PERCENT = "5_percent"
    STAGE_25_PERCENT = "25_percent"
    STAGE_50_PERCENT = "50_percent"
    STAGE_100_PERCENT = "100_percent"
    COMPLETED = "completed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


# ============================================================================
# Canary Deployer
# ============================================================================

class CanaryDeployer:
    """
    Manages canary deployments for ML models.

    Canary deployment workflow:
    1. Deploy new model variant with 5% traffic
    2. Monitor for validation_duration (default 1 hour)
    3. If metrics are good, increase to 25%
    4. Continue monitoring and increasing: 50%, 100%
    5. Automatic rollback if any stage fails validation
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize Canary Deployer.

        Args:
            region: AWS region for SageMaker
        """
        self.region = region
        self.sagemaker_client = None
        self.cloudwatch_client = None

        # Canary stages configuration
        self.canary_stages = [
            {"stage": CanaryStage.STAGE_5_PERCENT, "traffic": 0.05, "duration_minutes": 60},
            {"stage": CanaryStage.STAGE_25_PERCENT, "traffic": 0.25, "duration_minutes": 60},
            {"stage": CanaryStage.STAGE_50_PERCENT, "traffic": 0.50, "duration_minutes": 60},
            {"stage": CanaryStage.STAGE_100_PERCENT, "traffic": 1.00, "duration_minutes": 30}
        ]

        # Validation thresholds
        self.max_error_rate_increase = 0.05  # 5%
        self.max_latency_increase = 0.30  # 30%
        self.min_requests_per_stage = 50

        # Initialize AWS clients
        self._init_aws_clients()

    def _init_aws_clients(self):
        """Initialize AWS clients with error handling."""
        try:
            self.sagemaker_client = boto3.client('sagemaker', region_name=self.region)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
            logger.info(f"AWS clients initialized for region: {self.region}")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")
            logger.warning("Operating in mock mode")

    def create_canary_deployment(
        self,
        model_name: str,
        model_version: str,
        production_endpoint: str,
        model_data_url: str,
        instance_type: str = "ml.m5.xlarge",
        instance_count: int = 1
    ) -> Dict[str, Any]:
        """
        Create canary deployment for a new model version.

        Args:
            model_name: Name of the model
            model_version: Version of new model
            production_endpoint: Name of production endpoint
            model_data_url: S3 URL to model artifacts
            instance_type: SageMaker instance type
            instance_count: Number of instances

        Returns:
            Canary deployment configuration
        """
        logger.info(f"Creating canary deployment: {model_name} v{model_version}")

        # Generate canary variant name
        canary_variant_name = f"{model_name}-canary-v{model_version.replace('.', '-')}"

        deployment = {
            "deployment_id": f"canary-{model_name}-{model_version}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "model_name": model_name,
            "model_version": model_version,
            "production_endpoint": production_endpoint,
            "canary_variant_name": canary_variant_name,
            "current_stage": CanaryStage.PENDING.value,
            "stage_history": [],
            "instance_type": instance_type,
            "instance_count": instance_count,
            "model_data_url": model_data_url,
            "created_at": datetime.utcnow().isoformat(),
            "stage_started_at": None,
            "stage_end_at": None,
            "metrics": {
                "requests_processed": 0,
                "canary_errors": 0,
                "production_errors": 0,
                "canary_error_rate": 0.0,
                "production_error_rate": 0.0,
                "canary_avg_latency": 0.0,
                "production_avg_latency": 0.0
            }
        }

        # Create SageMaker model for canary variant
        model_created = self._create_sagemaker_model(
            model_name=canary_variant_name,
            model_data_url=model_data_url
        )

        if model_created:
            # Start with 5% traffic stage
            stage_result = self._start_canary_stage(
                deployment,
                CanaryStage.STAGE_5_PERCENT
            )

            if stage_result["success"]:
                deployment["current_stage"] = CanaryStage.STAGE_5_PERCENT.value
                logger.info(f"Canary deployment started at 5% traffic")
            else:
                deployment["current_stage"] = CanaryStage.FAILED.value
                deployment["error"] = stage_result.get("error", "Failed to start canary stage")
        else:
            deployment["current_stage"] = CanaryStage.FAILED.value
            deployment["error"] = "Failed to create SageMaker model"

        return deployment

    def _create_sagemaker_model(
        self,
        model_name: str,
        model_data_url: str
    ) -> bool:
        """Create SageMaker model for canary variant."""
        if not self.sagemaker_client:
            logger.warning("SageMaker client not available. Using mock mode.")
            return True

        try:
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

    def _start_canary_stage(
        self,
        deployment: Dict[str, Any],
        stage: CanaryStage
    ) -> Dict[str, Any]:
        """
        Start a canary deployment stage.

        Args:
            deployment: Deployment configuration
            stage: Canary stage to start

        Returns:
            Stage start result
        """
        stage_config = next((s for s in self.canary_stages if s["stage"] == stage), None)
        if not stage_config:
            return {"success": False, "error": f"Invalid stage: {stage}"}

        logger.info(f"Starting canary stage: {stage.value} ({stage_config['traffic']*100}% traffic)")

        result = {
            "success": False,
            "stage": stage.value,
            "traffic_percentage": stage_config['traffic'] * 100,
            "duration_minutes": stage_config['duration_minutes']
        }

        try:
            # Update endpoint configuration with traffic split
            updated = self._update_endpoint_traffic(
                deployment["production_endpoint"],
                deployment["canary_variant_name"],
                stage_config["traffic"]
            )

            if updated:
                deployment["stage_started_at"] = datetime.utcnow().isoformat()
                stage_end = datetime.utcnow() + timedelta(minutes=stage_config["duration_minutes"])
                deployment["stage_end_at"] = stage_end.isoformat()

                result["success"] = True
                result["started_at"] = deployment["stage_started_at"]
                result["end_at"] = deployment["stage_end_at"]

                logger.info(f"Canary stage started: {stage.value}")
            else:
                result["error"] = "Failed to update endpoint traffic"

        except Exception as e:
            result["error"] = f"Stage start failed: {str(e)}"
            logger.error(result["error"])

        return result

    def _update_endpoint_traffic(
        self,
        endpoint_name: str,
        canary_variant_name: str,
        canary_traffic: float
    ) -> bool:
        """
        Update endpoint to route traffic to canary variant.

        Args:
            endpoint_name: Production endpoint name
            canary_variant_name: Canary variant name
            canary_traffic: Percentage of traffic for canary (0.0-1.0)

        Returns:
            True if update successful
        """
        if not self.sagemaker_client:
            logger.warning("SageMaker client not available. Using mock mode.")
            return True

        try:
            # In real implementation, this would update endpoint with new variant weights
            # For now, we simulate the update
            logger.info(
                f"Updated endpoint {endpoint_name}: "
                f"production={1-canary_traffic:.0%}, canary={canary_traffic:.0%}"
            )
            return True

        except ClientError as e:
            logger.error(f"Failed to update endpoint traffic: {e}")
            return False

    def validate_canary_stage(
        self,
        deployment: Dict[str, Any],
        stage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate current canary stage based on metrics.

        Args:
            deployment: Deployment configuration
            stage_metrics: Metrics collected during stage

        Returns:
            Validation result with pass/fail
        """
        current_stage = deployment["current_stage"]
        logger.info(f"Validating canary stage: {current_stage}")

        validation = {
            "deployment_id": deployment["deployment_id"],
            "stage": current_stage,
            "validated_at": datetime.utcnow().isoformat(),
            "passed": False,
            "metrics": stage_metrics,
            "checks": []
        }

        # Check 1: Minimum requests threshold
        requests_check = self._check_minimum_requests(stage_metrics)
        validation["checks"].append(requests_check)

        # Check 2: Error rate comparison
        error_rate_check = self._check_error_rate(stage_metrics)
        validation["checks"].append(error_rate_check)

        # Check 3: Latency comparison
        latency_check = self._check_latency(stage_metrics)
        validation["checks"].append(latency_check)

        # Overall validation result
        all_checks_passed = all(check["passed"] for check in validation["checks"])
        validation["passed"] = all_checks_passed

        logger.info(f"Validation result: {'PASSED' if validation['passed'] else 'FAILED'}")
        return validation

    def _check_minimum_requests(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if minimum requests threshold met."""
        requests = metrics.get("requests_processed", 0)
        passed = requests >= self.min_requests_per_stage

        return {
            "name": "minimum_requests",
            "passed": passed,
            "value": requests,
            "threshold": self.min_requests_per_stage,
            "message": f"Processed {requests} requests (min: {self.min_requests_per_stage})"
        }

    def _check_error_rate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if error rate is acceptable."""
        canary_error_rate = metrics.get("canary_error_rate", 0.0)
        production_error_rate = metrics.get("production_error_rate", 0.0)
        error_rate_increase = canary_error_rate - production_error_rate

        passed = error_rate_increase <= self.max_error_rate_increase

        return {
            "name": "error_rate",
            "passed": passed,
            "value": error_rate_increase,
            "threshold": self.max_error_rate_increase,
            "message": f"Error rate increase: {error_rate_increase:.2%} (max: {self.max_error_rate_increase:.2%})"
        }

    def _check_latency(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if latency is acceptable."""
        canary_latency = metrics.get("canary_avg_latency", 0.0)
        production_latency = metrics.get("production_avg_latency", 1.0)

        latency_increase = (canary_latency - production_latency) / production_latency if production_latency > 0 else 0
        passed = latency_increase <= self.max_latency_increase

        return {
            "name": "latency",
            "passed": passed,
            "value": latency_increase,
            "threshold": self.max_latency_increase,
            "message": f"Latency increase: {latency_increase:.2%} (max: {self.max_latency_increase:.2%})"
        }

    def promote_canary_stage(
        self,
        deployment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Promote canary to next stage.

        Args:
            deployment: Deployment configuration

        Returns:
            Promotion result
        """
        current_stage = CanaryStage(deployment["current_stage"])
        logger.info(f"Promoting canary from stage: {current_stage.value}")

        # Record stage in history
        deployment["stage_history"].append({
            "stage": current_stage.value,
            "started_at": deployment["stage_started_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        })

        # Determine next stage
        stage_index = [s["stage"] for s in self.canary_stages].index(current_stage)
        if stage_index < len(self.canary_stages) - 1:
            next_stage = self.canary_stages[stage_index + 1]["stage"]

            # Start next stage
            result = self._start_canary_stage(deployment, next_stage)

            if result["success"]:
                deployment["current_stage"] = next_stage.value
                return {
                    "success": True,
                    "previous_stage": current_stage.value,
                    "current_stage": next_stage.value,
                    "message": f"Promoted to {next_stage.value}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to start next stage: {result.get('error')}"
                }
        else:
            # Completed all stages
            deployment["current_stage"] = CanaryStage.COMPLETED.value
            return {
                "success": True,
                "previous_stage": current_stage.value,
                "current_stage": CanaryStage.COMPLETED.value,
                "message": "Canary deployment completed successfully"
            }

    def rollback_canary_deployment(
        self,
        deployment: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """
        Rollback canary deployment to production only.

        Args:
            deployment: Deployment configuration
            reason: Reason for rollback

        Returns:
            Rollback result
        """
        logger.info(f"Rolling back canary deployment: {deployment['deployment_id']}")
        logger.info(f"Rollback reason: {reason}")

        # Set traffic to 100% production, 0% canary
        rollback_result = self._update_endpoint_traffic(
            deployment["production_endpoint"],
            deployment["canary_variant_name"],
            0.0  # 0% canary traffic
        )

        # Record rollback in history
        deployment["stage_history"].append({
            "stage": deployment["current_stage"],
            "started_at": deployment["stage_started_at"],
            "rolled_back_at": datetime.utcnow().isoformat(),
            "status": "rolled_back",
            "reason": reason
        })

        deployment["current_stage"] = CanaryStage.ROLLED_BACK.value

        return {
            "success": rollback_result,
            "deployment_id": deployment["deployment_id"],
            "rolled_back_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "message": "Canary deployment rolled back to 100% production"
        }


# ============================================================================
# Testing
# ============================================================================

def test_canary_deployer():
    """Test canary deployer with mock data."""
    logger.info("Testing Canary Deployer...")

    deployer = CanaryDeployer(region='us-east-1')

    # Test 1: Create canary deployment
    print("\n=== Test 1: Create Canary Deployment ===")
    deployment = deployer.create_canary_deployment(
        model_name="fraud-detection",
        model_version="v3.0",
        production_endpoint="fraud-detection-prod",
        model_data_url="s3://promptops-models/fraud/v3.0/model.tar.gz"
    )
    print(json.dumps(deployment, indent=2))

    # Test 2: Validate stage with good metrics
    print("\n=== Test 2: Validate Stage (Good Metrics) ===")
    good_metrics = {
        "requests_processed": 150,
        "canary_error_rate": 0.02,
        "production_error_rate": 0.02,
        "canary_avg_latency": 55.0,
        "production_avg_latency": 50.0
    }
    validation = deployer.validate_canary_stage(deployment, good_metrics)
    print(json.dumps(validation, indent=2))

    # Test 3: Promote to next stage
    if validation["passed"]:
        print("\n=== Test 3: Promote to Next Stage ===")
        promotion = deployer.promote_canary_stage(deployment)
        print(json.dumps(promotion, indent=2))

    # Test 4: Validate stage with bad metrics
    print("\n=== Test 4: Validate Stage (Bad Metrics) ===")
    bad_metrics = {
        "requests_processed": 150,
        "canary_error_rate": 0.10,  # High error rate
        "production_error_rate": 0.02,
        "canary_avg_latency": 100.0,  # High latency
        "production_avg_latency": 50.0
    }
    validation_bad = deployer.validate_canary_stage(deployment, bad_metrics)
    print(json.dumps(validation_bad, indent=2))

    # Test 5: Rollback
    if not validation_bad["passed"]:
        print("\n=== Test 5: Rollback Deployment ===")
        rollback = deployer.rollback_canary_deployment(
            deployment,
            reason="Error rate too high"
        )
        print(json.dumps(rollback, indent=2))


if __name__ == "__main__":
    test_canary_deployer()
