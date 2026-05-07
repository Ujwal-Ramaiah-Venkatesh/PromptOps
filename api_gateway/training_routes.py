"""
Training Pipeline API Routes for PromptOps
==========================================

API endpoints for ML model training:
- Training job generation
- Data validation
- Cost estimation
- Job submission and tracking

Author: Backend Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Add phase5-mlops to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-mlops'))

from training.sagemaker_training_generator import SageMakerTrainingGenerator
from training.training_data_validator import TrainingDataValidator
from training.mlflow_experiment_tracker import MLflowExperimentTracker
from training.training_cost_estimator import TrainingCostEstimator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/training", tags=["training"])

# Initialize components
training_generator = SageMakerTrainingGenerator()
data_validator = TrainingDataValidator()
experiment_tracker = MLflowExperimentTracker()
cost_estimator = TrainingCostEstimator()


# ============================================================================
# Request/Response Models
# ============================================================================

class TrainingJobRequest(BaseModel):
    """Request model for training job generation."""
    model_type: str = Field(..., description="Model type from ML intent")
    intent_params: Dict[str, Any] = Field(..., description="Parameters from ML classifier")
    s3_data_path: str = Field(..., description="S3 path to training data")
    s3_output_path: str = Field(..., description="S3 path for model artifacts")
    role_arn: str = Field(..., description="IAM role ARN for SageMaker")

    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "churn_prediction",
                "intent_params": {
                    "model_type": "churn_prediction",
                    "time_range": "90_days",
                    "data_source": "user_activity"
                },
                "s3_data_path": "s3://promptops-ml-data/churn/input",
                "s3_output_path": "s3://promptops-ml-models/churn/output",
                "role_arn": "arn:aws:iam::123456789012:role/PromptOpsSageMakerRole"
            }
        }


class TrainingJobResponse(BaseModel):
    """Response model for training job."""
    success: bool
    job_name: str
    job_arn: Optional[str] = None
    job_config: Dict[str, Any]
    cost_estimate: Dict[str, Any]
    mlflow_run_id: Optional[str] = None
    status: str
    message: str
    error: Optional[str] = None


class DataValidationRequest(BaseModel):
    """Request model for data validation."""
    data_path: str = Field(..., description="Path to training data")
    model_type: str = Field(..., description="Model type")
    expected_columns: Optional[List[str]] = Field(None, description="Expected columns")
    target_column: Optional[str] = Field(None, description="Target variable column")

    class Config:
        json_schema_extra = {
            "example": {
                "data_path": "/data/churn_training.csv",
                "model_type": "classification",
                "expected_columns": ["user_id", "activity_days", "churn"],
                "target_column": "churn"
            }
        }


class DataValidationResponse(BaseModel):
    """Response model for data validation."""
    valid: bool
    data_path: str
    model_type: str
    checks_passed: int
    checks_failed: int
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    report: str


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    instance_type: str
    instance_count: int = 1
    training_duration_hours: float
    storage_gb: int = 30

    class Config:
        json_schema_extra = {
            "example": {
                "instance_type": "ml.m5.xlarge",
                "instance_count": 1,
                "training_duration_hours": 2.0,
                "storage_gb": 30
            }
        }


class CostEstimateResponse(BaseModel):
    """Response model for cost estimate."""
    instance_type: str
    instance_count: int
    instance_price_per_hour: float
    training_duration_hours: float
    storage_gb: int
    compute_cost_usd: float
    storage_cost_usd: float
    total_cost_usd: float
    cost_per_hour: float
    region: str


class InstanceRecommendationRequest(BaseModel):
    """Request model for instance recommendation."""
    model_type: str
    dataset_size_gb: float
    budget_usd: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "classification",
                "dataset_size_gb": 5.0,
                "budget_usd": 10.0
            }
        }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/jobs/create", response_model=TrainingJobResponse)
async def create_training_job(request: TrainingJobRequest):
    """
    Create SageMaker training job from ML intent.

    **Workflow:**
    1. Generate SageMaker job config from intent parameters
    2. Estimate training cost
    3. Create MLflow tracking run
    4. Submit job to SageMaker (optional)

    **Supported Model Types:**
    - classification
    - regression
    - nlp
    - time_series
    - computer_vision
    """
    try:
        logger.info(f"Creating training job for: {request.model_type}")

        # Generate training job configuration
        job_config = training_generator.generate_training_config(
            intent_params=request.intent_params,
            s3_data_path=request.s3_data_path,
            s3_output_path=request.s3_output_path,
            role_arn=request.role_arn
        )

        job_name = job_config["TrainingJobName"]

        # Estimate cost (assume 2 hours as default)
        cost_estimate = cost_estimator.estimate_from_job_config(
            job_config=job_config,
            estimated_duration_hours=2.0
        )

        # Track in MLflow
        mlflow_run_id = experiment_tracker.track_training_job(
            job_name=job_name,
            job_config=job_config,
            model_type=request.model_type
        )

        # Build response
        response = TrainingJobResponse(
            success=True,
            job_name=job_name,
            job_config=job_config,
            cost_estimate=cost_estimate,
            mlflow_run_id=mlflow_run_id,
            status="configured",
            message=f"Training job configured: {job_name}"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to create training job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create training job: {str(e)}"
        )


@router.post("/jobs/submit", response_model=TrainingJobResponse)
async def submit_training_job(request: TrainingJobRequest):
    """
    Create and submit training job to SageMaker.

    **Note:** Requires AWS credentials configured.
    Will return mock response if credentials not available.
    """
    try:
        logger.info(f"Submitting training job for: {request.model_type}")

        # Generate training job configuration
        job_config = training_generator.generate_training_config(
            intent_params=request.intent_params,
            s3_data_path=request.s3_data_path,
            s3_output_path=request.s3_output_path,
            role_arn=request.role_arn
        )

        job_name = job_config["TrainingJobName"]

        # Submit to SageMaker
        submission_result = training_generator.submit_training_job(job_config)

        # Estimate cost
        cost_estimate = cost_estimator.estimate_from_job_config(
            job_config=job_config,
            estimated_duration_hours=2.0
        )

        # Track in MLflow
        mlflow_run_id = experiment_tracker.track_training_job(
            job_name=job_name,
            job_config=job_config,
            model_type=request.model_type
        )

        # Build response
        response = TrainingJobResponse(
            success=submission_result["status"] in ["submitted", "mock_mode"],
            job_name=job_name,
            job_arn=submission_result.get("job_arn"),
            job_config=job_config,
            cost_estimate=cost_estimate,
            mlflow_run_id=mlflow_run_id,
            status=submission_result["status"],
            message=submission_result.get("message", "Job submitted"),
            error=submission_result.get("error")
        )

        return response

    except Exception as e:
        logger.error(f"Failed to submit training job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit training job: {str(e)}"
        )


@router.get("/jobs/{job_name}/status")
async def get_training_job_status(job_name: str):
    """
    Get status of training job.

    Returns job status, metrics, and cost information.
    """
    try:
        logger.info(f"Getting status for job: {job_name}")

        # Get status from SageMaker
        status = training_generator.get_training_status(job_name)

        return status

    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.post("/validate", response_model=DataValidationResponse)
async def validate_training_data(request: DataValidationRequest):
    """
    Validate training data before submitting job.

    **Checks:**
    - Dataset not empty
    - Expected columns present
    - Target column exists
    - Missing values within threshold
    - No excessive duplicates
    - Appropriate data types
    - Target distribution (classification/regression)
    - Feature variance
    """
    try:
        logger.info(f"Validating data: {request.data_path}")

        # Validate dataset
        validation_results = data_validator.validate_dataset(
            data_path=request.data_path,
            model_type=request.model_type,
            expected_columns=request.expected_columns,
            target_column=request.target_column
        )

        # Generate report
        report = data_validator.generate_validation_report(validation_results)

        # Build response
        response = DataValidationResponse(
            valid=validation_results["valid"],
            data_path=validation_results["data_path"],
            model_type=validation_results["model_type"],
            checks_passed=validation_results["checks_passed"],
            checks_failed=validation_results["checks_failed"],
            errors=validation_results["errors"],
            warnings=validation_results["warnings"],
            statistics=validation_results["statistics"],
            report=report
        )

        return response

    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Data validation failed: {str(e)}"
        )


@router.post("/cost/estimate", response_model=CostEstimateResponse)
async def estimate_training_cost(request: CostEstimateRequest):
    """
    Estimate training cost for given configuration.

    **Returns:**
    - Compute cost
    - Storage cost
    - Total cost
    - Cost per hour
    """
    try:
        logger.info(f"Estimating cost for: {request.instance_type}")

        estimate = cost_estimator.estimate_training_cost(
            instance_type=request.instance_type,
            instance_count=request.instance_count,
            training_duration_hours=request.training_duration_hours,
            storage_gb=request.storage_gb
        )

        response = CostEstimateResponse(**estimate)
        return response

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cost estimation failed: {str(e)}"
        )


@router.post("/instances/recommend")
async def recommend_instance_type(request: InstanceRecommendationRequest):
    """
    Recommend instance type based on model type and dataset size.

    **Considers:**
    - Model type (classification, regression, nlp, time_series, cv)
    - Dataset size
    - Budget constraints
    """
    try:
        logger.info(f"Recommending instance for: {request.model_type}")

        recommendation = cost_estimator.recommend_instance_type(
            model_type=request.model_type,
            dataset_size_gb=request.dataset_size_gb,
            budget_usd=request.budget_usd
        )

        return recommendation

    except Exception as e:
        logger.error(f"Instance recommendation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Instance recommendation failed: {str(e)}"
        )


@router.get("/instances/compare")
async def compare_instance_costs(
    instance_types: str,
    duration_hours: float = 1.0
):
    """
    Compare costs across different instance types.

    **Query Parameters:**
    - instance_types: Comma-separated list (e.g., "ml.m5.large,ml.m5.xlarge")
    - duration_hours: Training duration for comparison

    **Example:**
    /api/v1/training/instances/compare?instance_types=ml.m5.large,ml.m5.xlarge&duration_hours=2.0
    """
    try:
        instance_list = [i.strip() for i in instance_types.split(',')]
        logger.info(f"Comparing costs for: {instance_list}")

        comparison = cost_estimator.compare_instance_costs(
            instance_types=instance_list,
            training_duration_hours=duration_hours
        )

        return comparison

    except Exception as e:
        logger.error(f"Cost comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cost comparison failed: {str(e)}"
        )


@router.get("/health")
async def training_pipeline_health():
    """
    Check training pipeline health.

    Returns status of all components.
    """
    return {
        "status": "healthy",
        "components": {
            "sagemaker_generator": "ok",
            "data_validator": "ok",
            "mlflow_tracker": "ok" if experiment_tracker.mlflow_available else "mock_mode",
            "cost_estimator": "ok"
        },
        "version": "1.0.0",
        "phase": "5_week_42-43"
    }
