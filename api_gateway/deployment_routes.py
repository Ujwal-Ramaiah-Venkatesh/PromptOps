"""
Deployment API Routes for PromptOps
===================================

API endpoints for ML model deployment:
- Shadow deployment (24-hour validation)
- Canary deployment (5%→25%→50%→100%)
- Prediction comparison
- Deployment management

Author: Backend Engineer - Phase 5 Week 44-45
Date: 2026-05-07
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Add phase5-mlops to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-mlops'))

from deployment.shadow_deployer import ShadowDeployer
from deployment.canary_deployer import CanaryDeployer
from deployment.prediction_comparator import PredictionComparator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/deployment", tags=["deployment"])

# Initialize components
shadow_deployer = ShadowDeployer()
canary_deployer = CanaryDeployer()
prediction_comparator = PredictionComparator()

# In-memory storage for active deployments (in production, use database)
active_deployments = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class ShadowDeploymentRequest(BaseModel):
    """Request model for shadow deployment."""
    model_name: str
    model_version: str
    production_endpoint: str
    model_data_url: str
    instance_type: str = "ml.m5.xlarge"
    instance_count: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "churn-prediction",
                "model_version": "v2.0",
                "production_endpoint": "churn-prediction-prod",
                "model_data_url": "s3://promptops-models/churn/v2.0/model.tar.gz",
                "instance_type": "ml.m5.xlarge",
                "instance_count": 1
            }
        }


class CanaryDeploymentRequest(BaseModel):
    """Request model for canary deployment."""
    model_name: str
    model_version: str
    production_endpoint: str
    model_data_url: str
    instance_type: str = "ml.m5.xlarge"
    instance_count: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "fraud-detection",
                "model_version": "v3.0",
                "production_endpoint": "fraud-detection-prod",
                "model_data_url": "s3://promptops-models/fraud/v3.0/model.tar.gz"
            }
        }


class PredictionComparisonRequest(BaseModel):
    """Request model for prediction comparison."""
    production_predictions: List[Dict[str, Any]]
    candidate_predictions: List[Dict[str, Any]]
    ground_truth: Optional[List[Any]] = None
    model_type: str = "classification"

    class Config:
        json_schema_extra = {
            "example": {
                "production_predictions": [
                    {"prediction": 0}, {"prediction": 1}, {"prediction": 0}
                ],
                "candidate_predictions": [
                    {"prediction": 0}, {"prediction": 1}, {"prediction": 1}
                ],
                "ground_truth": [0, 1, 0],
                "model_type": "classification"
            }
        }


class StageValidationRequest(BaseModel):
    """Request model for stage validation."""
    deployment_id: str
    stage_metrics: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "deployment_id": "canary-fraud-v3.0-20260507123456",
                "stage_metrics": {
                    "requests_processed": 150,
                    "canary_error_rate": 0.02,
                    "production_error_rate": 0.02,
                    "canary_avg_latency": 55.0,
                    "production_avg_latency": 50.0
                }
            }
        }


# ============================================================================
# Shadow Deployment Endpoints
# ============================================================================

@router.post("/shadow/create")
async def create_shadow_deployment(request: ShadowDeploymentRequest):
    """
    Create shadow deployment for model validation.

    **Workflow:**
    1. Deploy new model as shadow endpoint
    2. Route 100% traffic to production + copy to shadow
    3. Collect predictions from both for 24 hours
    4. Compare prediction quality
    5. Promote or rollback based on validation

    **Returns:**
    - deployment_id: Unique deployment identifier
    - shadow_endpoint: SageMaker endpoint name
    - validation_end: When validation period ends
    """
    try:
        logger.info(f"Creating shadow deployment: {request.model_name} v{request.model_version}")

        deployment = shadow_deployer.create_shadow_deployment(
            model_name=request.model_name,
            model_version=request.model_version,
            production_endpoint=request.production_endpoint,
            model_data_url=request.model_data_url,
            instance_type=request.instance_type,
            instance_count=request.instance_count
        )

        # Store deployment
        active_deployments[deployment["deployment_id"]] = {
            "type": "shadow",
            "deployment": deployment,
            "prediction_history": []
        }

        return deployment

    except Exception as e:
        logger.error(f"Failed to create shadow deployment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create shadow deployment: {str(e)}"
        )


@router.get("/shadow/{deployment_id}")
async def get_shadow_deployment(deployment_id: str):
    """
    Get shadow deployment status.

    Returns deployment configuration and current metrics.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]
    if deployment_data["type"] != "shadow":
        raise HTTPException(status_code=400, detail="Not a shadow deployment")

    return deployment_data["deployment"]


@router.post("/shadow/{deployment_id}/predict")
async def shadow_predict(deployment_id: str, input_data: Dict[str, Any]):
    """
    Make prediction using both production and shadow endpoints.

    **Use this endpoint** during shadow validation to collect comparison data.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]
    if deployment_data["type"] != "shadow":
        raise HTTPException(status_code=400, detail="Not a shadow deployment")

    try:
        predictions = shadow_deployer.invoke_shadow_prediction(
            deployment_data["deployment"],
            input_data
        )

        # Store prediction history
        deployment_data["prediction_history"].append(predictions)

        return predictions

    except Exception as e:
        logger.error(f"Shadow prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shadow prediction failed: {str(e)}"
        )


@router.post("/shadow/{deployment_id}/validate")
async def validate_shadow_deployment(deployment_id: str):
    """
    Validate shadow deployment based on collected predictions.

    **Checks:**
    - Minimum predictions threshold
    - Error rate comparison
    - Latency comparison
    - Agreement rate

    **Returns pass/fail decision** for promotion.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]
    if deployment_data["type"] != "shadow":
        raise HTTPException(status_code=400, detail="Not a shadow deployment")

    try:
        validation = shadow_deployer.validate_shadow_deployment(
            deployment_data["deployment"],
            deployment_data["prediction_history"]
        )

        return validation

    except Exception as e:
        logger.error(f"Shadow validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shadow validation failed: {str(e)}"
        )


@router.post("/shadow/{deployment_id}/promote")
async def promote_shadow(deployment_id: str):
    """
    Promote shadow deployment to production.

    Only call after validation passes.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]

    try:
        result = shadow_deployer.promote_shadow_to_production(
            deployment_data["deployment"]
        )

        if result["success"]:
            # Remove from active deployments
            del active_deployments[deployment_id]

        return result

    except Exception as e:
        logger.error(f"Shadow promotion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shadow promotion failed: {str(e)}"
        )


@router.post("/shadow/{deployment_id}/rollback")
async def rollback_shadow(deployment_id: str, reason: str = "Manual rollback"):
    """
    Rollback shadow deployment.

    Call this if validation fails or to cancel deployment.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]

    try:
        result = shadow_deployer.rollback_shadow_deployment(
            deployment_data["deployment"]
        )

        if result["success"]:
            # Remove from active deployments
            del active_deployments[deployment_id]

        return result

    except Exception as e:
        logger.error(f"Shadow rollback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Shadow rollback failed: {str(e)}"
        )


# ============================================================================
# Canary Deployment Endpoints
# ============================================================================

@router.post("/canary/create")
async def create_canary_deployment(request: CanaryDeploymentRequest):
    """
    Create canary deployment with gradual traffic shift.

    **Stages:**
    1. 5% traffic → validate 1 hour
    2. 25% traffic → validate 1 hour
    3. 50% traffic → validate 1 hour
    4. 100% traffic → complete

    **Automatic rollback** if any stage fails validation.
    """
    try:
        logger.info(f"Creating canary deployment: {request.model_name} v{request.model_version}")

        deployment = canary_deployer.create_canary_deployment(
            model_name=request.model_name,
            model_version=request.model_version,
            production_endpoint=request.production_endpoint,
            model_data_url=request.model_data_url,
            instance_type=request.instance_type,
            instance_count=request.instance_count
        )

        # Store deployment
        active_deployments[deployment["deployment_id"]] = {
            "type": "canary",
            "deployment": deployment
        }

        return deployment

    except Exception as e:
        logger.error(f"Failed to create canary deployment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create canary deployment: {str(e)}"
        )


@router.get("/canary/{deployment_id}")
async def get_canary_deployment(deployment_id: str):
    """
    Get canary deployment status.

    Returns current stage, traffic percentage, and metrics.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]
    if deployment_data["type"] != "canary":
        raise HTTPException(status_code=400, detail="Not a canary deployment")

    return deployment_data["deployment"]


@router.post("/canary/{deployment_id}/validate")
async def validate_canary_stage(request: StageValidationRequest):
    """
    Validate current canary stage.

    **Required Metrics:**
    - requests_processed
    - canary_error_rate
    - production_error_rate
    - canary_avg_latency
    - production_avg_latency
    """
    deployment_id = request.deployment_id

    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]

    try:
        validation = canary_deployer.validate_canary_stage(
            deployment_data["deployment"],
            request.stage_metrics
        )

        return validation

    except Exception as e:
        logger.error(f"Canary validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Canary validation failed: {str(e)}"
        )


@router.post("/canary/{deployment_id}/promote")
async def promote_canary_stage(deployment_id: str):
    """
    Promote canary to next stage.

    Call after current stage validation passes.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]

    try:
        result = canary_deployer.promote_canary_stage(
            deployment_data["deployment"]
        )

        # If completed, remove from active deployments
        if result.get("current_stage") == "completed":
            del active_deployments[deployment_id]

        return result

    except Exception as e:
        logger.error(f"Canary promotion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Canary promotion failed: {str(e)}"
        )


@router.post("/canary/{deployment_id}/rollback")
async def rollback_canary(deployment_id: str, reason: str = "Manual rollback"):
    """
    Rollback canary deployment to 100% production.
    """
    if deployment_id not in active_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment_data = active_deployments[deployment_id]

    try:
        result = canary_deployer.rollback_canary_deployment(
            deployment_data["deployment"],
            reason=reason
        )

        if result["success"]:
            del active_deployments[deployment_id]

        return result

    except Exception as e:
        logger.error(f"Canary rollback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Canary rollback failed: {str(e)}"
        )


# ============================================================================
# Prediction Comparison Endpoints
# ============================================================================

@router.post("/compare/predictions")
async def compare_predictions(request: PredictionComparisonRequest):
    """
    Compare predictions between production and candidate models.

    **Metrics Calculated:**
    - Agreement rate
    - Performance metrics (accuracy, RMSE, etc.)
    - Statistical significance tests (McNemar's, paired t-test)
    - Deployment recommendation

    **Returns:** Comprehensive comparison with recommendation.
    """
    try:
        comparison = prediction_comparator.compare_predictions(
            production_predictions=request.production_predictions,
            candidate_predictions=request.candidate_predictions,
            ground_truth=request.ground_truth,
            model_type=request.model_type
        )

        return comparison

    except Exception as e:
        logger.error(f"Prediction comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction comparison failed: {str(e)}"
        )


# ============================================================================
# Deployment Management Endpoints
# ============================================================================

@router.get("/deployments")
async def list_active_deployments():
    """
    List all active deployments (shadow + canary).
    """
    return {
        "total_deployments": len(active_deployments),
        "deployments": [
            {
                "deployment_id": dep_id,
                "type": data["type"],
                "model_name": data["deployment"]["model_name"],
                "model_version": data["deployment"]["model_version"],
                "current_stage": data["deployment"].get("current_stage", data["deployment"].get("state"))
            }
            for dep_id, data in active_deployments.items()
        ]
    }


@router.get("/health")
async def deployment_health():
    """
    Check deployment service health.
    """
    return {
        "status": "healthy",
        "components": {
            "shadow_deployer": "ok",
            "canary_deployer": "ok",
            "prediction_comparator": "ok"
        },
        "active_deployments": len(active_deployments),
        "version": "1.0.0",
        "phase": "5_week_44-45"
    }
