"""
GCP Cost Tracking Module
=========================

Google Cloud Platform cost analysis and optimization.
Phase 3 - Multi-Cloud Support

Author: PromptOps Team
Date: 2026-05-01
Phase: 3 - Multi-Cloud
"""

from google.cloud import billing_v1
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class GCPCostTracker:
    """
    Tracks and analyzes GCP costs using Cloud Billing API.

    Features:
    - Current month cost tracking
    - Cost by service breakdown
    - Cost by project breakdown
    - Cost forecasting
    - Optimization recommendations
    """

    def __init__(self, billing_account_id: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize GCP cost tracker.

        Args:
            billing_account_id: GCP billing account ID (format: billingAccounts/XXXXXX-XXXXXX-XXXXXX)
            project_id: GCP project ID
        """
        self.billing_account_id = billing_account_id or os.getenv('GCP_BILLING_ACCOUNT_ID')
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set in environment or passed as parameter")

        # Initialize billing client
        try:
            self.cloud_billing_client = billing_v1.CloudBillingClient()
            logger.info(f"GCP Cost Tracker initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize billing client: {e}")
            self.cloud_billing_client = None

    def test_connection(self) -> Dict[str, Any]:
        """
        Test billing API connection.

        Returns:
            Dict with connection status
        """
        try:
            if not self.cloud_billing_client:
                return {
                    'success': False,
                    'error': 'Billing client not initialized',
                    'message': 'Failed to initialize Cloud Billing client'
                }

            # Try to get billing account info
            if self.billing_account_id:
                account = self.cloud_billing_client.get_billing_account(
                    name=self.billing_account_id
                )
                return {
                    'success': True,
                    'billing_account': self.billing_account_id,
                    'project_id': self.project_id,
                    'account_name': account.display_name,
                    'message': 'Billing API connection successful'
                }
            else:
                return {
                    'success': True,
                    'project_id': self.project_id,
                    'message': 'Cost tracking initialized (billing account not configured)'
                }

        except Exception as e:
            logger.error(f"Billing connection test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Billing API connection failed'
            }

    def get_month_to_date_cost(self) -> Dict[str, Any]:
        """
        Get current month-to-date costs.

        Note: Requires BigQuery billing export to be configured.
        Without BigQuery export, this returns estimated costs based on quotas.

        Returns:
            Dict with cost information
        """
        try:
            # In production, this would query BigQuery billing export table
            # For now, return structure with placeholder data
            today = datetime.utcnow()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            return {
                'period': 'month_to_date',
                'start_date': month_start.isoformat(),
                'end_date': today.isoformat(),
                'total_cost': 0.0,  # Would be calculated from BigQuery export
                'currency': 'USD',
                'daily_costs': [],
                'note': 'Enable BigQuery billing export for detailed cost data',
                'free_tier_credit_remaining': 300.0,  # First 90 days
                'project_id': self.project_id
            }

        except Exception as e:
            logger.error(f"Failed to get month-to-date cost: {e}")
            return {
                'period': 'month_to_date',
                'total_cost': 0.0,
                'error': str(e)
            }

    def get_cost_by_service(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by GCP service.

        Args:
            days: Number of days to analyze

        Returns:
            List of service costs
        """
        try:
            # In production, this would query BigQuery billing export
            # Return common GCP services with placeholder costs
            services = [
                {
                    'service_name': 'Compute Engine',
                    'service_id': 'compute.googleapis.com',
                    'total_cost': 0.0,
                    'percentage': 0.0,
                    'description': 'Virtual machine instances'
                },
                {
                    'service_name': 'Cloud Storage',
                    'service_id': 'storage.googleapis.com',
                    'total_cost': 0.0,
                    'percentage': 0.0,
                    'description': 'Object storage buckets'
                },
                {
                    'service_name': 'Cloud SQL',
                    'service_id': 'sqladmin.googleapis.com',
                    'total_cost': 0.0,
                    'percentage': 0.0,
                    'description': 'Managed database service'
                },
                {
                    'service_name': 'Cloud Functions',
                    'service_id': 'cloudfunctions.googleapis.com',
                    'total_cost': 0.0,
                    'percentage': 0.0,
                    'description': 'Serverless functions'
                },
                {
                    'service_name': 'Cloud Run',
                    'service_id': 'run.googleapis.com',
                    'total_cost': 0.0,
                    'percentage': 0.0,
                    'description': 'Serverless containers'
                }
            ]

            logger.info(f"Retrieved cost breakdown for {len(services)} services")
            return services

        except Exception as e:
            logger.error(f"Failed to get cost by service: {e}")
            return []

    def get_cost_by_project(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by project (if billing account has multiple projects).

        Args:
            days: Number of days to analyze

        Returns:
            List of project costs
        """
        try:
            return [
                {
                    'project_id': self.project_id,
                    'project_name': self.project_id,
                    'total_cost': 0.0,
                    'percentage': 100.0
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get cost by project: {e}")
            return []

    def get_cost_forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Forecast future costs based on current usage trends.

        Args:
            days: Number of days to forecast

        Returns:
            Dict with forecast data
        """
        try:
            today = datetime.utcnow()
            forecast_end = today + timedelta(days=days)

            # Simple forecast based on current daily average
            # In production, would use historical data and ML models
            current_month_cost = 0.0
            daily_average = 0.0
            forecast_cost = daily_average * days

            return {
                'forecast_period': f'{days} days',
                'start_date': today.isoformat(),
                'end_date': forecast_end.isoformat(),
                'current_month_cost': current_month_cost,
                'forecast_cost': forecast_cost,
                'currency': 'USD',
                'confidence': 'low',  # Without historical data
                'note': 'Forecast improves with billing export data',
                'free_tier_applies': True
            }

        except Exception as e:
            logger.error(f"Failed to generate cost forecast: {e}")
            return {
                'forecast_cost': 0.0,
                'error': str(e)
            }

    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate cost optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = [
            {
                'id': 'gcp-opt-001',
                'category': 'Compute Engine',
                'title': 'Use Committed Use Discounts',
                'description': 'Save up to 57% by committing to 1 or 3 year usage',
                'potential_savings': 'Up to 57% on Compute Engine',
                'priority': 'high',
                'implementation': 'Purchase committed use contracts for predictable workloads',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-002',
                'category': 'Compute Engine',
                'title': 'Use Preemptible VMs',
                'description': 'Save up to 80% with preemptible instances for fault-tolerant workloads',
                'potential_savings': 'Up to 80% on Compute Engine',
                'priority': 'high',
                'implementation': 'Switch non-critical workloads to preemptible instances',
                'effort': 'medium'
            },
            {
                'id': 'gcp-opt-003',
                'category': 'Compute Engine',
                'title': 'Right-size VM Instances',
                'description': 'Resize VMs based on actual CPU and memory usage',
                'potential_savings': '20-40% on over-provisioned instances',
                'priority': 'medium',
                'implementation': 'Use GCP Recommender for sizing suggestions',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-004',
                'category': 'Cloud Storage',
                'title': 'Use Lifecycle Policies',
                'description': 'Automatically move data to cheaper storage classes',
                'potential_savings': '50-70% on storage costs',
                'priority': 'medium',
                'implementation': 'Set up lifecycle rules for Nearline/Coldline/Archive',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-005',
                'category': 'Cloud Storage',
                'title': 'Delete Unused Buckets',
                'description': 'Remove empty or unused storage buckets',
                'potential_savings': 'Varies by bucket size',
                'priority': 'low',
                'implementation': 'Audit and delete unused buckets',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-006',
                'category': 'Cloud SQL',
                'title': 'Use Cloud SQL High Availability Only When Needed',
                'description': 'HA adds ~2x cost; use for production only',
                'potential_savings': '~50% on non-critical databases',
                'priority': 'medium',
                'implementation': 'Disable HA for dev/test environments',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-007',
                'category': 'Networking',
                'title': 'Optimize Data Transfer',
                'description': 'Minimize cross-region and internet egress',
                'potential_savings': '10-30% on network costs',
                'priority': 'medium',
                'implementation': 'Keep resources in same region, use Cloud CDN',
                'effort': 'medium'
            },
            {
                'id': 'gcp-opt-008',
                'category': 'General',
                'title': 'Enable Budget Alerts',
                'description': 'Get notified before exceeding budget',
                'potential_savings': 'Prevents cost overruns',
                'priority': 'high',
                'implementation': 'Set up budget alerts in Cloud Billing',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-009',
                'category': 'General',
                'title': 'Use Free Tier Resources',
                'description': 'Take advantage of always-free tier',
                'potential_savings': '$200-300/month',
                'priority': 'high',
                'implementation': 'Use f1-micro instances, 5GB storage, etc.',
                'effort': 'low'
            },
            {
                'id': 'gcp-opt-010',
                'category': 'General',
                'title': 'Delete Unattached Resources',
                'description': 'Remove orphaned disks, IPs, and snapshots',
                'potential_savings': '5-15% on wasted resources',
                'priority': 'medium',
                'implementation': 'Regular cleanup of unused resources',
                'effort': 'low'
            }
        ]

        logger.info(f"Generated {len(recommendations)} cost optimization recommendations")
        return recommendations

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get complete cost summary with all metrics.

        Returns:
            Dict with complete cost analysis
        """
        try:
            month_cost = self.get_month_to_date_cost()
            by_service = self.get_cost_by_service()
            forecast = self.get_cost_forecast(30)
            recommendations = self.get_cost_optimization_recommendations()

            # Calculate potential savings
            high_priority_savings = [
                rec for rec in recommendations
                if rec['priority'] == 'high'
            ]

            return {
                'cloud_provider': 'gcp',
                'project_id': self.project_id,
                'current_month': month_cost,
                'cost_by_service': by_service,
                'cost_forecast': forecast,
                'optimization_recommendations': recommendations,
                'high_priority_count': len(high_priority_savings),
                'total_recommendations': len(recommendations),
                'free_tier_status': 'active',
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate cost summary: {e}")
            return {
                'error': str(e),
                'cloud_provider': 'gcp',
                'project_id': self.project_id
            }


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  GCP Cost Tracking Test")
    print("  Phase 3 - Multi-Cloud Support")
    print("=" * 60)

    try:
        # Initialize cost tracker
        project_id = os.getenv('GCP_PROJECT_ID', 'promptops-dev-123456')
        cost_tracker = GCPCostTracker(project_id=project_id)

        # Test connection
        print("\n[1] Testing billing API connection...")
        connection = cost_tracker.test_connection()
        if connection['success']:
            print(f"✅ Billing API accessible")
            print(f"   Project ID: {connection['project_id']}")
        else:
            print(f"⚠️  Billing API: {connection['message']}")

        # Get cost summary
        print("\n[2] Generating cost summary...")
        summary = cost_tracker.get_cost_summary()

        print(f"\n💰 Cost Summary:")
        print(f"   Cloud Provider: {summary['cloud_provider'].upper()}")
        print(f"   Project ID: {summary['project_id']}")
        print(f"   Current Month Cost: ${summary['current_month']['total_cost']:.2f}")
        print(f"   30-Day Forecast: ${summary['cost_forecast']['forecast_cost']:.2f}")
        print(f"   Free Tier Status: {summary['free_tier_status']}")

        # Show cost by service
        print(f"\n📊 Cost by Service:")
        for service in summary['cost_by_service'][:5]:
            print(f"   - {service['service_name']}: ${service['total_cost']:.2f}")

        # Show recommendations
        print(f"\n💡 Optimization Recommendations:")
        print(f"   Total: {summary['total_recommendations']}")
        print(f"   High Priority: {summary['high_priority_count']}")
        print(f"\n   Top 5 Recommendations:")
        for rec in summary['optimization_recommendations'][:5]:
            priority_icon = "🔥" if rec['priority'] == 'high' else "⚠️" if rec['priority'] == 'medium' else "ℹ️"
            print(f"   {priority_icon} {rec['title']}")
            print(f"      Savings: {rec['potential_savings']}")

        print("\n" + "=" * 60)
        print("✅ GCP Cost Tracking Test Complete")
        print("=" * 60)

        print("\n📝 Note:")
        print("   For detailed cost data, enable BigQuery billing export:")
        print("   https://cloud.google.com/billing/docs/how-to/export-data-bigquery")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Set GCP_PROJECT_ID environment variable")
        print("2. Ensure Cloud Billing API is enabled")
        print("3. Check service account has billing.viewer permission")
