"""
Multi-Cloud Cost Tracking API Routes
=====================================

Unified API endpoints for AWS, GCP, and Azure cost tracking.
Phase 3 - Multi-Cloud Support

Author: PromptOps Team
Date: 2026-05-01
Phase: 3 - Multi-Cloud
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2-aws'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase3-gcp'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase3-azure'))

from cost_explorer import AWSCostExplorer
from gcp_cost_tracking import GCPCostTracker
from azure_cost_tracking import AzureCostTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multicloud/cost", tags=["multi-cloud-cost"])


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ALL = "all"


class CostSummary(BaseModel):
    """Cost summary for a single provider."""
    cloud_provider: str
    current_month_cost: float
    previous_month_cost: float
    month_over_month_change: float
    forecast_30_day: float
    currency: str = "USD"
    top_services: List[Dict[str, Any]] = []
    recommendations_count: int = 0


class MultiCloudCostSummary(BaseModel):
    """Complete multi-cloud cost summary."""
    total_current_cost: float
    total_previous_cost: float
    total_forecast: float
    currency: str = "USD"
    providers: Dict[str, CostSummary]
    generated_at: str


class CostComparison(BaseModel):
    """Cost comparison across providers."""
    service_type: str
    aws_cost: float
    gcp_cost: float
    azure_cost: float
    cheapest_provider: str
    savings_opportunity: float


def get_aws_cost_summary() -> Optional[CostSummary]:
    """
    Get AWS cost summary.

    Returns:
        AWS cost summary or None if unavailable
    """
    try:
        cost_explorer = AWSCostExplorer(region='us-east-1')

        # Get current month cost
        current_cost = cost_explorer.get_total_cost(days=30)
        current_total = current_cost['total_cost']

        # Get previous month cost
        previous_cost = cost_explorer.get_total_cost(days=60)
        previous_total = previous_cost['total_cost'] - current_total

        # Calculate change
        if previous_total > 0:
            change = ((current_total - previous_total) / previous_total) * 100
        else:
            change = 0.0

        # Get forecast
        forecast = cost_explorer.get_cost_forecast(days=30)
        forecast_total = forecast['forecast_cost']

        # Get top services
        by_service = cost_explorer.get_cost_by_service(days=30)
        top_services = sorted(by_service, key=lambda x: x['total_cost'], reverse=True)[:5]

        # Get recommendations count
        recommendations = cost_explorer.get_cost_optimization_recommendations()

        return CostSummary(
            cloud_provider='aws',
            current_month_cost=current_total,
            previous_month_cost=previous_total,
            month_over_month_change=change,
            forecast_30_day=forecast_total,
            top_services=top_services,
            recommendations_count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Failed to get AWS cost summary: {e}")
        return None


def get_gcp_cost_summary() -> Optional[CostSummary]:
    """
    Get GCP cost summary.

    Returns:
        GCP cost summary or None if unavailable
    """
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.warning("GCP_PROJECT_ID not configured")
            return None

        cost_tracker = GCPCostTracker(project_id=project_id)

        # Get cost data
        month_cost = cost_tracker.get_month_to_date_cost()
        current_total = month_cost['total_cost']
        previous_total = 0.0  # Would need historical data

        # Get forecast
        forecast = cost_tracker.get_cost_forecast(days=30)
        forecast_total = forecast['forecast_cost']

        # Get top services
        by_service = cost_tracker.get_cost_by_service(days=30)
        top_services = sorted(by_service, key=lambda x: x['total_cost'], reverse=True)[:5]

        # Get recommendations count
        recommendations = cost_tracker.get_cost_optimization_recommendations()

        return CostSummary(
            cloud_provider='gcp',
            current_month_cost=current_total,
            previous_month_cost=previous_total,
            month_over_month_change=0.0,
            forecast_30_day=forecast_total,
            top_services=top_services,
            recommendations_count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Failed to get GCP cost summary: {e}")
        return None


def get_azure_cost_summary() -> Optional[CostSummary]:
    """
    Get Azure cost summary.

    Returns:
        Azure cost summary or None if unavailable
    """
    try:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            logger.warning("AZURE_SUBSCRIPTION_ID not configured")
            return None

        cost_tracker = AzureCostTracker(subscription_id=subscription_id)

        # Get cost data
        month_cost = cost_tracker.get_month_to_date_cost()
        current_total = month_cost['total_cost']
        previous_total = 0.0  # Would need historical data

        # Get forecast
        forecast = cost_tracker.get_cost_forecast(days=30)
        forecast_total = forecast['forecast_cost']

        # Get top services
        by_service = cost_tracker.get_cost_by_service(days=30)
        top_services = sorted(by_service, key=lambda x: x['total_cost'], reverse=True)[:5]

        # Get recommendations count
        recommendations = cost_tracker.get_cost_optimization_recommendations()

        return CostSummary(
            cloud_provider='azure',
            current_month_cost=current_total,
            previous_month_cost=previous_total,
            month_over_month_change=0.0,
            forecast_30_day=forecast_total,
            top_services=top_services,
            recommendations_count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Failed to get Azure cost summary: {e}")
        return None


@router.get("/summary", response_model=MultiCloudCostSummary)
async def get_multi_cloud_cost_summary() -> MultiCloudCostSummary:
    """
    Get complete cost summary across all cloud providers.

    Returns:
        Multi-cloud cost summary
    """
    providers_summary = {}
    total_current = 0.0
    total_previous = 0.0
    total_forecast = 0.0

    # Get AWS costs
    aws_summary = get_aws_cost_summary()
    if aws_summary:
        providers_summary['aws'] = aws_summary
        total_current += aws_summary.current_month_cost
        total_previous += aws_summary.previous_month_cost
        total_forecast += aws_summary.forecast_30_day

    # Get GCP costs
    gcp_summary = get_gcp_cost_summary()
    if gcp_summary:
        providers_summary['gcp'] = gcp_summary
        total_current += gcp_summary.current_month_cost
        total_previous += gcp_summary.previous_month_cost
        total_forecast += gcp_summary.forecast_30_day

    # Get Azure costs (when available)
    azure_summary = get_azure_cost_summary()
    if azure_summary:
        providers_summary['azure'] = azure_summary
        total_current += azure_summary.current_month_cost
        total_previous += azure_summary.previous_month_cost
        total_forecast += azure_summary.forecast_30_day

    return MultiCloudCostSummary(
        total_current_cost=total_current,
        total_previous_cost=total_previous,
        total_forecast=total_forecast,
        providers=providers_summary,
        generated_at=datetime.utcnow().isoformat()
    )


@router.get("/by-provider", response_model=List[Dict[str, Any]])
async def get_cost_by_provider() -> List[Dict[str, Any]]:
    """
    Get cost breakdown by cloud provider.

    Returns:
        List of provider costs
    """
    results = []

    # AWS
    aws_summary = get_aws_cost_summary()
    if aws_summary:
        results.append({
            'provider': 'aws',
            'current_month': aws_summary.current_month_cost,
            'forecast': aws_summary.forecast_30_day,
            'percentage': 0.0  # Will be calculated
        })

    # GCP
    gcp_summary = get_gcp_cost_summary()
    if gcp_summary:
        results.append({
            'provider': 'gcp',
            'current_month': gcp_summary.current_month_cost,
            'forecast': gcp_summary.forecast_30_day,
            'percentage': 0.0
        })

    # Azure
    azure_summary = get_azure_cost_summary()
    if azure_summary:
        results.append({
            'provider': 'azure',
            'current_month': azure_summary.current_month_cost,
            'forecast': azure_summary.forecast_30_day,
            'percentage': 0.0
        })

    # Calculate percentages
    total = sum(r['current_month'] for r in results)
    if total > 0:
        for result in results:
            result['percentage'] = (result['current_month'] / total) * 100

    return results


@router.get("/comparison", response_model=List[CostComparison])
async def get_cost_comparison() -> List[CostComparison]:
    """
    Compare costs for similar services across providers.

    Returns:
        List of service cost comparisons
    """
    # Service mapping between providers
    service_mappings = [
        {
            'service_type': 'Compute',
            'aws': ['Amazon Elastic Compute Cloud', 'EC2'],
            'gcp': ['Compute Engine'],
            'azure': ['Virtual Machines']
        },
        {
            'service_type': 'Storage',
            'aws': ['Amazon Simple Storage Service', 'S3'],
            'gcp': ['Cloud Storage'],
            'azure': ['Blob Storage']
        },
        {
            'service_type': 'Database',
            'aws': ['Amazon Relational Database Service', 'RDS'],
            'gcp': ['Cloud SQL'],
            'azure': ['SQL Database']
        },
        {
            'service_type': 'Serverless',
            'aws': ['AWS Lambda'],
            'gcp': ['Cloud Functions', 'Cloud Run'],
            'azure': ['Functions']
        },
        {
            'service_type': 'Load Balancing',
            'aws': ['Elastic Load Balancing', 'ELB'],
            'gcp': ['Cloud Load Balancing'],
            'azure': ['Load Balancer']
        }
    ]

    comparisons = []

    # Get cost data
    aws_summary = get_aws_cost_summary()
    gcp_summary = get_gcp_cost_summary()
    azure_summary = get_azure_cost_summary()

    for mapping in service_mappings:
        aws_cost = 0.0
        gcp_cost = 0.0
        azure_cost = 0.0

        # AWS costs
        if aws_summary:
            for service in aws_summary.top_services:
                if any(name in service['service_name'] for name in mapping['aws']):
                    aws_cost += service['total_cost']

        # GCP costs
        if gcp_summary:
            for service in gcp_summary.top_services:
                if any(name in service['service_name'] for name in mapping['gcp']):
                    gcp_cost += service['total_cost']

        # Azure costs
        if azure_summary:
            for service in azure_summary.top_services:
                if any(name in service['service_name'] for name in mapping['azure']):
                    azure_cost += service['total_cost']

        # Find cheapest
        costs = {
            'aws': aws_cost,
            'gcp': gcp_cost,
            'azure': azure_cost
        }
        cheapest = min(costs, key=costs.get)
        cheapest_cost = costs[cheapest]

        # Calculate savings
        total_cost = sum(costs.values())
        if cheapest_cost > 0 and total_cost > cheapest_cost:
            savings = total_cost - cheapest_cost
        else:
            savings = 0.0

        comparisons.append(CostComparison(
            service_type=mapping['service_type'],
            aws_cost=aws_cost,
            gcp_cost=gcp_cost,
            azure_cost=azure_cost,
            cheapest_provider=cheapest,
            savings_opportunity=savings
        ))

    return comparisons


@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_multi_cloud_recommendations() -> List[Dict[str, Any]]:
    """
    Get cost optimization recommendations across all providers.

    Returns:
        List of recommendations
    """
    all_recommendations = []

    # AWS recommendations
    try:
        aws_cost_explorer = AWSCostExplorer(region='us-east-1')
        aws_recs = aws_cost_explorer.get_cost_optimization_recommendations()
        for rec in aws_recs:
            rec['cloud_provider'] = 'aws'
            all_recommendations.append(rec)
    except Exception as e:
        logger.error(f"Failed to get AWS recommendations: {e}")

    # GCP recommendations
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        if project_id:
            gcp_cost_tracker = GCPCostTracker(project_id=project_id)
            gcp_recs = gcp_cost_tracker.get_cost_optimization_recommendations()
            for rec in gcp_recs:
                rec['cloud_provider'] = 'gcp'
                all_recommendations.append(rec)
    except Exception as e:
        logger.error(f"Failed to get GCP recommendations: {e}")

    # Azure recommendations
    try:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if subscription_id:
            azure_cost_tracker = AzureCostTracker(subscription_id=subscription_id)
            azure_recs = azure_cost_tracker.get_cost_optimization_recommendations()
            for rec in azure_recs:
                rec['cloud_provider'] = 'azure'
                all_recommendations.append(rec)
    except Exception as e:
        logger.error(f"Failed to get Azure recommendations: {e}")

    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))

    return all_recommendations


@router.get("/forecast", response_model=Dict[str, Any])
async def get_multi_cloud_forecast(days: int = 30) -> Dict[str, Any]:
    """
    Get cost forecast across all providers.

    Args:
        days: Number of days to forecast

    Returns:
        Multi-cloud cost forecast
    """
    forecasts = {}
    total_forecast = 0.0

    # AWS forecast
    try:
        aws_cost_explorer = AWSCostExplorer(region='us-east-1')
        aws_forecast = aws_cost_explorer.get_cost_forecast(days=days)
        forecasts['aws'] = aws_forecast
        total_forecast += aws_forecast['forecast_cost']
    except Exception as e:
        logger.error(f"Failed to get AWS forecast: {e}")

    # GCP forecast
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        if project_id:
            gcp_cost_tracker = GCPCostTracker(project_id=project_id)
            gcp_forecast = gcp_cost_tracker.get_cost_forecast(days=days)
            forecasts['gcp'] = gcp_forecast
            total_forecast += gcp_forecast['forecast_cost']
    except Exception as e:
        logger.error(f"Failed to get GCP forecast: {e}")

    # Azure forecast
    try:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if subscription_id:
            azure_cost_tracker = AzureCostTracker(subscription_id=subscription_id)
            azure_forecast = azure_cost_tracker.get_cost_forecast(days=days)
            forecasts['azure'] = azure_forecast
            total_forecast += azure_forecast['forecast_cost']
    except Exception as e:
        logger.error(f"Failed to get Azure forecast: {e}")

    return {
        'forecast_period': f'{days} days',
        'total_forecast': total_forecast,
        'currency': 'USD',
        'providers': forecasts,
        'generated_at': datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    providers_health = {}

    # Check AWS
    try:
        aws_cost_explorer = AWSCostExplorer(region='us-east-1')
        aws_cost_explorer.get_total_cost(days=1)
        providers_health['aws'] = 'healthy'
    except:
        providers_health['aws'] = 'unavailable'

    # Check GCP
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        if project_id:
            gcp_cost_tracker = GCPCostTracker(project_id=project_id)
            gcp_cost_tracker.test_connection()
            providers_health['gcp'] = 'healthy'
        else:
            providers_health['gcp'] = 'not_configured'
    except:
        providers_health['gcp'] = 'unavailable'

    # Check Azure
    try:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if subscription_id:
            azure_cost_tracker = AzureCostTracker(subscription_id=subscription_id)
            azure_cost_tracker.test_connection()
            providers_health['azure'] = 'healthy'
        else:
            providers_health['azure'] = 'not_configured'
    except:
        providers_health['azure'] = 'unavailable'

    return {
        'status': 'healthy',
        'service': 'multi-cloud-cost-tracking',
        'providers': providers_health,
        'timestamp': datetime.utcnow().isoformat()
    }
