"""
Tuning API Routes for PromptOps
===============================

API endpoints for hyperparameter tuning and AutoML:
- Hyperparameter tuning jobs
- Budget enforcement
- AutoML (SageMaker Autopilot)

Author: Backend Engineer - Phase 5 Week 48-49
Date: 2026-05-08
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Add phase5-mlops to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-mlops'))

from tuning.hyperparameter_tuner import HyperparameterTuner
from tuning.budget_enforcer import BudgetEnforcer
from tuning.automl_integrator import AutoMLIntegrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tuning", tags=["tuning"])

# Initialize components
tuner = HyperparameterTuner()
budget_enforcer = BudgetEnforcer()
automl_integrator = AutoMLIntegrator()


# ============================================================================
# Request/Response Models
# ============================================================================

class TuningJobRequest(BaseModel):
    """Request to create tuning job."""
    job_name: str
    model_type: str
    training_job_definition: Dict[str, Any]
    hyperparameter_ranges: Optional[Dict[str, Any]] = None
    objective_metric: Optional[Dict[str, str]] = None
    strategy: str = "bayesian"
    max_jobs: int = 20
    max_parallel_jobs: int = 2

    class Config:
        json_schema_extra = {
            "example": {
                "job_name": "tune-churn-model",
                "model_type": "xgboost",
                "training_job_definition": {},
                "strategy": "bayesian",
                "max_jobs": 20
            }
        }


class AutoMLJobRequest(BaseModel):
    """Request to create AutoML job."""
    job_name: str
    input_data_s3: str
    target_column: str
    output_s3: str
    role_arn: str
    problem_type: Optional[str] = None
    max_candidates: int = 10

    class Config:
        json_schema_extra = {
            "example": {
                "job_name": "automl-churn",
                "input_data_s3": "s3://bucket/data.csv",
                "target_column": "churn",
                "output_s3": "s3://bucket/output",
                "role_arn": "arn:aws:iam::123:role/Role"
            }
        }


# ============================================================================
# Hyperparameter Tuning Endpoints
# ============================================================================

@router.post("/jobs/create")
async def create_tuning_job(request: TuningJobRequest):
    """
    Create hyperparameter tuning job.

    **Strategies:**
    - random: Random search
    - bayesian: Bayesian optimization (default)
    - hyperband: Hyperband algorithm

    **Returns:** Tuning job configuration
    """
    try:
        # Estimate cost
        cost_estimate = budget_enforcer.estimate_tuning_cost(
            instance_type=request.training_job_definition.get("ResourceConfig", {}).get("InstanceType", "ml.m5.xlarge"),
            max_jobs=request.max_jobs,
            max_parallel_jobs=request.max_parallel_jobs
        )

        # Check budget
        budget_check = budget_enforcer.check_budget(cost_estimate["total_cost_usd"])

        if not budget_check["approved"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Budget exceeded",
                    "budget_check": budget_check,
                    "cost_estimate": cost_estimate
                }
            )

        # Create tuning job
        tuning_job = tuner.create_tuning_job(
            job_name=request.job_name,
            model_type=request.model_type,
            training_job_definition=request.training_job_definition,
            hyperparameter_ranges=request.hyperparameter_ranges,
            objective_metric=request.objective_metric,
            strategy=request.strategy,
            max_jobs=request.max_jobs,
            max_parallel_jobs=request.max_parallel_jobs
        )

        # Record spending estimate
        budget_enforcer.record_spending(
            cost=cost_estimate["total_cost_usd"],
            description=f"Tuning job: {request.job_name}"
        )

        return {
            "tuning_job": tuning_job,
            "cost_estimate": cost_estimate,
            "budget_check": budget_check
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create tuning job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_name}/status")
async def get_tuning_job_status(job_name: str):
    """Get tuning job status and results."""
    try:
        status = tuner.get_tuning_job_status(job_name)
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_name}/best")
async def get_best_hyperparameters(job_name: str):
    """Get best hyperparameters from completed tuning job."""
    try:
        best = tuner.get_best_hyperparameters(job_name)
        return best
    except Exception as e:
        logger.error(f"Failed to get best hyperparameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_name}/analyze")
async def analyze_tuning_results(job_name: str):
    """Analyze tuning job results with insights."""
    try:
        analysis = tuner.analyze_tuning_results(job_name)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_name}")
async def stop_tuning_job(job_name: str):
    """Stop running tuning job."""
    try:
        result = tuner.stop_tuning_job(job_name)
        return result
    except Exception as e:
        logger.error(f"Failed to stop job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Budget Endpoints
# ============================================================================

@router.post("/budget/check")
async def check_budget(estimated_cost: float, model_name: Optional[str] = None):
    """Check if operation is within budget."""
    try:
        result = budget_enforcer.check_budget(estimated_cost, model_name=model_name)
        return result
    except Exception as e:
        logger.error(f"Budget check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget/summary")
async def get_budget_summary():
    """Get current spending summary."""
    return budget_enforcer.get_spending_summary()


@router.post("/budget/estimate")
async def estimate_tuning_cost(
    instance_type: str,
    max_jobs: int,
    max_parallel_jobs: int,
    estimated_duration_hours: float = 1.0
):
    """Estimate cost of hyperparameter tuning job."""
    try:
        estimate = budget_enforcer.estimate_tuning_cost(
            instance_type=instance_type,
            max_jobs=max_jobs,
            max_parallel_jobs=max_parallel_jobs,
            estimated_duration_hours=estimated_duration_hours
        )
        return estimate
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AutoML Endpoints
# ============================================================================

@router.post("/automl/create")
async def create_automl_job(request: AutoMLJobRequest):
    """
    Create SageMaker Autopilot job for automated ML.

    **Problem Types:**
    - BinaryClassification
    - MulticlassClassification
    - Regression
    """
    try:
        job = automl_integrator.create_automl_job(
            job_name=request.job_name,
            input_data_s3=request.input_data_s3,
            target_column=request.target_column,
            output_s3=request.output_s3,
            role_arn=request.role_arn,
            problem_type=request.problem_type,
            max_candidates=request.max_candidates
        )
        return job
    except Exception as e:
        logger.error(f"Failed to create AutoML job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automl/{job_name}/status")
async def get_automl_status(job_name: str):
    """Get AutoML job status."""
    try:
        status = automl_integrator.get_automl_job_status(job_name)
        return status
    except Exception as e:
        logger.error(f"Failed to get AutoML status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automl/{job_name}/candidates")
async def list_automl_candidates(job_name: str, max_results: int = 10):
    """List candidate models from AutoML job."""
    try:
        candidates = automl_integrator.list_candidates(job_name, max_results=max_results)
        return {"total": len(candidates), "candidates": candidates}
    except Exception as e:
        logger.error(f"Failed to list candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@router.get("/strategies")
async def list_tuning_strategies():
    """List available tuning strategies."""
    return {
        "strategies": [
            {
                "name": "random",
                "description": "Random search - explores parameter space randomly",
                "best_for": "Quick exploration, small parameter spaces"
            },
            {
                "name": "bayesian",
                "description": "Bayesian optimization - uses probabilistic model",
                "best_for": "Expensive training jobs, medium parameter spaces (default)"
            },
            {
                "name": "hyperband",
                "description": "Hyperband - adaptive resource allocation",
                "best_for": "Large parameter spaces, early stopping friendly models"
            }
        ]
    }


@router.get("/health")
async def tuning_health():
    """Check tuning service health."""
    return {
        "status": "healthy",
        "components": {
            "hyperparameter_tuner": "ok",
            "budget_enforcer": "ok",
            "automl_integrator": "ok"
        },
        "version": "1.0.0",
        "phase": "5_week_48-49"
    }
