"""
Cost Tracking and Analytics API Routes
=======================================

ENH-004: Cost optimization dashboard endpoints.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Cost Optimization
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2-aws'))

try:
    from cost_explorer import AWSCostExplorer
    COST_EXPLORER_AVAILABLE = True
except ImportError:
    COST_EXPLORER_AVAILABLE = False
    logging.warning("Cost Explorer module not available")

# Import database dependencies
try:
    from auth.dependencies import get_current_active_user, get_db
    from auth.models import User as AuthUser
    from database import crud
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database not available")

router = APIRouter(prefix="/api/v1/cost", tags=["cost"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class CostSummaryResponse(BaseModel):
    """Cost summary response."""
    current_month: Dict[str, Any]
    previous_month: Dict[str, Any]
    change: Dict[str, Any]
    forecast: Dict[str, Any]
    by_service: List[Dict[str, Any]]
    by_region: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    total_potential_savings: float


class CostByServiceResponse(BaseModel):
    """Cost breakdown by service."""
    total_cost: float
    currency: str
    period_days: int
    services: List[Dict[str, Any]]


class CostByRegionResponse(BaseModel):
    """Cost breakdown by region."""
    total_cost: float
    currency: str
    period_days: int
    regions: List[Dict[str, Any]]


class CostForecastResponse(BaseModel):
    """Cost forecast response."""
    forecasted_cost: float
    currency: str
    forecast_period_days: int
    start_date: str
    end_date: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get comprehensive cost summary.

    Returns:
    - Current month costs
    - Previous month comparison
    - Cost forecast
    - Breakdown by service and region
    - Optimization recommendations
    - Total potential savings

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured. Please set up AWS credentials."
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        summary = cost_explorer.get_cost_summary()

        logger.info(f"Cost summary fetched by {current_user.email if current_user else 'anonymous'}")
        return CostSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Failed to get cost summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cost data: {str(e)}"
        )


@router.get("/by-service", response_model=CostByServiceResponse)
async def get_cost_by_service(
    days: int = 30,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get cost breakdown by AWS service.

    **Query Parameters:**
    - days: Number of days to look back (default: 30)

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured"
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        data = cost_explorer.get_cost_by_service(days=days)

        return CostByServiceResponse(**data)

    except Exception as e:
        logger.error(f"Failed to get cost by service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service costs: {str(e)}"
        )


@router.get("/by-region", response_model=CostByRegionResponse)
async def get_cost_by_region(
    days: int = 30,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get cost breakdown by AWS region.

    **Query Parameters:**
    - days: Number of days to look back (default: 30)

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured"
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        data = cost_explorer.get_cost_by_region(days=days)

        return CostByRegionResponse(**data)

    except Exception as e:
        logger.error(f"Failed to get cost by region: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch region costs: {str(e)}"
        )


@router.get("/forecast", response_model=CostForecastResponse)
async def get_cost_forecast(
    days: int = 30,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get cost forecast for next N days.

    **Query Parameters:**
    - days: Number of days to forecast (default: 30)

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured"
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        data = cost_explorer.get_cost_forecast(days=days)

        return CostForecastResponse(**data)

    except Exception as e:
        logger.error(f"Failed to get cost forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cost forecast: {str(e)}"
        )


@router.get("/recommendations")
async def get_optimization_recommendations(
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get cost optimization recommendations.

    Returns actionable recommendations to reduce AWS costs.

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured"
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        recommendations = cost_explorer.get_cost_optimization_recommendations()

        total_savings = sum(r.get('potential_savings', 0) for r in recommendations)

        return {
            'recommendations': recommendations,
            'total_potential_savings': round(total_savings, 2),
            'count': len(recommendations)
        }

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recommendations: {str(e)}"
        )


@router.get("/total")
async def get_total_cost(
    days: int = 30,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get total cost for last N days.

    **Query Parameters:**
    - days: Number of days to look back (default: 30)

    **Requires:** Any authenticated user
    """
    if not COST_EXPLORER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cost Explorer not configured"
        )

    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')
        data = cost_explorer.get_total_cost(days=days)

        return data

    except Exception as e:
        logger.error(f"Failed to get total cost: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch total cost: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check cost tracking service health."""
    return {
        "status": "healthy",
        "service": "cost_tracking",
        "version": "2.0.0",
        "cost_explorer_available": COST_EXPLORER_AVAILABLE
    }
