"""
AWS Cost Explorer Integration Module
=====================================

Fetches and analyzes AWS cost data using Cost Explorer API.
ENH-004: Cost Optimization Dashboard

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Cost Optimization (ENH-004)
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AWSCostExplorer:
    """
    Fetches and analyzes AWS cost data.

    Uses AWS Cost Explorer API (Free Tier includes limited queries).
    Note: $0.01 per API request after free tier.
    """

    def __init__(self, region: str = 'us-east-1', profile: Optional[str] = None):
        """
        Initialize AWS Cost Explorer client.

        Args:
            region: AWS region (Cost Explorer is global but needs region)
            profile: AWS CLI profile name (default: None uses default profile)
        """
        self.region = region
        self.profile = profile

        # Initialize boto3 session
        if profile:
            self.session = boto3.Session(profile_name=profile, region_name=region)
        else:
            self.session = boto3.Session(region_name=region)

        # Create Cost Explorer client
        self.ce_client = self.session.client('ce', region_name='us-east-1')  # CE is global

        logger.info("AWS Cost Explorer initialized")

    def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
        granularity: str = 'DAILY',
        metrics: List[str] = None,
        group_by: Optional[List[Dict[str, str]]] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get cost and usage data from AWS Cost Explorer.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics (e.g., ['UnblendedCost', 'UsageQuantity'])
            group_by: Group results by dimensions (e.g., [{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
            filter_dict: Filter expression for AWS Cost Explorer

        Returns:
            Cost and usage data
        """
        if metrics is None:
            metrics = ['UnblendedCost']

        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity,
                'Metrics': metrics
            }

            if group_by:
                params['GroupBy'] = group_by

            if filter_dict:
                params['Filter'] = filter_dict

            response = self.ce_client.get_cost_and_usage(**params)
            return response

        except ClientError as e:
            logger.error(f"Failed to get cost and usage: {e}")
            raise

    def get_total_cost(self, days: int = 30) -> Dict[str, Any]:
        """
        Get total cost for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dict with total cost and daily breakdown
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = self.get_cost_and_usage(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            granularity='DAILY',
            metrics=['UnblendedCost']
        )

        # Calculate total
        total_cost = 0.0
        daily_costs = []

        for result in response.get('ResultsByTime', []):
            date = result['TimePeriod']['Start']
            amount = float(result['Total']['UnblendedCost']['Amount'])
            total_cost += amount

            daily_costs.append({
                'date': date,
                'cost': amount,
                'unit': result['Total']['UnblendedCost']['Unit']
            })

        return {
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_costs': daily_costs
        }

    def get_cost_by_service(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost breakdown by AWS service.

        Args:
            days: Number of days to look back

        Returns:
            Dict with cost by service
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = self.get_cost_and_usage(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            granularity='MONTHLY',
            metrics=['UnblendedCost'],
            group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        # Parse service costs
        services = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])

                if service_name not in services:
                    services[service_name] = 0.0
                services[service_name] += cost

        # Sort by cost descending
        sorted_services = sorted(
            [{'service': k, 'cost': round(v, 2)} for k, v in services.items()],
            key=lambda x: x['cost'],
            reverse=True
        )

        total_cost = sum(s['cost'] for s in sorted_services)

        return {
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'period_days': days,
            'services': sorted_services
        }

    def get_cost_by_region(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost breakdown by AWS region.

        Args:
            days: Number of days to look back

        Returns:
            Dict with cost by region
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = self.get_cost_and_usage(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            granularity='MONTHLY',
            metrics=['UnblendedCost'],
            group_by=[{'Type': 'DIMENSION', 'Key': 'REGION'}]
        )

        # Parse region costs
        regions = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                region_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])

                if region_name not in regions:
                    regions[region_name] = 0.0
                regions[region_name] += cost

        # Sort by cost descending
        sorted_regions = sorted(
            [{'region': k, 'cost': round(v, 2)} for k, v in regions.items()],
            key=lambda x: x['cost'],
            reverse=True
        )

        total_cost = sum(r['cost'] for r in sorted_regions)

        return {
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'period_days': days,
            'regions': sorted_regions
        }

    def get_cost_forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost forecast for next N days.

        Args:
            days: Number of days to forecast

        Returns:
            Dict with forecasted cost
        """
        try:
            start_date = datetime.utcnow().date()
            end_date = start_date + timedelta(days=days)

            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )

            forecast_amount = float(response['Total']['Amount'])

            return {
                'forecasted_cost': round(forecast_amount, 2),
                'currency': 'USD',
                'forecast_period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'confidence': 'MEDIUM'  # AWS doesn't provide confidence, this is placeholder
            }

        except ClientError as e:
            logger.error(f"Failed to get cost forecast: {e}")
            return {
                'forecasted_cost': 0.0,
                'error': str(e)
            }

    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get cost by service for analysis
        service_costs = self.get_cost_by_service(days=30)

        # Recommendation 1: Top cost drivers
        top_services = service_costs['services'][:5]
        if top_services:
            recommendations.append({
                'id': 'top-cost-drivers',
                'title': 'Review Top Cost Drivers',
                'description': f"Your top 5 services account for ${sum(s['cost'] for s in top_services):.2f}/month",
                'services': [s['service'] for s in top_services],
                'potential_savings': 0.0,
                'priority': 'high',
                'category': 'analysis'
            })

        # Recommendation 2: EC2 Reserved Instances (if EC2 cost is high)
        ec2_cost = next((s['cost'] for s in service_costs['services'] if 'EC2' in s['service']), 0)
        if ec2_cost > 100:
            recommendations.append({
                'id': 'ec2-reserved-instances',
                'title': 'Consider EC2 Reserved Instances',
                'description': f"EC2 costs: ${ec2_cost:.2f}/month. RIs can save 40-60%",
                'potential_savings': round(ec2_cost * 0.5, 2),
                'priority': 'high',
                'category': 'compute',
                'action': 'Purchase 1-year Reserved Instances for stable workloads'
            })

        # Recommendation 3: S3 Intelligent-Tiering
        s3_cost = next((s['cost'] for s in service_costs['services'] if 'S3' in s['service']), 0)
        if s3_cost > 50:
            recommendations.append({
                'id': 's3-intelligent-tiering',
                'title': 'Enable S3 Intelligent-Tiering',
                'description': f"S3 costs: ${s3_cost:.2f}/month. Auto-tiering can save 20-30%",
                'potential_savings': round(s3_cost * 0.25, 2),
                'priority': 'medium',
                'category': 'storage',
                'action': 'Enable Intelligent-Tiering for infrequently accessed data'
            })

        # Recommendation 4: Delete unused resources
        recommendations.append({
            'id': 'delete-unused-resources',
            'title': 'Identify and Delete Unused Resources',
            'description': 'Scan for stopped EC2 instances, unattached EBS volumes, old snapshots',
            'potential_savings': round(service_costs['total_cost'] * 0.15, 2),
            'priority': 'medium',
            'category': 'general',
            'action': 'Run cleanup audit for resources with no activity in 30 days'
        })

        return recommendations

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dict with all cost metrics
        """
        # Get data for last 30 days
        total_cost_data = self.get_total_cost(days=30)
        service_costs = self.get_cost_by_service(days=30)
        region_costs = self.get_cost_by_region(days=30)
        forecast = self.get_cost_forecast(days=30)
        recommendations = self.get_cost_optimization_recommendations()

        # Calculate month-over-month change
        current_month_cost = total_cost_data['total_cost']
        previous_month_data = self.get_total_cost(days=60)
        previous_month_cost = sum(
            d['cost'] for d in previous_month_data['daily_costs'][-30:]
        )

        cost_change = current_month_cost - previous_month_cost
        cost_change_percent = (cost_change / previous_month_cost * 100) if previous_month_cost > 0 else 0

        return {
            'current_month': {
                'total_cost': current_month_cost,
                'currency': 'USD',
                'start_date': total_cost_data['start_date'],
                'end_date': total_cost_data['end_date']
            },
            'previous_month': {
                'total_cost': round(previous_month_cost, 2),
                'currency': 'USD'
            },
            'change': {
                'amount': round(cost_change, 2),
                'percent': round(cost_change_percent, 1)
            },
            'forecast': forecast,
            'by_service': service_costs['services'],
            'by_region': region_costs['regions'],
            'recommendations': recommendations,
            'total_potential_savings': round(
                sum(r.get('potential_savings', 0) for r in recommendations), 2
            )
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  AWS Cost Explorer Test")
    print("  Phase 2 - ENH-004: Cost Optimization")
    print("=" * 60)

    try:
        # Initialize Cost Explorer
        cost_explorer = AWSCostExplorer(region='us-east-1')

        # Get cost summary
        print("\n[1] Fetching cost summary (last 30 days)...")
        summary = cost_explorer.get_cost_summary()

        print(f"\n📊 Cost Summary:")
        print(f"   Current Month: ${summary['current_month']['total_cost']:.2f}")
        print(f"   Previous Month: ${summary['previous_month']['total_cost']:.2f}")
        print(f"   Change: ${summary['change']['amount']:.2f} ({summary['change']['percent']:+.1f}%)")
        print(f"   Forecasted (next 30 days): ${summary['forecast']['forecasted_cost']:.2f}")

        print(f"\n💰 Top 5 Services by Cost:")
        for i, service in enumerate(summary['by_service'][:5], 1):
            print(f"   {i}. {service['service']}: ${service['cost']:.2f}")

        print(f"\n🌍 Top 5 Regions by Cost:")
        for i, region in enumerate(summary['by_region'][:5], 1):
            print(f"   {i}. {region['region']}: ${region['cost']:.2f}")

        print(f"\n💡 Cost Optimization Recommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"   {i}. {rec['title']}")
            print(f"      Potential Savings: ${rec['potential_savings']:.2f}")
            print(f"      Priority: {rec['priority']}")

        print(f"\n   Total Potential Savings: ${summary['total_potential_savings']:.2f}/month")

        print("\n" + "=" * 60)
        print("✅ Cost Explorer Test Complete")
        print("=" * 60)

    except ClientError as e:
        print(f"\n❌ AWS API Error: {e}")
        print("\nNote: Cost Explorer API requires:")
        print("1. AWS credentials configured")
        print("2. IAM permission: ce:GetCostAndUsage")
        print("3. Cost Explorer enabled in AWS Console")
    except Exception as e:
        print(f"\n❌ Error: {e}")
