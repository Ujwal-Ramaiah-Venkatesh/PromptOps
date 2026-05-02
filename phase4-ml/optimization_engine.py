"""
Optimization Automation Engine
===============================

Automated scanning and optimization recommendations.
Phase 4 - Advanced Intelligence

Author: PromptOps Team
Date: 2026-05-01
Phase: 4 - Advanced Intelligence
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """
    Automated optimization scanning and recommendations.

    Features:
    - Idle resource detection
    - Unused resource identification
    - Auto-shutdown candidates
    - Tag compliance checking
    - Consolidated optimization reports
    """

    def __init__(self):
        """Initialize optimization engine."""
        logger.info("Optimization Engine initialized")

    def scan_idle_resources(
        self,
        resources: List[Dict[str, Any]],
        idle_threshold_days: int = 7
    ) -> Dict[str, Any]:
        """
        Scan for idle resources (low/no utilization).

        Args:
            resources: List of resources with utilization data
            idle_threshold_days: Days of inactivity to consider idle

        Returns:
            Idle resources and recommendations
        """
        try:
            idle_resources = []
            potential_savings = 0

            for resource in resources:
                # Check if resource has utilization data
                if 'utilization_data' not in resource:
                    continue

                # Calculate average utilization
                util_data = resource['utilization_data']
                if not util_data:
                    continue

                df = pd.DataFrame(util_data)
                avg_cpu = df['cpu_percent'].mean() if 'cpu_percent' in df.columns else 0
                avg_memory = df['memory_percent'].mean() if 'memory_percent' in df.columns else 0

                # Idle criteria: <5% CPU and <10% memory for threshold period
                if avg_cpu < 5 and avg_memory < 10:
                    cost_per_month = resource.get('cost_per_month', 0)
                    potential_savings += cost_per_month

                    idle_resources.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource.get('resource_type', 'unknown'),
                        'resource_name': resource.get('name', 'unnamed'),
                        'cloud_provider': resource.get('cloud_provider', 'unknown'),
                        'avg_cpu_percent': float(avg_cpu),
                        'avg_memory_percent': float(avg_memory),
                        'cost_per_month': cost_per_month,
                        'idle_days': len(df) / 24 if 'timestamp' in df.columns else 0,
                        'recommendation': 'Terminate or stop resource',
                        'priority': 'high' if cost_per_month > 50 else 'medium'
                    })

            return {
                'success': True,
                'idle_resources_count': len(idle_resources),
                'potential_monthly_savings': potential_savings,
                'potential_annual_savings': potential_savings * 12,
                'idle_resources': sorted(idle_resources, key=lambda x: x['cost_per_month'], reverse=True),
                'summary': f"Found {len(idle_resources)} idle resources with ${potential_savings:.2f}/month potential savings"
            }

        except Exception as e:
            logger.error(f"Idle resource scan failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def scan_unused_resources(
        self,
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scan for unused resources (unattached volumes, unused IPs, etc.).

        Args:
            resources: List of all resources

        Returns:
            Unused resources and recommendations
        """
        try:
            unused_resources = []
            potential_savings = 0

            for resource in resources:
                resource_type = resource.get('resource_type', '')
                status = resource.get('status', '').lower()

                # Check for unattached volumes
                if 'volume' in resource_type.lower() or 'disk' in resource_type.lower():
                    if status in ['available', 'unattached', 'detached']:
                        cost = resource.get('cost_per_month', 0)
                        potential_savings += cost

                        unused_resources.append({
                            'resource_id': resource['resource_id'],
                            'resource_type': resource_type,
                            'resource_name': resource.get('name', 'unnamed'),
                            'cloud_provider': resource.get('cloud_provider', 'unknown'),
                            'status': status,
                            'cost_per_month': cost,
                            'recommendation': 'Delete unattached volume',
                            'priority': 'high'
                        })

                # Check for unused elastic IPs (AWS) or static IPs
                elif 'ip' in resource_type.lower() or 'address' in resource_type.lower():
                    if not resource.get('attached_to'):
                        cost = resource.get('cost_per_month', 0)
                        potential_savings += cost

                        unused_resources.append({
                            'resource_id': resource['resource_id'],
                            'resource_type': resource_type,
                            'resource_name': resource.get('name', 'unnamed'),
                            'cloud_provider': resource.get('cloud_provider', 'unknown'),
                            'status': 'unattached',
                            'cost_per_month': cost,
                            'recommendation': 'Release unused IP address',
                            'priority': 'medium'
                        })

                # Check for old snapshots
                elif 'snapshot' in resource_type.lower():
                    created_date = resource.get('created_date')
                    if created_date:
                        age_days = (datetime.now() - pd.to_datetime(created_date)).days
                        if age_days > 90:  # Older than 90 days
                            cost = resource.get('cost_per_month', 0)
                            potential_savings += cost

                            unused_resources.append({
                                'resource_id': resource['resource_id'],
                                'resource_type': resource_type,
                                'resource_name': resource.get('name', 'unnamed'),
                                'cloud_provider': resource.get('cloud_provider', 'unknown'),
                                'age_days': age_days,
                                'cost_per_month': cost,
                                'recommendation': f'Delete snapshot older than {age_days} days',
                                'priority': 'low'
                            })

            return {
                'success': True,
                'unused_resources_count': len(unused_resources),
                'potential_monthly_savings': potential_savings,
                'potential_annual_savings': potential_savings * 12,
                'unused_resources': sorted(unused_resources, key=lambda x: x['cost_per_month'], reverse=True),
                'summary': f"Found {len(unused_resources)} unused resources with ${potential_savings:.2f}/month potential savings"
            }

        except Exception as e:
            logger.error(f"Unused resource scan failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def recommend_auto_shutdown(
        self,
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify resources that are candidates for auto-shutdown schedules.

        Args:
            resources: List of resources

        Returns:
            Auto-shutdown candidates and potential savings
        """
        try:
            candidates = []
            potential_savings = 0

            for resource in resources:
                # Only consider compute resources
                resource_type = resource.get('resource_type', '').lower()
                if not any(t in resource_type for t in ['instance', 'vm', 'virtual_machine']):
                    continue

                # Check tags for environment
                tags = resource.get('tags', {})
                environment = tags.get('environment', tags.get('env', 'unknown')).lower()

                # Dev/test/staging environments are candidates
                if environment in ['dev', 'development', 'test', 'testing', 'staging', 'qa']:
                    cost_per_month = resource.get('cost_per_month', 0)

                    # Assume 12 hours/day usage (50% savings)
                    monthly_savings = cost_per_month * 0.5
                    potential_savings += monthly_savings

                    candidates.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource['resource_type'],
                        'resource_name': resource.get('name', 'unnamed'),
                        'cloud_provider': resource.get('cloud_provider', 'unknown'),
                        'environment': environment,
                        'current_cost_per_month': cost_per_month,
                        'potential_monthly_savings': monthly_savings,
                        'recommendation': 'Implement auto-shutdown schedule (e.g., 7pm-7am, weekends)',
                        'priority': 'high' if cost_per_month > 100 else 'medium',
                        'suggested_schedule': {
                            'weekday': 'Stop at 19:00, Start at 07:00',
                            'weekend': 'Stop all day',
                            'savings_pct': 50
                        }
                    })

            return {
                'success': True,
                'candidates_count': len(candidates),
                'potential_monthly_savings': potential_savings,
                'potential_annual_savings': potential_savings * 12,
                'candidates': sorted(candidates, key=lambda x: x['potential_monthly_savings'], reverse=True),
                'summary': f"Found {len(candidates)} auto-shutdown candidates with ${potential_savings:.2f}/month potential savings"
            }

        except Exception as e:
            logger.error(f"Auto-shutdown scan failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_tag_compliance(
        self,
        resources: List[Dict[str, Any]],
        required_tags: List[str] = ['environment', 'owner', 'project']
    ) -> Dict[str, Any]:
        """
        Check tagging compliance for cost allocation.

        Args:
            resources: List of resources
            required_tags: List of required tag keys

        Returns:
            Tagging compliance report
        """
        try:
            untagged_resources = []
            partially_tagged = []
            compliant = []

            for resource in resources:
                tags = resource.get('tags', {})
                tag_keys = [k.lower() for k in tags.keys()]

                missing_tags = [tag for tag in required_tags if tag.lower() not in tag_keys]

                if len(missing_tags) == len(required_tags):
                    # No required tags
                    untagged_resources.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource.get('resource_type', 'unknown'),
                        'resource_name': resource.get('name', 'unnamed'),
                        'cloud_provider': resource.get('cloud_provider', 'unknown'),
                        'existing_tags': len(tags),
                        'missing_tags': missing_tags,
                        'recommendation': f'Add tags: {", ".join(missing_tags)}',
                        'priority': 'high'
                    })
                elif len(missing_tags) > 0:
                    # Some required tags missing
                    partially_tagged.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource.get('resource_type', 'unknown'),
                        'resource_name': resource.get('name', 'unnamed'),
                        'cloud_provider': resource.get('cloud_provider', 'unknown'),
                        'existing_tags': len(tags),
                        'missing_tags': missing_tags,
                        'recommendation': f'Add missing tags: {", ".join(missing_tags)}',
                        'priority': 'medium'
                    })
                else:
                    # All required tags present
                    compliant.append(resource['resource_id'])

            compliance_rate = (len(compliant) / len(resources) * 100) if resources else 0

            return {
                'success': True,
                'total_resources': len(resources),
                'compliant_resources': len(compliant),
                'partially_tagged': len(partially_tagged),
                'untagged_resources': len(untagged_resources),
                'compliance_rate': compliance_rate,
                'required_tags': required_tags,
                'untagged': untagged_resources[:20],  # Top 20
                'partially_tagged': partially_tagged[:20],
                'summary': f"Tag compliance: {compliance_rate:.1f}% ({len(compliant)}/{len(resources)} resources)"
            }

        except Exception as e:
            logger.error(f"Tag compliance check failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_optimization_report(
        self,
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report.

        Args:
            resources: List of all resources

        Returns:
            Complete optimization report
        """
        try:
            # Run all scans
            idle_scan = self.scan_idle_resources(resources)
            unused_scan = self.scan_unused_resources(resources)
            shutdown_scan = self.recommend_auto_shutdown(resources)
            tag_scan = self.check_tag_compliance(resources)

            # Calculate total potential savings
            total_savings = (
                idle_scan.get('potential_monthly_savings', 0) +
                unused_scan.get('potential_monthly_savings', 0) +
                shutdown_scan.get('potential_monthly_savings', 0)
            )

            # Compile all recommendations
            all_recommendations = []

            if idle_scan['success']:
                for item in idle_scan['idle_resources']:
                    all_recommendations.append({
                        'category': 'idle_resources',
                        'priority': item['priority'],
                        'savings': item['cost_per_month'],
                        **item
                    })

            if unused_scan['success']:
                for item in unused_scan['unused_resources']:
                    all_recommendations.append({
                        'category': 'unused_resources',
                        'priority': item['priority'],
                        'savings': item['cost_per_month'],
                        **item
                    })

            if shutdown_scan['success']:
                for item in shutdown_scan['candidates']:
                    all_recommendations.append({
                        'category': 'auto_shutdown',
                        'priority': item['priority'],
                        'savings': item['potential_monthly_savings'],
                        **item
                    })

            # Sort by savings (highest first)
            all_recommendations.sort(key=lambda x: x.get('savings', 0), reverse=True)

            return {
                'success': True,
                'generated_at': datetime.utcnow().isoformat(),
                'total_resources_analyzed': len(resources),
                'total_potential_monthly_savings': total_savings,
                'total_potential_annual_savings': total_savings * 12,
                'scans': {
                    'idle_resources': idle_scan,
                    'unused_resources': unused_scan,
                    'auto_shutdown_candidates': shutdown_scan,
                    'tag_compliance': tag_scan
                },
                'top_recommendations': all_recommendations[:20],  # Top 20 by savings
                'summary': {
                    'total_issues': sum([
                        idle_scan.get('idle_resources_count', 0),
                        unused_scan.get('unused_resources_count', 0),
                        shutdown_scan.get('candidates_count', 0)
                    ]),
                    'high_priority': len([r for r in all_recommendations if r['priority'] == 'high']),
                    'medium_priority': len([r for r in all_recommendations if r['priority'] == 'medium']),
                    'low_priority': len([r for r in all_recommendations if r['priority'] == 'low'])
                }
            }

        except Exception as e:
            logger.error(f"Optimization report generation failed: {e}")
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
    print("  Optimization Engine Test")
    print("  Phase 4 - Advanced Intelligence")
    print("=" * 60)

    # Generate sample resources
    sample_resources = [
        {
            'resource_id': 'i-001',
            'resource_type': 'ec2_instance',
            'name': 'dev-server-1',
            'cloud_provider': 'aws',
            'cost_per_month': 140,
            'tags': {'environment': 'dev', 'owner': 'team-a'},
            'utilization_data': [
                {'cpu_percent': 2, 'memory_percent': 5} for _ in range(168)
            ]
        },
        {
            'resource_id': 'vol-001',
            'resource_type': 'ebs_volume',
            'name': 'unused-volume',
            'cloud_provider': 'aws',
            'status': 'available',
            'cost_per_month': 20
        },
        {
            'resource_id': 'i-002',
            'resource_type': 'ec2_instance',
            'name': 'test-server-1',
            'cloud_provider': 'aws',
            'cost_per_month': 200,
            'tags': {'environment': 'test'}
        },
        {
            'resource_id': 'snap-001',
            'resource_type': 'snapshot',
            'name': 'old-backup',
            'cloud_provider': 'aws',
            'created_date': '2025-10-01',
            'cost_per_month': 5
        },
        {
            'resource_id': 'i-003',
            'resource_type': 'ec2_instance',
            'name': 'prod-server',
            'cloud_provider': 'aws',
            'cost_per_month': 300,
            'tags': {'environment': 'production', 'owner': 'team-b', 'project': 'app1'}
        }
    ]

    # Initialize engine
    engine = OptimizationEngine()

    # Generate full report
    print("\n[1] Generating optimization report...")
    report = engine.generate_optimization_report(sample_resources)

    if report['success']:
        print(f"[PASS] Optimization Report Generated:")
        print(f"\n   Total Resources Analyzed: {report['total_resources_analyzed']}")
        print(f"   Potential Monthly Savings: ${report['total_potential_monthly_savings']:.2f}")
        print(f"   Potential Annual Savings: ${report['total_potential_annual_savings']:.2f}")

        print(f"\n   Issues Found:")
        print(f"   - Total: {report['summary']['total_issues']}")
        print(f"   - High Priority: {report['summary']['high_priority']}")
        print(f"   - Medium Priority: {report['summary']['medium_priority']}")
        print(f"   - Low Priority: {report['summary']['low_priority']}")

        print(f"\n   Scan Results:")
        print(f"   - Idle Resources: {report['scans']['idle_resources']['idle_resources_count']}")
        print(f"   - Unused Resources: {report['scans']['unused_resources']['unused_resources_count']}")
        print(f"   - Auto-Shutdown Candidates: {report['scans']['auto_shutdown_candidates']['candidates_count']}")
        print(f"   - Tag Compliance: {report['scans']['tag_compliance']['compliance_rate']:.1f}%")

        print(f"\n   Top 3 Recommendations:")
        for i, rec in enumerate(report['top_recommendations'][:3], 1):
            print(f"   {i}. [{rec['category']}] {rec['resource_name']} - "
                  f"${rec['savings']:.2f}/month - {rec['recommendation']}")

        print("\n[PASS] Optimization Engine Test Complete")
    else:
        print(f"\n[FAIL] Test failed: {report.get('error')}")

    print("\n" + "=" * 60)
