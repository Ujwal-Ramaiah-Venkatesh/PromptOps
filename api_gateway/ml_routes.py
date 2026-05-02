"""
ML & Intelligence API Routes
=============================

API endpoints for ML-based features:
- Cost anomaly detection
- Cost forecasting
- Trend analysis
- Budget predictions

Phase 4 - Advanced Intelligence

Author: PromptOps Team
Date: 2026-05-01
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase4-ml'))

from anomaly_detector import CostAnomalyDetector
from cost_forecaster import CostForecaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["machine-learning"])


# Request/Response Models
class CostDataPoint(BaseModel):
    """Single cost data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    cost: float = Field(..., description="Cost amount")
    provider: Optional[str] = Field(None, description="Cloud provider (aws, gcp, azure)")


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection."""
    cost_data: List[CostDataPoint] = Field(..., description="Historical cost data")
    sensitivity: str = Field(default='medium', description="Detection sensitivity (low, medium, high)")
    train_model: bool = Field(default=True, description="Whether to train ML model")


class ForecastRequest(BaseModel):
    """Request model for cost forecasting."""
    cost_data: List[CostDataPoint] = Field(..., description="Historical cost data")
    forecast_days: int = Field(default=30, description="Number of days to forecast", ge=1, le=180)


class BudgetPredictionRequest(BaseModel):
    """Request model for budget exhaustion prediction."""
    cost_data: List[CostDataPoint] = Field(..., description="Historical cost data")
    total_budget: float = Field(..., description="Total budget", gt=0)
    spent_to_date: float = Field(..., description="Amount spent so far", ge=0)


# In-memory model storage (replace with persistent storage in production)
anomaly_models: Dict[str, CostAnomalyDetector] = {}
forecast_models: Dict[str, CostForecaster] = {}


@router.post("/anomalies/detect", response_model=Dict[str, Any])
async def detect_anomalies(request: AnomalyDetectionRequest) -> Dict[str, Any]:
    """
    Detect cost anomalies using ML and statistical methods.

    Args:
        request: Anomaly detection request with cost data

    Returns:
        Anomaly detection results
    """
    try:
        # Convert to dict format
        cost_data = [
            {'date': point.date, 'cost': point.cost}
            for point in request.cost_data
        ]

        # Initialize or get detector
        detector = CostAnomalyDetector(sensitivity=request.sensitivity)

        # Detect anomalies
        results = detector.detect_anomalies(
            cost_data=cost_data,
            train_model=request.train_model
        )

        if not results['success']:
            raise HTTPException(status_code=400, detail=results.get('error'))

        return results

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/generate", response_model=Dict[str, Any])
async def generate_forecast(request: ForecastRequest) -> Dict[str, Any]:
    """
    Generate cost forecast using time series ML.

    Args:
        request: Forecast request with historical data

    Returns:
        Cost forecast results
    """
    try:
        # Convert to dict format
        cost_data = [
            {'date': point.date, 'cost': point.cost}
            for point in request.cost_data
        ]

        # Initialize forecaster
        forecaster = CostForecaster()

        # Train model
        training_result = forecaster.train(cost_data)

        if not training_result['success']:
            raise HTTPException(status_code=400, detail=training_result.get('error'))

        # Generate forecast
        forecast = forecaster.forecast(days=request.forecast_days)

        if not forecast['success']:
            raise HTTPException(status_code=400, detail=forecast.get('error'))

        # Add training metrics
        forecast['training_metrics'] = training_result['metrics']

        return forecast

    except Exception as e:
        logger.error(f"Forecasting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast/multi-period", response_model=Dict[str, Any])
async def generate_multi_period_forecast(cost_data: List[CostDataPoint]) -> Dict[str, Any]:
    """
    Generate forecasts for multiple periods (7, 30, 90 days).

    Args:
        cost_data: Historical cost data

    Returns:
        Multi-period forecast results
    """
    try:
        # Convert to dict format
        data = [
            {'date': point.date, 'cost': point.cost}
            for point in cost_data
        ]

        # Initialize forecaster
        forecaster = CostForecaster()

        # Train model
        training_result = forecaster.train(data)

        if not training_result['success']:
            raise HTTPException(status_code=400, detail=training_result.get('error'))

        # Generate multi-period forecasts
        forecasts = forecaster.forecast_multiple_periods()

        if not forecasts['success']:
            raise HTTPException(status_code=400, detail=forecasts.get('error'))

        # Add training info
        forecasts['training_days'] = training_result['training_days']
        forecasts['training_metrics'] = training_result['metrics']

        return forecasts

    except Exception as e:
        logger.error(f"Multi-period forecasting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/predict-exhaustion", response_model=Dict[str, Any])
async def predict_budget_exhaustion(request: BudgetPredictionRequest) -> Dict[str, Any]:
    """
    Predict when budget will be exhausted.

    Args:
        request: Budget prediction request

    Returns:
        Budget exhaustion prediction
    """
    try:
        # Convert to dict format
        cost_data = [
            {'date': point.date, 'cost': point.cost}
            for point in request.cost_data
        ]

        # Initialize forecaster
        forecaster = CostForecaster()

        # Train model
        training_result = forecaster.train(cost_data)

        if not training_result['success']:
            raise HTTPException(status_code=400, detail=training_result.get('error'))

        # Predict budget exhaustion
        prediction = forecaster.predict_budget_exhaustion(
            current_budget=request.total_budget,
            spent_to_date=request.spent_to_date
        )

        if not prediction['success']:
            raise HTTPException(status_code=400, detail=prediction.get('error'))

        return prediction

    except Exception as e:
        logger.error(f"Budget prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends/analyze", response_model=Dict[str, Any])
async def analyze_trends(cost_data: List[CostDataPoint]) -> Dict[str, Any]:
    """
    Analyze cost trends using time series decomposition.

    Args:
        cost_data: Historical cost data

    Returns:
        Trend analysis results
    """
    try:
        # Convert to dict format
        data = [
            {'date': point.date, 'cost': point.cost}
            for point in cost_data
        ]

        # Initialize forecaster (used for trend analysis)
        forecaster = CostForecaster()

        # Train model
        training_result = forecaster.train(data)

        if not training_result['success']:
            raise HTTPException(status_code=400, detail=training_result.get('error'))

        # Get trend analysis
        trend = forecaster.get_trend_analysis()

        if not trend['success']:
            raise HTTPException(status_code=400, detail=trend.get('error'))

        return trend

    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/summary", response_model=Dict[str, Any])
async def get_ml_insights_summary(
    cost_data: List[CostDataPoint],
    budget: Optional[float] = None,
    spent: Optional[float] = None
) -> Dict[str, Any]:
    """
    Get comprehensive ML insights summary.

    Args:
        cost_data: Historical cost data
        budget: Optional total budget
        spent: Optional amount spent

    Returns:
        Complete ML insights
    """
    try:
        # Convert to dict format
        data = [
            {'date': point.date, 'cost': point.cost}
            for point in cost_data
        ]

        insights = {
            'generated_at': datetime.utcnow().isoformat(),
            'data_points': len(data)
        }

        # Anomaly detection
        try:
            detector = CostAnomalyDetector(sensitivity='medium')
            anomaly_results = detector.detect_anomalies(data, train_model=True)
            if anomaly_results['success']:
                insights['anomalies'] = {
                    'detected': anomaly_results['anomaly_days'],
                    'rate': anomaly_results['anomaly_rate'],
                    'severity_breakdown': anomaly_results['summary'].get('severity_breakdown'),
                    'recommendation': anomaly_results['summary'].get('recommendation')
                }
        except Exception as e:
            logger.warning(f"Anomaly detection failed in summary: {e}")
            insights['anomalies'] = {'error': str(e)}

        # Forecasting
        try:
            forecaster = CostForecaster()
            training_result = forecaster.train(data)
            if training_result['success']:
                multi_forecast = forecaster.forecast_multiple_periods()
                if multi_forecast['success']:
                    insights['forecasts'] = multi_forecast['periods']

                # Trend analysis
                trend = forecaster.get_trend_analysis()
                if trend['success']:
                    insights['trend'] = {
                        'direction': trend['trend_direction'],
                        'change_pct': trend['trend_change_pct'],
                        'interpretation': trend['interpretation']
                    }

                # Budget prediction if provided
                if budget is not None and spent is not None:
                    budget_pred = forecaster.predict_budget_exhaustion(budget, spent)
                    if budget_pred['success']:
                        insights['budget'] = {
                            'days_until_exhaustion': budget_pred.get('days_until_exhaustion'),
                            'exhaustion_date': budget_pred.get('exhaustion_date'),
                            'severity': budget_pred.get('severity'),
                            'recommendation': budget_pred.get('recommendation')
                        }
        except Exception as e:
            logger.warning(f"Forecasting failed in summary: {e}")
            insights['forecasts'] = {'error': str(e)}

        return {
            'success': True,
            'insights': insights
        }

    except Exception as e:
        logger.error(f"ML insights summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    ml_libraries = {
        'scikit-learn': False,
        'prophet': False,
        'pandas': False,
        'numpy': False
    }

    # Check ML libraries
    try:
        import sklearn
        ml_libraries['scikit-learn'] = True
    except:
        pass

    try:
        import prophet
        ml_libraries['prophet'] = True
    except:
        pass

    try:
        import pandas
        ml_libraries['pandas'] = True
    except:
        pass

    try:
        import numpy
        ml_libraries['numpy'] = True
    except:
        pass

    all_healthy = all(ml_libraries.values())

    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'service': 'ml-intelligence',
        'libraries': ml_libraries,
        'features': {
            'anomaly_detection': ml_libraries['scikit-learn'],
            'forecasting': ml_libraries['prophet'],
            'trend_analysis': ml_libraries['pandas']
        },
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """
    Get status of loaded ML models.

    Returns:
        Model status information
    """
    return {
        'anomaly_models': {
            'count': len(anomaly_models),
            'models': list(anomaly_models.keys())
        },
        'forecast_models': {
            'count': len(forecast_models),
            'models': list(forecast_models.keys())
        },
        'timestamp': datetime.utcnow().isoformat()
    }
