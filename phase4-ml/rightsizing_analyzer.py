"""
Resource Right-Sizing Analyzer
===============================

Analyzes resource utilization and recommends optimal sizing.
Phase 4 - Advanced Intelligence

Author: PromptOps Team
Date: 2026-05-01
Phase: 4 - Advanced Intelligence
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RightSizingAnalyzer:
    """
    Analyzes resource utilization and recommends right-sizing.

    Features:
    - CPU and memory utilization analysis
    - Instance type recommendations
    - Cost savings calculations
    - Over/under-provisioned detection
    """

    # Instance types and their specifications (AWS example)
    INSTANCE_TYPES = {
        # T-series (burstable)
        't2.micro': {'vcpu': 1, 'memory_gb': 1, 'cost_per_hour': 0.0116},
        't2.small': {'vcpu': 1, 'memory_gb': 2, 'cost_per_hour': 0.023},
        't2.medium': {'vcpu': 2, 'memory_gb': 4, 'cost_per_hour': 0.0464},
        't2.large': {'vcpu': 2, 'memory_gb': 8, 'cost_per_hour': 0.0928},
        't3.micro': {'vcpu': 2, 'memory_gb': 1, 'cost_per_hour': 0.0104},
        't3.small': {'vcpu': 2, 'memory_gb': 2, 'cost_per_hour': 0.0208},
        't3.medium': {'vcpu': 2, 'memory_gb': 4, 'cost_per_hour': 0.0416},
        't3.large': {'vcpu': 2, 'memory_gb': 8, 'cost_per_hour': 0.0832},
        # M-series (general purpose)
        'm5.large': {'vcpu': 2, 'memory_gb': 8, 'cost_per_hour': 0.096},
        'm5.xlarge': {'vcpu': 4, 'memory_gb': 16, 'cost_per_hour': 0.192},
        'm5.2xlarge': {'vcpu': 8, 'memory_gb': 32, 'cost_per_hour': 0.384},
        'm5.4xlarge': {'vcpu': 16, 'memory_gb': 64, 'cost_per_hour': 0.768},
        # C-series (compute optimized)
        'c5.large': {'vcpu': 2, 'memory_gb': 4, 'cost_per_hour': 0.085},
        'c5.xlarge': {'vcpu': 4, 'memory_gb': 8, 'cost_per_hour': 0.17},
        'c5.2xlarge': {'vcpu': 8, 'memory_gb': 16, 'cost_per_hour': 0.34},
        # R-series (memory optimized)
        'r5.large': {'vcpu': 2, 'memory_gb': 16, 'cost_per_hour': 0.126},
        'r5.xlarge': {'vcpu': 4, 'memory_gb': 32, 'cost_per_hour': 0.252},
        'r5.2xlarge': {'vcpu': 8, 'memory_gb': 64, 'cost_per_hour': 0.504},
    }

    def __init__(self):
        """Initialize right-sizing analyzer."""
        logger.info("Right-Sizing Analyzer initialized")

    def analyze_resource(
        self,
        resource_id: str,
        resource_type: str,
        current_instance_type: str,
        utilization_data: List[Dict[str, Any]],
        cloud_provider: str = 'aws'
    ) -> Dict[str, Any]:
        """
        Analyze a single resource and recommend right-sizing.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource (vm, instance, etc.)
            current_instance_type: Current instance type
            utilization_data: List of utilization metrics
            cloud_provider: Cloud provider (aws, gcp, azure)

        Returns:
            Analysis results with recommendations
        """
        try:
            # Prepare utilization data
            df = pd.DataFrame(utilization_data)

            if df.empty:
                return {
                    'success': False,
                    'error': 'No utilization data provided'
                }

            # Calculate utilization statistics
            cpu_stats = self._calculate_utilization_stats(df, 'cpu_percent')
            memory_stats = self._calculate_utilization_stats(df, 'memory_percent')

            # Get current instance specs
            current_specs = self.INSTANCE_TYPES.get(current_instance_type)
            if not current_specs:
                return {
                    'success': False,
                    'error': f'Unknown instance type: {current_instance_type}'
                }

            # Determine if over/under-provisioned
            provisioning_status = self._determine_provisioning_status(cpu_stats, memory_stats)

            # Get recommendations
            recommendations = self._get_recommendations(
                current_instance_type,
                current_specs,
                cpu_stats,
                memory_stats,
                provisioning_status
            )

            # Calculate savings
            savings = self._calculate_savings(
                current_specs,
                recommendations,
                hours_per_month=730
            )

            return {
                'success': True,
                'resource_id': resource_id,
                'resource_type': resource_type,
                'cloud_provider': cloud_provider,
                'current_instance': {
                    'type': current_instance_type,
                    'vcpu': current_specs['vcpu'],
                    'memory_gb': current_specs['memory_gb'],
                    'cost_per_hour': current_specs['cost_per_hour'],
                    'cost_per_month': current_specs['cost_per_hour'] * 730
                },
                'utilization': {
                    'cpu': cpu_stats,
                    'memory': memory_stats,
                    'data_points': len(df),
                    'period_days': (df['timestamp'].max() - df['timestamp'].min()).days if 'timestamp' in df.columns else 0
                },
                'status': provisioning_status,
                'recommendations': recommendations,
                'savings': savings,
                'analysis_date': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Resource analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_utilization_stats(
        self,
        df: pd.DataFrame,
        metric: str
    ) -> Dict[str, float]:
        """Calculate utilization statistics for a metric."""
        if metric not in df.columns:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'median': 0,
                'p95': 0,
                'p99': 0
            }

        values = df[metric].dropna()

        return {
            'min': float(values.min()),
            'max': float(values.max()),
            'mean': float(values.mean()),
            'median': float(values.median()),
            'p95': float(values.quantile(0.95)),
            'p99': float(values.quantile(0.99))
        }

    def _determine_provisioning_status(
        self,
        cpu_stats: Dict[str, float],
        memory_stats: Dict[str, float]
    ) -> str:
        """Determine if resource is over/under/correctly provisioned."""
        # Use P95 for decision making
        cpu_p95 = cpu_stats['p95']
        memory_p95 = memory_stats['p95']

        # Over-provisioned: both CPU and memory < 30% at P95
        if cpu_p95 < 30 and memory_p95 < 30:
            return 'significantly_over_provisioned'
        elif cpu_p95 < 50 and memory_p95 < 50:
            return 'over_provisioned'

        # Under-provisioned: either CPU or memory > 80% at P95
        elif cpu_p95 > 80 or memory_p95 > 80:
            return 'under_provisioned'

        # Well-provisioned: 50-80% utilization
        else:
            return 'well_provisioned'

    def _get_recommendations(
        self,
        current_type: str,
        current_specs: Dict[str, Any],
        cpu_stats: Dict[str, float],
        memory_stats: Dict[str, float],
        status: str
    ) -> List[Dict[str, Any]]:
        """Generate instance type recommendations."""
        recommendations = []

        # Get required resources based on P95 + buffer
        required_cpu = cpu_stats['p95'] / 100 * current_specs['vcpu'] * 1.2  # 20% buffer
        required_memory = memory_stats['p95'] / 100 * current_specs['memory_gb'] * 1.2

        # Find suitable instance types
        suitable_types = []
        for instance_type, specs in self.INSTANCE_TYPES.items():
            if specs['vcpu'] >= required_cpu and specs['memory_gb'] >= required_memory:
                # Calculate cost difference
                cost_diff = (specs['cost_per_hour'] - current_specs['cost_per_hour']) * 730
                savings_pct = ((current_specs['cost_per_hour'] - specs['cost_per_hour']) /
                              current_specs['cost_per_hour'] * 100) if current_specs['cost_per_hour'] > 0 else 0

                suitable_types.append({
                    'instance_type': instance_type,
                    'vcpu': specs['vcpu'],
                    'memory_gb': specs['memory_gb'],
                    'cost_per_hour': specs['cost_per_hour'],
                    'cost_per_month': specs['cost_per_hour'] * 730,
                    'cost_difference': cost_diff,
                    'savings_pct': savings_pct,
                    'is_current': instance_type == current_type
                })

        # Sort by cost (cheapest first)
        suitable_types.sort(key=lambda x: x['cost_per_hour'])

        # Generate recommendations
        if status in ['over_provisioned', 'significantly_over_provisioned']:
            # Recommend downsizing
            for candidate in suitable_types[:3]:
                if candidate['cost_per_hour'] < current_specs['cost_per_hour']:
                    recommendations.append({
                        **candidate,
                        'action': 'downsize',
                        'priority': 'high' if status == 'significantly_over_provisioned' else 'medium',
                        'reason': f"Current utilization is low (CPU: {cpu_stats['p95']:.1f}%, Memory: {memory_stats['p95']:.1f}%)"
                    })

        elif status == 'under_provisioned':
            # Recommend upsizing
            for candidate in suitable_types:
                if candidate['cost_per_hour'] > current_specs['cost_per_hour']:
                    recommendations.append({
                        **candidate,
                        'action': 'upsize',
                        'priority': 'high',
                        'reason': f"Current utilization is high (CPU: {cpu_stats['p95']:.1f}%, Memory: {memory_stats['p95']:.1f}%)"
                    })
                    break  # Only recommend one upsize option

        else:
            # Well-provisioned
            recommendations.append({
                'instance_type': current_type,
                **current_specs,
                'cost_per_month': current_specs['cost_per_hour'] * 730,
                'cost_difference': 0,
                'savings_pct': 0,
                'is_current': True,
                'action': 'keep',
                'priority': 'low',
                'reason': f"Current sizing is appropriate (CPU: {cpu_stats['p95']:.1f}%, Memory: {memory_stats['p95']:.1f}%)"
            })

        return recommendations[:3] if recommendations else []

    def _calculate_savings(
        self,
        current_specs: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        hours_per_month: int = 730
    ) -> Dict[str, Any]:
        """Calculate potential cost savings."""
        if not recommendations:
            return {
                'potential_monthly_savings': 0,
                'potential_annual_savings': 0,
                'savings_percentage': 0
            }

        # Get best recommendation (highest savings)
        best_rec = max(
            [r for r in recommendations if not r.get('is_current', False)],
            key=lambda x: x.get('savings_pct', 0),
            default=None
        )

        if not best_rec:
            return {
                'potential_monthly_savings': 0,
                'potential_annual_savings': 0,
                'savings_percentage': 0
            }

        monthly_savings = (current_specs['cost_per_hour'] - best_rec['cost_per_hour']) * hours_per_month
        annual_savings = monthly_savings * 12
        savings_pct = (monthly_savings / (current_specs['cost_per_hour'] * hours_per_month) * 100) if current_specs['cost_per_hour'] > 0 else 0

        return {
            'potential_monthly_savings': float(monthly_savings),
            'potential_annual_savings': float(annual_savings),
            'savings_percentage': float(savings_pct),
            'recommended_instance': best_rec['instance_type']
        }

    def analyze_multiple_resources(
        self,
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze multiple resources and aggregate results.

        Args:
            resources: List of resource data with utilization

        Returns:
            Aggregated analysis results
        """
        try:
            results = []
            total_current_cost = 0
            total_potential_savings = 0
            status_counts = {
                'over_provisioned': 0,
                'significantly_over_provisioned': 0,
                'under_provisioned': 0,
                'well_provisioned': 0
            }

            for resource in resources:
                analysis = self.analyze_resource(
                    resource_id=resource['resource_id'],
                    resource_type=resource.get('resource_type', 'instance'),
                    current_instance_type=resource['instance_type'],
                    utilization_data=resource['utilization_data'],
                    cloud_provider=resource.get('cloud_provider', 'aws')
                )

                if analysis['success']:
                    results.append(analysis)
                    total_current_cost += analysis['current_instance']['cost_per_month']
                    total_potential_savings += analysis['savings']['potential_monthly_savings']
                    status = analysis['status']
                    if status in status_counts:
                        status_counts[status] += 1

            # Calculate aggregate statistics
            total_savings_pct = (total_potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0

            return {
                'success': True,
                'total_resources': len(results),
                'current_monthly_cost': total_current_cost,
                'potential_monthly_savings': total_potential_savings,
                'potential_annual_savings': total_potential_savings * 12,
                'savings_percentage': total_savings_pct,
                'provisioning_summary': status_counts,
                'resources': results,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Multi-resource analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  Resource Right-Sizing Test")
    print("  Phase 4 - Advanced Intelligence")
    print("=" * 60)

    # Generate sample utilization data
    np.random.seed(42)
    dates = pd.date_range(start='2026-04-01', end='2026-04-30', freq='h')

    # Simulate under-utilized instance
    utilization_data = [
        {
            'timestamp': date,
            'cpu_percent': np.random.normal(25, 5),  # Low CPU usage
            'memory_percent': np.random.normal(30, 8)  # Low memory usage
        }
        for date in dates
    ]

    # Initialize analyzer
    analyzer = RightSizingAnalyzer()

    # Analyze single resource
    print("\n[1] Analyzing single resource (m5.xlarge)...")
    analysis = analyzer.analyze_resource(
        resource_id='i-1234567890',
        resource_type='ec2_instance',
        current_instance_type='m5.xlarge',
        utilization_data=utilization_data,
        cloud_provider='aws'
    )

    if analysis['success']:
        print(f"[PASS] Analysis complete:")
        print(f"\n   Current Instance:")
        print(f"   Type: {analysis['current_instance']['type']}")
        print(f"   vCPU: {analysis['current_instance']['vcpu']}")
        print(f"   Memory: {analysis['current_instance']['memory_gb']} GB")
        print(f"   Cost: ${analysis['current_instance']['cost_per_month']:.2f}/month")

        print(f"\n   Utilization:")
        print(f"   CPU - Mean: {analysis['utilization']['cpu']['mean']:.1f}%, "
              f"P95: {analysis['utilization']['cpu']['p95']:.1f}%, "
              f"Max: {analysis['utilization']['cpu']['max']:.1f}%")
        print(f"   Memory - Mean: {analysis['utilization']['memory']['mean']:.1f}%, "
              f"P95: {analysis['utilization']['memory']['p95']:.1f}%, "
              f"Max: {analysis['utilization']['memory']['max']:.1f}%")

        print(f"\n   Status: {analysis['status']}")

        print(f"\n   Recommendations:")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"   {i}. {rec['instance_type']} - ${rec['cost_per_month']:.2f}/month "
                  f"({rec['savings_pct']:+.1f}%) - {rec['action']}")
            print(f"      {rec['reason']}")

        print(f"\n   Potential Savings:")
        print(f"   Monthly: ${analysis['savings']['potential_monthly_savings']:.2f}")
        print(f"   Annual: ${analysis['savings']['potential_annual_savings']:.2f}")
        print(f"   Percentage: {analysis['savings']['savings_percentage']:.1f}%")

    # Analyze multiple resources
    print("\n[2] Analyzing multiple resources...")
    resources = [
        {
            'resource_id': 'i-001',
            'instance_type': 'm5.xlarge',
            'utilization_data': utilization_data
        },
        {
            'resource_id': 'i-002',
            'instance_type': 'm5.2xlarge',
            'utilization_data': utilization_data
        },
        {
            'resource_id': 'i-003',
            'instance_type': 'c5.xlarge',
            'utilization_data': utilization_data
        }
    ]

    multi_analysis = analyzer.analyze_multiple_resources(resources)

    if multi_analysis['success']:
        print(f"[PASS] Multi-resource analysis:")
        print(f"   Total resources: {multi_analysis['total_resources']}")
        print(f"   Current monthly cost: ${multi_analysis['current_monthly_cost']:.2f}")
        print(f"   Potential monthly savings: ${multi_analysis['potential_monthly_savings']:.2f}")
        print(f"   Potential annual savings: ${multi_analysis['potential_annual_savings']:.2f}")
        print(f"   Savings percentage: {multi_analysis['savings_percentage']:.1f}%")
        print(f"\n   Provisioning Summary:")
        for status, count in multi_analysis['provisioning_summary'].items():
            if count > 0:
                print(f"   - {status}: {count} resources")

    print("\n[PASS] Right-Sizing Analysis Test Complete")
    print("\n" + "=" * 60)
