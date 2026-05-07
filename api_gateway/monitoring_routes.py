"""
Monitoring API Routes for PromptOps
===================================

API endpoints for ML model monitoring:
- Performance metrics (accuracy, latency, throughput)
- Drift detection (prediction, concept, feature drift)
- Auto-retrain triggers
- Monitoring dashboard data

Author: Backend Engineer - Phase 5 Week 46-47
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

from monitoring.performance_monitor import PerformanceMonitor
from monitoring.drift_detector import DriftDetector
from monitoring.auto_retrain_trigger import AutoRetrainTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

# Initialize components
# Note: In production, these would be managed per-model in a database
active_monitors = {}  # model_name -> PerformanceMonitor
drift_detector = DriftDetector()
retrain_trigger = AutoRetrainTrigger()


# ============================================================================
# Request/Response Models
# ============================================================================

class MonitorCreateRequest(BaseModel):
    """Request to create performance monitor."""
    model_name: str
    endpoint_name: str
    window_size: int = 1000

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "churn-prediction",
                "endpoint_name": "churn-prediction-prod",
                "window_size": 1000
            }
        }


class PredictionRecordRequest(BaseModel):
    """Request to record a prediction."""
    model_name: str
    prediction: Any
    ground_truth: Optional[Any] = None
    latency_ms: float = 0.0
    error: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "churn-prediction",
                "prediction": 1,
                "ground_truth": 1,
                "latency_ms": 45.2,
                "error": False
            }
        }


class DriftDetectionRequest(BaseModel):
    """Request for drift detection."""
    reference_predictions: List[Any]
    current_predictions: List[Any]
    prediction_type: str = "classification"

    class Config:
        json_schema_extra = {
            "example": {
                "reference_predictions": [0, 1, 0, 1, 0],
                "current_predictions": [0, 1, 1, 1, 0],
                "prediction_type": "classification"
            }
        }


class ConceptDriftRequest(BaseModel):
    """Request for concept drift detection."""
    reference_data: Dict[str, List[Any]]
    current_data: Dict[str, List[Any]]
    model_type: str = "classification"

    class Config:
        json_schema_extra = {
            "example": {
                "reference_data": {
                    "predictions": [0, 1, 0],
                    "ground_truth": [0, 1, 0]
                },
                "current_data": {
                    "predictions": [0, 1, 1],
                    "ground_truth": [0, 1, 0]
                },
                "model_type": "classification"
            }
        }


class RetrainCheckRequest(BaseModel):
    """Request to check retrain conditions."""
    model_name: str
    performance_metrics: Optional[Dict[str, Any]] = None
    drift_results: Optional[Dict[str, Any]] = None
    data_stats: Optional[Dict[str, Any]] = None
    last_training_date: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "churn-prediction",
                "drift_results": {
                    "drift_detected": True,
                    "drift_score": 0.15
                }
            }
        }


# ============================================================================
# Performance Monitoring Endpoints
# ============================================================================

@router.post("/monitors/create")
async def create_monitor(request: MonitorCreateRequest):
    """
    Create performance monitor for a model.

    Starts tracking predictions, latency, errors, and quality metrics.
    """
    try:
        monitor = PerformanceMonitor(
            model_name=request.model_name,
            endpoint_name=request.endpoint_name,
            window_size=request.window_size
        )

        active_monitors[request.model_name] = monitor

        return {
            "success": True,
            "model_name": request.model_name,
            "endpoint_name": request.endpoint_name,
            "window_size": request.window_size,
            "message": f"Monitor created for {request.model_name}"
        }

    except Exception as e:
        logger.error(f"Failed to create monitor: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create monitor: {str(e)}"
        )


@router.post("/predictions/record")
async def record_prediction(request: PredictionRecordRequest):
    """
    Record a prediction for monitoring.

    Call this endpoint for each prediction made by the model.
    """
    if request.model_name not in active_monitors:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor not found for model: {request.model_name}"
        )

    try:
        monitor = active_monitors[request.model_name]

        monitor.record_prediction(
            prediction=request.prediction,
            ground_truth=request.ground_truth,
            latency_ms=request.latency_ms,
            error=request.error
        )

        return {
            "success": True,
            "model_name": request.model_name,
            "total_predictions": monitor.total_requests
        }

    except Exception as e:
        logger.error(f"Failed to record prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record prediction: {str(e)}"
        )


@router.get("/metrics/{model_name}")
async def get_metrics(model_name: str):
    """
    Get current performance metrics for a model.

    **Returns:**
    - Throughput (requests/second)
    - Latency (p50, p95, p99)
    - Error rates
    - Quality metrics (accuracy/RMSE if ground truth available)
    """
    if model_name not in active_monitors:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor not found for model: {model_name}"
        )

    try:
        monitor = active_monitors[model_name]
        metrics = monitor.get_current_metrics()

        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/metrics/{model_name}/cloudwatch")
async def get_cloudwatch_metrics(
    model_name: str,
    hours: int = 1,
    period: int = 300
):
    """
    Get CloudWatch metrics for SageMaker endpoint.

    **Query Parameters:**
    - hours: Number of hours to look back (default: 1)
    - period: Aggregation period in seconds (default: 300)
    """
    if model_name not in active_monitors:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor not found for model: {model_name}"
        )

    try:
        monitor = active_monitors[model_name]

        from datetime import datetime, timedelta
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        metrics = monitor.get_cloudwatch_metrics(
            start_time=start_time,
            end_time=end_time,
            period=period
        )

        return metrics

    except Exception as e:
        logger.error(f"Failed to get CloudWatch metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CloudWatch metrics: {str(e)}"
        )


@router.post("/degradation/check")
async def check_degradation(
    model_name: str,
    baseline_metrics: Dict[str, Any]
):
    """
    Check if model performance has degraded compared to baseline.

    **Baseline metrics should include:**
    - quality (accuracy or RMSE)
    - errors (error_rate)
    - latency (p95_ms)
    """
    if model_name not in active_monitors:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor not found for model: {model_name}"
        )

    try:
        monitor = active_monitors[model_name]
        degradation = monitor.check_performance_degradation(baseline_metrics)

        return degradation

    except Exception as e:
        logger.error(f"Failed to check degradation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check degradation: {str(e)}"
        )


# ============================================================================
# Drift Detection Endpoints
# ============================================================================

@router.post("/drift/prediction")
async def detect_prediction_drift(request: DriftDetectionRequest):
    """
    Detect drift in prediction distribution.

    **Statistical Tests:**
    - Classification: Chi-square, Jensen-Shannon divergence, PSI
    - Regression: Kolmogorov-Smirnov, Wasserstein distance

    **Returns:** Drift detected (yes/no), drift score, test results
    """
    try:
        result = drift_detector.detect_prediction_drift(
            reference_predictions=request.reference_predictions,
            current_predictions=request.current_predictions,
            prediction_type=request.prediction_type
        )

        return result

    except Exception as e:
        logger.error(f"Prediction drift detection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction drift detection failed: {str(e)}"
        )


@router.post("/drift/concept")
async def detect_concept_drift(request: ConceptDriftRequest):
    """
    Detect concept drift (change in feature-target relationship).

    **Requires ground truth labels** to compare model performance
    on reference vs current data.

    **Returns:** Drift detected, accuracy/RMSE comparison
    """
    try:
        result = drift_detector.detect_concept_drift(
            reference_data=request.reference_data,
            current_data=request.current_data,
            model_type=request.model_type
        )

        return result

    except Exception as e:
        logger.error(f"Concept drift detection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Concept drift detection failed: {str(e)}"
        )


# ============================================================================
# Auto-Retrain Endpoints
# ============================================================================

@router.post("/retrain/check")
async def check_retrain_conditions(request: RetrainCheckRequest):
    """
    Check if model should be retrained.

    **Checks:**
    - Performance degradation
    - Drift detection
    - Scheduled retrain
    - Data availability

    **Returns:** Decision (yes/no), trigger type, urgency
    """
    try:
        # Parse last_training_date if provided
        last_training_date = None
        if request.last_training_date:
            from datetime import datetime
            last_training_date = datetime.fromisoformat(request.last_training_date)

        decision = retrain_trigger.check_retrain_conditions(
            performance_metrics=request.performance_metrics,
            drift_results=request.drift_results,
            data_stats=request.data_stats,
            last_training_date=last_training_date
        )

        return decision

    except Exception as e:
        logger.error(f"Retrain check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Retrain check failed: {str(e)}"
        )


@router.post("/retrain/trigger")
async def trigger_retrain(
    model_name: str,
    model_version: str,
    trigger_type: str,
    reasons: List[str],
    urgency: str = "normal"
):
    """
    Manually trigger model retraining.

    **Trigger Types:**
    - performance_degradation
    - drift_detected
    - scheduled
    - data_threshold
    - manual
    """
    try:
        retrain_job = retrain_trigger.trigger_retrain(
            model_name=model_name,
            model_version=model_version,
            trigger_type=trigger_type,
            reasons=reasons,
            urgency=urgency
        )

        return retrain_job

    except Exception as e:
        logger.error(f"Failed to trigger retrain: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger retrain: {str(e)}"
        )


@router.get("/retrain/history")
async def get_retrain_history(
    model_name: Optional[str] = None,
    limit: int = 10
):
    """
    Get retrain history.

    **Query Parameters:**
    - model_name: Optional filter by model name
    - limit: Maximum number of records (default: 10)
    """
    try:
        history = retrain_trigger.get_retrain_history(
            model_name=model_name,
            limit=limit
        )

        return {
            "total": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Failed to get retrain history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get retrain history: {str(e)}"
        )


@router.get("/retrain/config")
async def get_retrain_config():
    """
    Get current retrain trigger configurations.
    """
    return retrain_trigger.get_trigger_configs()


@router.put("/retrain/config/{trigger_type}")
async def update_retrain_config(
    trigger_type: str,
    config: Dict[str, Any]
):
    """
    Update retrain trigger configuration.

    **Trigger Types:**
    - performance_degradation
    - drift_detection
    - scheduled
    - data_threshold
    """
    try:
        retrain_trigger.configure_triggers(trigger_type, config)

        return {
            "success": True,
            "trigger_type": trigger_type,
            "config": retrain_trigger.get_trigger_configs()[trigger_type]
        }

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update config: {str(e)}"
        )


# ============================================================================
# Dashboard & Status Endpoints
# ============================================================================

@router.get("/monitors")
async def list_monitors():
    """
    List all active monitors.
    """
    return {
        "total_monitors": len(active_monitors),
        "monitors": [
            {
                "model_name": name,
                "endpoint_name": monitor.endpoint_name,
                "total_requests": monitor.total_requests,
                "window_size": monitor.window_size
            }
            for name, monitor in active_monitors.items()
        ]
    }


@router.get("/health")
async def monitoring_health():
    """
    Check monitoring service health.
    """
    return {
        "status": "healthy",
        "components": {
            "performance_monitors": len(active_monitors),
            "drift_detector": "ok",
            "retrain_trigger": "ok"
        },
        "version": "1.0.0",
        "phase": "5_week_46-47"
    }


@router.delete("/monitors/{model_name}")
async def delete_monitor(model_name: str):
    """
    Delete performance monitor for a model.
    """
    if model_name not in active_monitors:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor not found for model: {model_name}"
        )

    del active_monitors[model_name]

    return {
        "success": True,
        "model_name": model_name,
        "message": f"Monitor deleted for {model_name}"
    }
